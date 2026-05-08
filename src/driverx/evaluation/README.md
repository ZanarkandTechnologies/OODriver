# Evaluation

## Purpose

Compute local proxy metrics and reports over saved run artifacts.

## Public API

- `average_displacement_error(prediction, ground_truth)`
- `evaluate_run_dir(run_dir)`
- `score_hero_demo(inputs, thresholds)`
- `score_environment_demo_readiness(inputs, thresholds)`
- `score_environment_reasoned_carla(environment_summary_path=..., visual_proof_path=..., keyframe_analysis_path=..., ...)`
- `score_generator_runtime(inputs)`
- `score_submission_readiness(inputs, thresholds)`
- `write_hero_demo_score(run_dir, report)`
- `write_environment_demo_score(run_dir, report)`
- `write_environment_reasoned_carla_score(run_dir, report)`
- `write_generator_runtime_score(run_dir, report)`
- `write_submission_readiness_score(run_dir, report)`

## Minimal Example

```python
ade = average_displacement_error(prediction, future)
```

```bash
PYTHONPATH=src python3 -m oodrive score-demo \
  --score-input qa/fixtures/hero_demo_score/candidate_demo.json
```

```bash
PYTHONPATH=src python3 -m oodrive score-submission \
  --score-input qa/fixtures/submission_readiness_score/target_submission.json
```

```bash
PYTHONPATH=src python3 -m oodrive score-env-demo \
  --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json \
  --demo-manifest artifacts/runs/task135-env-demo-v1/environment-demo-packs/task135-env-demo-v1/environment_demo_manifest.json
```

```bash
PYTHONPATH=src python3 -m oodrive score-env-proof \
  --environment-summary artifacts/runs/task135-env-demo-v1/environment_suite_summary.json \
  --visual-proof artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json \
  --keyframe-analysis artifacts/runs/task137-keyframe-analysis-v1/keyframe_analysis.json \
  --overlay-report artifacts/runs/task138-env-reasoned-carla-v1/environment_reasoned_carla_demo.json \
  --metric-only
```

```bash
PYTHONPATH=src python3 -m oodrive score-generator-runtime \
  --runtime-manifest artifacts/runs/task141-fake-carla-smoke/generated_scenario_runtime.json \
  --metric-only
```

For live CARLA proof pulled from Kasm:

```bash
PYTHONPATH=src python3 -m oodrive score-generator-runtime \
  --runtime-manifest artifacts/runs/task141-runpod-carla-live/generated_scenario_runtime.json \
  --metric-only
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_evaluation tests.test_hero_demo_score tests.test_environment_demo_score tests.test_environment_reasoned_carla tests.test_generated_carla_runtime tests.test_submission_readiness_score
```
