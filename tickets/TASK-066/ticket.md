# TASK-066: Regional OOD Behavior Pack V2

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-064
- location: `src/driverx/behaviors`, tests, docs
- enter when: the local OOD demo can consume deterministic behavior traces
- leave when: the behavior pack better covers dense regional driving cases
- blockers: none after TASK-064
- spawned follow-ups: none
- complexity: S

### Description
The existing behavior pack already covers no-signal cut-ins, sudden braking,
motorcycle filtering, wrong-way shoulder creep, informal right-of-way pushing,
and a stunt-motorcycle proxy. This ticket expands/validates those cases as the
main randomized-OOD simulation substrate.

### Goal
Give the simulator enough weird-but-plausible actor behavior to support the
submission thesis around minimal-shot generalization.

### Acceptance Criteria
- [x] AC-1: At least two additional regional behavior traces are added or the
  current six are wired into suite-level validation with explicit pass/fail
  metrics.
- [x] AC-2: Tests assert coordinate/time properties for erratic cases, not only
  serialization.
- [x] AC-3: Behavior report names the intended pressure on the autonomy policy.

## Evidence
- Added `double_parked_door_swerve` and `unsignaled_u_turn`.
- Focused test: `PYTHONPATH=src python3 -m unittest tests.test_behaviors`.
- Behavior report:
  `tickets/TASK-066/artifacts/behavior-pack-v2/behavior_report.md`.
- QA report: `tickets/TASK-064/artifacts/qa_report.md`.
- Review: `docs/reviews/TASK-064-067-local-ood-review.md`.

## Blockers
- None.
