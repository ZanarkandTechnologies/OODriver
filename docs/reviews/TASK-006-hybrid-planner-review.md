# TASK-006 Hybrid Planner Review

Date: 2026-05-03 14:34 +0800

## Verdict

PASS. Overall score: 4.2 / 5.0.

## Scope

- `tickets/archive/TASK-006/ticket.md`
- `tickets/archive/TASK-006/artifacts/qa/2026-05-03T063433Z/report.md`
- `src/driverx/planning/hybrid.py`
- `src/driverx/planning/baselines.py`
- `src/driverx/planning/ranking.py`
- `src/driverx/planning/candidates.py`
- `src/driverx/planning/smoothing.py`
- `src/driverx/pipeline/scene_run.py`
- `src/driverx/pipeline/experiment_run.py`
- `tests/test_trajectory.py`
- `tests/test_pipeline_mock.py`
- `tests/test_batch.py`
- `tests/test_experiment.py`
- `README.md`
- `docs/progress.md`
- `docs/HISTORY.md`
- `docs/MEMORY.md`
- `artifacts/runs/waymo-hybrid-batch-10/batch_summary.json`
- `artifacts/runs/waymo-hybrid-batch-10/batch_report.md`
- `artifacts/runs/waymo-hybrid-experiment-10/experiment_summary.json`
- `artifacts/runs/waymo-hybrid-experiment-10/experiment_report.md`

## Findings

No blocking findings remain.

The first review pass scored `3.7 / 5.0` because the code was stronger than the
closure evidence: TASK-006 still had pending QA/review links, and the latest
experiment rename from `intent_planner` to `hybrid_planner` had not been
reflected in fresh durable artifacts. The repair pass added the TASK-006 QA
artifact and reran a real 10-frame Waymo experiment as
`waymo-hybrid-experiment-10`, which now records `hybrid_planner` throughout the
summary/report.

The implementation is consistent with the ticket: `run-scene` and `run-batch`
use `generate_hybrid_candidates`, which combines semantic intent candidates
with motion-prior candidates. `rank_candidates` remains label-free and does not
read `future_xy`; future labels are still used only for ADE evaluation and
analysis-only oracle reporting.

Residual caveat: the first hybrid policy selects the constant-acceleration
motion prior for all 10 real Waymo frames. That is acceptable for TASK-006
because the purpose is to promote the strong deployable local action layer into
the main path. The next VLA/GPU ticket must show semantic value beyond this
baseline.

## Scores

- Spec contract: 4.2 / 5.0.
- Code quality: 4.2 / 5.0.
- Integration readiness: 4.2 / 5.0.
- Evidence quality: 4.1 / 5.0.

## Evidence

- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_trajectory tests.test_pipeline_mock tests.test_batch tests.test_experiment tests.test_cli`
  - PASS, 20 tests.
- Local gate: `bash scripts/pre_push_check.sh`
  - PASS, 40 tests.
- Real hybrid batch: `artifacts/runs/waymo-hybrid-batch-10`
  - mean ADE `3.73323`
  - selected source `constant_acceleration_smooth` for all 10 frames
  - worst scene frame index `6`, ADE `9.15508`
- Fresh real hybrid experiment: `artifacts/runs/waymo-hybrid-experiment-10`
  - `hybrid_planner` mean ADE `3.73323`
  - `constant_acceleration` mean ADE `3.73323`
  - `constant_velocity` mean ADE `3.835549`
  - `oracle_best_rule` mean ADE `3.732298`, analysis-only

## Residual Risk

The current mock semantic reasoner still does not add real semantic lift on the
first Waymo slice. That is now a clear next-ticket target, not a TASK-006
failure: future real-time VLA work should feed structured intent into this
hybrid layer and demonstrate that semantic overrides beat the motion prior.
