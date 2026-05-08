# TASK-157: Closed-Loop Alpamayo/CARLA Control Contract

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-141, TASK-145, TASK-146
- location: `src/driverx/policies`, `src/driverx/simulators`, `src/driverx/evaluation`, `src/driverx/scenarios/studio_product_cli.py`, `tests`, `tickets/TASK-157`
- enter when: OODrive has CARLA generated-scenario runs and Alpamayo open-loop reasoning, but no honest contract for when Alpamayo is actually controlling CARLA.
- leave when: OODrive defines closed-loop claim taxonomy, receding-horizon trace types, safety invariants, and a mechanical score that distinguishes cached replay, paused closed loop, and real-time closed loop.
- blockers: none for local contract and metric work; live Kasm execution remains TASK-160.
- spawned follow-ups: TASK-158 implements the paused runner, TASK-159 productizes Alpamayo inference, TASK-160 runs/scored live evidence.
- complexity: M

### Summary

Build the proof contract before chasing runtime. Closed-loop driving must mean an Alpamayo-derived action changes CARLA state and the next Alpamayo input observes that changed state. This ticket creates the taxonomy, typed trace, safety gates, CLI scoring, and tests that prevent us from relabeling cached/open-loop evidence as closed-loop.

### Brainstorm

#### Candidate Directions

1. **Cached trajectory replay**
   - User value: fast demo that shows Alpamayo-like trajectory converted to CARLA controls.
   - Implementation risk: low; repo already has `trajectory_to_control_trace`, `apply_control_trace`, and `run_cached_ood_replay`.
   - Speed to first lovable slice: fastest.
   - Dependency cost: no GPU/model runtime.
   - Verdict: useful baseline, but not enough. It is not closed loop because the model does not re-observe the world after its action.

2. **Paused receding-horizon closed loop**
   - User value: strongest feasible claim before deadline. CARLA waits while Alpamayo runs, then applies the model's next control chunk and captures the new observation.
   - Implementation risk: medium-high; requires sync ticks, checkpoint capture, inference bridge, trajectory/control conversion, safety clamps, and evidence scoring.
   - Speed to first lovable slice: realistic if fake/cached model mode lands first, then Kasm Alpamayo plugs in.
   - Dependency cost: Kasm CARLA + Alpamayo runtime for final proof, but local tests use fake adapters.
   - Verdict: recommended first bet.

3. **Real-time Alpamayo closed loop**
   - User value: highest prestige if achieved.
   - Implementation risk: very high. Current Alpamayo latency is roughly 70-125s per inference, so it cannot meet simulator real-time control without a server/latency breakthrough.
   - Speed to first lovable slice: poor.
   - Dependency cost: GPU serving, model optimization, possibly frame batching/streaming and lower-resolution model path.
   - Verdict: defer. Keep `real_time_vla_control=false`.

4. **Hybrid safety-pilot with Alpamayo gating**
   - User value: a practical AV-like architecture where a deterministic safety controller drives and Alpamayo approves/gates actions.
   - Implementation risk: medium.
   - Speed to first lovable slice: good, but the claim is weaker because Alpamayo is not the direct controller.
   - Dependency cost: less model latency pressure.
   - Verdict: follow-up fallback if direct paused receding horizon is unstable.

#### Recommended Direction

Use **paused receding-horizon closed loop** as the core contribution:

`CARLA checkpoint -> Alpamayo inference -> trajectory-to-control safety layer -> CARLA apply_control/world.tick -> next checkpoint`.

Claim it as `closed_loop_vla_control=paused_receding_horizon` only when at least two model-action-observation iterations are proven. Keep `real_time_vla_control=false` unless measured end-to-end latency supports real-time tick control.

### Gap Analysis

#### Capability + User

The operator wants OODrive to prove that a frozen minimal-shot model can navigate generated CARLA OOD cases, not just reason over captured frames after the fact.

#### Current State

- `src/driverx/simulators/carla_ood_demo.py` can spawn generated scenarios, capture RGB/tracks, and can apply an injected `ego_control_trace`.
- `src/driverx/policies/alpamayo_live.py` converts a saved Alpamayo prediction into a `PolicyDecision` with `TrajectoryCandidate`, but labels it open-loop.
- `src/driverx/policies/trajectory_control.py` converts a trajectory into bounded throttle/steer/brake commands.
- `src/driverx/simulators/carla_policy_replay.py` can apply a control trace to a CARLA-like actor and tick a world.
- `src/driverx/simulators/carla_cached_ood_replay.py` can replay cached policy decisions in CARLA, but the model is not queried again after the vehicle moves.
- TASK-104/TASK-146 prove Alpamayo+memory reasoning over cases, but all current Alpamayo evidence remains open-loop.

#### Comparable Implementations

- CARLA's official docs define the simulator as a server/client system where the client asks for information and requests changes; synchronous mode makes the client control when simulation steps advance. See [CARLA foundations](https://carla.readthedocs.io/en/0.9.14/foundations/).
- CARLA's synchrony docs recommend synchronous mode with fixed time-step for slow client applications and sensor alignment; GPU camera sensors can lag by a couple of frames, so queue-aligned capture matters. See [CARLA synchrony and time-step](https://carla.readthedocs.io/en/0.9.10/adv_synchrony_timestep/).
- CARLA's Python API exposes `apply_control`/`VehicleControl`, `apply_batch_sync`, and RSS restrictors that can modify `VehicleControl` before it reaches the vehicle. See [CARLA Python API](https://carla.readthedocs.io/en/latest/python_api/).

#### Production Expectation

A credible closed-loop evaluator must include:

- deterministic CARLA synchronous/fixed-delta stepping;
- sensor queues tied to frame ids/ticks;
- a policy inference boundary with measured latency/VRAM;
- conversion from model trajectory to bounded vehicle controls;
- safety clamps/interventions before `apply_control`;
- per-step action trace and planned-vs-actual path;
- proof that later model inputs came after earlier model actions;
- claim taxonomy separating cached replay, paused closed loop, and real-time control.

#### Missing Gaps

- No first-class `ClosedLoopRunTrace`.
- No scorer that rejects fake closed-loop claims.
- No contract for `model_input_frame_id > previous_action_frame_id`.
- No stable claim labels for paused receding-horizon control.
- No tests that catch cached replay being mislabeled as closed loop.

#### Recommendation

Land the closed-loop contract and scorer first. It keeps the next runtime work honest and gives TASK-158/TASK-160 a mechanical target.

### Plan

#### Change

Add the contract and score command:

```bash
PYTHONPATH=src python3 -m oodrive score-closed-loop \
  --trace artifacts/runs/task158-paused-closed-loop/closed_loop_trace.json \
  --metric-only
```

#### Why

The current repo can already produce convincing-looking video. The new risk is claim inflation. The contract makes it impossible to call a replay closed-loop unless the trace proves observe -> infer -> act -> tick -> observe recurrence.

#### Before -> After

- Before: `closed_loop_control` can be `"cached_replay"` and looks close to closed loop in downstream reports.
- After: closed-loop reports must state one of:
  - `closed_loop_vla_control=false`
  - `closed_loop_vla_control=cached_replay`
  - `closed_loop_vla_control=paused_receding_horizon`
  - `closed_loop_vla_control=real_time`

#### Touch

- `src/driverx/policies/closed_loop_types.py` (new)
- `src/driverx/evaluation/closed_loop_control_score.py` (new)
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/scenarios/studio_product_closed_loop_runtime.py` (new, scorer wrapper only in this ticket)
- `tests/test_closed_loop_control_score.py` (new)
- `tests/test_oodrive_cli.py`
- `docs/MEMORY.md`
- `tickets/TASK-157/ticket.md`

#### Inspect

- `src/driverx/simulators/carla_ood_demo.py`
- `src/driverx/simulators/carla_policy_replay.py`
- `src/driverx/simulators/carla_cached_ood_replay.py`
- `src/driverx/policies/trajectory_control.py`
- `src/driverx/policies/alpamayo_live.py`
- `tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/alpamayo_ood_batch_summary.json`
- `docs/MEMORY.md` MEM-0034, MEM-0038, MEM-0040, MEM-0042

#### Signature Delta

```python
src/driverx/policies/closed_loop_types.py / validate_closed_loop_trace(trace: dict) -> ClosedLoopValidation
src/driverx/evaluation/closed_loop_control_score.py / score_closed_loop_control(trace_path: Path) -> dict[str, Any]
src/driverx/scenarios/studio_product_closed_loop_runtime.py / run_studio_score_closed_loop(trace_path: Path, output_root: Path, run_id: str, metric_only: bool) -> StudioCommandResult
```

#### Type Sketch

```python
ClosedLoopRunTrace = {
  "run_id": str,
  "mode": "cached_replay" | "paused_receding_horizon" | "real_time",
  "steps": list[ClosedLoopStep],
  "latency_ms": {"mean": float, "max": float},
  "control_applied_count": int,
  "observed_after_action_count": int,
  "safety_interventions": list[str],
  "claim_boundaries": list[str],
}

ClosedLoopStep = {
  "step_index": int,
  "input_frame_id": int,
  "model_started_at_wall_s": float,
  "model_latency_ms": float,
  "prediction_path": str,
  "control_trace_path": str,
  "applied_control_count": int,
  "post_action_frame_id": int,
  "planned_path": list[dict],
  "actual_path": list[dict],
}
```

#### Typed Flow Example

`cached_ood_replay.json` with one precomputed policy decision scores as partial:

```json
{
  "mode": "cached_replay",
  "control_applied_count": 20,
  "observed_after_action_count": 0,
  "closed_loop_score": 35.0,
  "claim_boundaries": ["closed_loop_vla_control=cached_replay", "real_time_vla_control=false"]
}
```

A paused two-iteration run scores as closed loop:

```json
{
  "mode": "paused_receding_horizon",
  "steps": [
    {"input_frame_id": 10, "applied_control_count": 4, "post_action_frame_id": 14},
    {"input_frame_id": 14, "applied_control_count": 4, "post_action_frame_id": 18}
  ],
  "claim_boundaries": [
    "closed_loop_vla_control=paused_receding_horizon",
    "real_time_vla_control=false"
  ]
}
```

#### Execution Steps

1. Define `ClosedLoopRunTrace`, step validation, and claim taxonomy.
2. Implement score components: recurrence proof, applied control count, planned-vs-actual path, safety clamps, latency honesty, CARLA evidence paths, and claim honesty.
3. Add fixtures for cached replay, invalid overclaim, paused receding horizon, and real-time claim rejection.
4. Register `oodrive score-closed-loop`.
5. Add memory rule that real-time control remains false unless latency and tick cadence prove it.
6. Run focused tests and `bash scripts/pre_push_check.sh`.

#### Recommendation

Make this the first closed-loop ticket. It is small, it hardens the claim boundary, and it gives runtime tickets an objective pass/fail surface.

#### Options Considered

- Jump straight to live Kasm Alpamayo loop: high risk and easy to overclaim without a trace contract.
- Reuse cached replay as the demo: fast but not enough for "closed-loop VLA driving."
- Define the trace/scorer first: best balance of rigor and speed.

#### Blast Radius

- Additive CLI and scoring surface.
- No CARLA runtime behavior changes yet.
- Downstream submission/readiness scoring may later consume the score.

#### Risks

- The scorer can become too permissive. Mitigation: require model-action-observation recurrence and reject `real_time` without cadence proof.
- The taxonomy may confuse users. Mitigation: reports include plain English labels and exact claim boundaries.

### Acceptance Criteria

- [ ] AC-1: Closed-loop trace schema distinguishes cached replay, paused receding horizon, and real-time control.
- [ ] AC-2: `score-closed-loop` rejects invalid real-time and invalid closed-loop claims.
- [ ] AC-3: Cached replay remains explicitly non-real-time and does not receive full closed-loop credit.
- [ ] AC-4: Tests cover valid paused loop, cached replay, overclaim rejection, and missing CARLA evidence.

### Verification

```bash
PYTHONPATH=src python3 -m unittest tests.test_closed_loop_control_score tests.test_carla_policy_replay tests.test_carla_cached_ood_replay tests.test_oodrive_cli
bash scripts/pre_push_check.sh
```

### Plan Review

- `tickets/TASK-157/artifacts/review/task157-160-closed-loop-plan-review.json`

### Autonomy Readiness

- Local implementation requires no GPU, secrets, or CARLA.
- Live proof is intentionally out of scope for this ticket.
- Human gate: do not update final submission claims until TASK-160 produces live evidence and `score-closed-loop` passes.

### Refs

- CARLA foundations: `https://carla.readthedocs.io/en/0.9.14/foundations/`
- CARLA synchrony/time-step: `https://carla.readthedocs.io/en/0.9.10/adv_synchrony_timestep/`
- CARLA Python API: `https://carla.readthedocs.io/en/latest/python_api/`

### Evidence

- Planning source: user request to harden Alpamayo/CARLA into closed-loop driving.
- Local inspected seams: `trajectory_control.py`, `carla_policy_replay.py`, `carla_cached_ood_replay.py`, `carla_ood_demo.py`, `alpamayo_live.py`.
- Implementation: added `src/driverx/policies/closed_loop_types.py`, `src/driverx/evaluation/closed_loop_control_score.py`, `oodrive score-closed-loop`, and recurrence/overclaim tests.
- Proof: `PYTHONPATH=src python3 -m unittest tests.test_closed_loop_control_score tests.test_oodrive_cli` passed inside the focused and pre-push gates.
- Smoke: fake paused trace emitted `METRIC closed_loop_score=100.0000`.
- Review: `tickets/TASK-161/artifacts/review/task157-164-impl-review.json`

### Blockers

- None for contract/scoring.
