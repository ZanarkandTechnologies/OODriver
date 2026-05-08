#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "usage: $0 user@host" >&2
  exit 2
fi

REMOTE="$1"
ENV_FILE="${DRIVERX_ENV_FILE:-.env}"
if [ -f "${ENV_FILE}" ]; then
  set -a
  # shellcheck disable=SC1090
  . "${ENV_FILE}"
  set +a
fi

SSH_OPTIONS="${GPU_SSH_OPTS:-${SSH_OPTS:-}}"
ALPAMAYO_REPO_URL="${ALPAMAYO_REPO_URL:-https://github.com/NVlabs/alpamayo1.5.git}"
ALPAMAYO_REMOTE_ROOT="${ALPAMAYO_REMOTE_ROOT:-/workspace/alpamayo1.5}"
ALPAMAYO_VENV_NAME="${ALPAMAYO_VENV_NAME:-a1_5_venv}"
ALPAMAYO_SYNC_MODE="${ALPAMAYO_SYNC_MODE:-sdpa}"
ALPAMAYO_RUN_TEST="${ALPAMAYO_RUN_TEST:-0}"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
REMOTE_CACHE_ROOT="${REMOTE_CACHE_ROOT:-/workspace/.cache/driverx}"

if [ "${ALPAMAYO_SYNC_MODE}" != "sdpa" ] && [ "${ALPAMAYO_SYNC_MODE}" != "flash" ]; then
  echo "ALPAMAYO_SYNC_MODE must be either 'sdpa' or 'flash'." >&2
  exit 2
fi

ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new "$REMOTE" "mkdir -p '$(dirname "$ALPAMAYO_REMOTE_ROOT")'"

if [ -n "${HF_TOKEN:-}" ]; then
  printf '%s' "$HF_TOKEN" | ssh ${SSH_OPTIONS} "$REMOTE" "cat > '/tmp/driverx_hf_token' && chmod 600 '/tmp/driverx_hf_token'"
fi

ssh ${SSH_OPTIONS} "$REMOTE" \
  "ALPAMAYO_REPO_URL='$ALPAMAYO_REPO_URL' \
   ALPAMAYO_REMOTE_ROOT='$ALPAMAYO_REMOTE_ROOT' \
   ALPAMAYO_VENV_NAME='$ALPAMAYO_VENV_NAME' \
   ALPAMAYO_SYNC_MODE='$ALPAMAYO_SYNC_MODE' \
   ALPAMAYO_RUN_TEST='$ALPAMAYO_RUN_TEST' \
   PYTHON_BIN='$PYTHON_BIN' \
   REMOTE_CACHE_ROOT='$REMOTE_CACHE_ROOT' \
   bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail

mkdir -p "$REMOTE_CACHE_ROOT"
export UV_CACHE_DIR="$REMOTE_CACHE_ROOT/uv"
export TRANSFORMERS_CACHE="$REMOTE_CACHE_ROOT/huggingface"
export HF_HUB_CACHE="$REMOTE_CACHE_ROOT/huggingface/hub"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required on the remote host." >&2
  exit 3
fi

if [ ! -d "$ALPAMAYO_REMOTE_ROOT/.git" ]; then
  git clone "$ALPAMAYO_REPO_URL" "$ALPAMAYO_REMOTE_ROOT"
else
  git -C "$ALPAMAYO_REMOTE_ROOT" fetch --depth=1 origin
fi

cd "$ALPAMAYO_REMOTE_ROOT"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  REQUESTED_PYTHON="$PYTHON_BIN"
  if [[ "$REQUESTED_PYTHON" == python* ]]; then
    REQUESTED_PYTHON="${REQUESTED_PYTHON#python}"
  fi
  uv python install "$REQUESTED_PYTHON"
  PYTHON_BIN="$REQUESTED_PYTHON"
fi

uv venv "$ALPAMAYO_VENV_NAME" --python "$PYTHON_BIN"
# shellcheck disable=SC1091
. "$ALPAMAYO_VENV_NAME/bin/activate"

if [ "$ALPAMAYO_SYNC_MODE" = "sdpa" ]; then
  uv sync --active --no-install-package flash-attn
else
  if ! command -v nvcc >/dev/null 2>&1; then
    echo "nvcc is required for flash-attn sync; use ALPAMAYO_SYNC_MODE=sdpa or install CUDA Toolkit 12.x." >&2
    exit 5
  fi
  uv sync --active
fi

if [ -f /tmp/driverx_hf_token ]; then
  mkdir -p "$HOME/.cache/huggingface"
  python - <<'PY'
from pathlib import Path
token = Path("/tmp/driverx_hf_token").read_text(encoding="utf-8").strip()
Path.home().joinpath(".cache", "huggingface", "token").write_text(token, encoding="utf-8")
PY
  rm -f /tmp/driverx_hf_token
fi

python - <<'PY'
import json
import os
import shutil
import subprocess
import sys

payload = {
    "python": sys.version,
    "uv": shutil.which("uv"),
    "nvcc": shutil.which("nvcc"),
    "hf_auth_home": str(__import__("pathlib").Path.home().joinpath(".cache", "huggingface")),
    "uv_cache_dir": os.environ.get("UV_CACHE_DIR"),
    "hf_hub_cache": os.environ.get("HF_HUB_CACHE"),
}
try:
    completed = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total,compute_cap", "--format=csv,noheader"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
    )
    payload["nvidia_smi_exit_code"] = completed.returncode
    payload["nvidia_smi"] = completed.stdout.strip()
except Exception as exc:
    payload["nvidia_smi_error"] = f"{type(exc).__name__}: {exc}"
print(json.dumps(payload, indent=2))
PY

if [ "$ALPAMAYO_RUN_TEST" = "1" ]; then
  python src/alpamayo1_5/test_inference.py
fi
REMOTE_SCRIPT
