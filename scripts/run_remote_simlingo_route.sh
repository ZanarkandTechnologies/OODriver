#!/usr/bin/env bash
set -euo pipefail

echo "[legacy] SimLingo remote route runner is archived; forwarding to scripts/archive/simlingo/." >&2
exec bash scripts/archive/simlingo/run_remote_simlingo_route.sh "$@"
