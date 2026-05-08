# TASK-158: Paused Receding-Horizon CARLA Runner

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-157, TASK-141
- location: `src/driverx/simulators`, `src/driverx/policies`, `src/driverx/scenarios/studio_product_cli.py`, `tests`, `tickets/TASK-158`
- enter when: the closed-loop trace contract exists and generated CARLA scenarios can be run live or fake.
- leave when: OODrive can run a fake/cached paused receding-horizon loop that repeatedly captures CARLA observations, obtains a policy trajectory, applies bounded controls, ticks CARLA, and writes a valid `ClosedLoopRunTrace`.
- blockers: real Alpamayo runtime is TASK-159/TASK-160; this ticket must pass with fake/cached policy adapters.
- spawned follow-ups: TASK-159, TASK-160
- complexity: L

### Summary

Implement the controller loop independent of live model latency. The first proof uses fake/cached policy inference so we can harden synchronization, frame ordering, action application, safety clamps, planned-vs-actual path, and trace writing before plugging in remote Alpamayo.

### Gap Analysis

- Current state: `run_carla_ood_demo` owns a full scripted run; `run_cached_ood_replay` applies one precomputed trajectory; neither alternates policy inference and CARLA actions.
- Production expectation: a closed-loop runner coordinates sensors, policy inference, control application, world ticks, metrics, cleanup, and trace persistence.
- Missing gaps: no step orchestrator, no per-step checkpoint package, no recurrence trace, no planned-vs-actual deviation metric.
- Recommendation: build the runner with adapter modes `fake`, `cached-decision`, and later `alpamayo-remote`.

### Plan

#### Change

Add:

```bash
PYTHONPATH=src python3 -m oodrive closed-loop-run \
  --db artifacts/runs/task141-realistic-ood-generation-v1/scenario_studio_db.json \
  --scenario-id <scenario-id> \
  --policy fake-trajectory \
  --backend fake-carla \
  --run-id task158-paused-loop-fake
```

#### Why

Closed-loop bugs are usually orchestration bugs: stale sensor frames, bad tick ownership, controls not applied, or later observations not caused by earlier actions. Fake mode lets us solve those deterministically.

#### Before -> After

- Before: one policy decision is replayed or a full scripted run is captured.
- After: OODrive has a receding-horizon loop with N repeated observe/infer/act/tick steps and a trace compatible with TASK-157 scoring.

#### Touch

- `src/driverx/simulators/carla_closed_loop_runner.py` (new)
- `src/driverx/simulators/carla_ood_demo.py`
- `src/driverx/policies/closed_loop_types.py`
- `src/driverx/policies/trajectory_control.py`
- `src/driverx/scenarios/studio_product_closed_loop_runtime.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `tests/test_carla_closed_loop_runner.py` (new)
- `tests/test_closed_loop_control_score.py`
- `tests/test_oodrive_cli.py`

#### Inspect

- `src/driverx/simulators/carla_policy_replay.py`
- `src/driverx/simulators/carla_cached_ood_replay.py`
- `src/driverx/simulators/carla_alpamayo_capture.py`
- `src/driverx/policies/alpamayo_trajectory.py`
- `src/driverx/simulators/carla_road_frame.py`

#### Signature Delta

```python
run_paused_closed_loop(config: PausedClosedLoopConfig, run_dir: Path, policy_adapter: ClosedLoopPolicyAdapter, carla_module: object | None = None) -> ClosedLoopRunTrace
capture_closed_loop_observation(world, ego, cameras, step_index: int) -> ClosedLoopObservation
apply_control_chunk(ego, world, trace: ControlTrace, chunk_ticks: int) -> AppliedControlChunk
```

#### Type Sketch

```python
PausedClosedLoopConfig = {
  "backend": "fake-carla" | "carla-live",
  "steps": int,
  "control_ticks_per_step": int,
  "fixed_delta_seconds": float,
  "camera_width": int,
  "camera_height": int,
}

ClosedLoopObservation = {
  "frame_id": int,
  "sim_time_s": float,
  "image_paths": list[str],
  "ego_pose": dict,
  "actor_tracks": list[dict],
  "alpamayo_package_path": str | None,
}
```

#### Typed Flow Example

Step 0 captures frame 100, fake policy predicts a stop/creep trajectory, OODrive converts it into 4 bounded controls, applies them with `world.tick()`, then step 1 captures frame 104. The trace records `input_frame_id=100`, `post_action_frame_id=104`, and the next step's `input_frame_id=104`.

#### Execution Steps

1. Define policy adapter protocol for closed-loop step inference.
2. Build fake adapter returning deterministic trajectory candidates for stop, creep, and swerve cases.
3. Add fake-CARLA world/actor/camera tests that prove tick and frame ordering.
4. Add live-CARLA branch using synchronous mode/fixed delta when available.
5. Write `closed_loop_trace.json` and Markdown report.
6. Register `oodrive closed-loop-run`.
7. Run `score-closed-loop` on fake/cached outputs and focused tests.

#### Recommendation

Implement fake/cached first and make live CARLA a backend of the same runner, not a separate script. This keeps the final Kasm proof from becoming a one-off.

#### Options Considered

- Modify `run_carla_ood_demo` directly: tempting, but that file is already large and primarily owns scripted demo runs.
- New runner that reuses CARLA helpers: cleaner ownership and easier tests.
- ROS bridge: too much setup for deadline.

#### Blast Radius

- New runtime module plus additive CLI.
- Existing scripted CARLA demo remains unchanged except shared helper extraction if needed.

#### Risks

- Live synchronous mode can conflict with Traffic Manager or other clients. Mitigation: one-tick-owner invariant and explicit restore of world settings.
- Waypoint-to-control can leave road. Mitigation: reuse safety clamps and add road/lane-departure metrics.

### Acceptance Criteria

- [ ] AC-1: Fake backend writes a valid paused receding-horizon trace with at least 3 observe/infer/act/tick iterations.
- [ ] AC-2: Each step proves `post_action_frame_id >= input_frame_id + applied_control_count`.
- [ ] AC-3: Planned-vs-actual path and safety clamps are recorded.
- [ ] AC-4: `score-closed-loop` passes the fake/cached trace without real-time claims.

### Verification

```bash
PYTHONPATH=src python3 -m unittest tests.test_carla_closed_loop_runner tests.test_closed_loop_control_score tests.test_trajectory_control tests.test_oodrive_cli
bash scripts/pre_push_check.sh
```

### Blockers

- None for fake/cached runner.

### Implementation Evidence

- Added `src/driverx/simulators/carla_closed_loop_runner.py`.
- Added `oodrive closed-loop-run --backend fake-carla --policy fake-trajectory`.
- Smoke generated a 3-step paused receding-horizon trace with `control_applied_count=12`.
- `tests.test_carla_closed_loop_runner` passed; full `bash scripts/pre_push_check.sh` passed with `456 tests OK, 5 skipped`.
- Review: `tickets/TASK-161/artifacts/review/task157-164-impl-review.json`

### Plan Review

- `tickets/TASK-157/artifacts/review/task157-160-closed-loop-plan-review.json`
