#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CARLA_PYTHON_VERSION="${CARLA_PYTHON_VERSION:-0.9.16}"
IMAGE="${FAIL2DRIVE_CLIENT_DOCKER_IMAGE:-driverx-fail2drive-client:${CARLA_PYTHON_VERSION}}"
FAIL2DRIVE_ROOT="${FAIL2DRIVE_ROOT:-${ROOT}/../external/fail2drive}"
CARLA_PYTHONAPI_ROOT="${CARLA_PYTHONAPI_ROOT:-${ROOT}/../external/carla/PythonAPI/carla}"

if [ "$#" -eq 0 ]; then
  echo "usage: scripts/run_fail2drive_client_docker.sh <command...>" >&2
  echo "example: scripts/run_fail2drive_client_docker.sh python -m driverx plan-fail2drive-video-smoke --config configs/fail2drive_docker.local.yaml" >&2
  exit 2
fi

if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
  echo "Fail2Drive client Docker image not found: ${IMAGE}" >&2
  echo "Run scripts/build_fail2drive_client_docker.sh first." >&2
  exit 2
fi

docker run \
  --platform linux/amd64 \
  --rm \
  -e PYTHONPATH=/workspace/0xDriver/src:/workspace/fail2drive/scenario_runner:/workspace/fail2drive/leaderboard:/workspace/carla-pythonapi \
  -v "${ROOT}:/workspace/0xDriver" \
  -v "${FAIL2DRIVE_ROOT}:/workspace/fail2drive" \
  -v "${CARLA_PYTHONAPI_ROOT}:/workspace/carla-pythonapi" \
  -w /workspace/0xDriver \
  "${IMAGE}" \
  "$@"
