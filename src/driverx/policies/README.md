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
- `inspect_alpamayo_release(...)`
- `alpamayo_prediction_to_trajectory(...)`
- `select_policy_adapter(name, memory_aware=False)`
- `run_policy_fixture(...)`
- `write_policy_decision(...)`

## Example

```bash
PYTHONPATH=src python3 -m driverx run-policy-fixture --policy mock --run-id task13-policy
PYTHONPATH=src python3 -m driverx probe-alpamayo --artifact-root artifacts/remote/alpamayo-probe/latest
PYTHONPATH=src python3 -m driverx inspect-alpamayo-release --repo ../external/alpamayo1.5
PYTHONPATH=src python3 -m driverx convert-alpamayo-trajectory --prediction-json artifacts/sample_pred_xyz.json
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_policies
```
