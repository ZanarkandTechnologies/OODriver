#!/usr/bin/env bash
set -euo pipefail

REMOTE_ROOT="${REMOTE_ROOT:-/workspace}"
REMOTE_RUN_ID="${REMOTE_RUN_ID:-task20}"
DRIVERX_ROOT="${DRIVERX_ROOT:-${REMOTE_ROOT}/0xDriver}"
EXTERNAL_ROOT="${EXTERNAL_ROOT:-${REMOTE_ROOT}/external}"
SIMLINGO_ROOT="${SIMLINGO_ROOT:-${EXTERNAL_ROOT}/simlingo}"
CARLA_ROOT="${CARLA_ROOT:-${REMOTE_ROOT}/software/carla0915}"
MODEL_ROOT="${MODEL_ROOT:-${REMOTE_ROOT}/models/simlingo}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-${REMOTE_ROOT}/artifacts/${REMOTE_RUN_ID}}"
MINIFORGE_ROOT="${MINIFORGE_ROOT:-${REMOTE_ROOT}/conda}"
MINIFORGE_URL="${MINIFORGE_URL:-https://github.com/conda-forge/miniforge/releases/download/25.9.1-0/Miniforge3-25.9.1-0-Linux-x86_64.sh}"
CONDA_ENV="${CONDA_ENV:-simlingo}"
DRIVERX_PYTHON="${DRIVERX_PYTHON:-/usr/bin/python3}"
RUNTIME_USER="${RUNTIME_USER:-driverx}"
SIMLINGO_REF="${SIMLINGO_REF:-743b243afd6cf5ff51b9fa1f8cac86f22d569684}"
HF_REVISION="${HF_REVISION:-26c7c89e797d4e25bbf640013317af8da26a5454}"
ROUTE_PATH="${ROUTE_PATH:-leaderboard/data/bench2drive_split/bench2drive_00.xml}"
CHECKPOINT_RELATIVE_PATH="${CHECKPOINT_RELATIVE_PATH:-simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt}"
CHECKPOINT_PATH="${CHECKPOINT_PATH:-${MODEL_ROOT}/${CHECKPOINT_RELATIVE_PATH}}"

ensure_carla_compat_layout() {
  if [ -x "${CARLA_ROOT}/CarlaUE4.sh" ]; then
    chmod +x "${CARLA_ROOT}/CarlaUE4.sh"
  elif [ -x "${CARLA_ROOT}/Binaries/Linux/CarlaUE4-Linux-Shipping" ]; then
    cat > "${CARLA_ROOT}/CarlaUE4.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LD_LIBRARY_PATH="${root}/Binaries/Linux:${root}/Binaries/ThirdParty/PhysX3/Linux/x86_64-unknown-linux-gnu:${LD_LIBRARY_PATH:-}"
cd "${root}"
exec "${root}/Binaries/Linux/CarlaUE4-Linux-Shipping" CarlaUE4 "$@"
EOF
    chmod +x "${CARLA_ROOT}/CarlaUE4.sh"
  fi

  if [ -d "${CARLA_ROOT}/carla" ] && [ ! -e "${CARLA_ROOT}/PythonAPI/carla" ]; then
    mkdir -p "${CARLA_ROOT}/PythonAPI"
    ln -s "${CARLA_ROOT}/carla" "${CARLA_ROOT}/PythonAPI/carla"
  fi
}

carla_python_path() {
  paths=()
  [ -d "${CARLA_ROOT}/PythonAPI" ] && paths+=("${CARLA_ROOT}/PythonAPI")
  [ -d "${CARLA_ROOT}/PythonAPI/carla" ] && paths+=("${CARLA_ROOT}/PythonAPI/carla")
  [ -d "${CARLA_ROOT}/carla" ] && paths+=("${CARLA_ROOT}/carla")
  while IFS= read -r egg; do
    paths+=("${egg}")
  done < <(find "${CARLA_ROOT}" -path "*/carla/dist/carla-0.9.15*py3*linux-x86_64.egg" -type f 2>/dev/null | sort)
  (IFS=:; printf "%s" "${paths[*]}")
}

prepare_runtime_user() {
  if [ "$(id -u)" -ne 0 ]; then
    return 0
  fi
  if ! id "${RUNTIME_USER}" >/dev/null 2>&1; then
    useradd -m -s /bin/bash "${RUNTIME_USER}"
  fi
  chmod a+x \
    "${REMOTE_ROOT}" \
    "${REMOTE_ROOT}/artifacts" \
    "${EXTERNAL_ROOT}" \
    "${REMOTE_ROOT}/models" \
    "${REMOTE_ROOT}/software" \
    2>/dev/null || true
  chmod -R a+rX "${MINIFORGE_ROOT}"
  chown -R "${RUNTIME_USER}:${RUNTIME_USER}" \
    "${ARTIFACT_ROOT}" \
    "${MODEL_ROOT}" \
    "${SIMLINGO_ROOT}" \
    "${CARLA_ROOT}"
}

mkdir -p "${EXTERNAL_ROOT}" "${MODEL_ROOT}" "${ARTIFACT_ROOT}" "${REMOTE_ROOT}/software"
exec > >(tee -a "${ARTIFACT_ROOT}/bootstrap.log") 2>&1

echo "== remote SimLingo bootstrap =="
date -Is
echo "run_id=${REMOTE_RUN_ID}"
echo "driverx=${DRIVERX_ROOT}"
echo "simlingo=${SIMLINGO_ROOT}"
echo "carla=${CARLA_ROOT}"
echo "model_root=${MODEL_ROOT}"

echo "== apt prerequisites =="
if command -v vulkaninfo >/dev/null 2>&1 && command -v ffmpeg >/dev/null 2>&1; then
  echo "apt prerequisites already available; skipping apt"
else
  timeout 180 apt-get update || echo "apt-get update timed out or failed; continuing with existing package state"
  timeout 300 env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git wget curl rsync ca-certificates bzip2 unzip tmux screen \
    libvulkan1 vulkan-tools mesa-vulkan-drivers \
    libomp5 libjpeg-turbo8 libpng16-16 libtiff5 libglib2.0-0 \
    libsm6 libxext6 libxrender1 libgl1 ffmpeg \
    || echo "apt prerequisite install failed; continuing until a concrete runtime blocker appears"
fi

echo "== miniforge =="
if [ ! -x "${MINIFORGE_ROOT}/bin/conda" ]; then
  curl -L -o /tmp/miniforge.sh "${MINIFORGE_URL}"
  bash /tmp/miniforge.sh -b -p "${MINIFORGE_ROOT}"
fi
source "${MINIFORGE_ROOT}/etc/profile.d/conda.sh"
conda config --set auto_activate_base false
conda --version

echo "== simlingo checkout =="
git config --global --add safe.directory "${SIMLINGO_ROOT}" || true
if [ ! -d "${SIMLINGO_ROOT}/.git" ]; then
  git clone https://github.com/RenzKa/simlingo.git "${SIMLINGO_ROOT}"
else
  git -C "${SIMLINGO_ROOT}" fetch --all --prune
fi
git -C "${SIMLINGO_ROOT}" checkout --detach "${SIMLINGO_REF}"
git -C "${SIMLINGO_ROOT}" rev-parse HEAD

echo "== carla 0.9.15 =="
ensure_carla_compat_layout
tmp_tar="${REMOTE_ROOT}/software/CARLA_0.9.15.tar.gz"
if [ ! -x "${CARLA_ROOT}/CarlaUE4.sh" ] || [ ! -d "${CARLA_ROOT}/Engine/Content" ] || [ ! -d "${CARLA_ROOT}/PythonAPI/carla" ]; then
  mkdir -p "${CARLA_ROOT}"
  wget -c -O "${tmp_tar}" \
    https://carla-releases.s3.us-east-005.backblazeb2.com/Linux/CARLA_0.9.15.tar.gz
  find "${CARLA_ROOT}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  tar --no-same-owner -xzf "${tmp_tar}" -C "${CARLA_ROOT}"
  ensure_carla_compat_layout
fi
if [ ! -d "${CARLA_ROOT}/Import/AdditionalMaps_0.9.15" ] && [ ! -f "${CARLA_ROOT}/Import/AdditionalMaps_0.9.15.tar.gz.done" ]; then
  mkdir -p "${CARLA_ROOT}/Import"
  wget -c -O "${CARLA_ROOT}/Import/AdditionalMaps_0.9.15.tar.gz" \
    https://carla-releases.s3.us-east-005.backblazeb2.com/Linux/AdditionalMaps_0.9.15.tar.gz
  (cd "${CARLA_ROOT}" && tar --no-same-owner --keep-newer-files -xzf "Import/AdditionalMaps_0.9.15.tar.gz")
  ensure_carla_compat_layout
  touch "${CARLA_ROOT}/Import/AdditionalMaps_0.9.15.tar.gz.done"
fi
echo "carla_server=${CARLA_ROOT}/CarlaUE4.sh"
echo "carla_python_path=$(carla_python_path)"

echo "== simlingo conda env =="
if ! conda env list | awk "{print \$1}" | grep -qx "${CONDA_ENV}"; then
  conda env create -f "${SIMLINGO_ROOT}/environment.yaml"
fi
conda activate "${CONDA_ENV}"
python --version
python - <<'PY'
import sys
print(sys.executable)
PY

echo "== runtime python packages =="
python -m pip install --upgrade pip
python -m pip install "torch==2.2.0" "huggingface-hub==0.27.0"
python -m pip install "flash-attn==2.7.0.post2" --no-build-isolation || echo "flash-attn install failed; continuing to capture blocker"
echo "== torch cuda compatibility =="
python - <<PY
import json
from pathlib import Path
import torch

payload = {
    "torch_version": torch.__version__,
    "torch_cuda": torch.version.cuda,
    "cuda_available": torch.cuda.is_available(),
    "device_name": None,
    "device_capability": None,
    "required_arch": None,
    "compiled_arches": torch.cuda.get_arch_list(),
    "compatible": False,
}
if torch.cuda.is_available():
    capability = torch.cuda.get_device_capability(0)
    required_arch = f"sm_{capability[0]}{capability[1]}"
    payload.update(
        {
            "device_name": torch.cuda.get_device_name(0),
            "device_capability": list(capability),
            "required_arch": required_arch,
            "compatible": required_arch in payload["compiled_arches"],
        }
    )
Path("${ARTIFACT_ROOT}/torch_cuda_compatibility.json").write_text(
    json.dumps(payload, indent=2),
    encoding="utf-8",
)
print(json.dumps(payload, indent=2))
PY

echo "== huggingface checkpoint =="
python - <<PY
import os
from huggingface_hub import snapshot_download
from pathlib import Path
target = Path("${MODEL_ROOT}")
target.mkdir(parents=True, exist_ok=True)
snapshot_download(
    repo_id="RenzKa/simlingo",
    local_dir=str(target),
    revision="${HF_REVISION}",
    token=os.environ.get("HF_TOKEN") or None,
)
checkpoint = Path("${CHECKPOINT_PATH}")
if not checkpoint.exists():
    candidates = sorted(target.rglob("pytorch_model.pt"))
    raise FileNotFoundError(
        f"Expected checkpoint missing: {checkpoint}. Candidates: {[str(path) for path in candidates]}"
    )
print(checkpoint)
PY
printf "%s\n" "${HF_REVISION}" > "${ARTIFACT_ROOT}/model_revision.txt"
sha256sum "${CHECKPOINT_PATH}" > "${ARTIFACT_ROOT}/checkpoint.sha256"
unset HF_TOKEN

echo "== driverx remote checks =="
cd "${DRIVERX_ROOT}"
"${DRIVERX_PYTHON}" -m compileall -q src tests
PYTHONPATH=src "${DRIVERX_PYTHON}" -m unittest discover -s tests
PYTHONPATH=src "${DRIVERX_PYTHON}" -m driverx inspect-simlingo --root "${SIMLINGO_ROOT}" --output-root "${ARTIFACT_ROOT}" --run-id readiness
cat > "${ARTIFACT_ROOT}/simlingo_gpu.yaml" <<EOF
simlingo:
  root: ${SIMLINGO_ROOT}
  checkpoint_path: ${CHECKPOINT_PATH}
  route_path: ${ROUTE_PATH}
  output_dir: ${ARTIFACT_ROOT}
  seed: 1
  world_port: 20000
  traffic_manager_port: 10000
  timeout_s: 600
carla:
  root: ${CARLA_ROOT}
EOF
PYTHONPATH=src "${DRIVERX_PYTHON}" -m driverx plan-simlingo-run \
  --config "${ARTIFACT_ROOT}/simlingo_gpu.yaml" \
  --checkpoint-path "${CHECKPOINT_PATH}" \
  --route-path "${ROUTE_PATH}" \
  --output-root "${ARTIFACT_ROOT}" \
  --run-id plan

echo "== next manual/live command =="
CARLA_PYTHON_PATH_VALUE="$(carla_python_path)"
cat > "${ARTIFACT_ROOT}/start_carla_server.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
mkdir -p "${ARTIFACT_ROOT}/carla"
if [ -f "${ARTIFACT_ROOT}/carla/carla.pid" ] && kill -0 "\$(cat "${ARTIFACT_ROOT}/carla/carla.pid")" 2>/dev/null; then
  echo "CARLA already running with pid \$(cat "${ARTIFACT_ROOT}/carla/carla.pid")"
  exit 0
fi
export SDL_VIDEODRIVER=offscreen
export VK_ICD_FILENAMES="\${VK_ICD_FILENAMES:-}"
nohup "${CARLA_ROOT}/CarlaUE4.sh" -RenderOffScreen -nosound -quality-level=Low -carla-rpc-port=20000 > "${ARTIFACT_ROOT}/carla/carla.log" 2>&1 &
echo "\$!" > "${ARTIFACT_ROOT}/carla/carla.pid"
python - <<'PY'
import socket
import time

deadline = time.time() + 120
last_error = None
while time.time() < deadline:
    try:
        with socket.create_connection(("127.0.0.1", 20000), timeout=2):
            print("CARLA port 20000 is reachable")
            raise SystemExit(0)
    except OSError as exc:
        last_error = exc
        time.sleep(1)
raise SystemExit(f"CARLA did not open port 20000 within 120s: {last_error}")
PY
EOF
chmod +x "${ARTIFACT_ROOT}/start_carla_server.sh"
cat > "${ARTIFACT_ROOT}/stop_carla_server.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
if [ -f "${ARTIFACT_ROOT}/carla/carla.pid" ]; then
  pid="\$(cat "${ARTIFACT_ROOT}/carla/carla.pid")"
  kill "\${pid}" 2>/dev/null || true
  rm -f "${ARTIFACT_ROOT}/carla/carla.pid"
fi
EOF
chmod +x "${ARTIFACT_ROOT}/stop_carla_server.sh"
cat > "${ARTIFACT_ROOT}/run_one_route.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
source "${MINIFORGE_ROOT}/etc/profile.d/conda.sh"
conda activate "${CONDA_ENV}"
cd "${SIMLINGO_ROOT}"
export CARLA_ROOT="${CARLA_ROOT}"
export WORK_DIR="${SIMLINGO_ROOT}"
export SCENARIO_RUNNER_ROOT="${SIMLINGO_ROOT}/Bench2Drive/scenario_runner"
export LEADERBOARD_ROOT="${SIMLINGO_ROOT}/Bench2Drive/leaderboard"
export SAVE_PATH="${ARTIFACT_ROOT}/viz"
export PYTHONPATH="${SIMLINGO_ROOT}:${CARLA_PYTHON_PATH_VALUE}:${SIMLINGO_ROOT}/Bench2Drive/scenario_runner:${SIMLINGO_ROOT}/Bench2Drive/leaderboard:\${PYTHONPATH:-}"
python -u "${SIMLINGO_ROOT}/Bench2Drive/leaderboard/leaderboard/leaderboard_evaluator.py" \\
  --routes="${SIMLINGO_ROOT}/${ROUTE_PATH}" \\
  --repetitions=1 \\
  --track=SENSORS \\
  --checkpoint="${ARTIFACT_ROOT}/res/seed_1_res.json" \\
  --timeout=600 \\
  --agent="${SIMLINGO_ROOT}/team_code/agent_simlingo.py" \\
  --agent-config="${CHECKPOINT_PATH}" \\
  --traffic-manager-seed=1 \\
  --port=20000 \\
  --traffic-manager-port=10000
EOF
chmod +x "${ARTIFACT_ROOT}/run_one_route.sh"
cat > "${ARTIFACT_ROOT}/run_one_route_with_carla.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
bash "${ARTIFACT_ROOT}/start_carla_server.sh"
trap 'bash "${ARTIFACT_ROOT}/stop_carla_server.sh"' EXIT
bash "${ARTIFACT_ROOT}/run_one_route.sh"
EOF
chmod +x "${ARTIFACT_ROOT}/run_one_route_with_carla.sh"
cat > "${ARTIFACT_ROOT}/run_one_route_as_user.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
if [ "\$(id -u)" -eq 0 ]; then
  exec runuser -u "${RUNTIME_USER}" -- env HOME="/home/${RUNTIME_USER}" XDG_CONFIG_HOME="/home/${RUNTIME_USER}/.config" bash -c 'cd "\${HOME}" && exec bash "${ARTIFACT_ROOT}/run_one_route.sh"'
fi
exec bash "${ARTIFACT_ROOT}/run_one_route.sh"
EOF
chmod +x "${ARTIFACT_ROOT}/run_one_route_as_user.sh"
cat > "${ARTIFACT_ROOT}/run_one_route_with_carla_as_user.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
if [ "\$(id -u)" -eq 0 ]; then
  exec runuser -u "${RUNTIME_USER}" -- env HOME="/home/${RUNTIME_USER}" XDG_CONFIG_HOME="/home/${RUNTIME_USER}/.config" bash -c 'cd "\${HOME}" && exec bash "${ARTIFACT_ROOT}/run_one_route_with_carla.sh"'
fi
exec bash "${ARTIFACT_ROOT}/run_one_route_with_carla.sh"
EOF
chmod +x "${ARTIFACT_ROOT}/run_one_route_with_carla_as_user.sh"
prepare_runtime_user

echo "bootstrap complete: ${ARTIFACT_ROOT}"
