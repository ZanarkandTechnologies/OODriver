# Scenario Workbench Bundle: generated-base-animals-0076-regional-driving-behavior-000__motorcycle_filtering

- Scenario: `generated-base-animals-0076-regional-driving-behavior-000`
- Behavior: `motorcycle_filtering`
- Video: `artifacts/exported/task102_high_fidelity_hero_v6_full.mp4`
- Export status: `local_file`

## Product Loop

| Stage | Status | Evidence | Why it matters |
| --- | --- | --- | --- |
| generate | proved | 10 prompts -> 20 candidates | Scenario Studio turns human OOD briefs into deterministic simulator-ready cases. |
| simulate | proved | 84.0s video, export_status=local_file | The generated case is rendered as CARLA evidence rather than staying a text prompt. |
| detect_risk | pending | No risk timeline linked yet. | Simulator ground truth creates a timeline of what the autonomy stack should notice. |
| retrieve_memory | proved | 1 memory ids: mem-sample-motorcycle-filtering | Minimal-shot behavior is scaffolded by retrieved prior failure principles, not fine-tuning. |
| reason | proved | Alpamayo record linked; reasoning_changed=False, latency_ms=[108765.59, 46129.12] | The demo can show what the VLA/RAG layer is saying at key risk moments. |
| curate | proved | status=linked, score=0.7 | Accepted failures and scenario variants feed the next dataset/replay queue. |

## Claim Boundaries

- `minimal_shot_scenario_generation=true`
- `time_warped_offline_demo=true`
- `sampled_open_loop_reasoning=true`
- `real_time_vla_control=false`
- `scripted_carla_ood_demo=true`
- `stock_fail2drive_score=false`
- `closed_loop_vla_control=false`
- `fast_ffmpeg_no_reasoning_overlay=true`
- `alpamayo_batch_open_loop_policy_evaluation=true`
- `closed_loop_carla_control=false`
- `model_weights_frozen=true`
- `Alpamayo evidence is open-loop trajectory-intent and reasoning evaluation, not closed-loop car control.`
- `Fail2Drive linkage is a benchmark reference layer, not an official leaderboard score.`
- `Generated candidates marked accept_partial still need live CARLA/model evidence before becoming accepted dataset rows.`
- `Hero video is generated simulator evidence and may be shown in the final demo.`
- `Scenario Studio is deterministic unless a future provider-backed generator is explicitly configured.`
- `ai_scenario_authoring=false_without_provider_run`
- `closed_loop_carla_execution=false`
- `dataset_curation_heuristic=true`
- `deterministic_reproducible_generation=true`
- `fail2drive_reference_layer=true`
- `generated_cases_are_driverx_extensions=true`
- `live_fail2drive_execution=false`
- `official_fail2drive_score_claim=false`
- `prompt_to_ood_compiler=true`

## Linkage Warnings

- Studio candidate is a best-effort fallback; exact scenario_id match was not found.

## Source Artifacts

- `studio_batch_path`: `tickets/TASK-103/artifacts/scenario-studio-v1/scenario_studio_batch.json`
- `video_evidence_path`: `tickets/TASK-102/artifacts/task102-high-fidelity-hero-v6/ood_video_evidence.json`
- `alpamayo_batch_path`: `tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/alpamayo_ood_batch_summary.json`
- `final_pack_path`: `tickets/TASK-106/artifacts/final-submission-pack-v7/final_submission_pack_v7.json`
- `risk_timeline_path`: `None`
- `memory_events_path`: `None`
- `reasoning_events_path`: `None`
