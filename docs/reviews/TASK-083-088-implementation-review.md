# TASK-083 Through TASK-088 Implementation Review

- reviewed_at: `2026-05-06 21:35 +0800`
- work_type: backend, simulator integration, evidence pipeline, submission docs
- rubrics: code-quality, integration-readiness, evidence-quality
- verdict: pass
- overall_score: `4.1/5.0`
- rerun_required: false

## Scope

Reviewed the TASK-083 through TASK-088 tickets, changed CLI registrations,
pipeline/simulator modules, regenerated evidence artifacts, README/progress
writeback, blocker ledger, and focused/full test output.

## Findings

- No blocking findings remain.
- The first QA/review pass correctly found three evidence gaps: TASK-086 lacked
  VRAM aggregation, TASK-087 did not explicitly checklist live video and
  Alpamayo comparison artifacts, and TASK-085's strongest campaign summary had
  manual `local-video` drift. The implementation now fixes those in source:
  `alpamayo_ood_batch` aggregates `vram_peak_mb`, `submission_dossier` derives
  live-video/comparison checklist rows, and `scripted_ood_campaign` has
  resume-aware case/video evidence reuse.
- Remaining caveat: stock Fail2Drive full-route scoring is still an external
  graphics-host handoff, intentionally isolated in TASK-088. The V5 dossier
  labels this as pending and does not claim real-time closed-loop VLA control.

## Evidence

- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_policy_replay tests.test_carla_cached_ood_replay tests.test_reasoning_video_pack tests.test_scripted_ood_campaign tests.test_alpamayo_ood_batch tests.test_submission_dossier tests.test_fail2drive_host_plan tests.test_ood_video_evidence`
  passed `24` tests.
- Full local gate:
  `bash scripts/pre_push_check.sh` passed with `325` tests and `2` skips.
- TASK-083 live cached replay evidence:
  `tickets/archive/TASK-083/artifacts/task83-live-cached-replay-video/ood_video_evidence.md`.
- TASK-084 reasoning pack evidence:
  `tickets/archive/TASK-084/artifacts/task84-reasoning-pack/reasoning_video_pack.html`.
- TASK-085 live campaign evidence:
  `tickets/archive/TASK-085/artifacts/task85-live-campaign-2b/scripted_ood_campaign_summary.md`.
- TASK-086 batch evidence:
  `tickets/archive/TASK-086/artifacts/task86-plan-cache/alpamayo_ood_batch_summary.md`.
- TASK-087 V5 source of truth:
  `tickets/archive/TASK-087/artifacts/submission-dossier-v5-live/submission_dossier.md`.
- TASK-088 host handoff:
  `tickets/archive/TASK-088/artifacts/task88-host-plan/fail2drive_host_plan.md`.

## Rubric Notes

- code-quality: `4.0/5.0`; modules are small, typed, tested, and CLI seams are
  explicit. Private regeneration helper use was kept outside committed code.
- integration-readiness: `4.0/5.0`; local CARLA/Docker, Alpamayo evidence, and
  submission docs are connected with explicit claim boundaries.
- evidence-quality: `4.2/5.0`; canonical artifacts are regenerated from source
  and now include VRAM, live video, comparison, campaign, replay, blocker, and
  host-handoff surfaces.

## Next Action

Keep TASK-083 through TASK-088 in `done` state. The next product ticket should
either render the final 1-5 minute deck/video from the V5 dossier or provision
a graphics-capable Linux CARLA host for stock Fail2Drive full-route scoring.
