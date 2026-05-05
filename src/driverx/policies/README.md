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
- `load_alpamayo_torch_tensors(...)`
- `inspect_alpamayo_release(...)`
- `alpamayo_prediction_to_trajectory(...)`
- `run_alpamayo_offline_fixture(...)`
- `select_policy_adapter(name, memory_aware=False)`
- `run_policy_fixture(...)`
- `write_policy_decision(...)`

## Example

```bash
PYTHONPATH=src python3 -m driverx run-policy-fixture --policy mock --run-id task13-policy
PYTHONPATH=src python3 -m driverx probe-alpamayo --artifact-root artifacts/remote/alpamayo-probe/latest
PYTHONPATH=src python3 -m driverx build-alpamayo-input --fixture construction_merge --with-memory
PYTHONPATH=src python3 -m driverx materialize-alpamayo-input --package artifacts/runs/task51-live-alpamayo-capture/alpamayo_carla_input_package.json
PYTHONPATH=src python3 -m driverx inspect-alpamayo-release --repo ../external/alpamayo1.5
PYTHONPATH=src python3 -m driverx convert-alpamayo-trajectory --prediction-json artifacts/sample_pred_xyz.json
PYTHONPATH=src python3 -m driverx run-alpamayo-offline --prediction-json artifacts/sample_pred_xyz.json --with-memory
ALPAMAYO_ATTN_IMPLEMENTATION=eager bash scripts/run_remote_alpamayo_probe.sh root@195.26.233.80 artifacts/remote/alpamayo-probe/latest
```

For the current RunPod RTX 6000 Ada Alpamayo lane, use eager attention for
load probes. SDPA is rejected by Alpamayo's custom architecture; this is tracked
as `MEM-0019`.

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_policies
```
