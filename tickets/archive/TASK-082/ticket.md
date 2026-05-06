# TASK-082: Submission Pack V4 Live CARLA Evidence Refresh

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-078, TASK-079, TASK-080, TASK-081
- location: `src/driverx/pipeline`, docs, `tickets/TASK-082/artifacts`
- enter when: the live CARLA retry batch has produced its best available evidence
- leave when: V4 demo pack uses the strongest current live CARLA and Alpamayo evidence with honest blockers
- blockers: none for V4 pack; full stock Fail2Drive score remains TASK-060
- spawned follow-ups:
- complexity: M

### Description
Regenerate the final submission pack so the current best live CARLA evidence is
front and center. Keep fixture/local evidence as backup and clearly label every
claim boundary.

### Goal
Produce a V4 storyboard/dossier that tells the strongest current submission
story after the live CARLA retry batch.

### Acceptance Criteria
- [x] AC-1: V4 pack consumes TASK-079 video evidence when available.
- [x] AC-2: V4 pack consumes TASK-081 comparison or records the exact blocker.
- [x] AC-3: Headline artifact selection prefers live CARLA video over fixture/local evidence only when source labels prove it.
- [x] AC-4: README/progress/blockers reflect the newest evidence.

### Agent Contract
- Open: `src/driverx/pipeline/submission_demo_pack.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_submission_demo_pack`
- Stabilize: never let partial evidence inflate claims.
- Inspect: `tickets/TASK-077/artifacts/submission-pack-v3-v2/submission_demo_pack.md`
- Expected artifacts: `tickets/TASK-082/artifacts/*/submission_demo_pack.{json,md}` and QA report.

### Evidence
- Created 2026-05-06 for the live CARLA retry batch.
- V4 pack:
  `tickets/TASK-082/artifacts/submission-pack-v4-live-carlasame-v3/submission_demo_pack.md`.
  Headline artifact is `long_carla_ood_video`, with live scripted CARLA OOD
  video, same-scene Alpamayo reasoning, same-capture memory comparison, and
  explicit open-loop/closed-loop claim boundaries.
- Docs updated: `README.md`, `ARCHITECTURE.md`, `docs/progress.md`,
  `blockers.md`, `docs/HISTORY.md`, and `docs/MEMORY.md`.
- QA:
  `tickets/TASK-082/artifacts/qa/TASK-078-082-qa-report.md`.
- Review:
  `docs/reviews/TASK-078-082-implementation-review.md`.

### Blockers
- None for this ticket. Open project blockers remain in `blockers.md`.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
