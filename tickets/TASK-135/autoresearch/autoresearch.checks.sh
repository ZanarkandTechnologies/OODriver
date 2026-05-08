#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

PYTHONPATH=src python3 -m unittest \
  tests.test_environment_generator \
  tests.test_environment_demo_pack \
  tests.test_environment_demo_score \
  tests.test_oodrive_cli \
  tests.test_submission_story_pack
