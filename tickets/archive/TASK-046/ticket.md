# TASK-046: Alpamayo Trajectory Conversion

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-045
- location: `src/driverx/policies`, tests
- enter when: Alpamayo release contract identifies native trajectory shape
- leave when: DriverX can convert native Alpamayo `pred_xyz` into the existing
  20-point policy trajectory contract without importing Alpamayo or torch
- blockers: live Alpamayo inference remains blocked by GPU SSH; this ticket
  uses fixture predictions only
- spawned follow-ups: TASK-039 Alpamayo CARLA adapter
- complexity: M

## Summary

Implement the deterministic conversion layer between Alpamayo's native
`B x num_traj_sets x num_traj_samples x 64 x 3` output and DriverX's
`TrajectoryCandidate` shape of 20 xy points. This keeps model execution and
control conversion decoupled.

## Acceptance Criteria

- [x] Select one native trajectory sample from common nested output shapes.
- [x] Resample ego-local xy from 10 Hz native output to 4 Hz over 5 seconds.
- [x] Write a `TrajectoryCandidate` with useful metadata.
- [x] Add a CLI for converting a saved fixture `pred_xyz` JSON.
- [x] Tests cover interpolation, sample selection, error handling, and CLI
  artifact writing.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_trajectory tests.test_alpamayo_release tests.test_alpamayo_probe`
- `PYTHONPATH=src python3 -m driverx convert-alpamayo-trajectory --prediction-json artifacts/runs/task46-input/pred_xyz.json --output-root artifacts/runs --run-id task46-alpamayo-trajectory-conversion`
- `bash scripts/pre_push_check.sh`

## Evidence

- Module: `src/driverx/policies/alpamayo_trajectory.py`
- CLI: `src/driverx/policies/alpamayo_trajectory_cli.py`
- Tests: `tests/test_alpamayo_trajectory.py`
- Conversion JSON:
  `artifacts/runs/task46-alpamayo-trajectory-conversion/alpamayo_trajectory.json`
- Conversion report:
  `artifacts/runs/task46-alpamayo-trajectory-conversion/alpamayo_trajectory.md`
- Review: `tickets/archive/TASK-046/artifacts/review/20260505T225500-review.json`

## Result

DriverX can now select Alpamayo native outputs shaped as
`[B][sets][samples][T][3]`, `[sets][samples][T][3]`, `[samples][T][3]`, or
`[T][3]`, then linearly resample ego-local xy points from 10 Hz to the existing
20-point 4 Hz policy chunk. Short native trajectories fail explicitly instead
of silently producing truncated control evidence.
