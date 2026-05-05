# TASK-039: Alpamayo CARLA Adapter

## Status

- state: blocked
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-038
- location: `src/driverx/policies`, `src/driverx/simulators`, tests
- enter when: Alpamayo offline probe establishes load and trajectory shape
- leave when: CARLA camera/ego/nav observations can be transformed into
  Alpamayo inputs and its trajectory can be converted into CARLA control intent
- blockers: waits on a live Alpamayo probe artifact with observed input/output
  shape; TASK-038 shipped the local classifier and remote probe script but did
  not load the model
- spawned follow-ups: TASK-040 submission demo pack
- complexity: L

## Summary

Build the closed-loop Alpamayo adapter only after the offline probe proves the
model shape. This ticket should not guess at undocumented tensors.

## Acceptance Criteria

- [ ] Observation transform uses documented/probed camera, egomotion, and route
  fields.
- [ ] Trajectory output converts to control intent with validation.
- [ ] Adapter has offline replay tests before live CARLA.

## Verification

- pending TASK-038.

## Blockers

- TASK-038 produced `scripts/run_remote_alpamayo_probe.sh` and
  `probe-alpamayo`, but the local report status is `not_run`. This ticket must
  remain blocked until a remote artifact includes a successful load or shape
  observation.
