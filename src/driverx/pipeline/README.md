# Pipeline

## Purpose

Coordinate complete scene and batch runs across loader, reasoner, planner,
evaluator, renderer, and submission packager.

## Public API

- `inspect_scene(config)`
- `run_scene(config)`
- `run_loaded_scene(config, frame)`
- `run_batch(config, fixture_names=None, frame_start=None, frame_count=None)`
- `run_experiment(config, frame_start=None, frame_count=None)`
- `run_rag_comparison(policy, fixture, behavior_id, output_root, run_id)`
- `run_end_to_end_ood_demo(config)`
- `build_alpamayo_ood_evaluation(run_dir, inputs)`
- `build_alpamayo_ood_scene_report(run_dir, inputs)`
- `build_bad_path_stress_demo(output_root=..., run_id=..., case_ids=...)`
- `build_fail2drive_extension_report(generated_source_paths=..., output_dir=...)`
- `build_final_submission_pack(run_dir, eval_matrix_path=..., scenario_studio_path=..., ...)`
- `build_ood_video_evidence(run_dir, inputs)`
- `build_environment_demo_pack(environment_summary_path=..., output_root=..., run_id=...)`
- `select_carla_keyframes(visual_proof_path=..., run_manifest_path=..., limit=...)`
- `build_keyframe_analysis(visual_proof_path=..., db_path=..., run_manifest_path=..., backend=..., ...)`
- `build_environment_reasoned_carla_video(environment_summary_path=..., visual_proof_path=..., keyframe_analysis_path=..., ...)`
- `build_submission_demo_pack(run_dir, ...)`
- `build_submission_story_pack(db_path=..., run_manifest_path=..., evaluation_path=..., hero_video_path=..., hero_score_path=..., ...)`
- `build_ood_suite_report(run_dir, scenario_summary_path=..., route_pack_path=..., ...)`

## Minimal Example

```python
from pathlib import Path

from driverx.core.config import load_config
from driverx.pipeline import EndToEndOodDemoConfig, run_batch, run_end_to_end_ood_demo
from driverx.pipeline import run_experiment, run_rag_comparison, run_scene

result = run_scene(load_config("configs/mock.yaml"))
batch = run_batch(load_config("configs/mock.yaml"))
experiment = run_experiment(load_config("configs/mock.yaml"))
comparison = run_rag_comparison(
    policy="mock",
    fixture="construction_merge",
    behavior_id="motorcycle_filtering",
    output_root=Path("artifacts/runs"),
    run_id="rag-comparison",
)
demo = run_end_to_end_ood_demo(EndToEndOodDemoConfig(run_id="local-ood-demo"))
```

```bash
PYTHONPATH=src python3 -m driverx run-end-to-end-ood-demo \
  --run-id local-ood-demo
```

```bash
PYTHONPATH=src python3 -m driverx build-alpamayo-ood-comparison \
  --baseline-decision tickets/archive/TASK-039/artifacts/live-capture-summary/alpamayo_policy_decision.json \
  --source-package artifacts/runs/task51-live-alpamayo-capture/alpamayo_carla_input_package.json \
  --route-evidence tickets/archive/TASK-055/artifacts/town10-route-evidence/run_evidence.json
```

```bash
PYTHONPATH=src python3 -m driverx build-alpamayo-ood-scene \
  --package tickets/TASK-074/artifacts/generated-scene-package/alpamayo_carla_input_package.json \
  --video-evidence tickets/TASK-073/artifacts/fixture-long-ood-video-v2/ood_video_evidence.json \
  --scenario-report tickets/TASK-072/artifacts/task72-live-candidate/carla_ood_demo.json
```

```bash
PYTHONPATH=src python3 -m driverx build-final-submission-pack \
  --eval-matrix tickets/TASK-101/artifacts/submission-eval-matrix/submission_eval_matrix.json \
  --scenario-studio tickets/TASK-103/artifacts/scenario-studio-v1/scenario_studio_batch.json \
  --alpamayo-rag-batch tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/alpamayo_ood_batch_summary.json \
  --fail2drive-extension tickets/TASK-105/artifacts/fail2drive-extension-report/fail2drive_extension_report.json \
  --hero-video-evidence tickets/TASK-102/artifacts/task102-high-fidelity-hero-v6/ood_video_evidence.json \
  --scenario-browser tickets/archive/TASK-097/artifacts/task97-submission-browser-runpod-v4/scenario_browser.html \
  --run-id final-submission-pack-v7-task102
```

```bash
PYTHONPATH=src python3 -m driverx run-scripted-ood-campaign \
  --config configs/scripted_ood_campaign.runpod.high_fidelity.yaml \
  --run-id task102-high-fidelity-hero
```

```bash
PYTHONPATH=src python3 -m driverx build-fail2drive-extension-report \
  --source tickets/TASK-103/artifacts/scenario-studio-v1/scenario_studio_batch.json \
  --source tickets/TASK-101/artifacts/submission-eval-matrix/submission_eval_matrix.json \
  --run-id fail2drive-extension-report
```

```bash
PYTHONPATH=src python3 -m driverx build-ood-suite-report \
  --scenario-summary artifacts/runs/scenario-forge/scenario_suite_summary.json \
  --route-pack artifacts/runs/bench2drive-route-pack/bench2drive_route_pack.json \
  --overlay-plan artifacts/runs/overlay-injection/overlay_injection_plan.json \
  --sidecar-plan artifacts/runs/simlingo-sidecar/simlingo_sidecar_plan.json \
  --sidecar-run artifacts/runs/simlingo-sidecar-run/simlingo_sidecar_run.json
```

```bash
PYTHONPATH=src python3 -m oodrive export-submission \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --run artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/run_manifest.json \
  --evaluation artifacts/runs/task128-oodrive-live-product/reasoning/evaluations/task128-oodrive-live-alpamayo-fresh-evaluation/policy_evaluation.json \
  --hero-video artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/oodrive_hero_demo.mp4 \
  --hero-score artifacts/runs/task128-oodrive-live-product/demo-scores/task131-score-gated-hero-v2-score/hero_demo_score.json
```

```bash
PYTHONPATH=src python3 -m oodrive export-env-demo \
  --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json \
  --hero-video artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/oodrive_hero_demo.mp4
```

```bash
PYTHONPATH=src python3 -m oodrive render-env \
  --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json \
  --template-id roadside_market_occlusion \
  --prompt "wet Malaysian roadside market occlusion with scooter filtering" \
  --run-id task136-env-c3-proof-v1
```

```bash
PYTHONPATH=src python3 -m oodrive analyze-keyframes \
  --visual-proof artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json \
  --db artifacts/runs/task136-env-c3-proof-v1/scenario_studio_db.json \
  --run artifacts/runs/task136-env-c3-proof-v1/runs/task136-env-c3-proof-v1/run_manifest.json \
  --backend fake \
  --run-id task137-keyframe-analysis-v1
```

`env-demo-video` assembles an MP4 when the visual proof and keyframe analysis
contain same-lineage image paths. Without those frames, it writes a blocked
story/overlay pack and keeps the claim boundaries explicit.

```bash
PYTHONPATH=src python3 -m oodrive env-demo-video \
  --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json \
  --visual-proof artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json \
  --keyframe-analysis artifacts/runs/task137-keyframe-analysis-v1/keyframe_analysis.json \
  --run-id task138-env-reasoned-carla-v1
```

```bash
PYTHONPATH=src python3 -m oodrive stress-demo \
  --run-id task140-bad-path-stress-v3-lane-safe \
  --target-duration-s 72 \
  --fps 8
```

`stress-demo` is a local scripted bad-path proof, not CARLA visual evidence. A
guarded response only passes when it avoids the collision proxy and keeps
`lane_departure_proxy=false`.

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_pipeline_mock tests.test_batch tests.test_rag_comparison tests.test_end_to_end_ood_demo tests.test_alpamayo_ood_evaluation tests.test_alpamayo_ood_scene tests.test_fail2drive_extension_report tests.test_final_submission_pack tests.test_ood_video_evidence tests.test_ood_suite_report tests.test_environment_demo_pack tests.test_submission_story_pack tests.test_environment_to_carla_visual_proof tests.test_keyframe_analysis tests.test_environment_reasoned_carla tests.test_bad_path_stress_demo
```
