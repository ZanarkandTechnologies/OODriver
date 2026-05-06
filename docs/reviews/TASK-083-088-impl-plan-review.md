# TASK-083..TASK-088 Impl-Plan Review

## Verdict

- work_type: `planning`, `runtime`, `simulation`, `submission`
- rubrics_used: `implementation-plan`, `spec-contract`, `evidence-quality`,
  `integration-readiness`
- overall_score: `4.1`
- overall_threshold: `4.0`
- verdict: `pass`
- rerun_required: `false`

## Scope Checked

- PRD: `docs/prd.md`
- Roadmap: `docs/specs/minimal-shot-vla-roadmap.md`
- Current evidence: TASK-078 through TASK-082 artifacts
- Current blockers: `blockers.md`
- Memory rules: `MEM-0007`, `MEM-0012`, `MEM-0016`, `MEM-0019`, `MEM-0021`
- Code seams:
  `src/driverx/simulators/carla_ood_demo.py`,
  `src/driverx/simulators/carla_policy_replay.py`,
  `src/driverx/policies/trajectory_control.py`,
  `src/driverx/pipeline/ood_video_evidence.py`,
  `src/driverx/pipeline/generated_ood_suite.py`,
  `src/driverx/pipeline/alpamayo_ood_evaluation.py`,
  `src/driverx/pipeline/submission_dossier.py`

## Findings

No blocking findings.

- medium / high confidence / integration-readiness:
  TASK-083 live proof still depends on local CARLA responsiveness. The plan is
  acceptable because fake-CARLA implementation and partial live blocker evidence
  are explicit acceptance paths.
- low / high confidence / evidence-quality:
  TASK-086 can become slow because eager Alpamayo inference is expensive. The
  plan mitigates this with plan/cache mode, `limit`, and one-case live proof.

## Rubric Summary

### Spec Contract

- score: `4.2`
- threshold: `4.0`
- pass: `true`
- rationale:
  The ticket train maps directly to the project goal: generate OOD scenarios,
  show how policies react, compare frozen Alpamayo with memory, and prepare
  final submission evidence without overclaiming closed-loop VLA autonomy.

### Implementation Plan

- score: `4.1`
- threshold: `4.0`
- pass: `true`
- rationale:
  Each ticket has file maps, signature deltas, typed flow examples, ordered
  execution steps, and concrete verification. The split boundaries are real:
  replay, reasoning presentation, campaign generation, Alpamayo batch runtime,
  final dossier, and blocked stock-score handoff.

### Evidence Quality

- score: `4.0`
- threshold: `4.0`
- pass: `true`
- rationale:
  The plans name observable artifacts and commands. The only caveat is that
  live CARLA/GPU proof remains conditional for TASK-083/TASK-086; both tickets
  preserve partial/blocker proof paths.

### Integration Readiness

- score: `4.0`
- threshold: `4.0`
- pass: `true`
- rationale:
  The train starts with local/fake seams, uses the existing RTX 6000 Ada only
  for Alpamayo when needed, and keeps stock Fail2Drive full score isolated to a
  handoff ticket rather than blocking the main submission.

## Next Action

Start `$impl` with TASK-083. If live CARLA blocks, finish fake-CARLA replay
evidence and proceed to TASK-084, which requires no CARLA or GPU.
