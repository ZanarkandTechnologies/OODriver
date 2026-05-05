# TASK-057: Demo Pack Refresh

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-055, TASK-056
- location: `src/driverx/pipeline/submission_demo_pack.py`, `tickets/TASK-057/artifacts`
- enter when: live route evidence and Alpamayo OOD comparison evidence exist
- leave when: demo pack includes route video evidence, live Alpamayo memory comparison, updated model declarations, and current blockers
- blockers: none
- spawned follow-ups: none
- complexity: S

### Description
Refresh the judge-facing demo pack after the live Alpamayo memory comparison.
The pack should tell the current strongest story: randomized OOD harness, route
video proof, and retrieval-guided open-loop reasoning-VLA evaluation.

### Goal
Produce a fresh demo pack that no longer presents Alpamayo as merely setup
gated and no longer centers SimLingo/Vulkan as the main path.

### Acceptance Criteria
- [x] AC-1: `build-demo-pack` accepts route evidence and Alpamayo comparison
  paths.
- [x] AC-2: Storyboard includes route video evidence and Alpamayo no-memory vs
  memory evaluation.
- [x] AC-3: Model declarations include `alpamayo-live-ood-comparison` with
  open-loop state, latency, and VRAM fields.
- [x] AC-4: Failure case is updated to the current route-score gap instead of
  stale missing-video-helper text when route evidence is supplied.
- [x] AC-5: Fresh JSON/Markdown demo pack artifacts are written under
  `tickets/TASK-057/artifacts/refreshed-demo-pack`.

### Agent Contract
- Open: `src/driverx/pipeline/submission_demo_pack.py`,
  `src/driverx/pipeline/submission_demo_pack_cli.py`,
  `tests/test_submission_demo_pack.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_submission_demo_pack`
- Stabilize: keep the demo pack honest about open-loop Alpamayo and partial
  route video evidence.
- Expected artifacts: `tickets/TASK-057/artifacts/*`

### Evidence Checklist
- [x] Demo pack JSON:
  `tickets/TASK-057/artifacts/refreshed-demo-pack/submission_demo_pack.json`
- [x] Demo pack Markdown:
  `tickets/TASK-057/artifacts/refreshed-demo-pack/submission_demo_pack.md`
- [x] Focused tests log
- [x] Full local gate log
- [x] QA report

### Build Notes
- Added optional `--route-evidence` and `--alpamayo-comparison` inputs to
  `build-demo-pack`.
- Updated the storyboard beats to show route video evidence and Alpamayo memory
  comparison.
- Added a `live_evidence` section and a live Alpamayo model declaration.
- Preferred the current Town13/local route-score blocker in the closing beat
  over the older PhysicalAI sample dataset gate.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS

### Artifact Links
- `tickets/TASK-057/artifacts/refreshed-demo-pack/submission_demo_pack.json`
- `tickets/TASK-057/artifacts/refreshed-demo-pack/submission_demo_pack.md`

### User Evidence
- Supporting evidence: demo pack highlights route video evidence and
  `2.8886m` final trajectory delta in the Alpamayo memory comparison.
- QA report: `tickets/TASK-057/artifacts/qa_report.md`
- Review: `tickets/TASK-057/artifacts/review.md`
- Final verdict: complete.

### Required Evidence
- [x] Unit/integration/e2e tests pass (as applicable)
- [x] Lint passes
