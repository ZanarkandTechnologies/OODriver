# TASK-068: CARLA Town13 Route Runner Resume

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-058, TASK-060
- location: `src/driverx/simulators`, `tickets/TASK-060`, `blockers.md`
- enter when: local CARLA has been relaunched after Town13 map install
- leave when: TASK-060 route evidence is produced or reclassified with fresh
  live logs
- blockers: none; follow-up route completion waits on faster graphics runtime
- spawned follow-ups: TASK-069
- complexity: M

### Description
This ticket resumes the higher-fidelity CARLA path after the local simulator
artifact exists. It should not block local OOD demo progress.

### Goal
Start the stock Fail2Drive Town13 route and collect score/video evidence if the
local CARLA wrapper can sustain it.

### Acceptance Criteria
- [x] AC-1: No-load map probe proves the relaunched CARLA server is responsive.
- [x] AC-2: TASK-060 route runner starts against Town13 or records a precise
  fresh blocker.
- [x] AC-3: `blockers.md` is updated with current CARLA status.

## Evidence
- 2026-05-06 04:33 +0800: Docker no-load probe connected to local CARLA
  0.9.16, listed `Town13`, and reported current map `Town10HD_Opt`.
  Evidence:
  `tickets/TASK-068/artifacts/town13-no-load-probe-after-local-demo/carla_map_inventory.md`.
- 2026-05-06 04:33 +0800: Docker load probe successfully loaded
  `Carla/Maps/Town13/Town13`. Evidence:
  `tickets/TASK-068/artifacts/town13-load-probe-after-local-demo/carla_map_inventory.md`.
- 2026-05-06 04:33 +0800: Stock Fail2Drive
  `Generalization_PedestriansOnRoad_1088` route started against Town13 through
  Docker after rebuilding the Fail2Drive client with optional torch support.
  It wrote a checkpoint, produced 10 RGB frames, and timed out at the 300s cap
  because local Mac/Kegworks/Wine simulation speed was about `0.075x`.
  Evidence:
  `tickets/TASK-068/artifacts/town13-route-run-with-torch/fail2drive_route_run.md`.
- Partial video/evidence bundle:
  `tickets/TASK-068/artifacts/town13-route-evidence-partial-001/run_evidence.md`.
- Partial MP4 assembly report:
  `tickets/TASK-068/artifacts/town13-partial-video-assembly/route_video_assembly.md`.
- Full gate: `bash scripts/pre_push_check.sh` passed with 288 tests.
- Review:
  `docs/reviews/TASK-068-070-local-first-submission-review.md`.

## Blockers
- None for this resume ticket. TASK-060 remains blocked on either a faster
  graphics-capable Linux NVIDIA host or a much longer local route run.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
