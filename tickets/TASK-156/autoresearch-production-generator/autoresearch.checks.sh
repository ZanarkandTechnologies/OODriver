#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

PYTHONPATH=src python3 -m unittest tests.test_assets tests.test_carla_asset_mapping tests.test_generated_carla_runtime tests.test_production_scenario_generator
python3 -m json.tool tickets/TASK-156/autoresearch-production-generator/baseline_score.json >/dev/null
python3 -m json.tool tickets/TASK-153/artifacts/qa/prompt-to-carla-image-qa.json >/dev/null
