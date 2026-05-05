# TASK-062: Trajectory Intent To CARLA Control Dry Run

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-061
- location: `src/driverx/policies`, `src/driverx/simulators`, tests,
  `tickets/TASK-062/artifacts`
- enter when: route-aligned Alpamayo trajectory intent exists
- leave when: DriverX can convert an open-loop trajectory into a conservative
  CARLA control plan in fake-CARLA tests and a short local smoke run
- blockers: live Alpamayo latency is too high for real-time steering, so v1 is a
  dry-run/control-plan bridge unless explicitly run with cached trajectories
- spawned follow-ups: future closed-loop cached-trajectory route pilot
- complexity: L

### Description
The current Alpamayo adapter stops at trajectory intent. This ticket builds the
safe bridge from a DriverX trajectory to CARLA vehicle controls without claiming
real-time VLA driving.

### Goal
Prepare the first closed-loop control seam by replaying a cached trajectory
chunk through a conservative local controller.

## Plan

### Change
Add a trajectory-to-control planner that converts 20 `(x, y)` future waypoints
into speed/steer/brake commands relative to the current ego transform. Apply it
only in controlled fake-CARLA tests and short smoke runs with explicit safety
limits.

### Why
The eventual end goal is a car reacting in simulation, not just a VLA answering
questions. This ticket creates the control seam while respecting Alpamayo's
current 100s eager inference latency.

### Before -> After
- Before: `alpamayo-live` writes a `PolicyDecision` but cannot affect a CARLA
  actor.
- After: a cached `PolicyDecision` can produce a bounded control trace, and fake
  CARLA tests prove commands are applied and cleaned up.

### Touch
- `src/driverx/policies/trajectory_control.py`: trajectory preview controller.
- `src/driverx/simulators/carla_policy_replay.py`: fake/live replay harness.
- `src/driverx/simulators/carla_policy_replay_cli.py`: CLI for cached decision
  replay.
- `src/driverx/simulators/__init__.py`, `src/driverx/cli.py`.
- `tests/test_trajectory_control.py`, `tests/test_carla_policy_replay.py`.

### Inspect
- `src/driverx/core/types.py`
- `src/driverx/policies/types.py`
- `src/driverx/policies/alpamayo_live.py`
- `src/driverx/simulators/carla_ego.py`

### Signature Delta
```python
src/driverx/policies/trajectory_control.py / trajectory_to_control_trace(decision: PolicyDecision, ego_pose: EgoPose, config: TrajectoryControlConfig) -> ControlTrace
src/driverx/simulators/carla_policy_replay.py / replay_policy_decision(config: CarlaPolicyReplayConfig) -> CarlaPolicyReplayResult
```

### Type Sketch
```python
TrajectoryControlConfig = {
  "trajectory_frame": "ego" | "world",
  "max_speed_mps": 6.0,
  "max_steer": 0.35,
  "max_brake": 0.5,
  "lookahead_points": 3,
  "dt_s": 0.25,
}

ControlTrace = {
  "source_policy_id": "alpamayo-live",
  "closed_loop_control": False | "cached_replay",
  "commands": [{"tick": int, "steer": float, "throttle": float, "brake": float}],
  "safety_clamps": list[str],
}
```

### Typed Flow Example
`alpamayo_policy_decision.json`
-> parse 20-point trajectory
-> current CARLA ego pose
-> preview heading/speed controller
-> clamped controls
-> fake-CARLA actor receives commands
-> `policy_replay_report.md`.

### Execution Steps
1. Implement pure-Python trajectory controller with unit tests.
2. Add fake-CARLA replay harness to prove command application without live CARLA.
3. Add CLI and report artifacts.
4. Run optional live smoke on a spawned ego with a cached trajectory only after
   fake tests pass.
5. Keep all docs explicit that this is cached replay, not real-time Alpamayo
   closed-loop.

### Recommendation
Build this after TASK-061, not before. The control bridge is most meaningful
when replaying a route-aligned Alpamayo trajectory.

### Options Considered
- Use CARLA BasicAgent directly: faster but harder to tie to Alpamayo waypoints.
- Build a minimal preview controller: transparent and testable.
- Full MPC: overkill for the submission deadline.

### Blast Radius
New policy/control modules and simulator replay command only. No live route code
should depend on this until it is proven.

### Risks
- Coordinate frames may be wrong if trajectory points are ego-frame and replay
  expects world-frame; tests must pin the convention.
- Naive control may oscillate; keep speed/steer conservative.
- Users may overread this as real-time VLA control; reports must label cached
  replay clearly.

## Acceptance Criteria
- [x] AC-1: Pure controller tests cover straight, left, right, stop, and clamp
  cases.
- [x] AC-2: Fake-CARLA replay applies command traces and reports cleanup.
- [x] AC-3: CLI consumes a saved `alpamayo_policy_decision.json` and writes
  `carla_policy_replay.json/.md`.
- [x] AC-4: Live smoke is optional; if run, it is labeled cached replay.
- [x] AC-5: No claim of real-time Alpamayo closed-loop control appears in docs.

## Verification
- Unit:
  `PYTHONPATH=src python3 -m unittest tests.test_trajectory_control tests.test_carla_policy_replay`
- Gate: `bash scripts/pre_push_check.sh`
- Optional live:
  `scripts/run_carla_client_docker.sh python -m driverx replay-policy-decision --decision ...`

## Autonomy Readiness
- Fully implementable locally with fake CARLA tests.
- Live smoke requires CARLA running but not the RunPod model.

## Evidence
- 2026-05-06 03:36 +0800: Implemented pure cached trajectory replay before
  TASK-061 because it is locally testable and directly supports the original
  mission of turning VLA intent into simulator behavior. Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_trajectory_control tests.test_carla_policy_replay`
  passed with 11 tests.
- 2026-05-06 03:36 +0800: CLI consumed the archived TASK-039
  `alpamayo_policy_decision.json` and wrote
  `tickets/TASK-062/artifacts/cached-alpamayo-replay/carla_policy_replay.md`.
  The controller correctly labeled this as `cached_replay` and braked instead
  of steering because the archived trajectory points sit behind the ego frame.
  The report now records `trajectory_frame=ego`.
- 2026-05-06 03:34 +0800: Hardened the coordinate-frame contract:
  `trajectory_frame=ego` is the default for Alpamayo/DriverX trajectory intent,
  while `trajectory_frame=world` explicitly applies the CARLA ego pose transform.
- Review: `docs/reviews/TASK-062-trajectory-replay-review.md` passed with
  4.1/5.0 and no blocking findings.

## Blockers
- None for fake tests; live replay waits on CARLA availability.
