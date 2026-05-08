#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src python3 -m unittest \
  tests.test_carla_closed_loop_runner \
  tests.test_closed_loop_video \
  tests.test_oodrive_cli
