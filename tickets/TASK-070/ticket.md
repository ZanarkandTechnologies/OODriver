# TASK-070: Submission Pack V2 Local Plus CARLA Evidence

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-064, TASK-067, TASK-068, TASK-069, TASK-071
- location: `src/driverx/pipeline`, `README.md`, `ARCHITECTURE.md`, docs,
  tickets
- enter when: at least TASK-064 local end-to-end evidence exists
- leave when: the final demo pack leads with the strongest available runnable
  artifact and cleanly separates local sim, CARLA, and Alpamayo claims
- blockers: none for local submission refresh
- spawned follow-ups: final video/deck work
- complexity: M

### Description
This ticket refreshes the judge-facing story after the local runnable artifact
exists. It should consume CARLA/Alpamayo live evidence where available, but it
must not wait forever for external runtime.

### Goal
Make the repository submission coherent: local OOD simulator end-to-end now,
CARLA route/video where available, Alpamayo open-loop reactions, and explicit
future serving/closed-loop limits.

### Acceptance Criteria
- [x] AC-1: Demo pack includes TASK-064 local runnable artifact as the first
  proof surface.
- [x] AC-2: CARLA and Alpamayo evidence are included only when current and
  clearly labeled.
- [x] AC-3: Remaining blockers are short, current, and human-actionable.
- [x] AC-4: Final review passes evidence and claim-boundary checks.

## Evidence
- 2026-05-06 04:33 +0800: `build-demo-pack` now accepts
  `--local-demo` and the generated pack leads with the TASK-064 local OOD
  simulator as the first runnable proof. Evidence:
  `tickets/TASK-070/artifacts/submission-pack-v2-final/submission_demo_pack.md`.
- The pack includes current supporting evidence only:
  dataset-backed Alpamayo probe, open-loop Alpamayo memory comparison, cached
  replay, and the TASK-071 partial Town13 route video evidence. Claim
  boundaries explicitly say Alpamayo is open-loop, cached replay is not
  real-time VLA steering, and the route video does not imply full route score.
- 2026-05-06 11:36 +0800: Regenerated
  `tickets/TASK-070/artifacts/submission-pack-v2-final/submission_demo_pack.md`
  against `tickets/TASK-071/artifacts/town13-early-route-evidence/run_evidence.json`.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_route_evidence tests.test_submission_demo_pack`.
- Full gate: `bash scripts/pre_push_check.sh` passed with 288 tests.
- Review:
  `docs/reviews/TASK-068-070-local-first-submission-review.md`.
- Fresh TASK-071 evidence review:
  `docs/reviews/TASK-071-fast-town13-video-review.md`.

## Blockers
- None for this ticket. TASK-060 and TASK-069 remain the live-runtime follow-up
  tickets.
