# Review: TASK-072 Through TASK-077 Impl Plan Train

- reviewed_at: 2026-05-06 18:16 +0800
- work_type: planning
- scope: `tickets/archive/TASK-072/ticket.md` through `tickets/archive/TASK-077/ticket.md`,
  `docs/progress.md`, `docs/HISTORY.md`
- rubrics_used: `spec-contract`, `implementation-plan`
- overall_score: 4.2 / 5.0
- threshold: 4.0
- verdict: pass
- rerun_required: false

## Search Scope

- Active PRD/spec context:
  - `docs/prd.md`
  - `docs/specs/minimal-shot-vla-roadmap.md`
  - `docs/MEMORY.md`
  - `docs/TROUBLES.md`
  - `blockers.md`
  - `docs/progress.md`
- Neighboring implementation surfaces:
  - `src/driverx/simulators/carla_script.py`
  - `src/driverx/simulators/carla_injection.py`
  - `src/driverx/simulators/carla_alpamayo_capture.py`
  - `src/driverx/simulators/route_video_assembly.py`
  - `src/driverx/pipeline/alpamayo_ood_evaluation.py`
  - `src/driverx/pipeline/submission_demo_pack.py`
  - `src/driverx/assets/pipeline.py`

## Rubric Scores

### Spec Contract: 4.2 / 5.0

- story-coherence: 4.4
- parallelization-fit: 4.0
- ticket-sizing: 4.1
- acceptance-testability: 4.2
- scope-clarity: 4.3

The train now has a clear submission-first story: produce long CARLA OOD video,
then overlay evidence, then Alpamayo reasoning and memory comparison, then
refresh the final pack. The tickets remain independent enough to build serially
or continue when live CARLA/GPU proof blocks. TASK-077 is correctly dependent on
the evidence tickets rather than trying to absorb runtime work.

Minor caveat: TASK-072 and TASK-076 will touch adjacent CARLA spawn code and
should be implemented carefully to avoid duplicate fake-CARLA helpers.

### Implementation Plan: 4.1 / 5.0

- human-readability: 4.2
- bloatability: 4.0
- modularity: 4.1
- proof-clarity: 4.2
- execution-order: 4.2
- risk-clarity: 4.1
- decision-tone: 4.2
- autonomy-readiness: 4.1

Each ticket includes file map, inspected files, signature deltas, type sketches,
typed flow, concrete execution order, acceptance criteria, verification, and
autonomy readiness. The proof paths are actionable and distinguish fake-CARLA
tests from optional live simulator/GPU evidence.

Minor caveat: live CARLA proof remains an operational risk; the plans correctly
contain fallback artifact/blocker behavior.

## Findings

- No blocking findings.
- Non-blocking: during TASK-072 implementation, prefer extracting shared fake
  CARLA helpers if tests begin duplicating setup across capture, injection, and
  OOD demo modules.
- Non-blocking: during TASK-073 implementation, keep overlays visually minimal
  so they do not hide the important CARLA scene evidence.

## Verdict

The ticket train is approval-ready. The next implementation pass should start
with TASK-072, because it unblocks the long video and supplies the capture
surface for Alpamayo reasoning.
