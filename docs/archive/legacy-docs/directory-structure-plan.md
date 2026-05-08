# Directory Structure And Stub Plan

This is the implementation plan for the first code-bearing pass. It is not code;
it defines the shape future tickets should create.

## Recommended First Runtime Layout

```text
0xDriver/
  pyproject.toml
  src/
    driverx/
      __init__.py
      config.py
      datasets/
        __init__.py
        waymo_e2e.py
        README.md
        AGENTS.md
      visualization/
        __init__.py
        camera_panels.py
        trajectories.py
        README.md
        AGENTS.md
      reasoning/
        __init__.py
        schema.py
        base.py
        mock.py
        README.md
        AGENTS.md
      planning/
        __init__.py
        candidates.py
        smoothing.py
        ranking.py
        README.md
        AGENTS.md
      evaluation/
        __init__.py
        ade.py
        latency.py
        README.md
        AGENTS.md
      submission/
        __init__.py
        waymo_packager.py
        README.md
        AGENTS.md
      pipeline/
        __init__.py
        run_scene.py
        README.md
        AGENTS.md
  notebooks/
    01_waymo_e2e_exploration.ipynb
    02_pipeline_analysis.ipynb
  configs/
    local.sample.yaml
    mock_reasoner.yaml
  data/
    README.md
    .gitignore
  artifacts/
    README.md
    .gitignore
  tests/
    test_reasoning_schema.py
    test_trajectory_shapes.py
    test_ade.py
    test_submission_packager.py
```

## Module Responsibilities

- `config`: load dataset path, output path, backend selection, and run limits.
- `datasets`: parse Waymo E2E TFRecords and expose a small frame bundle object.
- `visualization`: render camera strips and overlay trajectories.
- `reasoning`: define validated structured intent and backend adapters.
- `planning`: create, smooth, and rank candidate trajectories.
- `evaluation`: compute ADE and stage latency summaries.
- `submission`: generate Waymo E2E protobuf shards and tar/gzip packaging.
- `pipeline`: orchestrate one scene or a tiny validation slice end to end.

## First Stub Contracts

```python
class FrameBundle:
    frame_name: str
    front_images: list[np.ndarray]
    ego_history_xy: np.ndarray
    future_xy: np.ndarray | None

class DrivingIntent:
    scene_type: str
    hazards: list[str]
    ego_intent: str
    target_behavior: str
    speed_profile: str
    lateral_bias: str
    uncertainty: float

class Reasoner:
    def infer_intent(self, frame: FrameBundle) -> DrivingIntent: ...

def generate_candidates(frame: FrameBundle, intent: DrivingIntent) -> list[np.ndarray]: ...

def smooth_trajectory(candidate: np.ndarray) -> np.ndarray: ...

def average_displacement_error(prediction: np.ndarray, ground_truth: np.ndarray) -> float: ...
```

These signatures are illustrative; implementation tickets should tighten them
with concrete types after package selection.

## Build Order

1. Packaging and config skeleton.
2. Waymo loader plus one-frame visualization.
3. Mock reasoner schema and evidence writer.
4. Candidate trajectory generator.
5. Smoothing/ranking layer.
6. ADE and latency reporting.
7. Submission packager dry-run.
8. Analysis notebook and demo artifacts.
9. Optional cloud VLA backend.

## 1 -> 10 -> 100 Ramp

- 1: one frame, mock reasoner, one generated prediction, one overlay.
- 10: small validation slice, ADE table, latency table, failure case.
- 100: batched inference cache, resumable artifacts, submission shards.

## Design Rules

- Keep Waymo-specific protobuf handling isolated to `datasets` and `submission`.
- Keep model/provider code out of `planning`.
- Treat model output as untrusted until schema validation passes.
- Save enough intermediate artifacts to debug failures without rerunning cloud
  inference.
- Do not optimize FlashDrive-style CUDA internals until the offline pipeline
  proves useful.
