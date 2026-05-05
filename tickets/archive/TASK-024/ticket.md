# TASK-024: Live Timed SimLingo Sidecar Execution

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-020, TASK-022, TASK-023
- location: `src/driverx/simulators`, `src/driverx/cli.py`, tests,
  `tickets/TASK-024/artifacts`
- enter when: SimLingo sidecar plans exist and H100/CARLA runtime is becoming
  available
- leave when: a timed runner can execute the stock SimLingo process and DriverX
  overlay injector process from one plan, record logs, and report process
  outcomes
- blockers: live H100 route proof still pending under TASK-020; local process
  supervision is unblocked
- spawned follow-ups: generated OOD suite execution
- complexity: M

## Summary

Turn the TASK-023 manual two-process plan into an executable process supervisor.
This ticket does not claim the live H100 policy result by itself; it creates the
runner that will launch SimLingo and the DriverX overlay injector together once
the stock route path is stable.

## Acceptance Criteria

- [x] AC-1: `run-simlingo-sidecar` CLI consumes a sidecar plan JSON.
- [x] AC-2: The runner respects per-command `start_after_s` delays.
- [x] AC-3: stdout/stderr logs, process exit codes, timing, and success are
  written as JSON/Markdown.
- [x] AC-4: Dry-run mode validates the plan without executing commands.
- [x] AC-5: Unit and CLI tests cover success and setup-error cases.

## Evidence

- `tickets/TASK-024/artifacts/2026-05-05T153000+0800/sample-sidecar-run/simlingo_sidecar_run.json`
- `tickets/TASK-024/artifacts/2026-05-05T153000+0800/sample-sidecar-run/simlingo_sidecar_run.md`
- `PYTHONPATH=src python3 -m unittest tests.test_simlingo_sidecar_runner tests.test_cli_simlingo_sidecar_runner`
  passed with 4 tests.
- `bash scripts/pre_push_check.sh` passed with 143 tests.

## Blockers

- Live H100 SimLingo route execution is still tracked in TASK-020.
