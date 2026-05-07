#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src python3 -m unittest \
  tests.test_hero_demo_score \
  tests.test_scenario_quality \
  tests.test_reasoning_video_pack \
  tests.test_oodrive_cli
