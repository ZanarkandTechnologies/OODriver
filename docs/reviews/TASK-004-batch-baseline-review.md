# TASK-004 Batch Baseline Review

Date: 2026-05-02 20:56 +0800

## Verdict

PASS. Overall score: 4.4 / 5.0.

## Scope

- `tickets/archive/TASK-004/ticket.md`
- `tickets/archive/TASK-004/artifacts/qa/2026-05-02T125206Z/report.md`
- `src/driverx/cli.py`
- `src/driverx/datasets/waymo_e2e.py`
- `src/driverx/datasets/__init__.py`
- `src/driverx/pipeline/batch_run.py`
- `src/driverx/pipeline/scene_run.py`
- `src/driverx/pipeline/__init__.py`
- `src/driverx/pipeline/README.md`
- `tests/test_batch.py`
- `tests/test_cli.py`
- `tests/test_waymo_loader.py`
- `README.md`
- `docs/progress.md`
- `docs/MEMORY.md`
- `artifacts/runs/waymo-batch-default-10/batch_summary.json`
- `artifacts/runs/waymo-batch-default-10/batch_report.md`

## Findings

No blocking findings.

The first review found two issues: fixture defaults were split between CLI and
API, and the default Waymo 10-frame behavior was not directly proven. The repair
centralized fixture and Waymo defaults in `run_batch`, changed the CLI to pass
fixture arguments through unchanged, updated the pipeline README public API, and
added tests for CLI/API fixture-default agreement plus omitted-`frame_count`
Waymo behavior.

## Scores

- Code quality: 4.4 / 5.0.
- Integration readiness: 4.4 / 5.0.
- Evidence quality: 4.3 / 5.0.

## Evidence

- `bash scripts/pre_push_check.sh`: PASS, 34 tests.
- `PYTHONPATH=src python3 -m unittest tests.test_batch tests.test_cli`: PASS, 7 tests.
- `python3 -m compileall -q src tests`: PASS.
- Real explicit-count Docker run: `artifacts/runs/waymo-batch-10`.
- Real default-count Docker run: `artifacts/runs/waymo-batch-default-10`.
- Default-count batch summary reports `frame_count: 10`, `num_scenes: 10`, mean
  ADE `6.204769`, best ADE `0.517203` at frame index `4`, and worst ADE
  `13.953167` at frame index `6`.
- Worst-scene SVG:
  `artifacts/runs/waymo-batch-default-10/frame-000006/scene_prediction.svg`.

## Residual Risk

The baseline still uses the deterministic mock reasoner by design. TASK-004
proves real-data ingestion, batch execution, aggregation, and evidence surfaces;
it does not claim VLA inference quality or cloud-GPU latency.
