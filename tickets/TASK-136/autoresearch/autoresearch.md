# Autoresearch: Environment To Reasoned CARLA Proof

## Objective

Maximize the proof that OODrive can generate an environment from the product CLI, render that exact environment into CARLA visual evidence, and attach frame-linked Alpamayo keyframe analysis that can be turned into a judge-visible video.

This session optimizes the user's concrete desired flow:

```text
oodrive generate-envs -> oodrive render-env -> CARLA preview/image -> oodrive analyze-keyframes -> oodrive env-demo-video
```

## Metric

- Primary: `environment_to_reasoned_carla_score` (0-100 points, higher is better)
- Verify: `tickets/TASK-136/autoresearch/autoresearch.sh`
- Guard: `tickets/TASK-136/autoresearch/autoresearch.checks.sh`
- Direction: higher
- Target: `>=90`
- Max iterations: 10
- Noise policy: deterministic artifact score; rerun any gain above 10 points before keeping.

## Scope

- Editable:
  - `src/driverx/environments/`
  - `src/driverx/scenarios/studio_product_cli.py`
  - `src/driverx/scenarios/studio_product_environment_runtime.py`
  - `src/driverx/scenarios/studio_product_runtime.py`
  - `src/driverx/simulators/`
  - `src/driverx/pipeline/`
  - `src/driverx/policies/`
  - `src/driverx/evaluation/`
  - `src/oodrive/`
  - `tests/`
  - `README.md`
  - `docs/HISTORY.md`
  - `tickets/TASK-136/`
  - `tickets/TASK-137/`
  - `tickets/TASK-138/`
- Read-only:
  - TASK-128/TASK-131/TASK-135 source evidence unless a ticket explicitly renders a new derivative under ignored `artifacts/`
  - existing exported MP4s, except as fallback visual source with clear lineage labels
  - completed ticket archive
- Off limits:
  - secrets, HF tokens, model weights, dataset shards, public uploads, destructive remote operations, scorer threshold lowering, and false closed-loop or real-time VLA claims.

## Constraints

- Reward same-lineage evidence over generic video polish.
- Do not mark fake Alpamayo analysis as real model evidence.
- Do not promote blocked/local dry-run CARLA as live navigation evidence.
- Claim labels must remain visible and exact:
  - `closed_loop_vla_control=false`
  - `real_time_vla_control=false`
  - `sampled_open_loop_reasoning=true`
  - `time_warped_offline_demo=true`
- Generated MP4s, screenshots, and CARLA run folders stay ignored under `artifacts/`.

## Metric Components

- `cli_generation` (20): OODrive environment generation command exists and produces a multi-family environment summary.
- `same_run_carla_visual` (25): selected environment recipe traces to a CARLA run/preview image from the same run.
- `keyframe_reasoning` (25): at least five keyframes point to concrete CARLA frames with source times, reasoning/action fields or honest blockers, and backend labels.
- `video_readiness` (20): a 1-5 minute MP4 or story pack ties CLI generation, CARLA visual proof, keyframe analysis, risk/RAG panels, and claim labels together.
- `reproducibility` (10): commands, manifests, tests, QA, and review artifacts make the proof replayable.

## What's Been Tried

- TASK-135 built `oodrive generate-envs`, `export-env-demo`, and `score-env-demo`; current Environment Studio readiness reached `100`.
- TASK-131/TASK-133 provide strong hero and submission-pack evidence, but they do not yet prove a newly generated environment became a CARLA image and frame-linked Alpamayo analysis in one same-lineage flow.
- Baseline for this session is expected to be low because `render-env`, `analyze-keyframes`, `env-demo-video`, and `score-env-proof` do not exist yet.

## Next Ideas

- Build TASK-136 first: same-run environment-to-CARLA preview PNG.
- Build TASK-137 second: keyframe analysis over TASK-136 frames with fake/blocked/real backend modes.
- Build TASK-138 third: scored MP4/story pack and integrate the score into the final submission pack only after the metric clears `90`.
- Use Kasm/RunPod only when a fresh live CARLA preview is needed; local dry-run and blocked artifacts should keep implementation moving.
