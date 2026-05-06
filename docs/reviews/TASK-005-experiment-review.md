# TASK-005 Experiment Review

Date: 2026-05-02 21:39 +0800

## Verdict

PASS. Overall score: 4.3 / 5.0.

## Scope

- `tickets/archive/TASK-005/ticket.md`
- `tickets/archive/TASK-005/artifacts/qa/2026-05-02T133535Z/report.md`
- `src/driverx/planning/baselines.py`
- `src/driverx/planning/ranking.py`
- `src/driverx/planning/README.md`
- `src/driverx/planning/AGENTS.md`
- `src/driverx/pipeline/experiment_run.py`
- `src/driverx/pipeline/README.md`
- `src/driverx/cli.py`
- `tests/test_trajectory.py`
- `tests/test_experiment.py`
- `tests/test_cli.py`
- `README.md`
- `docs/progress.md`
- `docs/HISTORY.md`
- `docs/MEMORY.md`
- `artifacts/runs/waymo-experiment-10/experiment_summary.json`
- `artifacts/runs/waymo-experiment-10/experiment_report.md`

## Findings

No blocking findings.

The review confirmed that deployable strategy ranking does not use ground truth:
`rank_candidates` uses candidate priors plus obstacle, smoothness, and speed
penalties. The ADE-based `oracle_best_rule` path is explicitly marked
analysis-only in code, summary artifacts, and the report. The Waymo
`run-experiment` default of 10 frames is now visible in CLI help and README
prose and is covered by tests.

Low residual polish: the README states the default-count rule in prose, while
the nearby command still shows `--frame-count 10`. This is acceptable because
CLI help and tests prove the behavior, but a later docs polish pass can show an
omitted-count example too.

## Scores

- Code quality: 4.3 / 5.0.
- Integration readiness: 4.3 / 5.0.
- Evidence quality: 4.2 / 5.0.

## Evidence

- `PYTHONPATH=src python3 -m driverx run-experiment --help`: PASS.
- `PYTHONPATH=src python3 -m unittest tests.test_trajectory tests.test_experiment tests.test_cli`: PASS.
- `bash scripts/pre_push_check.sh`: PASS, 39 tests.
- Real Docker experiment: `artifacts/runs/waymo-experiment-10`.
- Best deployable strategy: `constant_acceleration`, mean ADE `3.73323`.
- Current mock intent planner: mean ADE `6.204769`.
- Best analysis-only strategy: `oracle_best_rule`, mean ADE `3.732298`.

## Residual Risk

This ticket intentionally shows that the mock intent planner is weaker than a
simple motion baseline on the first 10 validation frames. That is a useful
constraint for the next VLA/GPU ticket rather than a TASK-005 failure.
