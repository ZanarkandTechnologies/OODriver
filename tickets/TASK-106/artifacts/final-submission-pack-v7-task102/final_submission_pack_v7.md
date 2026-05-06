# 0xDriver: Scenario Studio For Minimal-Shot Driving Evaluation

- Status: `submission_ready`

## Thesis

0xDriver contributes a randomized OOD scenario-generation and evidence-management harness for testing frozen reasoning VLAs on weird but plausible driving cases without fine-tuning.

## Scorecard

- `selected_cases`: `6`
- `hero_cases`: `1`
- `scenario_studio_prompts`: `10`
- `scenario_studio_candidates`: `20`
- `alpamayo_rag_cases`: `3`
- `alpamayo_rag_passed`: `3`
- `alpamayo_reasoning_changed`: `2`
- `alpamayo_mean_latency_ms`: `92550.1317`
- `alpamayo_max_vram_peak_mb`: `23557.31`
- `fail2drive_extension_cases`: `26`
- `fail2drive_reference_count`: `4`
- `hero_video_duration_s`: `84.0`
- `hero_video_path`: `artifacts/exported/task102_high_fidelity_hero_v6_full.mp4`
- `hero_video_export_status`: `local_file`

## Evidence Rows

| claim | status | artifact | why it matters | boundary |
|---|---|---|---|---|
| We can author randomized minimal-shot driving cases from short briefs. | proved | tickets/TASK-103/artifacts/scenario-studio-v1/scenario_studio_batch.json | 10 prompts generated 20 candidate cases with curation rows. | deterministic prompt compiler; live LLM/Meshy generation is not claimed. |
| We have a judge-visible CARLA OOD video for the generated simulator path. | proved | artifacts/exported/task102_high_fidelity_hero_v6_full.mp4 | Hero video duration is 84.0 seconds; export_status=local_file. | scripted simulator evidence; not an official Fail2Drive route score; exported media is available for final demo assembly. |
| Frozen Alpamayo can be evaluated with and without retrieved memory on OOD cases. | proved | tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/alpamayo_ood_batch_summary.json | 3 passed comparisons; 2 changed reasoning. | open-loop trajectory-intent evaluation; not closed-loop VLA steering. |
| DriverX generated cases extend Fail2Drive-style OOD families. | proved | tickets/TASK-105/artifacts/fail2drive-extension-report/fail2drive_extension_report.json | 26 generated cases linked to 4 references and 2 memory entries. | reference layer only; official Fail2Drive score is false. |
| The final submission scope is selected and auditable. | proved | tickets/TASK-101/artifacts/submission-eval-matrix/submission_eval_matrix.json | 6 cases are role-classified for the submission. | selection matrix is planning/evidence management, not runtime execution. |

## Claim Boundaries

- Alpamayo evidence is open-loop trajectory-intent and reasoning evaluation, not closed-loop car control.
- Fail2Drive linkage is a benchmark reference layer, not an official leaderboard score.
- Generated candidates marked accept_partial still need live CARLA/model evidence before becoming accepted dataset rows.
- Hero video is generated simulator evidence and may be shown in the final demo.
- Scenario Studio is deterministic unless a future provider-backed generator is explicitly configured.
- ai_scenario_authoring=false_without_provider_run
- alpamayo_batch_open_loop_policy_evaluation=true
- closed_loop_carla_control=false
- closed_loop_carla_execution=false
- dataset_curation_heuristic=true
- deterministic_reproducible_generation=true
- fail2drive_reference_layer=true
- generated_cases_are_driverx_extensions=true
- live_fail2drive_execution=false
- model_weights_frozen=true
- official_fail2drive_score_claim=false
- prompt_to_ood_compiler=true
- real_time_vla_control=false

## Artifact Map

- `eval_matrix_path`: `tickets/TASK-101/artifacts/submission-eval-matrix/submission_eval_matrix.json`
- `scenario_studio_path`: `tickets/TASK-103/artifacts/scenario-studio-v1/scenario_studio_batch.json`
- `alpamayo_rag_batch_path`: `tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/alpamayo_ood_batch_summary.json`
- `fail2drive_extension_path`: `tickets/TASK-105/artifacts/fail2drive-extension-report/fail2drive_extension_report.json`
- `hero_video_evidence_path`: `tickets/TASK-102/artifacts/task102-high-fidelity-hero-v6/ood_video_evidence.json`
- `scenario_browser_path`: `tickets/archive/TASK-097/artifacts/task97-submission-browser-runpod-v4/scenario_browser.html`
- `blockers_path`: `blockers.md`
