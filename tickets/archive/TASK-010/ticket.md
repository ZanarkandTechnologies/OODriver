# TASK-010: Regional Driving Behavior Library

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-007
- location: `src/driverx/behaviors`, `tests`, reports
- enter when: scenario recipes exist and need executable actor behavior intent
- leave when: deterministic OOD behavior traces can be generated and validated offline
- blockers: none for offline behavior simulation
- spawned follow-ups: TASK-011 CARLA script compiler
- complexity: M

## Summary

Create a behavior library for regional/OOD traffic, including Malaysian-style
traffic patterns: no-signal cut-ins, sudden braking, motorcycle filtering,
wrong-way shoulder creep, informal right-of-way pushes, and low-profile fast
two-wheeler stunt proxies.

## Scope

In scope:

- typed behavior plans.
- deterministic trace simulation.
- metrics for lateral aggression, braking jerk, gap acceptance, wrong-way time,
  and route conflict.
- JSON/Markdown reports.

Out of scope:

- real CARLA actor control; that is TASK-011.
- real traffic prediction models.

## Acceptance Criteria

- [x] At least six behavior templates exist.
- [x] Each template generates deterministic actor coordinates over time.
- [x] Tests assert the intended erratic property for each behavior.
- [x] Reports summarize behavior metrics and expected failure pressure.
- [x] Scenario recipes can reference behavior ids through stable behavior ids/tags.

## Verification

- `bash scripts/pre_push_check.sh`
- `PYTHONPATH=src python3 -m driverx generate-behaviors --run-id task10-behaviors`

## Blockers

- None.

## Evidence

- Local tests: `PYTHONPATH=src python3 -m unittest tests.test_behaviors tests.test_cli` passed with 19 tests.
- Behavior suite command: `PYTHONPATH=src python3 -m driverx generate-behaviors --run-id task10-behaviors`.
- Report: `artifacts/runs/task10-behaviors/behavior_report.md`.
- Trace JSON: `artifacts/runs/task10-behaviors/behavior_traces.json`.
- Generated behaviors: `no_signal_cut_in`, `sudden_brake`,
  `motorcycle_filtering`, `wrong_way_shoulder_creep`,
  `informal_right_of_way_push`, `stunt_motorcycle_proxy`.
