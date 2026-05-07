# TASK-129: Productize OODrive Live Alpamayo Inference

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-128
- location: `src/driverx/policies`, `src/driverx/scenarios`, `src/oodrive`, `tests`
- enter when: TASK-128 proves live Alpamayo inference through a manual remote bridge
- leave when: `oodrive infer --db ... --run ...` builds or reuses the Alpamayo package, runs local GPU inference where Alpamayo is installed, writes `alpamayo_live_prediction.json`, and returns the exact `oodrive reason` command
- blockers: none for planning; real execution requires an Alpamayo-capable GPU host with the model cache/HF auth already configured
- spawned follow-ups: none
- complexity: M

### Summary

Remove the last manual step from the TASK-128 proof. Today the product story is
real, but the live Alpamayo call is invoked by staging a package and running the
extracted remote inference script. This ticket turns that bridge into a first
class OODrive command.

### Scope

- In scope: in-place Alpamayo package staging, optional-dependency GPU inference
  runner, `oodrive infer`, DB command/run artifact writeback, tests with a fake
  inference backend, and clear blocked artifacts when Alpamayo dependencies are
  unavailable.
- Out of scope: real-time closed-loop control, SSH orchestration, HF token
  management, and performance optimization.

### Plan

#### Change

Add:

```bash
oodrive infer \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --run artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/run_manifest.json \
  --run-id task129-live-infer
```

The command should build the Alpamayo package from the live CARLA run if needed,
run Alpamayo locally when the current Python environment provides
`alpamayo1_5`, `torch`, and CUDA, then write:

- `alpamayo_live_prediction.json`
- `alpamayo_live_summary.md`
- `gpu_snapshot.txt`
- `memory_usage.json`
- DB command artifact pointing to the next `oodrive reason` command.

#### Why

The final demo should be operator-simple: generate, place, infer, reason. The
manual bridge is acceptable evidence for TASK-128, but it is too fragile for a
repeatable product workflow.

#### Before -> After

- Before: live inference works but requires manually extracting and invoking
  the remote script.
- After: OODrive owns the live inference command and can fail cleanly with
  actionable setup blockers.

#### Touch

- `src/driverx/policies/alpamayo_local_inference.py`
- `src/driverx/policies/alpamayo_local_inference_cli.py`
- `src/driverx/scenarios/studio_product_runtime.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/cli_extensions.py`
- `tests/test_alpamayo_local_inference.py`
- `tests/test_oodrive_cli.py`
- `README.md`, `docs/HISTORY.md`

#### Signature Delta

```python
stage_alpamayo_package_for_local_inference(
    package_path: Path,
    run_dir: Path,
) -> dict[str, Any]

run_alpamayo_local_inference(
    package_path: Path,
    output_root: Path,
    *,
    run_id: str,
    model_id: str = "nvidia/Alpamayo-1.5-10B",
    attn_implementation: str = "eager",
    num_traj_samples: int = 1,
    max_generation_length: int = 256,
) -> dict[str, Any]

run_studio_infer(
    db_path: Path,
    *,
    run_manifest_path: Path | None,
    package_path: Path | None,
    output_root: Path | None,
    run_id: str | None,
) -> StudioCommandResult
```

#### Type Sketch

```python
AlpamayoInferenceResult = {
  "status": "passed" | "blocked" | "failed",
  "prediction_path": str,
  "summary_path": str,
  "latency_ms": float | None,
  "vram_peak_mb": float | None,
  "output_shapes": dict[str, list[int]],
  "cot_summary": str,
  "blockers": list[str],
}
```

#### Typed Flow Example

`oodrive infer --db ... --run ...`
-> load run manifest
-> build `alpamayo_carla_input_package.json` from RGB/tracks
-> stage package under `reasoning/inference/<run-id>/input`
-> run Alpamayo in the current GPU env
-> write prediction JSON
-> append DB command
-> next command: `oodrive reason --prediction-json <prediction>`.

### Acceptance Criteria

- [ ] AC-1: `oodrive infer --help` exists and is product-facing.
- [ ] AC-2: The command can build/reuse an Alpamayo package from a live run.
- [ ] AC-3: Missing Alpamayo/CUDA dependencies produce a blocked prediction
  artifact rather than a stack trace.
- [ ] AC-4: A fake-backend unit test proves DB artifact writeback and next
  command generation.
- [ ] AC-5: On the Kasm pod, real `oodrive infer` completes against the
  TASK-128 package or records the exact runtime blocker.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_local_inference tests.test_oodrive_cli`
- `bash scripts/pre_push_check.sh`
- Optional live Kasm proof using TASK-128 DB/run manifest.

### Evidence

- Pending.

### Blockers

- Pending implementation.
