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
- blockers: waits on TASK-053 live inference shape evidence; TASK-052 now proves
  model load on RunPod RTX 6000 Ada with eager attention
- spawned follow-ups: TASK-040 submission demo pack, TASK-053 live Alpamayo
  inference shape probe
- complexity: L

## Summary

Build the closed-loop Alpamayo adapter only after the remote probe proves the
inference input and output shapes. This ticket should not guess at undocumented
tensors.

## Acceptance Criteria

- [ ] Observation transform uses documented/probed camera, egomotion, and route
  fields.
- [ ] Trajectory output converts to control intent with validation.
- [ ] Adapter has offline replay tests before live CARLA.

## Verification

- pending TASK-038.

## Blockers

- TASK-052 proved `nvidia/Alpamayo-1.5-10B` load-only execution on the RunPod
  RTX 6000 Ada pod with `ALPAMAYO_ATTN_IMPLEMENTATION=eager`, but it did not
  execute a sample trajectory call. This ticket must remain blocked until
  TASK-053 produces observed input/output shape evidence from live inference.
