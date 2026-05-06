# TASK-023 Review: SimLingo Sidecar Orchestration Plan

- work_type: backend/CLI dry-run orchestration
- rubrics_used: code-quality, integration-readiness, evidence-quality
- overall_score: 4.0 / 5.0
- threshold: 4.0
- verdict: pass
- rerun_required: false
- hard_gate_failures: none

## Scope

- `tickets/archive/TASK-023/ticket.md`
- `src/driverx/simulators/simlingo_sidecar.py`
- `src/driverx/simulators/__init__.py`
- `src/driverx/cli.py`
- `tests/test_simlingo_sidecar.py`
- `tests/test_cli_simlingo_sidecar.py`
- `tickets/archive/TASK-023/artifacts/qa/2026-05-05T053000Z/sidecar-plan/*`
- `README.md`, `src/driverx/simulators/README.md`
- `docs/HISTORY.md`, `docs/progress.md`,
  `docs/specs/minimal-shot-vla-roadmap.md`

## Findings And Fixes

- The first review found that `--route-limit` made the paired sidecar contract
  inconsistent: SimLingo would still run the full route suite while the overlay
  injector ran only a subset. Fixed by removing sidecar-level route limiting
  from the planner API, CLI, tests, and regenerated artifact.
- The first review noted simulator module docs did not list the new public API.
  Fixed by adding the sidecar builder/writer to
  `src/driverx/simulators/README.md`.

## Passing Review Notes

- The plan now emits two coherent dry-run command entries: stock
  SimLingo/Bench2Drive and DriverX overlay injector.
- SimLingo environment, expected outputs, and live blockers are preserved.
- Overlay validation errors and empty-route cases are surfaced as blockers.
- The artifact stays honest: it is a manual two-process launch plan, not a live
  supervisor or proof of model behavior changes.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_simlingo_sidecar tests.test_cli_simlingo_sidecar`
  passed with 4 tests.
- `python3 -m compileall -q src tests` passed.
- `bash scripts/pre_push_check.sh` passed with 139 tests.
