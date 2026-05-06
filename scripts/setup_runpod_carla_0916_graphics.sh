#!/usr/bin/env bash
set -euo pipefail

CARLA_ROOT="${CARLA_ROOT:-/workspace/carla}"
CARLA_DIR="${CARLA_DIR:-${CARLA_ROOT}/CARLA_0.9.16}"
CARLA_TAR="${CARLA_TAR:-${CARLA_ROOT}/CARLA_0.9.16.tar.gz}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-/workspace/driverx_remote_artifacts}"
ICD="${DRIVERX_NVIDIA_VULKAN_ICD:-${CARLA_ROOT}/nvidia_icd.json}"
PORT="${CARLA_PORT:-2000}"
PYTHON_VENV="${DRIVERX_RUNPOD_PYTHON_VENV:-/workspace/driverx_py312}"
LOG_PREFIX="[driverx-carla-setup]"

mkdir -p "${CARLA_ROOT}" "${ARTIFACT_ROOT}"
export PATH="${HOME}/.local/bin:${PATH}"

cat > "${ICD}" <<'JSON'
{
  "file_format_version": "1.0.0",
  "ICD": {"library_path": "libGLX_nvidia.so.0", "api_version": "1.3.0"}
}
JSON

echo "${LOG_PREFIX} installing packages"
sudo apt-get update -y >/tmp/driverx_apt_update.log 2>&1 || true
sudo apt-get install -y \
  vulkan-tools \
  python3-pip \
  python3-venv \
  psmisc \
  procps \
  curl \
  ffmpeg \
  tar \
  gzip \
  libomp5 \
  libpng16-16 \
  libtiff5 \
  >/tmp/driverx_apt_install.log 2>&1 || {
    tail -100 /tmp/driverx_apt_install.log
    exit 1
  }

echo "${LOG_PREFIX} probing NVIDIA Vulkan"
DISPLAY= VK_ICD_FILENAMES="${ICD}" timeout 30s vulkaninfo \
  > "${ARTIFACT_ROOT}/vulkaninfo_nvidia.txt" 2>&1 || true
grep -E 'deviceName|apiVersion|driverVersion|NVIDIA RTX' \
  "${ARTIFACT_ROOT}/vulkaninfo_nvidia.txt" | head -40 || true

if [[ ! -s "${CARLA_TAR}" ]]; then
  echo "${LOG_PREFIX} downloading CARLA 0.9.16 tarball"
  curl -L --fail --retry 5 --retry-delay 10 -C - \
    -o "${CARLA_TAR}" \
    https://carla-releases.s3.us-east-005.backblazeb2.com/Linux/CARLA_0.9.16.tar.gz
fi

if [[ ! -x "${CARLA_DIR}/CarlaUE4.sh" ]]; then
  echo "${LOG_PREFIX} extracting CARLA"
  rm -rf "${CARLA_DIR}"
  mkdir -p "${CARLA_DIR}"
  tar -xzf "${CARLA_TAR}" -C "${CARLA_DIR}"
  chmod +x "${CARLA_DIR}/CarlaUE4.sh" || true
fi

if [[ ! -x "${CARLA_DIR}/CarlaUE4.sh" ]]; then
  echo "${LOG_PREFIX} CARLA launcher missing after extraction: ${CARLA_DIR}/CarlaUE4.sh" >&2
  echo "${LOG_PREFIX} archive head:" >&2
  tar -tzf "${CARLA_TAR}" | head -30 >&2 || true
  exit 2
fi

echo "${LOG_PREFIX} installing CARLA PythonAPI"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi
uv python install 3.12 >/tmp/driverx_uv_python.log 2>&1
uv venv --python 3.12 "${PYTHON_VENV}" >/tmp/driverx_uv_venv.log 2>&1
WHL="$(find "${CARLA_DIR}/PythonAPI/carla/dist" -name 'carla-*.whl' | head -1 || true)"
if [[ -f "${CARLA_DIR}/PythonAPI/carla/dist/carla-0.9.16-cp312-cp312-manylinux_2_31_x86_64.whl" ]]; then
  WHL="${CARLA_DIR}/PythonAPI/carla/dist/carla-0.9.16-cp312-cp312-manylinux_2_31_x86_64.whl"
fi
if [[ -z "${WHL}" ]]; then
  echo "${LOG_PREFIX} no CARLA wheel found under ${CARLA_DIR}/PythonAPI/carla/dist" >&2
  exit 2
fi
uv pip install --python "${PYTHON_VENV}/bin/python" "${WHL}" >/tmp/driverx_carla_pip.log 2>&1 || {
  tail -100 /tmp/driverx_carla_pip.log
  exit 1
}
uv pip install --python "${PYTHON_VENV}/bin/python" pillow >/tmp/driverx_pillow_pip.log 2>&1 || {
  tail -100 /tmp/driverx_pillow_pip.log
  exit 1
}
"${PYTHON_VENV}/bin/python" - <<'PY'
import carla
from PIL import Image
print("carla_import_ok", getattr(carla, "__version__", "unknown"))
print("pillow_import_ok", Image.__module__)
PY

echo "${LOG_PREFIX} launching CARLA smoke server on port ${PORT}"
pkill -f CarlaUE4 || true
cd "${CARLA_DIR}"
DISPLAY= VK_ICD_FILENAMES="${ICD}" ./CarlaUE4.sh \
  -RenderOffScreen \
  -nosound \
  -quality-level=Low \
  "-carla-port=${PORT}" \
  > "${ARTIFACT_ROOT}/carla_server_smoke.log" 2>&1 &
echo $! > "${ARTIFACT_ROOT}/carla_server_smoke.pid"

echo "${LOG_PREFIX} waiting for port ${PORT}"
"${PYTHON_VENV}/bin/python" - <<PY
import socket
import sys
import time

port = int("${PORT}")
for attempt in range(90):
    sock = socket.socket()
    sock.settimeout(1)
    try:
        sock.connect(("127.0.0.1", port))
        print("port_open", attempt)
        sys.exit(0)
    except Exception:
        time.sleep(2)
    finally:
        sock.close()
print("port_not_open")
sys.exit(1)
PY

"${PYTHON_VENV}/bin/python" - <<PY
import carla

client = carla.Client("127.0.0.1", int("${PORT}"))
client.set_timeout(20)
world = client.get_world()
print("connected_map", world.get_map().name)
print("actors", len(world.get_actors()))
PY

echo "${LOG_PREFIX} done"
