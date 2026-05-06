#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/sync_runpod_proxy_workspace.sh USER@ssh.runpod.io SSH_KEY [REMOTE_DIR]

Sync a lightweight 0xDriver workspace through RunPod's proxied SSH endpoint.

This is for Kasm/Desktop templates where normal rsync/scp fail because the
proxy requires a PTY and opens an interactive shell. The script sends a tarball
as base64 through a heredoc with terminal echo disabled, then unpacks it on the
remote host.

Environment:
  DRIVERX_REMOTE_TEST=1   Run a focused remote unittest smoke after unpacking.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 2 ]]; then
  usage >&2
  exit 2
fi

HOST="$1"
KEY_FILE="$2"
REMOTE_DIR="${3:-/workspace/0xDriver}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TMP_TAR="$(mktemp /tmp/driverx-runpod-proxy.XXXXXX.tgz)"

cleanup() {
  rm -f "${TMP_TAR}"
}
trap cleanup EXIT

cd "${ROOT}"

TAR_ARGS=(
  --exclude='__pycache__'
  --exclude='*.pyc'
  --exclude='.DS_Store'
  --exclude='.env'
  --exclude='.env.*'
  --exclude='.git'
  --exclude='artifacts'
  --exclude='data'
  --exclude='.venv'
  --exclude='.venv-*'
  -czf "${TMP_TAR}"
  AGENTS.md ARCHITECTURE.md PROJECT_RULES.md README.md blockers.md pyproject.toml
  configs docker docs requirements scripts src tests tickets
)

if tar --help 2>&1 | grep -q -- '--no-xattrs'; then
  TAR_ARGS=(--no-xattrs "${TAR_ARGS[@]}")
fi
if tar --disable-copyfile -cf /tmp/driverx-tar-probe.tar --files-from /dev/null >/dev/null 2>&1; then
  TAR_ARGS=(--disable-copyfile "${TAR_ARGS[@]}")
fi
rm -f /tmp/driverx-tar-probe.tar

COPYFILE_DISABLE=1 tar \
  "${TAR_ARGS[@]}"

REMOTE_SCRIPT="$(mktemp /tmp/driverx-runpod-proxy-script.XXXXXX.sh)"
trap 'rm -f "${TMP_TAR}" "${REMOTE_SCRIPT}"' EXIT

{
  cat <<EOF
set -euo pipefail
mkdir -p /workspace
stty -echo || true
cat > /tmp/driverx_sync.tgz.b64 <<'DRIVERX_BUNDLE_EOF'
EOF
  base64 -i "${TMP_TAR}"
  cat <<EOF
DRIVERX_BUNDLE_EOF
stty echo || true
base64 -d /tmp/driverx_sync.tgz.b64 > /tmp/driverx_sync.tgz
rm -rf '${REMOTE_DIR}'
mkdir -p '${REMOTE_DIR}'
tar -xzf /tmp/driverx_sync.tgz -C '${REMOTE_DIR}'
rm -f /tmp/driverx_sync.tgz /tmp/driverx_sync.tgz.b64
cd '${REMOTE_DIR}'
echo "driverx_proxy_sync_ok \$(pwd)"
if [[ "${DRIVERX_REMOTE_TEST:-0}" == "1" ]]; then
  PYTHON_BIN="/workspace/driverx_py312/bin/python"
  if [[ ! -x "\${PYTHON_BIN}" ]]; then
    PYTHON_BIN="python3"
  fi
  PYTHONPATH=src "\${PYTHON_BIN}" -m unittest \
    tests.test_carla_road_frame \
    tests.test_carla_ood_demo \
    tests.test_scripted_ood_campaign \
    tests.test_submission_scenario_browser
fi
exit
EOF
} > "${REMOTE_SCRIPT}"

ssh -tt \
  -o BatchMode=yes \
  -o StrictHostKeyChecking=accept-new \
  -o ConnectTimeout=30 \
  -o ServerAliveInterval=10 \
  -i "${KEY_FILE}" \
  "${HOST}" < "${REMOTE_SCRIPT}"
