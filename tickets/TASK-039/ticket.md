# TASK-039: Alpamayo CARLA Adapter

## Status

- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-038
- location: `src/driverx/policies`, `src/driverx/simulators`, tests
- enter when: Alpamayo offline probe establishes load and trajectory shape
- leave when: CARLA camera/ego/nav observations can be transformed into
  Alpamayo inputs and its trajectory can be converted into CARLA control intent
- blockers: none for planning; TASK-053 provides live shape evidence from
  synthetic Alpamayo-shaped tensors, while real PhysicalAI sample data remains
  gated
- spawned follow-ups: TASK-040 submission demo pack, TASK-053 live Alpamayo
  inference shape probe
- complexity: L

## Summary

Build the Alpamayo adapter against the live input/output shapes observed in
TASK-053. Keep v1 open-loop: return trajectory intent and evidence artifacts,
not direct CARLA steering.

## Acceptance Criteria

- [ ] Observation transform uses documented/probed camera, egomotion, and route
  fields.
- [ ] Trajectory output converts to control intent with validation.
- [ ] Adapter has offline replay tests before live CARLA.

## Verification

- pending TASK-038.

## Blockers

- TASK-053 observed live Alpamayo inference shapes on the RunPod RTX 6000 Ada
  pod with `ALPAMAYO_ATTN_IMPLEMENTATION=eager`:
  `pred_xyz=[1,1,1,64,3]`, `pred_rot=[1,1,1,64,3,3]`,
  `extra.cot=[1,1,1]`, `extra.meta_action=[1,1,1]`, and
  `extra.answer=[1,1,1]`.
- The upstream PhysicalAI dataset remains gated, so adapter implementation
  should use DriverX/CARLA tensor materialization rather than depend on the
  upstream sample loader.
