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
- 2026-05-06 11:44 +0800: A route-aligned capture attempt briefly succeeded
  inside the CARLA client Docker wrapper, attaching to hero actor `4719` and
  capturing 12 images, but it used the Fail2Drive wrapper path
  `/workspace/0xDriver` and wrote into the ephemeral container filesystem.
  Durable rule added as `MEM-0020`: CARLA-client Docker output roots must use
  `/workspace`, not `/workspace/0xDriver`.
- 2026-05-06 11:45 +0800: Retried with the correct mounted output root. Both
  `town13-live-attach-attempt-003` and `town13-live-attach-attempt-004` failed
  while the long Fail2Drive route was running because CARLA did not answer the
  capture client within 10s/60s. Evidence:
  `tickets/TASK-069/artifacts/town13-live-attach-attempt-003/carla_alpamayo_capture.json`
  and
  `tickets/TASK-069/artifacts/town13-live-attach-attempt-004/carla_alpamayo_capture.json`.
- Review:
  `docs/reviews/TASK-060-069-long-route-attempt-review.md`.

## Blockers
- The attach seam can find a route actor when CARLA is responsive, but the
  local Mac/Wine route run does not stay responsive enough for durable capture
  during synchronous Fail2Drive execution. Next unblock path is the same as
  TASK-060: run the stock route on a graphics-capable Linux NVIDIA CARLA host,
  or change the local route/capture scheduling so CARLA serves a second client
  while the route is active.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
