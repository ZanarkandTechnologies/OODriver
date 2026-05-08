#!/usr/bin/env bash
set -euo pipefail

echo "[legacy] SimLingo remote bootstrap runner is archived; forwarding to scripts/archive/simlingo/." >&2
exec bash scripts/archive/simlingo/run_remote_simlingo_bootstrap.sh "$@"
