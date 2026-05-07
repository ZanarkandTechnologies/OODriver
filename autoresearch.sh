#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src python3 -m oodrive score-demo \
  --score-input qa/fixtures/hero_demo_score/candidate_demo.json \
  --metric-only
