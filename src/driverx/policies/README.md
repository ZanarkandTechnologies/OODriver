# driverx.policies

## Purpose

Owns the runtime boundary between generated CARLA scenarios and autonomy
policies. The same interface can wrap mock policies, deterministic local
fallbacks, API VLMs, SimLingo/CarLLaVA, or Alpamayo later.

## Public API

- `PolicyContext`
- `PolicyDecision`
- `expected_alpamayo_schema(...)`
- `classify_alpamayo_probe_artifacts(...)`
- `build_alpamayo_input_package(...)`
- `materialize_alpamayo_input(...)`
- `build_alpamayo_package_from_ood_demo(...)`
- `load_alpamayo_torch_tensors(...)`
- `run_alpamayo_live_package(...)`
- `inspect_alpamayo_release(...)`
- `alpamayo_prediction_to_trajectory(...)`
- `run_alpamayo_offline_fixture(...)`
- `trajectory_to_control_trace(...)`
- `load_policy_decision_trajectory(...)`
- `select_policy_adapter(name, memory_aware=False)`
- `run_policy_fixture(...)`
- `write_policy_decision(...)`

`trajectory_to_control_trace(...)` defaults to the SimLingo/Fail2Drive-style
PID bridge: future waypoints define desired speed and a lookahead target, then
speed PID and lateral PID produce bounded `steer`, `throttle`, and `brake`.
Use `TrajectoryControlConfig(controller="geometric")` only for legacy contract
tests that need the older point-by-point geometric mapping.

## Example

```bash
PYTHONPATH=src python3 -m driverx run-policy-fixture --policy mock --run-id task13-policy
PYTHONPATH=src python3 -m driverx probe-alpamayo --artifact-root artifacts/remote/alpamayo-probe/latest
PYTHONPATH=src python3 -m driverx build-alpamayo-input --fixture construction_merge --with-memory
PYTHONPATH=src python3 -m driverx build-alpamayo-ood-package --rgb-folder tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb --tracks tickets/TASK-078/artifacts/task78-live-ood-capture-v3/entity_tracks.json --scenario-report tickets/TASK-078/artifacts/task78-live-ood-capture-v3/carla_ood_demo.json --video-evidence tickets/TASK-079/artifacts/task79-live-ood-video/ood_video_evidence.json
PYTHONPATH=src python3 -m driverx materialize-alpamayo-input --package artifacts/runs/task51-live-alpamayo-capture/alpamayo_carla_input_package.json
PYTHONPATH=src python3 -m driverx run-alpamayo-live --package artifacts/runs/task51-live-alpamayo-capture/alpamayo_carla_input_package.json --prediction-json artifacts/remote/alpamayo-live/latest/alpamayo_live_prediction.json
PYTHONPATH=src python3 -m driverx inspect-alpamayo-release --repo ../external/alpamayo1.5
PYTHONPATH=src python3 -m driverx convert-alpamayo-trajectory --prediction-json artifacts/sample_pred_xyz.json
PYTHONPATH=src python3 -m driverx run-alpamayo-offline --prediction-json artifacts/sample_pred_xyz.json --with-memory
PYTHONPATH=src python3 -m driverx replay-policy-decision --decision tickets/archive/TASK-039/artifacts/live-capture-summary/alpamayo_policy_decision.json --trajectory-frame ego
ALPAMAYO_ATTN_IMPLEMENTATION=eager bash scripts/run_remote_alpamayo_probe.sh root@195.26.233.80 artifacts/remote/alpamayo-probe/latest
```

For the current RunPod RTX 6000 Ada Alpamayo lane, use eager attention for
load probes. SDPA is rejected by Alpamayo's custom architecture; this is tracked
as `MEM-0019`.

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_policies
PYTHONPATH=src python3 -m unittest tests.test_trajectory_control
```
