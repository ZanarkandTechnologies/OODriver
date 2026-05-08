#!/usr/bin/env bash
set -euo pipefail

echo "[legacy] SimLingo remote artifact pull is archived; forwarding to scripts/archive/simlingo/." >&2
exec bash scripts/archive/simlingo/pull_remote_simlingo_artifacts.sh "$@"
