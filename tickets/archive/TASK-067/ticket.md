# TASK-067: Local Policy Reaction Matrix

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-064
- location: `src/driverx/pipeline`, `src/driverx/policies`, tests
- enter when: TASK-064 emits one local OOD run with policy decisions
- leave when: the same OOD scenario can compare multiple policy adapters and
  cached Alpamayo decisions where available
- blockers: live Alpamayo row optional for future work
- spawned follow-ups: TASK-070
- complexity: M

### Description
The repo has policy readiness and RAG comparison surfaces, but the local OOD
demo should also expose a compact reaction matrix over the same scenario. This
ticket turns policy behavior into a table suitable for the final evidence pack.

### Goal
Compare baseline, memory-guided, local hybrid, and optional cached Alpamayo
policy reactions against the same OOD behavior.

### Acceptance Criteria
- [x] AC-1: Matrix rows include policy id, setup status, latency, target speed,
  yield flag, memory ids, infractions, and safety score.
- [x] AC-2: Current local matrix covers ready mock, memory-guided mock, and
  hybrid rows; setup-row handling remains covered by existing adapter tests.
- [x] AC-3: TASK-064 report links to the matrix when generated.

## Evidence
- Policy matrix:
  `tickets/TASK-064/artifacts/local-ood-demo/policy/policy_reaction_matrix.md`.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_end_to_end_ood_demo tests.test_policies tests.test_rag_comparison`.
- QA report: `tickets/TASK-064/artifacts/qa_report.md`.
- Review: `docs/reviews/TASK-064-067-local-ood-review.md`.

## Blockers
- Optional live/cached Alpamayo artifacts may be absent.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
