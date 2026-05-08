# TASK-133 QA: Judge-Intuitive Submission Pack

## Commands

```bash
PYTHONPATH=src python3 -m unittest tests.test_submission_story_pack tests.test_submission_readiness_score tests.test_oodrive_cli

PYTHONPATH=src python3 -m oodrive export-submission \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --run artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/run_manifest.json \
  --evaluation artifacts/runs/task128-oodrive-live-product/reasoning/evaluations/task128-oodrive-live-alpamayo-fresh-evaluation/policy_evaluation.json \
  --hero-video artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/oodrive_hero_demo.mp4 \
  --hero-score artifacts/runs/task128-oodrive-live-product/demo-scores/task131-score-gated-hero-v2-score/hero_demo_score.json \
  --output-root artifacts/runs/task128-oodrive-live-product/submission-packs \
  --run-id task133-submission-pack-v1

PYTHONPATH=src python3 -m oodrive score-submission \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --run artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/run_manifest.json \
  --evaluation artifacts/runs/task128-oodrive-live-product/reasoning/evaluations/task128-oodrive-live-alpamayo-fresh-evaluation/policy_evaluation.json \
  --hero-score artifacts/runs/task128-oodrive-live-product/demo-scores/task131-score-gated-hero-v2-score/hero_demo_score.json \
  --overlay-report artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/hero_demo_video.json \
  --pack-manifest artifacts/runs/task128-oodrive-live-product/submission-packs/task133-submission-pack-v1/submission_manifest.json \
  --checks-report tickets/TASK-132/artifacts/qa/checks_report.json \
  --output-root artifacts/runs/task128-oodrive-live-product/submission-scores \
  --run-id task133-submission-pack-v1-score

./autoresearch.sh
```

## Results

- Focused tests: PASS, 15 tests.
- `oodrive export-submission`: PASS, generated all required pack files.
- `oodrive score-submission`: PASS, `submission_readiness_score=96.35`.
- `./autoresearch.sh`: PASS, emits `METRIC submission_readiness_score=96.3500`.
- `bash scripts/pre_push_check.sh`: PASS, 410 tests, 4 skipped.

## Key Artifacts

- Pack index:
  `artifacts/runs/task128-oodrive-live-product/submission-packs/task133-submission-pack-v1/index.html`
- Pack README:
  `artifacts/runs/task128-oodrive-live-product/submission-packs/task133-submission-pack-v1/README.md`
- Pack manifest:
  `artifacts/runs/task128-oodrive-live-product/submission-packs/task133-submission-pack-v1/submission_manifest.json`
- Claim matrix:
  `artifacts/runs/task128-oodrive-live-product/submission-packs/task133-submission-pack-v1/claim_matrix.json`
- Artifact inventory:
  `artifacts/runs/task128-oodrive-live-product/submission-packs/task133-submission-pack-v1/artifact_inventory.json`
- Score report:
  `artifacts/runs/task128-oodrive-live-product/submission-scores/task133-submission-pack-v1-score/submission_readiness_score.md`

## Claim Boundary

- `closed_loop_vla_control=false`
- `real_time_vla_control=false`
- `sampled_open_loop_reasoning=true`
- `time_warped_offline_demo=true`
