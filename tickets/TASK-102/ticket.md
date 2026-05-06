# TASK-102: High-Fidelity CARLA OOD Scenario Runner V2

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-097, TASK-101
- location: `src/driverx/simulators/carla_ood_demo.py`, `src/driverx/pipeline/scripted_ood_campaign.py`, `configs`, `tickets/TASK-102/artifacts`
- enter when: TASK-101 selects the scenarios that need stronger video evidence
- leave when: at least one selected case produces a longer, denser, road-aligned CARLA video with smoother actor motion and clear quality gates
- blockers: RunPod Kasm CARLA server must remain reachable for live evidence; fallback is local/fake quality proof plus blocker report
- spawned follow-ups: TASK-104, TASK-106
- complexity: M
- assignee: generalPurpose

### Summary

Upgrade the video from deterministic harness proof into a judge-visible
simulation artifact. This ticket improves road-following, density, camera
composition, and actor smoothness without trying to make Alpamayo drive
closed-loop yet.

### Scope

- In scope: route-following ego option, Traffic Manager background traffic,
  smoother OOD actor interpolation, chase/front camera presets, denser parked
  and moving actors, stronger video report, and stricter quality thresholds.
- Out of scope: real Meshy GLB import, stock Fail2Drive score, SimLingo, and
  Alpamayo closed-loop control.

### Plan

#### Change

Add a `high_fidelity` mode to the DriverX CARLA OOD demo/campaign path.

#### Why

The current video proves the harness but looks sparse and scripted. The
submission needs a video that communicates "simulation environment for
minimal-shot OOD driving" in the first 10 seconds.

#### Before -> After

- Before: single ego, one scripted OOD actor, sparse props, one camera, low
  traffic density.
- After: road-aligned ego, smoother OOD actor motion, optional background
  traffic, better camera preset, visible environment/behavior labels, and
  quality gates that block weak videos.

#### Touch

- `src/driverx/simulators/carla_ood_demo.py`: high-fidelity config, background
  traffic spawn, smoother control mode, camera preset.
- `src/driverx/pipeline/scripted_ood_campaign.py`: pass new config fields and
  aggregate density/fidelity metrics.
- `src/driverx/pipeline/ood_video_evidence.py`: include camera/fidelity metrics
  in evidence overlay/report if needed.
- `configs/carla_ood_demo.runpod.high_fidelity.yaml`: RunPod target config.
- `configs/scripted_ood_campaign.runpod.high_fidelity.yaml`: selected case run.
- Tests under `tests/test_carla_ood_demo.py` and
  `tests/test_scripted_ood_campaign.py`.

#### Inspect

- `src/driverx/simulators/carla_ood_demo.py / run_carla_ood_demo`
- `src/driverx/simulators/carla_road_frame.py`
- `src/driverx/behaviors/library.py`
- `tickets/TASK-097/artifacts/pulled/.../entity_tracks.json`
- `tickets/TASK-097/artifacts/pulled/.../ood_video_evidence.json`

#### Signature Delta

```python
CarlaOodDemoConfig(...,
  fidelity_mode: str = "scripted",
  background_vehicle_count: int = 0,
  background_pedestrian_count: int = 0,
  camera_preset: str = "ego_front",
  ood_motion_smoothing: str = "linear",
)

run_carla_ood_demo(config, run_dir, *, recipe, behavior, asset_manifests, ...): CarlaOodDemoResult

CarlaOodDemoResult(...,
  background_actor_ids: list[int],
  fidelity_metrics: dict[str, Any],
)
```

#### Type Sketch

```python
FidelityMetrics = {
  "background_vehicle_count": int,
  "background_pedestrian_count": int,
  "camera_preset": str,
  "mean_ood_step_m": float,
  "max_ood_step_m": float,
  "ego_route_progress_m": float,
  "visible_actor_count_mean": float | None,
}
```

#### Typed Flow Example

`EvalMatrixCase(role="hero", behavior_id="motorcycle_filtering")`
-> high-fidelity campaign config
-> `run_carla_ood_demo(...)`
-> `entity_tracks.json + fidelity_metrics`
-> `ood_video_evidence.mp4`
-> quality gates pass only if duration, road alignment, conflict, and density
targets pass.

#### Execution Steps

1. Add config fields with safe defaults preserving existing behavior.
2. Implement background traffic spawn using stock CARLA vehicle/pedestrian
   blueprints and cleanup accounting.
3. Add camera presets: `ego_front`, `chase`, and `wide_context`.
4. Smooth OOD actor transforms by limiting per-tick jumps and recording motion
   metrics.
5. Extend quality evidence with density/fidelity metrics.
6. Run fake-CARLA tests locally.
7. Run one selected case on RunPod Kasm if the server is reachable.
8. Pull back compact artifacts and update TASK-101 matrix status.

#### Recommendation

Prioritize one high-quality hero video over many mediocre videos. Breadth can
come from the scenario browser; the video must sell the environment.

#### Options Considered

- Add Meshy/custom objects first: flashy but risky and not necessary for the
  judging brief.
- Chase stock Fail2Drive route score first: higher benchmark purity but too
  runtime-risky under deadline.
- Recommended: improve DriverX-owned CARLA evidence because it is under our
  control and directly satisfies "create a simulation environment."

#### Blast Radius

Medium. Touches CARLA runtime code but defaults must preserve existing tests and
artifacts.

#### Risks

- Background actors can destabilize quality gates. Keep counts low and cleanup
  strict.
- RunPod CARLA may hang. Preserve fake-CARLA tests and produce a precise live
  blocker if needed.

### Gap Analysis

Current video is submission-credible as proof, but not yet persuasive as a
simulator demo. A production-grade OOD sim demo needs road-local placement,
dense enough context, readable camera framing, smooth actor motion, and explicit
quality gates. This ticket moves to that bar without expanding into custom
engine work.

### Acceptance Criteria

- [ ] AC-1: Existing scripted OOD tests pass with default mode unchanged.
- [ ] AC-2: High-fidelity mode records background actor counts and motion
  smoothness metrics.
- [ ] AC-3: One selected case produces or attempts a 45-90s RunPod CARLA video
  with quality report.
- [ ] AC-4: Weak/buggy videos are blocked from hero promotion by quality gates.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_carla_ood_demo tests.test_scripted_ood_campaign tests.test_scenario_quality`
- `bash scripts/pre_push_check.sh`
- Optional live proof on RunPod Kasm:
  `PYTHONPATH=src /workspace/driverx_py312/bin/python -m driverx run-scripted-ood-campaign --config configs/scripted_ood_campaign.runpod.high_fidelity.yaml --run-id task102-high-fidelity-hero`

### Autonomy Readiness

- Inputs available: RunPod Kasm SSH/Kasm workspace, current CARLA runtime,
  existing configs.
- Human gates: if Kasm pod dies, user must restart/provide pod access.
- Compute: RunPod Kasm for live video, local tests otherwise.
- Stop condition: one better video or a precise CARLA runtime blocker.

### Evidence

- `tickets/TASK-102/artifacts/high_fidelity_campaign_summary.json`
- `tickets/TASK-102/artifacts/high_fidelity_video_evidence.json`
- `tickets/TASK-102/artifacts/high_fidelity_preview.png`
- QA/review report

### Blockers

- Live video depends on a reachable graphics-capable CARLA server.
