# TASK-064: Local OOD End-To-End Demo Runner

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-010, TASK-014, TASK-062
- location: `src/driverx/pipeline`, `src/driverx/simulators`, tests,
  `tickets/TASK-064/artifacts`
- enter when: user needs a runnable end-to-end artifact before more CARLA/VLA
  integration work
- leave when: one command generates an OOD scenario, policy reactions,
  control traces, visual local simulation, and report evidence without CARLA
- blockers: none
- spawned follow-ups: TASK-065, TASK-066, TASK-067
- complexity: M

### Description
The project has strong pieces but no dependency-light command that shows the
whole OOD loop running end to end. This ticket composes existing scenario
generation, behavior traces, retrieval memory, mock policy adapters, cached
trajectory replay, and a small top-down simulator into one artifact pack.

### Goal
Produce the first locally runnable OOD simulator demo that is honest about being
2D/local, while proving the intended data flow before CARLA/Town13/Alpamayo are
stable.

## Plan

### Change
Add `run-end-to-end-ood-demo`.

### Before -> After
- Before: users had to run scenario forge, behavior generation, RAG comparison,
  and replay commands separately, with no single simulation surface.
- After: one command writes a scenario recipe, behavior trace, memory bank,
  no-memory and memory-guided policy decisions, control traces, local sim
  timeline, SVG/HTML visual evidence, and Markdown report.

### Touch
- `src/driverx/simulators/local_ood_sim.py`
- `src/driverx/pipeline/end_to_end_ood_demo.py`
- `src/driverx/cli.py`
- `tests/test_local_ood_sim.py`
- `tests/test_end_to_end_ood_demo.py`
- `README.md`, `ARCHITECTURE.md`, `docs/progress.md`, `docs/HISTORY.md`

### Acceptance Criteria
- [x] AC-1: `PYTHONPATH=src python3 -m driverx run-end-to-end-ood-demo`
  runs without CARLA, Docker, GPU, or Hugging Face access.
- [x] AC-2: The run writes JSON, Markdown, SVG, and HTML evidence under the
  selected run directory.
- [x] AC-3: The report shows generated OOD recipe, behavior pressure, retrieved
  memory ids, no-memory vs memory policy outcomes, control traces, and local
  simulator safety summary.
- [x] AC-4: The artifact explicitly labels itself as a local 2D simulator and
  does not claim closed-loop CARLA/VLA control.
- [x] AC-5: Focused tests and `bash scripts/pre_push_check.sh` pass.

## Evidence
- 2026-05-06 04:08 +0800: Implemented `run-end-to-end-ood-demo`, local 2D OOD
  simulator rendering, and policy reaction matrix integration.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_behaviors tests.test_local_ood_sim tests.test_end_to_end_ood_demo tests.test_policies tests.test_rag_comparison`
  passed with 21 tests.
- Full gate: `bash scripts/pre_push_check.sh` passed with 287 tests. It warned
  about existing large tracked files but found no oversized source failures
  after extracting the new CLI command from `src/driverx/cli.py`.
- Runnable artifact:
  `tickets/TASK-064/artifacts/local-ood-demo/end_to_end_demo.md`.
- Visual evidence:
  `tickets/TASK-064/artifacts/local-ood-demo/local-sim/local_ood_sim.html`
  and `tickets/TASK-064/artifacts/local-ood-demo/local-sim/local_ood_sim.svg`.
- Policy matrix:
  `tickets/TASK-064/artifacts/local-ood-demo/policy/policy_reaction_matrix.md`.
- QA report: `tickets/TASK-064/artifacts/qa_report.md`.
- Review: `docs/reviews/TASK-064-067-local-ood-review.md`.

## Blockers
- None.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
