# TASK-056: Alpamayo OOD Evaluation Harness

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-039, TASK-054, TASK-055
- location: `src/driverx/pipeline/alpamayo_ood_evaluation.py`, `tickets/archive/TASK-056/artifacts`
- enter when: live Alpamayo open-loop CARLA policy output and route/video evidence exist
- leave when: Alpamayo no-memory vs memory open-loop comparison writes JSON/Markdown evidence with trajectory, CoC, latency, and safety flags
- blockers: none
- spawned follow-ups: TASK-057 demo pack refresh
- complexity: M

### Description
TASK-056 connects the live Alpamayo policy path to the minimal-shot memory
story. It compares the already-proven baseline Alpamayo CARLA capture against a
memory-augmented prompt-side rerun while keeping the result explicitly
open-loop.

### Goal
Produce one measurable Alpamayo OOD comparison report that shows whether
retrieved DriverX safety memory changed the chain-of-causation and trajectory
intent, without claiming live CARLA steering.

### Acceptance Criteria
- [x] AC-1: `build-alpamayo-ood-comparison` writes
  `alpamayo_ood_comparison.json` and `.md`.
- [x] AC-2: The report includes memory ids, CoC snippets, latency, VRAM,
  trajectory delta, route video availability, and closed-loop safety flags.
- [x] AC-3: If no memory Alpamayo decision exists, the harness writes a
  torch-ready memory-augmented package and an actionable next step instead of
  faking a comparison.
- [x] AC-4: Live memory-augmented Alpamayo evidence is incorporated when
  present.
- [x] AC-5: Output is labeled `open_loop_policy_evaluation=true` and
  `closed_loop_control=false`.

### Agent Contract
- Open: `src/driverx/pipeline/alpamayo_ood_evaluation.py`,
  `src/driverx/pipeline/alpamayo_ood_evaluation_cli.py`,
  `scripts/run_remote_alpamayo_carla_inference.sh`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_ood_evaluation`
- Stabilize: do not claim Alpamayo drove CARLA; this ticket compares trajectory
  intent from saved CARLA capture packages.
- Expected artifacts: `tickets/archive/TASK-056/artifacts/*`

### Evidence Checklist
- [x] Comparison JSON:
  `tickets/archive/TASK-056/artifacts/town10-memory-comparison/alpamayo_ood_comparison.json`
- [x] Comparison report:
  `tickets/archive/TASK-056/artifacts/town10-memory-comparison/alpamayo_ood_comparison.md`
- [x] Memory-augmented live Alpamayo decision:
  `tickets/archive/TASK-056/artifacts/live-memory-run-summary/alpamayo_policy_decision.json`
- [x] Focused tests log
- [x] Full local gate log
- [x] QA report

### Build Notes
- Added a pipeline/CLI harness that can compare two Alpamayo policy decision
  artifacts, compute trajectory deltas, compare CoC snippets, and pull route
  video evidence into one report.
- Added a memory-augmented package writer that injects DriverX memory as
  prompt-side context through `nav_text` plus `memory_context`, then validates
  the package with the Alpamayo materializer.
- Updated the remote Alpamayo CARLA inference script to pass `nav_text` and up
  to three DriverX memory entries into Alpamayo `helper.create_message(...)`.
- Live RunPod memory-augmented inference succeeded with eager attention. It
  produced a different CoC and a different trajectory from the baseline:
  baseline CoC: `Accelerate to proceed through the intersection since the
  traffic light turns green`; memory CoC: `Keep lane since the intersection is
  clear and no lead vehicle is present`.
- Current comparison is intentionally open-loop: the model output did not steer
  the CARLA route.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS

### Artifact Links
- `tickets/archive/TASK-056/artifacts/town10-memory-comparison/alpamayo_ood_comparison.json`
- `tickets/archive/TASK-056/artifacts/town10-memory-comparison/alpamayo_ood_comparison.md`
- `tickets/archive/TASK-056/artifacts/live-memory-run-summary/alpamayo_policy_decision.json`
- `tickets/archive/TASK-056/artifacts/live-memory-run/alpamayo_live_prediction.json`

### User Evidence
- Supporting evidence: baseline Alpamayo vs memory-augmented Alpamayo trajectory
  delta is captured in the comparison report.
- QA report: `tickets/archive/TASK-056/artifacts/qa_report.md`
- Review: `tickets/archive/TASK-056/artifacts/review.md`
- Final verdict: complete; ready for TASK-057.

### Required Evidence
- [x] Unit/integration/e2e tests pass (as applicable)
- [x] Lint passes
