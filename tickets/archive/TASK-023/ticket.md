# TASK-023: SimLingo Sidecar Orchestration Plan

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-018, TASK-021, TASK-022
- location: `src/driverx/simulators`, CLI, tests, docs
- enter when: SimLingo command plans, overlay injection plans, and companion runner exist
- leave when: a dry-run launch plan pairs stock SimLingo with the DriverX overlay injector
- blockers: live proof needs a CARLA/SimLingo runtime where the stock model can execute
- spawned follow-ups: live timed sidecar execution on H100/H200
- complexity: M

### Summary
Add the orchestration layer that tells an operator or future automation how to
run stock SimLingo and the DriverX overlay injector against the same CARLA
server. This remains a dry-run command plan; it does not launch processes,
coordinate route lifecycle timing, or claim live VLA behavior.

### Acceptance Criteria
- [x] Load an existing `simlingo_command_plan.json`.
- [x] Load an existing `overlay_injection_plan.json`.
- [x] Build explicit SimLingo and overlay-injector command entries.
- [x] Preserve SimLingo environment and live blockers.
- [x] Surface overlay validation errors and missing-route blockers.
- [x] Write JSON/Markdown launch-plan artifacts.
- [x] Add CLI entrypoint and tests.
- [x] Run `bash scripts/pre_push_check.sh`.

### Evidence
- Sidecar launch plan:
  `tickets/TASK-023/artifacts/qa/2026-05-05T053000Z/sidecar-plan/simlingo_sidecar_plan.md`
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_simlingo_sidecar tests.test_cli_simlingo_sidecar`
  passed with `4` tests.
- Local gate: `bash scripts/pre_push_check.sh` passed with `139` tests.
