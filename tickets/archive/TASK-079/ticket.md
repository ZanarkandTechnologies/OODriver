# TASK-079: Live OOD Video Evidence Assembly

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-078
- location: `src/driverx/pipeline`, `src/driverx/simulators`, `tickets/TASK-079/artifacts`
- enter when: TASK-078 has RGB frames and `entity_tracks.json`, or a fixture fallback is needed
- leave when: live or clearly labeled partial/fallback OOD video evidence is written with telemetry and claim boundaries
- blockers: none
- spawned follow-ups: TASK-082
- complexity: M

### Description
Assemble live DriverX CARLA OOD RGB frames into a submission-ready MP4 with
scenario, behavior, source, and risk telemetry overlays.

### Goal
Promote the video evidence from fixture proof to live CARLA proof whenever
TASK-078 succeeds, while preserving honest source labels for partial/fallback
evidence.

### Acceptance Criteria
- [x] AC-1: `assemble-ood-video` consumes TASK-078 frames and tracks when available.
- [x] AC-2: Output includes `ood_video_evidence.json`, `ood_video_evidence.md`, overlay frame count, duration, and source kind.
- [x] AC-3: Live CARLA source is never mislabeled as fixture, and fixture fallback is never mislabeled as live.
- [x] AC-4: MP4/frame artifacts remain ignored by git; JSON/Markdown evidence is commit-safe.

### Agent Contract
- Open: `src/driverx/pipeline/ood_video_evidence.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_ood_video_evidence`
- Stabilize: patch evidence labels if source-kind ambiguity appears.
- Inspect: `tickets/TASK-078/artifacts`
- Expected artifacts: `tickets/TASK-079/artifacts/*/ood_video_evidence.{json,md}` and ignored MP4.

### Evidence
- Created 2026-05-06 for the live CARLA retry batch.
- Live video evidence passed at
  `tickets/TASK-079/artifacts/task79-live-ood-video/ood_video_evidence.md`:
  120 overlay frames, 24.0s MP4, `source_kind=live_carla`, and worst risk at
  tick 27 near `generated_asset_asset_fallen_cargo_sack`.
- MP4 and overlay PNGs are generated artifacts and remain ignored by git.

### Blockers
- None for this ticket.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
