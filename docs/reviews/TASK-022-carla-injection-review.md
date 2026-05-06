# TASK-022 Review: Live Companion CARLA Actor Injector

- work_type: backend/CLI runtime adapter
- rubrics_used: code-quality, integration-readiness, evidence-quality
- overall_score: 4.0 / 5.0
- threshold: 4.0
- verdict: pass
- rerun_required: false
- hard_gate_failures: none

## Scope

- `tickets/archive/TASK-022/ticket.md`
- `src/driverx/simulators/carla_injection.py`
- `src/driverx/simulators/__init__.py`
- `src/driverx/cli.py`
- `tests/test_carla_injection.py`
- `tests/test_cli_carla_injection.py`
- `tickets/archive/TASK-022/artifacts/qa/2026-05-05T051500Z/local-missing-carla/*`
- `README.md`, `src/driverx/simulators/README.md`
- `docs/HISTORY.md`, `docs/progress.md`,
  `docs/specs/minimal-shot-vla-roadmap.md`

## Findings And Fixes

- The first review found that companions from route N stayed alive when route
  N+1 started. Fixed by making the runner clean up route-local actors after
  each route, and adding fake-CARLA live-count assertions.
- The second review found per-route `destroyed_actor_ids` were reconstructed in
  spawn order for multi-companion routes. Fixed by preserving the actual
  route-local destroy order and adding a multi-companion cleanup regression.

## Passing Review Notes

- The injector consumes TASK-021 `overlay_injection_plan.json` artifacts and
  only touches `companion_actor_*` entries.
- It does not spawn ego, sensors, or stock route actors; those remain owned by
  SimLingo/Bench2Drive.
- The local native artifact correctly reports the missing `carla` Python package
  setup blocker, while fake-CARLA tests prove spawn, tick, track, and cleanup
  behavior.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_carla_injection tests.test_cli_carla_injection`
  passed with 5 tests.
- `python3 -m compileall -q src tests` passed.
- `bash scripts/pre_push_check.sh` passed with 135 tests.
