# TASK-083 Through TASK-088 QA Report

- qa_at: `2026-05-06 21:35 +0800`
- verdict: pass after fixes
- scope: TASK-083 cached replay, TASK-084 reasoning pack, TASK-085 campaign,
  TASK-086 Alpamayo batch, TASK-087 dossier, TASK-088 host handoff

## Result

The first QA pass failed TASK-086 and TASK-087 and flagged TASK-085 evidence
drift. Those gaps were fixed in code and the canonical artifacts were
regenerated.

## Fixed Gaps

- TASK-086 now reports `mean_vram_peak_mb`, `max_vram_peak_mb`, and per-record
  `vram_peak_mb` in
  `tickets/TASK-086/artifacts/task86-plan-cache/alpamayo_ood_batch_summary.json`.
- TASK-087 now explicitly checklists live OOD video evidence, the live MP4,
  the Alpamayo comparison artifact, reasoning HTML, campaign videos, batch,
  replay, and blocker ledger in
  `tickets/TASK-087/artifacts/submission-dossier-v5-live/submission_dossier.md`.
- TASK-085 now has source-level resume/video evidence reuse, and the promoted
  live campaign summary records `video_status=passed` plus the selected
  `local-video` evidence paths.

## Commands

- `PYTHONPATH=src python3 -m unittest tests.test_carla_policy_replay tests.test_carla_cached_ood_replay tests.test_reasoning_video_pack tests.test_scripted_ood_campaign tests.test_alpamayo_ood_batch tests.test_submission_dossier tests.test_fail2drive_host_plan tests.test_ood_video_evidence`
  -> `24` tests, OK.
- Full gate for the train:
  `bash scripts/pre_push_check.sh`
  -> `325` tests, OK, `2` skipped.
- Secret scan:
  `rg -n "hf_[A-Za-z0-9]{20,}|RUNPOD_API_KEY|HF_TOKEN=.*[A-Za-z0-9]" ...`
  -> no real leaked tokens; only placeholders/test fixtures.

## Evidence Checklist

- TASK-083 live cached replay video:
  `tickets/TASK-083/artifacts/task83-live-cached-replay-video/ood_video_evidence.md`.
- TASK-084 reasoning pack:
  `tickets/TASK-084/artifacts/task84-reasoning-pack/reasoning_video_pack.md`
  and `.html`.
- TASK-085 two-case live campaign:
  `tickets/TASK-085/artifacts/task85-live-campaign-2b/scripted_ood_campaign_summary.md`.
- TASK-086 Alpamayo batch:
  `tickets/TASK-086/artifacts/task86-plan-cache/alpamayo_ood_batch_summary.md`.
- TASK-087 V5 dossier and video script:
  `tickets/TASK-087/artifacts/submission-dossier-v5-live/submission_dossier.md`
  and `video_script.md`.
- TASK-088 host handoff:
  `tickets/TASK-088/artifacts/task88-host-plan/fail2drive_host_plan.md`.

## Residual Blocker

Stock Fail2Drive full-route scoring still needs a graphics-capable Linux CARLA
host. This is a scoped external runtime blocker, not a blocker for the current
submission packet.
