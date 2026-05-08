#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT}"

PYTHONPATH=src python3 -m unittest \
  tests.test_environment_generator \
  tests.test_environment_demo_pack \
  tests.test_environment_demo_score \
  tests.test_environment_reasoned_carla \
  tests.test_keyframe_analysis \
  tests.test_reasoning_timeline_overlay \
  tests.test_hero_demo_score \
  tests.test_oodrive_cli
