# Autoresearch: Closed-Loop CARLA Video Quality

## Objective

Make paused closed-loop CARLA videos prove the thing a skeptical judge expects:
a visible ego vehicle drives toward a visible cone/hazard, the video advances at
a believable pace, and the trace shows observe/infer/act recurrence instead of
stretching a few checkpoint stills into a slow fake movie.

## Metric

- Primary: `closed_loop_video_score` (0-100 points, higher is better)
- Verify: `./autoresearch.sh`
- Guard: `./autoresearch.checks.sh`
- Direction: higher
- Target: `>=85`
- Max iterations: 6
- Noise policy: deterministic local fixture score; live RunPod proof is required
  before final media promotion, but the local metric must block sparse/no-ego
  videos without needing CARLA.

## Scope

- Editable:
  - `src/driverx/simulators/carla_closed_loop_runner.py`
  - `src/driverx/pipeline/closed_loop_video.py`
  - `src/driverx/evaluation/closed_loop_video_score.py`
  - `src/driverx/scenarios/studio_product_closed_loop_cli.py`
  - `src/driverx/scenarios/studio_product_closed_loop_runtime.py`
  - `tests/test_carla_closed_loop_runner.py`
  - `tests/test_closed_loop_video.py`
  - `tests/test_oodrive_cli.py`
  - `tickets/TASK-160/`
  - `docs/HISTORY.md`
  - `docs/MEMORY.md`
  - `docs/TROUBLES.md`
  - `AGENTS.md`
  - `autoresearch.*`
- Read-only:
  - existing pulled media under `artifacts/runs/task160-live-alpamayo-authfix-2step-video/`
  - historical TASK-160 review evidence
- Off limits:
  - model weights, credentials, HF tokens, RunPod secrets, destructive remote
    operations, threshold lowering, fake real-time claims, and judge-media
    promotion without local/public export.

## Constraints

- The renderer must not stretch sparse checkpoint stills into a long video.
- The promoted hero path must use a third-person/spectator/chase view where the
  ego vehicle is visible.
- The trace/video manifest must expose `source_frame_count`,
  `action_rgb_frame_count`, `seconds_per_source_frame`, `ego_vehicle_visible`,
  and `visual_camera_role`.
- Alpamayo latency can remain slow; the video should show the simulated action
  briskly and label `real_time_vla_control=false`.

## What's Been Tried

- TASK-160 proved live CARLA + Alpamayo closed-loop recurrence, but the first
  video used front/ego camera frames and stretched four checkpoint images across
  60 seconds.
- Pulling the MP4 locally confirmed the failure: no ego vehicle is visible, and
  the scene barely moves.
- The root cause is sparse capture/stitching, not lack of GPU rendering speed.

## Current Hypothesis

The highest leverage fix is to record a third-person chase camera and capture
visual frames during each action tick. The score gate should then reject any
video that lacks ego visibility or has too few source frames for its duration.

## Next Ideas

- Add a spectator camera option if attached chase camera does not show the car
  cleanly enough in live CARLA.
- Increase `control_ticks_per_step` for the visual proof after the Alpamayo
  handoff is stable, because more CARLA ticks are what make the video move.
- Add frame-difference scoring from real MP4 samples if manifest-level pacing
  can still be gamed.
