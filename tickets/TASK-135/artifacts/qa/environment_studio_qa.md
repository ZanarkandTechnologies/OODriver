# TASK-135 QA: Environment Studio Demo

## Verdict

PASS. OODrive now exposes the environment generator as product-facing commands,
builds a recordable static Environment Studio page, links it into a refreshed
submission pack, and passes the environment-demo readiness gate.

## Artifact Proof

- Environment Studio HTML:
  `artifacts/runs/task135-env-demo-v1/environment-demo-packs/task135-env-demo-v1/index.html`
- Environment demo manifest:
  `artifacts/runs/task135-env-demo-v1/environment-demo-packs/task135-env-demo-v1/environment_demo_manifest.json`
- Environment score report:
  `artifacts/runs/task135-env-demo-v1/environment-demo-packs/task135-env-demo-v1/environment-demo-scores/task135-env-demo-v1-score-report/environment_demo_score.md`
- Visual QA screenshot:
  `tickets/TASK-135/artifacts/visual/index.html.png`
- Submission pack refreshed with environment demo link:
  `artifacts/runs/task128-oodrive-live-product/submission-packs/task135-submission-pack-with-env-demo/index.html`

## Commands

```bash
PYTHONPATH=src python3 -m oodrive generate-envs \
  --template-id construction_lane_closure \
  --template-id roadside_market_occlusion \
  --template-id flooded_road \
  --template-id night_rain_fog \
  --template-id dense_regional_traffic \
  --template-id school_zone_unstructured_crossing \
  --severity 4 \
  --count 6 \
  --seed 31 \
  --run-id task135-env-demo-v1
```

Result: `6` recipes, `11` asset requests, families
`construction`, `pedestrian_occlusion`, `regional_market`, `regional_traffic`,
`visibility`, `weather_surface`.

```bash
PYTHONPATH=src python3 -m oodrive export-env-demo \
  --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json \
  --submission-pack artifacts/runs/task128-oodrive-live-product/submission-packs/task133-submission-pack-v1/submission_manifest.json \
  --hero-video artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/oodrive_hero_demo.mp4 \
  --run-id task135-env-demo-v1
```

Result: `index.html`, `environment_demo_manifest.json`, `commands.sh`, and
`video_storyboard.md` written under the environment demo pack directory.

```bash
PYTHONPATH=src python3 -m oodrive score-env-demo \
  --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json \
  --demo-manifest artifacts/runs/task135-env-demo-v1/environment-demo-packs/task135-env-demo-v1/environment_demo_manifest.json \
  --run-id task135-env-demo-v1-score \
  --metric-only
```

Result:

```text
METRIC environment_demo_readiness_score=100.0000
METRIC generation_substance=30.0000
METRIC product_surface=20.0000
METRIC judge_app_legibility=25.0000
METRIC video_readiness=15.0000
METRIC reproducibility=10.0000
```

## Checks

- PASS: `tickets/TASK-135/autoresearch/autoresearch.sh`
- PASS: `tickets/TASK-135/autoresearch/autoresearch.checks.sh`
- PASS: `PYTHONPATH=src python3 -m unittest tests.test_environment_generator tests.test_environment_demo_pack tests.test_environment_demo_score tests.test_oodrive_cli tests.test_submission_story_pack`
- PASS: `./autoresearch.sh`
- PASS: `./autoresearch.checks.sh`
- PASS: `bash scripts/pre_push_check.sh`

## Visual QA

Quick Look rendered the generated HTML to
`tickets/TASK-135/artifacts/visual/index.html.png`. The first viewport shows:

- OODrive Environment Studio title.
- One-sentence value proposition tied to CARLA-ready environment variants.
- Counts for `6` families, `6` recipes, `11` asset requests, and `4` claim
  labels.
- Sections for randomized environment generation, CARLA-ready controls,
  minimal-shot pressure, and evidence linkage.
- First row of environment cards.

## Claim Boundaries

- `closed_loop_vla_control=false`
- `real_time_vla_control=false`
- `sampled_open_loop_reasoning=true`
- `time_warped_offline_demo=true`
