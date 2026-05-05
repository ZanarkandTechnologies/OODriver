#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "${ROOT}"

PYTHONPATH="${ROOT}/src" python3 -m driverx install-carla-additional-maps "$@"
