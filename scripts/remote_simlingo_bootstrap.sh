#!/usr/bin/env bash
set -euo pipefail

echo "[legacy] SimLingo remote bootstrap is archived; forwarding to scripts/archive/simlingo/." >&2
exec bash scripts/archive/simlingo/remote_simlingo_bootstrap.sh "$@"
