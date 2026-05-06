# TASK-071: Fast Town13 Route Video Evidence Runner

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-060, TASK-068
- location: `src/driverx/simulators`, tests, `tickets/TASK-071/artifacts`
- enter when: CARLA is relaunched on Town13 but full Fail2Drive scoring is
  too slow for rapid demo evidence
- leave when: route logs stream during execution and a short MP4 can be
  assembled as soon as enough RGB frames exist
- blockers: none for early video; full route scoring remains TASK-060 follow-up
- spawned follow-ups: none
- complexity: M

### Description
TASK-068 proved the stock Fail2Drive Town13 route starts and emits RGB frames,
but the route runner buffered logs until process exit and waited for full
route completion or timeout before video assembly. This ticket adds an
early-video path so the project can capture judge-visible Town13 evidence
without waiting for a full scored route.

### Goal
Produce fresh Town13 video evidence quickly and label it as partial unless the
route actually completes.

## Plan

### Change
Add frame watching and early MP4 assembly to `run-fail2drive-route`.

### Why
The local Mac/Kegworks/Wine CARLA runtime is slow. The submission still needs
visible simulator evidence, so the runner should preserve frames and assemble
video as soon as the video proof is available.

### Before -> After
- Before: stdout/stderr and video evidence appear only when the route exits or
  times out.
- After: logs are streamed to files, the RGB folder is watched, and
  `--stop-after-video` can terminate after enough frames are captured.

### Touch
- `src/driverx/simulators/fail2drive_route_runner.py`
- `src/driverx/simulators/fail2drive_route_runner_cli.py`
- `src/driverx/simulators/route_video_assembly.py`
- `src/driverx/simulators/__init__.py`
- `tests/test_fail2drive_route_runner.py`
- `tests/test_route_video_assembly.py`
- `blockers.md`, `docs/progress.md`, `docs/HISTORY.md`

### Acceptance Criteria
- [x] AC-1: Route runner supports `--min-video-frames`,
  `--video-timeout-s`, `--video-fps`, `--ffmpeg-path`, and
  `--stop-after-video`.
- [x] AC-2: Unit tests prove frame watching and early video assembly without
  CARLA.
- [x] AC-3: Live Town13 run either produces fresh MP4 evidence or records a
  precise Docker/CARLA blocker.
- [x] AC-4: Route evidence and blockers distinguish partial video from full
  scored route completion.
- [x] AC-5: Heavy video/JPG artifacts stay ignored.

## Evidence
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_route_video_assembly tests.test_fail2drive_route_runner`.
- Focused regression after submission-pack refresh:
  `PYTHONPATH=src python3 -m unittest tests.test_route_video_assembly tests.test_fail2drive_route_runner tests.test_route_evidence tests.test_submission_demo_pack`.
- Full gate: `bash scripts/pre_push_check.sh` passed with 292 tests.
- Video probe: `ffprobe` reported H.264, 1920x1080, 10fps, 5 frames, 0.5s,
  507730 bytes.
- 2026-05-06 11:34 +0800: Live Town13 early-video run captured 5 RGB frames
  from `Generalization_PedestriansOnRoad_1088`, assembled a 0.5s MP4 with host
  ffmpeg, and built partial route evidence. The route was intentionally stopped
  after video capture, so route score/completion remain unavailable by design.
- Route run:
  `tickets/TASK-071/artifacts/town13-early-video-after-restart/fail2drive_route_run.md`.
- Video assembly:
  `tickets/TASK-071/artifacts/town13-early-video-assembly/route_video_assembly.md`.
- Route evidence:
  `tickets/TASK-071/artifacts/town13-early-route-evidence/run_evidence.md`.
- Video artifact, ignored by git:
  `tickets/TASK-071/artifacts/town13-early-video-after-restart/Generalization_PedestriansOnRoad_1088_early.mp4`.
- Review:
  `docs/reviews/TASK-071-fast-town13-video-review.md`.

## Blockers
- None for this ticket. Docker ffmpeg is absent, but host ffmpeg assembled the
  MP4 successfully; full scored route completion remains TASK-060 scope.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
