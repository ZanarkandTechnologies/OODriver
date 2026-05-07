# TASK-108 Through TASK-113 Plan Review

- work_type: `implementation-plan`, `demo-quality`, `evidence-quality`
- verdict: `pass`
- overall_score: `4.1 / 5.0`
- threshold: `4.0`
- rerun_required: `false`
- evidence_quality: `pass`
- integration_readiness: `pass`
- traceability: `pass`
- freshness: `pass`

## Search Scope

- Planning skill: `impl-plan`
- Product truth: `docs/prd.md`
- Spec truth: `docs/specs/scenario-studio-data-engine.md`
- New spec: `docs/specs/scenario-workbench-v2-plan.md`
- Durable rules: `docs/MEMORY.md`
- Repeated misses: `docs/TROUBLES.md`
- Code seams:
  - `src/driverx/scenarios/studio.py`
  - `src/driverx/pipeline/scripted_ood_campaign.py`
  - `src/driverx/simulators/carla_ood_demo.py`
  - `src/driverx/simulators/ood_video_overlay.py`
  - `src/driverx/pipeline/alpamayo_ood_evaluation.py`
  - `src/driverx/pipeline/reasoning_video_pack.py`

## Result

The plan train is coherent and pointed at the user-corrected gap. It does not
pretend Alpamayo runs real-time closed-loop, and it does not throw away the
existing CARLA/Scenario Studio work. Instead it makes the missing demo loop
explicit:

1. unify evidence with `ScenarioRunBundle`
2. generate and curate OOD cases agentically
3. derive simulator-grounded risk/perception events from CARLA tracks
4. overlay risk, memory, and sampled VLA reasoning into video
5. produce longer smooth time-warped CARLA footage
6. rebuild the final V8 pack around that story

## Findings

No blocking findings.

### Watch Item: Ticket Count

Six tickets is enough but not too many because each has a separate proof
boundary. TASK-108/TASK-110/TASK-111 should land before spending runtime on
TASK-112, because better footage without better overlays repeats the current
demo problem.

### Watch Item: Claim Boundaries

The plans correctly preserve:

- `real_time_vla_control=false`
- `sampled_open_loop_reasoning=true`
- `time_warped_offline_demo=true`
- simulator risk detection, not image-detector claim

Those labels must survive implementation and final packaging.

## Next Action

Start implementation with TASK-108, then TASK-110 and TASK-111. Run TASK-109 in
parallel only if implementation bandwidth allows. Defer fresh CARLA runtime
work in TASK-112 until the overlay loop can make the current video legible.
