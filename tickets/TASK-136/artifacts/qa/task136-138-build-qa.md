# TASK-136 through TASK-138 Build QA

- Captured at: `2026-05-08 05:04 +0800`
- Scope: `oodrive render-env`, `oodrive analyze-keyframes`, `oodrive env-demo-video`, `oodrive score-env-proof`
- Verdict: local product chain passes dry-run/blocked QA; final 90+ proof remains blocked on live Kasm CARLA RGB frames and real/model-backed keyframe evidence.

## Commands

```bash
PYTHONPATH=src python3 -m oodrive render-env --help
```

PASS.

```bash
PYTHONPATH=src python3 -m oodrive render-env \
  --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json \
  --template-id roadside_market_occlusion \
  --prompt "wet Malaysian roadside market occlusion with scooter filtering" \
  --run-id task136-env-c3-proof-v1
```

PASS. Wrote dry-run same-lineage candidate artifacts and a blocked/no-preview visual proof manifest.

```bash
PYTHONPATH=src python3 -m oodrive render-env \
  --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json \
  --template-id roadside_market_occlusion \
  --prompt "wet Malaysian roadside market occlusion with scooter filtering" \
  --run-id task136-env-c3-proof-live-blocked-v2 \
  --live
```

PASS/BLOCKED AS EXPECTED. Local host lacks CARLA Python/runtime; manifest includes Kasm RunPod setup guidance.

```bash
PYTHONPATH=src python3 -m oodrive analyze-keyframes --help
```

PASS.

```bash
PYTHONPATH=src python3 -m oodrive analyze-keyframes \
  --visual-proof artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json \
  --db artifacts/runs/task136-env-c3-proof-v1/scenario_studio_db.json \
  --run artifacts/runs/task136-env-c3-proof-v1/runs/task136-env-c3-proof-v1/run_manifest.json \
  --backend fake \
  --keyframes 8 \
  --run-id task137-keyframe-analysis-v1
```

PASS/BLOCKED AS EXPECTED. The command wrote `keyframe_analysis.json` and reported that no CARLA keyframe images are available until `render-env --live` runs on Kasm.

```bash
PYTHONPATH=src python3 -m oodrive env-demo-video --help
PYTHONPATH=src python3 -m oodrive score-env-proof --help
```

PASS.

```bash
PYTHONPATH=src python3 -m oodrive env-demo-video \
  --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json \
  --visual-proof artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json \
  --keyframe-analysis artifacts/runs/task137-keyframe-analysis-v1/keyframe_analysis.json \
  --run-id task138-env-reasoned-carla-v1
```

PASS/BLOCKED AS EXPECTED. Story/overlay report is written; MP4 rendering is withheld because the source proof has no preview/keyframe images.

```bash
PYTHONPATH=src python3 -m oodrive score-env-proof \
  --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json \
  --visual-proof artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json \
  --keyframe-analysis artifacts/runs/task137-keyframe-analysis-v1/keyframe_analysis.json \
  --overlay-report artifacts/runs/task138-env-reasoned-carla-v1/environment_reasoned_carla_demo.json \
  --run-id task138-env-reasoned-carla-score-v1 \
  --metric-only
```

PASS/BLOCKED AS EXPECTED.

```text
METRIC environment_to_reasoned_carla_score=45.0000
METRIC cli_generation=20.0000
METRIC same_run_carla_visual=7.0000
METRIC keyframe_reasoning=2.0000
METRIC video_readiness=6.0000
METRIC reproducibility=10.0000
```

```bash
python3 -m compileall -q src tests
```

PASS.

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_environment_reasoned_carla \
  tests.test_keyframe_analysis \
  tests.test_environment_to_carla_visual_proof \
  tests.test_environment_demo_pack \
  tests.test_environment_demo_score \
  tests.test_oodrive_cli
```

PASS: 24 tests OK.

```bash
tickets/TASK-136/autoresearch/autoresearch.sh
```

PASS: `environment_to_reasoned_carla_score=45.0000`.

```bash
tickets/TASK-136/autoresearch/autoresearch.checks.sh
```

PASS: 33 tests OK.

```bash
./autoresearch.sh
```

PASS. Repo-level submission readiness remains strong:

```text
METRIC submission_readiness_score=96.3500
METRIC hero_demo_score=100.0000
METRIC challenge_adherence=15.0000
METRIC minimal_shot_simulation_environment=17.2500
METRIC judge_comprehension_pack=16.0000
METRIC operator_reproducibility=12.0000
METRIC code_quality=7.0000
```

```bash
./autoresearch.checks.sh
```

PASS: 22 tests OK.

```bash
bash scripts/pre_push_check.sh
```

PASS: 425 tests OK, 5 skipped. The large-file warning remains advisory and pre-existing in this repository shape.

## Evidence Artifacts

- `artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json`
- `artifacts/runs/task136-env-c3-proof-live-blocked-v2/env_carla_proof_manifest.json`
- `artifacts/runs/task137-keyframe-analysis-v1/keyframe_analysis.json`
- `artifacts/runs/task138-env-reasoned-carla-v1/environment_reasoned_carla_demo.json`
- `artifacts/runs/task138-env-reasoned-carla-score-v1/environment_reasoned_carla_score.json`

## Remaining Blockers

- Live Kasm/CARLA run must produce `carla_environment_preview.png` and RGB frames for the selected generated environment.
- `oodrive analyze-keyframes` must be rerun against those frames; fake backend is sufficient for product smoke, while `alpamayo-local` is required for real model evidence.
- `oodrive env-demo-video` can now assemble MP4s from preview/keyframe images, but the current local artifact has no source images to render.
- Final score target remains `>=90`; current local dry-run/blocked score is `45.0`.
