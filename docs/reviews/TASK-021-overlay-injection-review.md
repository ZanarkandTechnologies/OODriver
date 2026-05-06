# TASK-021 Review: Overlay Injection Plan

- work_type: backend/CLI dry-run planning
- rubrics_used: code-quality, integration-readiness, evidence-quality
- overall_score: 4.4 / 5.0
- threshold: 4.0
- verdict: pass
- rerun_required: false
- hard_gate_failures: none

## Scope

- `tickets/archive/TASK-021/ticket.md`
- `src/driverx/simulators/overlay_injection.py`
- `src/driverx/simulators/bench2drive_routes.py`
- `src/driverx/simulators/__init__.py`
- `src/driverx/cli.py`
- `tests/test_overlay_injection.py`
- `tests/test_cli.py`
- `tests/test_cli_simlingo_result.py`
- `tickets/archive/TASK-021/artifacts/qa/2026-05-04T220000Z/overlay-injection/*`
- `README.md`, `src/driverx/simulators/README.md`
- `docs/HISTORY.md`, `docs/progress.md`,
  `docs/specs/minimal-shot-vla-roadmap.md`

## Findings And Fixes

- The first review found that overlay actors were preserved only as metadata.
  Fixed by adding route-specific companion CARLA actors, blueprints, spawn
  ticks, and cleanup order entries directly into each route `script_plan`.
- The first review found the runtime contract field was renamed. Fixed by
  preserving the exact `driverx_runtime_contract` field in the serialized plan.
- The final hardening review found contract validation only checked presence.
  Fixed by validating exact equality with `OVERLAY_CONTRACT` and adding a
  contract-drift regression test.

## Passing Review Notes

- The dry-run plan now emits distinct executable companion actor content per
  route: `occluder` maps to `static.prop.streetbarrier`, and `distractor` maps
  to `static.prop.trafficwarning`.
- The CLI output remains compact while the JSON artifact preserves full actor,
  sensor, tick, expected-output, memory-query, failure-mode, and cleanup data.
- The ticket stays honest that no live CARLA companion injector exists yet; this
  ticket proves artifact shape and planning only.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_overlay_injection tests.test_cli tests.test_cli_simlingo_result`
  passed with 29 tests.
- `python3 -m compileall -q src tests` passed.
- `bash scripts/pre_push_check.sh` passed with 130 tests.
