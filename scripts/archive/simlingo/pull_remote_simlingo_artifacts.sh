#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-${GPU_SSH_HOST:-root@31.22.104.74}}"
REMOTE_RUN_ID="${REMOTE_RUN_ID:-task20}"
REMOTE_ARTIFACT_DIR="${2:-${REMOTE_ARTIFACT_DIR:-/workspace/artifacts/${REMOTE_RUN_ID}}}"
LOCAL_ARTIFACT_DIR="${3:-${LOCAL_ARTIFACT_DIR:-tickets/TASK-020/artifacts/${REMOTE_RUN_ID}-remote}}"
SSH_OPTIONS="${GPU_SSH_OPTS:-}"
SSH_RSH="ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new"
SOURCE="${HOST}:${REMOTE_ARTIFACT_DIR%/}/"
RSYNC_RSH_ARGS=(-e "${SSH_RSH}")

if [ -n "${LOCAL_SIMLINGO_ARTIFACT_SOURCE:-}" ]; then
  SOURCE="${LOCAL_SIMLINGO_ARTIFACT_SOURCE%/}/"
  RSYNC_RSH_ARGS=()
fi

mkdir -p "${LOCAL_ARTIFACT_DIR}"

set +u
rsync -rltz --prune-empty-dirs \
  "${RSYNC_RSH_ARGS[@]}" \
  --no-owner \
  --no-group \
  --exclude='viz/***' \
  --exclude='*/viz/***' \
  --exclude='models/***' \
  --exclude='*/models/***' \
  --exclude='software/***' \
  --exclude='*/software/***' \
  --exclude='carla/***' \
  --exclude='*/carla/***' \
  --exclude='.cache/***' \
  --exclude='*/.cache/***' \
  --include='*/' \
  --include='bootstrap.log' \
  --include='torch_cuda_compatibility.json' \
  --include='model_revision.txt' \
  --include='checkpoint.sha256' \
  --include='*.md' \
  --include='*.json' \
  --include='*.sha256' \
  --include='*.log' \
  --include='*.sh' \
  --exclude='*.tar' \
  --exclude='*.tar.gz' \
  --exclude='*.zip' \
  --exclude='*.pt' \
  --exclude='*.pth' \
  --exclude='*.ckpt' \
  --exclude='*.safetensors' \
  --exclude='*.mp4' \
  --exclude='*.avi' \
  --exclude='*.mov' \
  --exclude='*.png' \
  --exclude='*.jpg' \
  --exclude='*.jpeg' \
  --exclude='*' \
  "${SOURCE}" \
  "${LOCAL_ARTIFACT_DIR}/"
set -u

echo "Pulled compact SimLingo evidence into ${LOCAL_ARTIFACT_DIR}"
