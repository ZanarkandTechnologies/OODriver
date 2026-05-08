# TASK-162: Closed-Loop Control Safety And Lane-Adherence Guardrails

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-157, TASK-158, TASK-161
- location: `src/driverx/policies`, `src/driverx/simulators`, `tests`, `tickets/TASK-162`
- enter when: closed-loop runner can convert model trajectories into controls and apply them to fake or live CARLA actors.
- leave when: every Alpamayo-derived control chunk passes deterministic safety checks for speed, brake/throttle conflict, lane/corridor adherence, emergency stop, and planned-vs-actual deviation before it can be scored as closed-loop evidence.
- blockers: high-fidelity CARLA lane metadata may be unavailable locally; fake tests use road-frame corridor proxies.
- spawned follow-ups: none
- complexity: M

### Summary

Harden the action side of the Alpamayo/CARLA loop. The car must not “avoid” obstacles by leaving the lane or applying nonsensical throttle/brake commands. This ticket adds a control-safety layer between Alpamayo trajectory intent and CARLA `VehicleControl`.

### Scope

In scope:
- Validate generated controls before application.
- Add emergency stop, corridor clamp, speed cap, and brake/throttle conflict checks.
- Record interventions into `ClosedLoopRunTrace`.
- Score lane-departure and planned-vs-actual deviation as blockers for promotion.

Out of scope:
- Building a full MPC controller.
- Claiming perfect route following.
- Optimizing Alpamayo trajectory quality.

### Gap Analysis

Current state:
- `src/driverx/policies/trajectory_control.py` converts waypoints into bounded throttle/steer/brake and logs simple clamps.
- `src/driverx/simulators/carla_policy_replay.py` applies those controls to real or fake actors.
- TASK-140 already found that local stress demos can look wrong if lateral avoidance leaves the drivable corridor.

Production expectation:
- A policy adapter for AV proof needs a safety envelope around model output.
- Every intervention should be trace-visible.
- The scorer should reject “success” when the vehicle leaves the road/corridor or ignores a blocker.

Missing gaps:
- No explicit closed-loop control safety report.
- No lane/corridor adherence check in the trajectory-to-control layer.
- No emergency-stop override for unsafe/behind/too-near targets.
- No planned-vs-actual deviation threshold in closed-loop scoring.

Recommendation:
- Add a small `control_safety` module and make `apply_control_trace` consume prevalidated chunks.

### Plan

#### Change

Insert a guardrail layer:

```python
safe_chunk = validate_control_chunk(
    trace,
    road_frame=road_frame,
    actor_tracks=recent_tracks,
    config=ClosedLoopSafetyConfig(),
)
application = apply_control_trace(actor, safe_chunk.control_trace, world=world)
```

#### Why

A judge will not trust a closed-loop demo if the car swerves out of lane, accelerates into a blocker, or hides safety overrides. The proof must show what the policy wanted and what the safety envelope allowed.

#### Before -> After

- Before: trajectory controls are bounded numerically but not evaluated as driving behavior.
- After: every applied chunk carries `interventions`, `lane_departure_proxy`, `max_abs_y_m`, `speed_cap_applied`, and `emergency_stop_applied` fields.

#### Touch

- `src/driverx/policies/control_safety.py` (new)
- `src/driverx/policies/trajectory_control.py`
- `src/driverx/simulators/carla_policy_replay.py`
- `src/driverx/simulators/carla_closed_loop_runner.py` (from TASK-158)
- `src/driverx/evaluation/closed_loop_control_score.py` (from TASK-157)
- `tests/test_control_safety.py` (new)
- `tests/test_trajectory_control.py`
- `tests/test_closed_loop_control_score.py`

#### Inspect

- `src/driverx/pipeline/bad_path_stress_demo.py`
- `src/driverx/simulators/carla_road_frame.py`
- `src/driverx/simulators/carla_ood_demo.py`
- `docs/MEMORY.md` MEM-0023, MEM-0041

#### Signature Delta

```python
src/driverx/policies/control_safety.py / ClosedLoopSafetyConfig(max_abs_y_m: float, max_speed_mps: float, min_blocker_distance_m: float): dataclass
src/driverx/policies/control_safety.py / validate_control_chunk(trace: ControlTrace, context: SafetyContext, config: ClosedLoopSafetyConfig): SafeControlChunk
src/driverx/policies/control_safety.py / score_path_adherence(planned_path: list[dict], actual_path: list[dict], corridor_half_width_m: float): PathAdherenceReport
src/driverx/evaluation/closed_loop_control_score.py / score_closed_loop_control(...): include safety/adherence terms
```

#### Type Sketch

```python
SafeControlChunk = {
  "control_trace": ControlTrace,
  "interventions": ["emergency_stop", "steer_clamp"],
  "lane_departure_proxy": bool,
  "max_abs_y_m": float,
  "speed_cap_applied": bool,
  "emergency_stop_applied": bool,
  "planned_vs_actual_error_m": float | None
}
```

#### Typed Flow Example

Alpamayo predicts a path that swerves around a road hole with `target_y=3.2m`. The guardrail caps lateral motion to the configured corridor, records `steer_clamp`, applies slow throttle, and blocks score promotion if the actual track exceeds the corridor.

#### Execution Steps

1. Define safety context and safe chunk data classes.
2. Move reusable speed/steer/brake checks out of prose clamps into structured intervention records.
3. Add corridor/lane proxy checks using road-frame local coordinates.
4. Add emergency stop when a target is unsafe, behind ego, or below blocker distance.
5. Wire safety reports into closed-loop trace steps.
6. Update scorer to reject lane-departure and unsafe throttle/brake conflicts.
7. Cover static blocker, road-hole swerve, rolling-object yield, and unsafe trajectory fixtures.

#### Recommendation

Prioritize conservative stop/slow behavior over flashy swerves. For SoTA judges, a car that stops safely in a novel bad path is more credible than one that “solves” the scene by leaving the lane.

#### Options Considered

- Trust Alpamayo trajectory directly: fastest but too fragile.
- Full MPC/controller: better long-term, too large for this sprint.
- Deterministic safety wrapper: best deadline ROI and easiest to prove.

#### Blast Radius

- Policy-control path and closed-loop scorer.
- Existing open-loop reasoning outputs remain unchanged.

#### Risks

- Over-conservative controls may make the vehicle stop too often. Mitigation: report interventions honestly and choose simple blocker proof first.
- Lane metadata may not exist in fake mode. Mitigation: use road-frame corridor proxies and mark them as proxies.

### Acceptance Criteria

- [ ] AC-1: Unsafe throttle/brake conflicts and speed excesses are clamped and recorded.
- [ ] AC-2: Lane/corridor departure proxy blocks closed-loop score promotion.
- [ ] AC-3: Static blocker fixture triggers emergency stop or slow-to-stop behavior.
- [ ] AC-4: Road-hole swerve fixture stays inside configured corridor.
- [ ] AC-5: Closed-loop trace includes safety reports for each applied control chunk.

### Verification

```bash
PYTHONPATH=src python3 -m unittest tests.test_control_safety tests.test_trajectory_control tests.test_closed_loop_control_score tests.test_carla_policy_replay
bash scripts/pre_push_check.sh
```

### Autonomy Readiness

- Local work is deterministic and does not need CARLA.
- Live CARLA proof must not promote if safety reports are missing or failing.

### Evidence

- Planning source: user complaint that obstacle avoidance looked like the car drove away/out of lane.
- Inspected seams: `trajectory_control.py`, `carla_policy_replay.py`, `bad_path_stress_demo.py`.
- Plan review: `tickets/TASK-161/artifacts/review/task161-164-hardening-plan-review.json`
- Implementation: added `src/driverx/policies/control_safety.py` and wired fake closed-loop chunks through safety reports.
- Proof: `tests.test_control_safety` passed for corridor clamping and emergency stop; full `bash scripts/pre_push_check.sh` passed with `456 tests OK, 5 skipped`.
- Review: `tickets/TASK-161/artifacts/review/task157-164-impl-review.json`

### Blockers

- None for local guardrail work.
