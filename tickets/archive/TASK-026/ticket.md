# TASK-026: Remote SimLingo Evidence Classifier

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-020 compact artifact pullback
- location: `src/driverx/simulators`, `src/driverx/cli.py`, `tests`,
  `tickets/TASK-026/artifacts`
- enter when: TASK-020 remote bootstrap or route artifacts may arrive in a
  compact local artifact directory
- leave when: local code can classify pulled SimLingo evidence as success,
  setup blocker, runtime blocker, or still-running/no-result without CARLA or
  SimLingo installed
- blockers: none for local implementation
- spawned follow-ups: none
- complexity: S

## Summary

Add a local evidence scanner for pulled H100 SimLingo artifacts. The scanner
turns a compact artifact directory into a deterministic JSON/Markdown verdict,
including bootstrap state, route-result discovery, route-log signals, CUDA
compatibility, and any precise blocker.

## Acceptance Criteria

- [x] AC-1: Scanner detects missing artifact roots, running bootstrap logs,
  completed bootstrap logs, route result JSONs, route logs, and CUDA
  compatibility JSON.
- [x] AC-2: Scanner reuses the existing SimLingo result parser when a
  `*_res.json` route result exists.
- [x] AC-3: CLI command writes `remote_simlingo_evidence.json` and
  `remote_simlingo_evidence.md`.
- [x] AC-4: Unit and CLI tests cover route-result success/failure and
  no-result blocker classification without CARLA, SimLingo, TensorFlow, or GPU.
- [x] AC-5: TASK-020 docs/progress can point to this scanner as the default
  pullback classification step.

## Build Notes

- Keep this as a local artifact-classification layer only; do not touch the
  running remote H100 tmux session.
- Large logs may be noisy. Reports should include compact markers and a short
  tail, not full log copies.

## Evidence

- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_simlingo_evidence` passed
  with `6` tests.
- Combined focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_simlingo_evidence tests.test_cli_simlingo_result tests.test_ood_suite_report`
  passed with `10` tests.
- Local current TASK-020 classifier proof:
  `tickets/TASK-020/artifacts/task20-evidence-final/remote_simlingo_evidence.json`
  and
  `tickets/TASK-020/artifacts/task20-evidence-final/remote_simlingo_evidence.md`
  classify the H100 route attempt as `route_infrastructure_blocked`.
- Review:
  `tickets/TASK-026/artifacts/review/2026-05-05_171339_review.md`
  passed with overall score `4.0`.

## Blockers

- None currently.
