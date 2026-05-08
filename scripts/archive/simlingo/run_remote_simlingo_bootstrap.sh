#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-${GPU_SSH_HOST:-root@31.22.104.74}}"
REMOTE_DIR="${2:-${REMOTE_WORKDIR:-/workspace/0xDriver}}"
SESSION_NAME="${SESSION_NAME:-task20}"
SSH_OPTIONS="${GPU_SSH_OPTS:-}"
REMOTE_ROOT="${REMOTE_ROOT:-/workspace}"
REMOTE_RUN_ID="${REMOTE_RUN_ID:-${SESSION_NAME}}"
REMOTE_CACHE_ROOT="${REMOTE_CACHE_ROOT:-${REMOTE_ROOT}/.cache}"
REMOTE_MINIFORGE_ROOT="${REMOTE_MINIFORGE_ROOT:-${REMOTE_ROOT}/conda}"

load_env_value() {
  local key="$1"
  local env_file="${2:-.env}"
  if [ -n "${!key:-}" ]; then
    printf "%s" "${!key}"
    return 0
  fi
  if [ -f "${env_file}" ]; then
    awk -F= -v key="${key}" '
      $1 == key {
        value = substr($0, length(key) + 2)
        gsub(/^["'\'']|["'\'']$/, "", value)
        print value
        found = 1
        exit
      }
      END { if (!found) exit 1 }
    ' "${env_file}" || true
  fi
}

HF_TOKEN_VALUE="$(load_env_value HF_TOKEN)"
if [ -z "${HF_TOKEN_VALUE}" ]; then
  echo "HF_TOKEN is not set in the environment or .env; continuing without a Hugging Face token." >&2
fi

REMOTE_TOKEN_FILE="/tmp/driverx_hf_token_${SESSION_NAME}_$$"

cleanup_remote_token_file() {
  ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new "${HOST}" \
    "rm -f '${REMOTE_TOKEN_FILE}'" >/dev/null 2>&1 || true
}

trap cleanup_remote_token_file EXIT

if [ -n "${HF_TOKEN_VALUE}" ]; then
  printf "%s" "${HF_TOKEN_VALUE}" | ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new "${HOST}" \
    "umask 077 && cat > '${REMOTE_TOKEN_FILE}'"
fi

ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new "${HOST}" "set -euo pipefail
tmux kill-session -t '${SESSION_NAME}' 2>/dev/null || true
tmux new-session -d -s '${SESSION_NAME}' \"cd '${REMOTE_DIR}' && if [ -f '${REMOTE_TOKEN_FILE}' ]; then export HF_TOKEN=\\\$(cat '${REMOTE_TOKEN_FILE}'); rm -f '${REMOTE_TOKEN_FILE}'; fi; export REMOTE_ROOT='${REMOTE_ROOT}' REMOTE_RUN_ID='${REMOTE_RUN_ID}' MINIFORGE_ROOT='${REMOTE_MINIFORGE_ROOT}' XDG_CACHE_HOME='${REMOTE_CACHE_ROOT}' HF_HOME='${REMOTE_CACHE_ROOT}/huggingface' TRANSFORMERS_CACHE='${REMOTE_CACHE_ROOT}/huggingface'; bash scripts/remote_simlingo_bootstrap.sh; rm -f '${REMOTE_TOKEN_FILE}'\"
tmux ls
"
