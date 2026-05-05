# TASK-051: Live CARLA Alpamayo Input Capture

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-047, TASK-050
- location: `src/driverx/simulators`, tests
- enter when: local CARLA 0.9.16 is reachable through the Docker client
- leave when: DriverX can spawn an ego vehicle, attach Alpamayo-style cameras,
  capture temporal frames, and write an input package manifest
- blockers: live model inference remains blocked on remote GPU SSH
- spawned follow-ups: TASK-039 Alpamayo CARLA adapter
- complexity: M

## Summary

Capture a live CARLA sensor package shaped for Alpamayo: front-left/front/front-right
RGB camera windows, ego history, input manifest, tracks, and cleanup evidence.

## Acceptance Criteria

- [x] Add a CARLA capture runner for three Alpamayo camera ids `[0, 1, 2]`.
- [x] Save four RGB frames per camera and a package JSON/Markdown manifest.
- [x] Record ego track history and destroyed actor ids.
- [x] Tests cover fake-CARLA spawn/capture/cleanup and missing `carla` package.
- [x] Run a live Docker client capture against local CARLA when available.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_carla_alpamayo_capture tests.test_carla_ego`
- `scripts/run_carla_client_docker.sh python -m driverx capture-alpamayo-carla-input --config configs/fail2drive_docker.local.yaml --output-root artifacts/runs --run-id task51-live-alpamayo-capture --tick-count 4 --camera-width 160 --camera-height 90 --timeout-s 10`
- `bash scripts/pre_push_check.sh`

## Evidence

- Module: `src/driverx/simulators/carla_alpamayo_capture.py`
- CLI: `src/driverx/simulators/carla_alpamayo_capture_cli.py`
- Tests: `tests/test_carla_alpamayo_capture.py`
- Live capture summary:
  `artifacts/runs/task51-live-alpamayo-capture/carla_alpamayo_capture.json`
- Live input package:
  `artifacts/runs/task51-live-alpamayo-capture/alpamayo_carla_input_package.json`
- Live report:
  `artifacts/runs/task51-live-alpamayo-capture/alpamayo_carla_capture.md`
- Live images:
  `artifacts/runs/task51-live-alpamayo-capture/images/`
- Review: `tickets/archive/TASK-051/artifacts/review/20260505T231400-review.json`

## Result

Live capture against local CARLA succeeded through Docker. It spawned ego actor
`24` and camera actors `[25, 26, 27]`, saved `12` RGB images, wrote tensor shape
`3 x 4 x 3 x 90 x 160`, wrote a 16-step ego history scaffold, and destroyed all
spawned actors `[27, 26, 25, 24]`.
