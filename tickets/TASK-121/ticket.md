# TASK-121: Flagship CARLA Checkpoint Capture Loop

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-120
- location: `src/driverx/simulators`, `configs`, `tickets/TASK-121/artifacts`
- enter when: TASK-120 defines the flagship scenario contract and H100 Kasm VM is available
- leave when: CARLA can run the flagship scenario slowly and save timestamped camera frames, ego history, actor tracks, risk events, and a checkpoint manifest
- blockers: waiting for H100 Kasm VM endpoint and CARLA host readiness
- spawned follow-ups: TASK-122
- complexity: M

### Summary

Implement the capture side of paused receding-horizon evaluation. The runner
does not need Alpamayo yet; it must produce model-ready checkpoints from the
flagship scenario.

### Plan

#### Change

Add a checkpoint capture runner that reuses the high-fidelity CARLA OOD demo
setup, advances CARLA at controlled ticks, and writes periodic Alpamayo input
packages plus simulator ground-truth tracks.

#### Signature Delta

```python
run_flagship_carla_capture(config: FlagshipCaptureConfig) -> FlagshipCaptureSummary
write_flagship_capture(run_dir: Path, summary: FlagshipCaptureSummary) -> dict[str, Any]
```

#### Type Sketch

```python
FlagshipCheckpoint = {
  "checkpoint_id": str,
  "sim_time_s": float,
  "camera_images": list[str],
  "ego_history": list[dict],
  "actor_snapshot": list[dict],
  "risk_events": list[dict],
  "alpamayo_package": str,
}
```

### Acceptance Criteria

- [ ] AC-1: Captures at least 8 checkpoints over one flagship run.
- [ ] AC-2: Each checkpoint has camera image paths and ego history.
- [ ] AC-3: Tracks and risk timeline are written.
- [ ] AC-4: Missing CARLA writes a precise blocker instead of crashing.

### Verification

- Fake-CARLA unit test.
- Live H100/Kasm smoke when VM is available.
- `bash scripts/pre_push_check.sh`.

### Blockers

- H100 Kasm VM endpoint and CARLA runtime.
