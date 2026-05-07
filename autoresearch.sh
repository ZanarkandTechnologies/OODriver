#!/usr/bin/env bash
set -euo pipefail

python3 qa/fixtures/hero_demo_score/score_fixture.py \
  qa/fixtures/hero_demo_score/candidate_demo.json
