# TASK-060/TASK-069 Review: Long Town13 Route And Capture Attempt

## Verdict

- overall_score: 4.0 / 5.0
- threshold: 4.0
- verdict: pass-for-blocker-evidence
- rerun_required: false
- reviewed_at: 2026-05-06 11:50 +0800

## Scope Reviewed

- `tickets/TASK-060/artifacts/town13-long-score-attempt-001/fail2drive_route_run.md`
- `tickets/TASK-060/artifacts/town13-long-score-attempt-001-evidence/run_evidence.md`
- `tickets/TASK-069/artifacts/town13-live-attach-attempt-003/carla_alpamayo_capture.json`
- `tickets/TASK-069/artifacts/town13-live-attach-attempt-004/carla_alpamayo_capture.json`
- `tickets/TASK-060/ticket.md`
- `tickets/TASK-069/ticket.md`
- `blockers.md`

## Rubric Scores

| family | score | threshold | pass |
|---|---:|---:|---|
| evidence-quality | 4.0 | 4.0 | yes |
| integration-readiness | 4.0 | 4.0 | yes |

## Findings

- No blocking findings for blocker classification.
- The evidence does not satisfy TASK-060 score/completion or TASK-069 live Alpamayo decision acceptance criteria. It does satisfy the narrower question of what blocks those tickets next: local CARLA under Mac/Kegworks/Wine is not responsive enough during this synchronous Fail2Drive route for long scoring plus second-client capture.

## Evidence Checked

- Long route run started `Generalization_PedestriansOnRoad_1088`, wrote a result checkpoint, and reached game time `0.600s` at about `0.142x`.
- The route was manually terminated after 257.79s wall time because logs stopped advancing and concurrent capture could not get CARLA ticks.
- Capture attempts with the correct mounted output root failed with 10s and 60s CARLA client timeouts.
- Full gate still passed after docs/artifact writeback:
  `bash scripts/pre_push_check.sh` with 292 tests.

## Next Action

Keep TASK-060 and TASK-069 open. The next productive path is a graphics-capable
Linux NVIDIA CARLA runtime or a local scheduling change that lets Fail2Drive
route execution and the capture client coexist while CARLA is in synchronous
mode.
