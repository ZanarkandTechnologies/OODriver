# TASK-123: Time-Warped Alpamayo Trajectory Replay Controller

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-121, TASK-122
- location: `src/driverx/simulators`, `src/driverx/policies`, `tickets/TASK-123/artifacts`
- enter when: checkpoint predictions exist for the flagship scenario
- leave when: CARLA replay follows Alpamayo waypoint chunks in a paused/time-warped loop and records planned-vs-actual paths
- blockers: waiting for H100 Kasm VM and TASK-122 predictions
- spawned follow-ups: TASK-124
- complexity: L

### Summary

Turn Alpamayo's open-loop checkpoint predictions into a conservative CARLA
trajectory replay. The target is not real-time control; it is a transparent
paused receding-horizon demo where the model's planned path affects the ego
trajectory.

### Plan

#### Change

Add a trajectory follower that consumes checkpoint predictions, projects
waypoints into CARLA's road-local frame, applies bounded throttle/brake/steer or
teleport-smooth controls, and records actual path deviation.

#### Signature Delta

```python
run_alpamayo_timewarped_replay(config: ReplayConfig) -> ReplaySummary
```

#### Type Sketch

```python
ReplayStep = {
  "checkpoint_id": str,
  "planned_waypoints": list[dict],
  "actual_path": list[dict],
  "control_trace": list[dict],
  "safety_interventions": list[str],
}
```

### Acceptance Criteria

- [ ] AC-1: Replay writes planned-vs-actual path for each checkpoint.
- [ ] AC-2: Video and tracks show ego moving on-road through the OOD setup.
- [ ] AC-3: Safety/claim boundaries label `time_warped_offline_demo=true`.
- [ ] AC-4: If control is unstable, fallback to smooth waypoint teleport is
  recorded explicitly.

### Verification

- Unit test for waypoint/control conversion.
- Live replay proof on H100 Kasm VM.
- Video duration and quality gate.

### Blockers

- H100 Kasm VM, CARLA runtime, TASK-122 predictions.
