# 0xDriver Minimal-Shot OOD Driving Harness

## Thesis

Use generated long-tail CARLA/Bench2Drive scenarios, retrieved safety memory, and frozen VLA policy adapters to test minimal-shot driving behavior without fine-tuning on the generated cases.

## Readiness

- `scenario_generation_ready`: `True`
- `live_carla_video_available`: `True`
- `alpamayo_reasoning_available`: `True`
- `alpamayo_memory_comparison_available`: `True`
- `cached_replay_available`: `True`
- `stock_fail2drive_full_score_available`: `False`

## Metric Highlights

- `campaign_case_count`: `2`
- `campaign_live_case_count`: `2`
- `campaign_mean_min_distance_m`: `0.2637`
- `live_ood_video_duration_s`: `24.0`
- `cached_replay_duration_s`: `8.0`
- `alpamayo_batch_mean_latency_ms`: `77447.355`
- `alpamayo_batch_mean_vram_peak_mb`: `23532.505`
- `alpamayo_batch_max_vram_peak_mb`: `23557.31`
- `alpamayo_batch_mean_trajectory_final_l2_m`: `2.6886`

## Artifact Checklist

- [x] V4 demo pack: `tickets/TASK-082/artifacts/submission-pack-v4-live-carlasame-v3/submission_demo_pack.json` heavy=`False`
- [x] Reasoning overlay pack: `tickets/TASK-084/artifacts/task84-reasoning-pack/reasoning_video_pack.json` heavy=`False`
- [x] Scripted OOD campaign: `tickets/TASK-085/artifacts/task85-live-campaign-2b/scripted_ood_campaign_summary.json` heavy=`False`
- [x] Alpamayo OOD batch: `tickets/TASK-086/artifacts/task86-plan-cache/alpamayo_ood_batch_summary.json` heavy=`False`
- [x] Cached Alpamayo replay: `tickets/TASK-083/artifacts/task83-live-cached-replay/cached_ood_replay.json` heavy=`False`
- [x] Blocker ledger: `blockers.md` heavy=`False`
- [x] Live OOD video evidence: `tickets/TASK-079/artifacts/task79-live-ood-video/ood_video_evidence.json` heavy=`False`
- [x] Live OOD MP4: `tickets/TASK-079/artifacts/task79-live-ood-video/generated-base-animals-0076-regional-driving-behavior-000_ood.mp4` heavy=`True`
- [x] Alpamayo comparison artifact: `tickets/TASK-081/artifacts/task81-live-same-scene-comparison/alpamayo_ood_comparison.json` heavy=`False`
- [x] Reasoning HTML pack: `tickets/TASK-084/artifacts/task84-reasoning-pack/reasoning_video_pack.html` heavy=`False`
- [x] Campaign case 000 MP4: `tickets/TASK-085/artifacts/task85-live-campaign-2b/cases/000-generated-base-animals-0076-visual-noise-000-motorcycle_filtering/local-video/generated-base-animals-0076-visual-noise-000_ood.mp4` heavy=`True`
- [x] Campaign case 000 video evidence: `tickets/TASK-085/artifacts/task85-live-campaign-2b/cases/000-generated-base-animals-0076-visual-noise-000-motorcycle_filtering/local-video/ood_video_evidence.json` heavy=`False`
- [x] Campaign case 001 MP4: `tickets/TASK-085/artifacts/task85-live-campaign-2b/cases/001-generated-generalization-customobstacles-1028-occlusion-001-sudden_brake/local-video/generated-generalization-customobstacles-1028-occlusion-001_ood.mp4` heavy=`True`
- [x] Campaign case 001 video evidence: `tickets/TASK-085/artifacts/task85-live-campaign-2b/cases/001-generated-generalization-customobstacles-1028-occlusion-001-sudden_brake/local-video/ood_video_evidence.json` heavy=`False`

## Claim Boundaries

- `randomized_ood_scenario_generation=true`
- `model_weights_frozen=true`
- `alpamayo_open_loop_policy_evaluation=true`
- `production_autonomy_claim=false`
- `reasoning_pack_is_evidence_surface=true`
- `scripted_carla_video_may_be_live_or_cached=true`
- `real_time_vla_control=false`
- `scripted_ood_campaign=true`
- `stock_fail2drive_score=false`
- `alpamayo_batch_open_loop_policy_evaluation=true`
- `closed_loop_carla_control=false`
- `cached_alpamayo_replay=true`
- `live_carla_replay=true`
- `policy_output_source=cached_policy_decision`

## Slide Outline

- **Minimal-Shot Autonomy Thesis**: Frozen VLA + generated OOD stress tests + retrieved safety memory. (`submission_dossier.md`)
- **Randomized Scenario Forge**: Campaign cases: 2. (`scripted_ood_campaign_summary.json`)
- **Reasoning VLA Evidence**: Scenario: generated-base-animals-0076-regional-driving-behavior-000. (`tickets/TASK-084/artifacts/task84-reasoning-pack/reasoning_video_pack.html`)
- **Policy-To-Control Bridge**: Cached replay status: passed. (`cached_ood_replay.json`)
- **Evaluation And Limits**: Alpamayo batch status: passed. (`alpamayo_ood_batch_summary.json`)

## Two-Page Write-Up Draft

### Motivation

Minimal-shot autonomy should be judged by how systems respond to strange-but-plausible scenes that were not memorized during data collection.

### Architecture

0xDriver combines a deterministic OOD scenario forge, CARLA execution/evidence capture, a frozen reasoning VLA adapter, retrieved safety memory, and a conservative trajectory-control bridge.

### What Worked

Generated campaign status: passed; reasoning pack scenario: generated-base-animals-0076-regional-driving-behavior-000; cached replay status: passed.

### What Did Not

Stock Fail2Drive full-route scoring still needs a stable graphics-capable Linux CARLA host. The current Alpamayo evidence is open-loop or cached replay, not real-time closed-loop VLA control.

### Next

Use funding for a stable CARLA graphics host, route-aligned closed-loop evaluation, and larger randomized OOD campaigns.


## GPU Host

- overall_state: `alpamayo_open_loop_ready__stock_fail2drive_score_host_pending`
- recommendation: RTX 6000 Ada evidence is sufficient for Alpamayo 1.5 single-sample open-loop inference; stock Fail2Drive full-score execution remains a graphics-capable Linux CARLA host handoff.

## Open Blockers

- 2026-05-06 11:48 +0800 | fail2drive,carla,town13,score,capture | TASK-060 long-score attempt `town13-long-score-attempt-001` started the stock `Generalization_PedestriansOnRoad_1088` route and reached game time `0.600s` at about `0.142x`, then stopped making observable progress. A concurrent route-aligned Alpamayo capture attempt with a 60s CARLA timeout also failed waiting for the simulator. I terminated the route evaluator cleanly to avoid burning the full 1200s timeout on a stalled local Mac/Wine simulation. Evidence: `tickets/TASK-060/artifacts/town13-long-score-attempt-001-evidence/run_evidence.md` and `tickets/TASK-069/artifacts/town13-live-attach-attempt-004/carla_alpamayo_capture.json`. Next unblock path: use a graphics-capable Linux NVIDIA CARLA host for Fail2Drive scoring/capture, or rerun locally only after confirming CARLA can sustain route ticks and serve a second Python client during synchronous mode.
- 2026-05-06 11:34 +0800 | fail2drive,carla,town13,score | TASK-071 produced fresh Town13 MP4 evidence from the stock Fail2Drive `Generalization_PedestriansOnRoad_1088` route, but full route score/completion remains open because the run intentionally stops after early video capture. Restarted CARLA improved route speed to about `0.23x`, but the local Mac/Kegworks/Wine path is still not a fast full-suite scoring runtime. Evidence: `tickets/TASK-071/artifacts/town13-early-route-evidence/run_evidence.md`. Next unblock path: rerun without `--stop-after-video` for a long local route scoring attempt, or move the route to a faster graphics-capable Linux NVIDIA CARLA host.
- 2026-05-05 17:07 +0800 | h100,carla,vulkan | TASK-020 stock SimLingo H100 route run cannot reach policy execution because CARLA 0.9.15 exits before opening port `20000` on the RunPod H100 container. CUDA is compatible for SimLingo (`sm_90`), but CARLA needs a working graphics/Vulkan runtime; diagnostics show default Vulkan only exposes `llvmpipe`, forcing the NVIDIA ICD fails with `ERROR_INCOMPATIBLE_DRIVER`, and CARLA exits with status `1`. Evidence: `tickets/archive/TASK-020/artifacts/task20-evidence-final/remote_simlingo_evidence.md` and `tickets/archive/TASK-020/artifacts/task20-remote/carla_runtime_diagnostics.md`. Next unblock path: move the stock route to a graphics-capable Ampere host such as RTX 3090 / RTX A6000 / A40 / A10, or rebuild the SimLingo torch stack for the earlier RTX PRO 6000 Blackwell host where CARLA did launch.

## Demo Outline

1. Show generated OOD recipes and Bench2Drive route pack.
2. Show overlay/sidecar plan that injects companion actors into CARLA.
3. Show RAG comparison result (Alpamayo final trajectory delta: 2.6886m).
4. Show live-policy readiness honestly (alpamayo_memory_comparison_available=True, gpu_host=alpamayo_open_loop_ready__stock_fail2drive_score_host_pending).
5. Close with the current blocker and the next graphics-capable NVIDIA host run.

## Recent Progress

> - TASK-083 through TASK-088 landed the next submission train. New strongest
>   artifacts: an 8.0s live CARLA cached-Alpamayo replay video at
>   `tickets/TASK-083/artifacts/task83-live-cached-replay-video/ood_video_evidence.md`,
>   a reasoning/trajectory HTML pack at
>   `tickets/TASK-084/artifacts/task84-reasoning-pack/reasoning_video_pack.html`,
>   a two-case live scripted OOD campaign at
>   `tickets/TASK-085/artifacts/task85-live-campaign-2b/scripted_ood_campaign_summary.md`,
>   a cached Alpamayo batch comparison at
>   `tickets/TASK-086/artifacts/task86-plan-cache/alpamayo_ood_batch_summary.md`,
>   a V5 dossier plus video script at
>   `tickets/TASK-087/artifacts/submission-dossier-v5-live/submission_dossier.md`,
>   and a stock Fail2Drive host handoff at
>   `tickets/TASK-088/artifacts/task88-host-plan/fail2drive_host_plan.md`.
