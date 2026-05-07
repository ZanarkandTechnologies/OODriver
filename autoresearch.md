# Autoresearch: Improve OODrive Hero Demo Quality

## Objective

Maximize the judge-visible quality of the OODrive hero demo. The demo must make
the product contribution obvious: natural-language OOD generation, live CARLA
placement, time-warped simulator video, sampled Alpamayo reasoning, RAG memory
retrieval, risk/object telemetry, and honest claim boundaries.

## Metric

- Primary: `hero_demo_score` (0-100 points, higher is better)
- Verify: `./autoresearch.sh`
- Guard: `./autoresearch.checks.sh`
- Direction: higher
- Max iterations: 12
- Noise policy: deterministic fixture baseline now; after TASK-130 lands,
  compare only runs from the same source fixture or the same named live run.

## Scope

- Editable:
  - `src/driverx/evaluation/`
  - `src/driverx/simulators/ood_video_overlay.py`
  - `src/driverx/simulators/reasoning_timeline_overlay.py`
  - `src/driverx/pipeline/reasoning_overlay_video.py`
  - `src/driverx/scenarios/quality.py`
  - `src/driverx/scenarios/studio_product_cli.py`
  - `src/oodrive/`
  - `tests/`
  - `qa/fixtures/hero_demo_score/`
  - `scripts/`
- Read-only:
  - `tickets/archive/`
  - existing remote RunPod artifacts unless copied into ignored local exports
  - historical `artifacts/runs/` evidence used as references
- Off limits:
  - dataset shards, model weights, generated videos intended to remain ignored,
    credentials, HF tokens, RunPod secrets, and destructive remote operations.

## Constraints

- The metric must be mechanical and must not depend on manual visual judgment.
- The score must reward legibility, not merely raw simulator runtime.
- Claim boundaries must stay explicit:
  `time_warped_offline_demo=true`, `sampled_open_loop_reasoning=true`,
  `real_time_vla_control=false` unless a real closed-loop VLA controller exists.
- Do not optimize by hiding low-quality footage, deleting risks, or inflating
  fake reasoning counts. Scoring inputs must be traceable to DB/run/reasoning
  artifacts after TASK-130.

## What's Been Tried

- Baseline fixture created from the TASK-128 weakness: live CARLA placement and
  fresh Alpamayo reasoning exist, but the video lacks visible frame/time,
  repeated reasoning checkpoints, and enough RAG/risk overlays.

## Next Ideas

- Implement `oodrive score-demo` from the same metric fields as the fixture.
- Add frame number and source timestamp to every video frame.
- Create a reasoning/RAG overlay video from sampled Alpamayo checkpoints.
- Produce a stricter flagship demo report that fails if the video is too slow,
  off-road, missing generated object visibility, or missing reasoning callouts.
- Add `oodrive demo-video` to assemble the final time-warped reasoning video
  from a DB/run/reasoning artifact set.
