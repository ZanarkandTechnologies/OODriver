#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

PYTHONPATH=src python3 -m unittest \
  tests.test_scenario_forge \
  tests.test_alpamayo_ood_evaluation \
  tests.test_reasoning_timeline_overlay \
  tests.test_fail2drive_extension_report \
  tests.test_hero_demo_score
