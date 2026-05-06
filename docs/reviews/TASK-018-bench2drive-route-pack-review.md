# TASK-018 Review: Generated Bench2Drive Route Pack Export

- work_type: backend
- rubrics_used: code-quality, integration-readiness, evidence-quality
- overall_score: 4.2 / 5.0
- threshold: 4.0
- verdict: pass
- rerun_required: false
- hard_gate_failures: none

## Scope

- `tickets/archive/TASK-018/ticket.md`
- `src/driverx/simulators/bench2drive_routes.py`
- `src/driverx/cli.py`
- `tests/test_bench2drive_route_export.py`
- `tests/test_cli.py`
- `tests/fixtures/fail2drive_like/fail2drive_split/*.xml`
- `tickets/archive/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/**`
- `tickets/archive/TASK-018/artifacts/qa/2026-05-04T210000Z/external-fail2drive/**`
- `README.md`, `AGENTS.md`, `docs/MEMORY.md`, `docs/progress.md`

## Initial Findings And Fixes

- The first pass only proved one-route export. Fixed by adding a two-recipe
  exporter test, two-route fixture artifacts, and a direct CLI multi-recipe
  regression.
- The external Fail2Drive smoke claim was initially prose-only. Fixed by
  persisting a durable external route-pack artifact under
  `tickets/archive/TASK-018/artifacts/qa/2026-05-04T210000Z/external-fail2drive/`.
- The overlay runtime contract was ambiguous. Fixed by clarifying that
  per-recipe `route_path` is for single-route replay/debugging, while suite
  execution uses `route_suite_path` or the generated SimLingo command plan.

## Passing Review Notes

- The exporter preserves input order and writes indexed per-route XML,
  sidecar overlays, and merged suite manifest entries.
- The generated SimLingo plan uses an absolute merged
  `--routes=.../generated_routes.xml` path.
- Docs and memory avoid overclaiming runtime injection; sidecar overlays are
  explicitly inert until a companion CARLA actor injector exists.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_bench2drive_route_export tests.test_cli`
  passed with 28 tests.
- `python3 -m compileall -q src tests` passed.
- `bash scripts/pre_push_check.sh` passed with 125 tests.
