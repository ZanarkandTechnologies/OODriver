# TASK-122: Alpamayo Checkpoint Inference Batch

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-121
- location: `src/driverx/policies`, `src/driverx/pipeline`, `tickets/TASK-122/artifacts`
- enter when: TASK-121 has checkpoint packages and the H100 Kasm VM has Alpamayo/HF auth ready
- leave when: sampled Alpamayo reasoning and trajectories are produced for each flagship checkpoint with latency/VRAM evidence
- blockers: waiting for H100 Kasm VM and HF-authenticated Alpamayo runtime
- spawned follow-ups: TASK-123
- complexity: M

### Summary

Run Alpamayo frame-by-frame over the captured flagship CARLA checkpoints. This
ticket produces the reasoning/trajectory trace; it does not yet steer CARLA.

### Plan

#### Change

Add a batch runner that consumes `FlagshipCheckpoint` manifests, invokes the
existing Alpamayo materializer/live adapter, and writes one prediction record
per checkpoint.

#### Signature Delta

```python
run_alpamayo_checkpoint_batch(manifest: Path, remote: AlpamayoRemoteConfig) -> AlpamayoCheckpointBatch
```

#### Type Sketch

```python
AlpamayoCheckpointPrediction = {
  "checkpoint_id": str,
  "cot": str,
  "trajectory_xyz": list,
  "latency_ms": float,
  "peak_vram_mb": float,
  "memory_context": list[str],
}
```

### Acceptance Criteria

- [ ] AC-1: At least 8 checkpoint predictions are written.
- [ ] AC-2: Each prediction includes CoC/reasoning text and trajectory shape.
- [ ] AC-3: Latency and VRAM are recorded.
- [ ] AC-4: Failed checkpoints preserve individual blockers and do not discard
  successful predictions.

### Verification

- Fake-prediction unit test.
- Live H100 batch proof.
- `bash scripts/pre_push_check.sh`.

### Blockers

- H100 Kasm VM, HF auth, Alpamayo environment.
