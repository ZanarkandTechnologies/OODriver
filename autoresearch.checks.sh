#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src python3 -m unittest \
  tests.test_carla_closed_loop_runner \
  tests.test_closed_loop_video \
  tests.test_fail2drive_catalog \
  tests.test_fail2drive_route_validation \
  tests.test_fail2drive_route_authoring \
  tests.test_fail2drive_reasoning \
  tests.test_fail2drive_demo_video \
  tests.test_fail2drive_model_reaction \
  tests.test_oodrive_cli
