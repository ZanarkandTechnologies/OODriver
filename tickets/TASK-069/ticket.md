# TASK-069: Route-Aligned Alpamayo Live Capture Resume

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-061, TASK-068
- location: `src/driverx/simulators`, `src/driverx/pipeline`,
  `tickets/TASK-061`
- enter when: a live CARLA route actor is available
- leave when: Alpamayo no-memory and memory decisions run on a route-aligned
  capture
- blockers: waits on a live route actor from a completed or long-running
  Fail2Drive route; TASK-068 route startup timed out before capture handoff
- spawned follow-ups: TASK-070
- complexity: M

### Description
TASK-061 already has the fake-CARLA attach seam. This ticket resumes the live
proof once the Town13 route actor exists.

### Goal
Use Alpamayo as the frozen reasoning VLA on a generated/Fail2Drive OOD route
capture, clearly labeled as open-loop policy evaluation.

### Acceptance Criteria
- [ ] AC-1: Capture package records route, map, actor id, camera windows, ego
  history, and memory context.
- [ ] AC-2: Alpamayo baseline and memory-guided decisions are compared on the
  same capture.
- [ ] AC-3: Report includes CoC snippets, trajectory deltas, latency, VRAM, and
  open-loop labels.

## Evidence
- Pending.

## Blockers
- TASK-068 proved route startup but not a stable long-running route actor for
  capture. Next unblock path is the same as TASK-060: run the stock route on a
  faster graphics-capable Linux NVIDIA CARLA host, or rerun local CARLA much
  longer and attach during the active route window.
