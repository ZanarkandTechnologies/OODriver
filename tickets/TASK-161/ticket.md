# TASK-161: CARLA Synchronous Sensor Barrier For Alpamayo Checkpoints

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-157, TASK-158
- location: `src/driverx/simulators`, `tests`, `tickets/TASK-161`
- enter when: TASK-158 starts implementing repeated CARLA observations for a paused closed-loop run.
- leave when: closed-loop observations use a deterministic CARLA sync session and multi-camera frame barrier that proves all Alpamayo camera windows came from aligned simulator ticks, with world settings restored on cleanup.
- blockers: none for fake/local tests; live CARLA validation happens through TASK-160.
- spawned follow-ups: none
- complexity: M

### Summary

Harden the observation side of the Alpamayo/CARLA loop. Closed-loop proof fails if the model sees stale, mixed, or post-hoc frames, so this ticket adds a small sync/session layer around CARLA world settings, sensor queues, frame ids, and cleanup.

### Scope

In scope:
- Add a dependency-light CARLA sync helper that can run against fake worlds in tests.
- Capture `frame_id`, `sensor_frame_id`, `sim_time_s`, and camera index for each checkpoint image.
- Drain stale sensor frames before each checkpoint and require all cameras to cross the same target tick.
- Restore prior CARLA world settings after the run.

Out of scope:
- Alpamayo inference execution.
- Control policy changes.
- Real-time serving.

### Gap Analysis

Current state:
- `src/driverx/simulators/carla_alpamayo_capture.py` captures camera windows, but it waits for ticks and then reads queues without a first-class frame barrier.
- `src/driverx/simulators/carla_ood_demo.py` captures a single RGB camera for videos and can apply controls, but it does not own a reusable closed-loop checkpoint contract.
- `src/driverx/simulators/carla_policy_replay.py` can tick a world while applying controls, but it does not verify sensor observations after those ticks.

Production expectation:
- CARLA should run in synchronous/fixed-delta mode for a paused controller.
- A single loop owner advances the world.
- Sensor events should be matched to target frames/ticks.
- Cleanup should restore settings and stop/destroy sensors reliably.

Missing gaps:
- No reusable sync-session helper.
- No explicit stale-frame drain.
- No aligned multi-camera checkpoint object.
- No trace proof that Alpamayo inputs are causally after applied controls.

Recommendation:
- Build a small `carla_sync` module and make TASK-158 consume it for closed-loop observations.

### Plan

#### Change

Add a sync barrier used by the closed-loop runner:

```python
with CarlaSyncSession(world, fixed_delta_seconds=0.25) as session:
    checkpoint = session.capture_checkpoint(cameras, target_after_frame=previous_post_action_frame)
```

#### Why

The submission claim depends on causality. If camera frames are stale or mixed across ticks, the proof can look closed-loop while still being open-loop in substance.

#### Before -> After

- Before: camera queue reads are best-effort and local to capture scripts.
- After: each closed-loop observation records aligned camera frames, target world frame, queue freshness, and settings restore status.

#### Touch

- `src/driverx/simulators/carla_sync.py` (new)
- `src/driverx/simulators/carla_alpamayo_capture.py`
- `src/driverx/simulators/carla_closed_loop_runner.py` (from TASK-158)
- `tests/test_carla_sync.py` (new)
- `tests/test_carla_closed_loop_runner.py`

#### Inspect

- `src/driverx/simulators/carla_ood_demo.py`
- `src/driverx/simulators/carla_policy_replay.py`
- `src/driverx/simulators/carla_ego.py`
- `docs/MEMORY.md` MEM-0025, MEM-0038, MEM-0042

#### Signature Delta

```python
src/driverx/simulators/carla_sync.py / CarlaSyncConfig(fixed_delta_seconds: float, timeout_s: float): dataclass
src/driverx/simulators/carla_sync.py / CarlaSyncSession(world: object, config: CarlaSyncConfig): context manager
src/driverx/simulators/carla_sync.py / capture_aligned_checkpoint(session, sensors: dict[int, object], output_dir: Path, min_frame_id: int | None): SyncedCarlaCheckpoint
src/driverx/simulators/carla_alpamayo_capture.py / build_alpamayo_package_from_synced_checkpoint(checkpoint: SyncedCarlaCheckpoint, route_context: dict): dict[str, Any]
```

#### Type Sketch

```python
SyncedCarlaCheckpoint = {
  "checkpoint_id": str,
  "world_frame_id": int,
  "sim_time_s": float,
  "min_required_frame_id": int | None,
  "camera_frames": [
    {"camera_index": 0, "sensor_frame_id": int, "path": str, "width": int, "height": int}
  ],
  "queue_drain_count": int,
  "settings_restored": bool
}
```

#### Typed Flow Example

Step 0 applies 4 controls and reaches world frame 104. The next checkpoint requests `min_frame_id=104`, drains older sensor events, captures all three Alpamayo cameras at frame `>=104`, and writes those paths into `alpamayo_carla_input_package.json`.

#### Execution Steps

1. Add fake-world and fake-sensor test doubles for frame-controlled tests.
2. Implement `CarlaSyncSession` with previous settings capture and restore.
3. Implement sensor queue drain and aligned image capture.
4. Add package conversion for the existing Alpamayo input shape.
5. Wire TASK-158 runner observations to use synced checkpoints.
6. Test mixed-frame rejection, stale-frame drain, timeout reporting, and cleanup restore.

#### Recommendation

Do this before live Kasm proof. It is the cheapest way to avoid a false closed-loop artifact.

#### Options Considered

- Keep queue logic inside `carla_alpamayo_capture.py`: fewer files, but closed-loop runner would duplicate sensor synchronization.
- Add a reusable sync module: slightly more surface, but directly addresses the riskiest integration failure.
- Use CARLA ScenarioRunner for sync ownership: too heavy for this deadline.

#### Blast Radius

- Additive helper module plus capture/runner integration.
- No generated video or model behavior changes.

#### Risks

- CARLA camera sensors can lag GPU frames. Mitigation: allow `>= min_frame_id` with recorded sensor/world ids, not an exact-only brittle match.
- Settings restore can fail if CARLA disconnects. Mitigation: record restore error and block closed-loop promotion.

### Acceptance Criteria

- [ ] AC-1: Fake-world tests prove sync settings are applied and restored.
- [ ] AC-2: Mixed/stale camera frames are drained or rejected before package writing.
- [ ] AC-3: `SyncedCarlaCheckpoint` records world frame, camera frame ids, sim time, and image paths.
- [ ] AC-4: TASK-158 closed-loop traces include checkpoint frame provenance for every model input.

### Verification

```bash
PYTHONPATH=src python3 -m unittest tests.test_carla_sync tests.test_carla_closed_loop_runner tests.test_alpamayo_ood_package
bash scripts/pre_push_check.sh
```

### Autonomy Readiness

- Local work uses fake CARLA objects only.
- Live validation waits for TASK-160.
- Do not claim closed-loop from traces with missing sensor frame provenance.

### Evidence

- Planning source: user request to harden Alpamayo/CARLA integration.
- Inspected seams: `carla_alpamayo_capture.py`, `carla_ood_demo.py`, `carla_policy_replay.py`.
- Plan review: `tickets/TASK-161/artifacts/review/task161-164-hardening-plan-review.json`
- Implementation: added `src/driverx/simulators/carla_sync.py` with `CarlaSyncSession`, aligned checkpoint capture, stale-frame drain, and Alpamayo package conversion.
- Proof: `tests.test_carla_sync` passed; full `bash scripts/pre_push_check.sh` passed with `456 tests OK, 5 skipped`.
- Review: `tickets/TASK-161/artifacts/review/task157-164-impl-review.json`

### Blockers

- None for local planning/build.
