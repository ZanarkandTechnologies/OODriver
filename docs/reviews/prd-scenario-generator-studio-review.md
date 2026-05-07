# Review: Scenario Generator Studio PRD

Reviewed at: 2026-05-07 17:08 +0800

## Scope

- `docs/prd.md`
- `docs/HISTORY.md`
- Existing project surfaces referenced from the PRD:
  - `src/driverx/scenarios/`
  - `src/driverx/workbench/`
  - `src/driverx/simulators/`
  - `src/driverx/pipeline/alpamayo_ood_*.py`

## Rubrics

### Spec Contract

- Score: 4.1 / 5.0
- Threshold: 4.0
- Verdict: pass
- Dimension notes:
  - Story coherence: pass. The PRD now centers one clear product thesis:
    scenario generation, closed-loop policy execution, reasoning replay, and
    curation.
  - Acceptance testability: pass. User stories now name app screens, generated
    artifacts, closed-loop outputs, and fallback boundaries.
  - Scope clarity: pass. It explicitly avoids simulator rebuilds, Meshy, model
    fine-tuning, and realtime VLA claims in the critical path.

### Implementation Plan Readiness

- Score: 4.0 / 5.0
- Threshold: 4.0
- Verdict: pass
- Dimension notes:
  - Execution order: pass. The next SLC is explicit: app first screen, generate
    scenarios, queue one run, execute on RunPod/CARLA, replay evidence, export.
  - Autonomy readiness: pass with caveat. Human gates and fallback behavior are
    named, but the next implementation pass still needs fresh tickets.
  - Proof clarity: pass. It names screenshots, closed-loop run artifacts,
    timing logs, risk/reasoning timelines, and final video export.

## Findings

- No blocking findings.
- Minor caveat: the PRD is intentionally not a ticket batch. The next pass must
  translate the Scenario Generator Studio V1 SLC into concrete tickets before
  build work so the implementation does not scatter across old task numbers.

## Next Action

Create the next ticket batch around:

1. Scenario Studio app shell and artifact-backed scenario cards.
2. Closed-loop RunPod/CARLA runner command and evidence pullback.
3. Policy adapter interface with `mock`, `carla-autopilot`, and
   `alpamayo-trajectory`.
4. Replay screen with video, risk timeline, RAG memory, reasoning, and action
   intent.
5. Submission export refresh.
