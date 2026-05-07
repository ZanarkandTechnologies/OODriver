# 0xDriver: Agentic OOD Scenario Workbench For Minimal-Shot Driving

- Status: `submission_ready_with_claim_boundaries`

## Thesis

0xDriver contributes a simulator data engine for minimal-shot autonomy: generate weird-but-plausible CARLA scenarios, render time-warped evidence, expose simulator-grounded risk, retrieve prior failure memory, and evaluate frozen reasoning VLAs without AV fine-tuning.

## Scorecard

- `agentic_briefs`: `24`
- `agentic_candidates`: `24`
- `agentic_accepted`: `12`
- `risk_events`: `281`
- `max_risk_level`: `critical`
- `overlay_status`: `passed`
- `overlay_events`: `10`
- `overlay_frame_count`: `420`
- `timewarp_status`: `passed`
- `timewarp_input_duration_s`: `84.0`
- `timewarp_output_duration_s`: `28.0`
- `alpamayo_cases`: `3`
- `alpamayo_reasoning_changed`: `2`
- `alpamayo_mean_latency_ms`: `92550.1317`
- `alpamayo_max_vram_peak_mb`: `23557.31`
- `final_demo_video_exists`: `True`

## Evidence Rows

| Claim | Status | Artifact | Boundary |
| --- | --- | --- | --- |
| Agentic Scenario Studio grows the OOD dataset queue. | proved | `tickets/TASK-109/artifacts/agentic-ood-loop-v1/agentic_ood_generation_loop.json` | deterministic agent loop; live LLM/Meshy provider is future polish. |
| One scenario lineage links generation, CARLA evidence, Alpamayo/RAG, and curation. | proved | `tickets/TASK-108/artifacts/workbench-bundle-v1-with-risk/scenario_run_bundle.json` | linkage warnings are kept visible when artifacts are fallback-matched. |
| CARLA ground truth produces a readable risk/perception timeline. | proved | `tickets/TASK-110/artifacts/risk-timeline-v1/risk_timeline.json` | simulator ground truth, not camera CV detection. |
| The demo video shows risk, RAG memory, VLA reasoning, and action intent. | proved | `tickets/TASK-111/artifacts/reasoning-overlay-v1/reasoning_overlay_video.json` | sampled open-loop reasoning; not real-time closed-loop control. |
| Time-warped offline rendering makes CARLA evidence watchable and honest. | proved | `tickets/TASK-112/artifacts/timewarp-v1/video_timewarp.json` | source video retimed for presentation. |
| Frozen Alpamayo 1.5 is evaluated with retrieved memory on OOD cases. | proved | `tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/alpamayo_ood_batch_summary.json` | no AV fine-tuning and no real-time steering claim. |

## Claim Boundaries

- `Alpamayo evidence is open-loop trajectory-intent and reasoning evaluation, not closed-loop car control.`
- `Fail2Drive linkage is a benchmark reference layer, not an official leaderboard score.`
- `Generated candidates marked accept_partial still need live CARLA/model evidence before becoming accepted dataset rows.`
- `Hero video is generated simulator evidence and may be shown in the final demo.`
- `Scenario Studio is deterministic unless a future provider-backed generator is explicitly configured.`
- `ai_scenario_authoring=false_without_provider_run`
- `alpamayo_batch_open_loop_policy_evaluation=true`
- `carla_execution=false`
- `closed_loop_carla_control=false`
- `closed_loop_carla_execution=false`
- `closed_loop_vla_control=false`
- `dataset_curation_heuristic=true`
- `dataset_curation_queue=true`
- `deterministic_agentic_generation=true`
- `deterministic_reproducible_generation=true`
- `fail2drive_reference_layer=true`
- `generated_cases_are_driverx_extensions=true`
- `image_based_object_detection=false`
- `live_fail2drive_execution=false`
- `live_llm_generation=false`
- `live_meshy_asset_generation=false`
- `mesh_asset_generation=false`
- `minimal_shot_scenario_generation=true`
- `model_weights_frozen=true`
- `official_fail2drive_score=false`
- `official_fail2drive_score_claim=false`
- `overlay_uses_simulator_ground_truth_risk=true`
- `prompt_to_ood_compiler=true`
- `real_time_vla_control=false`
- `risk_timeline_for_demo_explanation=true`
- `sampled_open_loop_reasoning=true`
- `scripted_carla_ood_demo=true`
- `simulator_ground_truth_risk=true`
- `simulator_ground_truth_tracks=true`
- `source_video_retimed_for_presentation=true`
- `stock_fail2drive_score=false`
- `time_warped_offline_demo=true`
