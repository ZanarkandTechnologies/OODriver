# TASK-042: Local Fail2Drive Route Runner

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-033, TASK-034, TASK-041
- location: `src/driverx/simulators`, `src/driverx/cli.py`, tests
- enter when: CARLA is running locally and Fail2Drive route video planning
  exists
- leave when: DriverX can execute a planned Fail2Drive route command with logs,
  timeout, output discovery, and structured runtime blockers
- blockers: live run may require Fail2Drive Python dependencies and CARLA client
  compatibility
- spawned follow-ups: TASK-043 route video evidence, TASK-044 generated OOD route ramp
- complexity: M

## Summary

Execute the route command produced by `plan-fail2drive-video-smoke` while
capturing stdout/stderr, exit code, duration, expected outputs, and next-step
blockers. This ticket should not require a successful route; a precise local
dependency or runtime failure is useful evidence.

## Acceptance Criteria

- [x] Runner loads a `fail2drive_video_smoke_plan.json`.
- [x] Runner executes only when route-run prerequisites exist; missing video
  tool/RGB frames do not block route execution.
- [x] Logs, exit code, duration, expected output existence, and blockers are
  written as JSON/Markdown.
- [x] CLI supports timeout and dry-run.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_route_runner`
- `PYTHONPATH=src python3 -m driverx plan-fail2drive-video-smoke --config configs/carla_local.sample.yaml --output-root artifacts/runs --run-id task42-route-plan`
- `PYTHONPATH=src python3 -m driverx run-fail2drive-route --plan artifacts/runs/task42-route-plan/fail2drive_video_smoke_plan.json --timeout-s 45 --output-root artifacts/runs --run-id task42-route-run-numpy-blocker`

## Evidence

- Code: `src/driverx/simulators/fail2drive_route_runner.py`
- CLI: `python -m driverx run-fail2drive-route`
- Local run report: `artifacts/runs/task42-route-run-numpy-blocker/fail2drive_route_run.md`
- Review: `tickets/TASK-042/artifacts/review/20260505T221000-review.json`

## Blockers

- Local route execution reached the Fail2Drive evaluator but native macOS Python
  failed immediately with `ModuleNotFoundError: No module named 'numpy'`.
  Next step is a Dockerized Fail2Drive client environment instead of installing
  the full stack into the Mac Python.
