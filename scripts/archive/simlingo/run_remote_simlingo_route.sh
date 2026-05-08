#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-${GPU_SSH_HOST:-root@31.22.104.74}}"
REMOTE_RUN_ID="${REMOTE_RUN_ID:-task20}"
REMOTE_ARTIFACT_DIR="${REMOTE_ARTIFACT_DIR:-/workspace/artifacts/${REMOTE_RUN_ID}}"
LOCAL_ARTIFACT_DIR="${LOCAL_ARTIFACT_DIR:-tickets/TASK-020/artifacts/${REMOTE_RUN_ID}-remote}"
REMOTE_ROUTE_SCRIPT="${REMOTE_ROUTE_SCRIPT:-${REMOTE_ARTIFACT_DIR}/run_one_route_with_carla_as_user.sh}"
REMOTE_ROUTE_LOG="${REMOTE_ROUTE_LOG:-${REMOTE_ARTIFACT_DIR}/run_one_route_with_carla.log}"
PULL_REMOTE_ARTIFACTS_SCRIPT="${PULL_REMOTE_ARTIFACTS_SCRIPT:-scripts/archive/simlingo/pull_remote_simlingo_artifacts.sh}"
SSH_OPTIONS="${GPU_SSH_OPTS:-}"

set +e
ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new "${HOST}" "set -euo pipefail
if [ ! -x '${REMOTE_ROUTE_SCRIPT}' ]; then
  echo 'Missing executable remote route script: ${REMOTE_ROUTE_SCRIPT}' >&2
  exit 78
fi
mkdir -p '${REMOTE_ARTIFACT_DIR}'
bash '${REMOTE_ROUTE_SCRIPT}' 2>&1 | tee '${REMOTE_ROUTE_LOG}'
exit \${PIPESTATUS[0]}
"
route_status=$?
set -e

if [ -x "${PULL_REMOTE_ARTIFACTS_SCRIPT}" ]; then
  set +e
  GPU_SSH_HOST="${HOST}" \
  GPU_SSH_OPTS="${SSH_OPTIONS}" \
  REMOTE_RUN_ID="${REMOTE_RUN_ID}" \
  REMOTE_ARTIFACT_DIR="${REMOTE_ARTIFACT_DIR}" \
  LOCAL_ARTIFACT_DIR="${LOCAL_ARTIFACT_DIR}" \
  bash "${PULL_REMOTE_ARTIFACTS_SCRIPT}"
  pull_status=$?
  set -e
  if [ "${pull_status}" -ne 0 ]; then
    echo "Artifact pullback failed with status ${pull_status}; preserving route status ${route_status}." >&2
  fi
else
  echo "Artifact pullback script is not executable: ${PULL_REMOTE_ARTIFACTS_SCRIPT}" >&2
fi

exit "${route_status}"
