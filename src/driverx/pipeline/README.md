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
- `build_alpamayo_ood_evaluation(run_dir, inputs)`
- `build_ood_suite_report(run_dir, scenario_summary_path=..., route_pack_path=..., ...)`

## Minimal Example

```python
from pathlib import Path

from driverx.core.config import load_config
from driverx.pipeline import run_batch, run_experiment, run_rag_comparison, run_scene

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
```

```bash
PYTHONPATH=src python3 -m driverx build-alpamayo-ood-comparison \
  --baseline-decision tickets/TASK-039/artifacts/live-capture-summary/alpamayo_policy_decision.json \
  --source-package artifacts/runs/task51-live-alpamayo-capture/alpamayo_carla_input_package.json \
  --route-evidence tickets/TASK-055/artifacts/town10-route-evidence/run_evidence.json
```

```bash
PYTHONPATH=src python3 -m driverx build-ood-suite-report \
  --scenario-summary artifacts/runs/scenario-forge/scenario_suite_summary.json \
  --route-pack artifacts/runs/bench2drive-route-pack/bench2drive_route_pack.json \
  --overlay-plan artifacts/runs/overlay-injection/overlay_injection_plan.json \
  --sidecar-plan artifacts/runs/simlingo-sidecar/simlingo_sidecar_plan.json \
  --sidecar-run artifacts/runs/simlingo-sidecar-run/simlingo_sidecar_run.json
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_pipeline_mock tests.test_batch tests.test_rag_comparison tests.test_alpamayo_ood_evaluation tests.test_ood_suite_report
```
