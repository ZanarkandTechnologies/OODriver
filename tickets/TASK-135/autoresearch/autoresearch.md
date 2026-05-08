# Autoresearch: Raise OODrive Environment Demo Readiness

## Objective

Optimize the environment-generation feature until it is strong enough to demo
as an OODrive app/workflow for SoTA judges. The demo should show that OODrive
can generate varied CARLA OOD environments from minimal controls, expose the
weather/assets/placement/policy-pressure details, link them to the live hero
CARLA proof, and provide a 1-5 minute screen-recording path.

## Metric

- Primary: `environment_demo_readiness_score` (0-100 points, higher is better)
- Verify: `tickets/TASK-135/autoresearch/autoresearch.sh`
- Guard: `tickets/TASK-135/autoresearch/autoresearch.checks.sh`
- Direction: higher
- Target: `>=90`
- Max iterations: 8
- Noise policy: deterministic file/artifact score; rerun any gain above 10
  points before treating it as durable.

## Scope

- Editable:
  - `src/driverx/environments/`
  - `src/driverx/scenarios/studio_product_cli.py`
  - `src/driverx/scenarios/studio_product_environment_runtime.py`
  - `src/driverx/pipeline/environment_demo_pack.py`
  - `src/driverx/evaluation/environment_demo_score.py`
  - `src/oodrive/`
  - `tests/test_environment_generator.py`
  - `tests/test_environment_demo_pack.py`
  - `tests/test_environment_demo_score.py`
  - `tests/test_oodrive_cli.py`
  - `tests/test_submission_story_pack.py`
  - `README.md`
  - `docs/HISTORY.md`
  - `tickets/TASK-135/`
- Read-only:
  - TASK-128/TASK-131/TASK-133 evidence under ignored `artifacts/runs/`
  - existing exported MP4s
  - completed ticket archive
  - root `autoresearch.*` submission-readiness session unless explicitly
    retargeting the whole project after TASK-135 passes
- Off limits:
  - dataset shards, model weights, generated videos intended to remain ignored,
    credentials, HF tokens, RunPod secrets, destructive remote operations,
    threshold lowering, and false closed-loop/real-time VLA claims.

## Constraints

- The metric is an internal environment-demo readiness score, not an official
  CARLA driving score.
- The demo must be artifact-backed: real environment recipes, assets, weather,
  traffic, and road-local placements from the generator.
- Keep the core product name `OODrive`; `driverx` remains internal/compat.
- Claim boundaries stay explicit:
  `closed_loop_vla_control=false`, `real_time_vla_control=false`,
  `sampled_open_loop_reasoning=true`, `time_warped_offline_demo=true`.
- Do not spend the iteration loop on fresh GPU setup unless the local demo
  score is already passing and a live reel becomes the next bottleneck.

## What's Been Tried

- Baseline local environment generator exists and is strong:
  `driverx forge-environments` writes 6 recipes and 11 asset requests from the
  sample config.
- Baseline `tests.test_environment_generator` passes.
- Current root `submission_readiness_score` is already `96.35`, so this session
  uses a narrower non-saturated score for environment demo visibility.
- TASK-135 implementation added `oodrive generate-envs`, `oodrive
  export-env-demo`, `oodrive score-env-demo`, a static Environment Studio HTML
  pack, and tests. The metric now reports
  `environment_demo_readiness_score=100.0`.

## Next Ideas

- Add `oodrive generate-envs` as a product-facing alias over the existing
  environment forge.
- Add an Environment Studio HTML pack with six cards, asset placement tables,
  weather/traffic panels, proof links, and claim labels.
- Add `oodrive score-env-demo` so future changes are kept only when the demo is
  more judge-visible.
- Add a video storyboard that a screen recording can follow directly.
- Optional next lift: render a short screen-recording MP4 from the Environment
  Studio page and the existing hero CARLA video if the final submission wants a
  single stitched demo rather than a live walkthrough.
