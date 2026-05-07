# 0xDriver V8 Two-Page Write-Up

## Motivation

Autonomy that waits for data collection will always trail reality. 0xDriver focuses on the minimal-shot testing loop: make rare situations, run them, explain what the model noticed, and preserve the failure as memory.

## Architecture

Scenario Studio generates OOD briefs and candidates; CARLA renders the selected case; the risk timeline derives perception from simulator tracks; RAG supplies prior safety principles; frozen Alpamayo 1.5 supplies sampled open-loop reasoning and trajectory intent; the curation queue decides what to run next.

## What Worked

The V8 packet links 24 generated candidates, 281 risk events, a 28.0s time-warped clip, and 3 Alpamayo/RAG comparisons. The reasoning overlay rendered 420 frames.

## What Did Not Work

The current system is not closed-loop VLA driving. The video is time-warped offline evidence, and Alpamayo is sampled as an open-loop reasoning/trajectory evaluator. A live LLM/Meshy generator and real-time VLA serving are future work, not claims in this submission.

## Where Prize Money Goes

The next prototype step is a persistent graphics/CUDA host for repeated closed-loop CARLA runs, richer generated 3D assets, and a larger OOD memory bank built from repeated failures.

## Open Blockers

2026-05-07 16:36 +0800 | carla,video,paper-demo | TASK-112 fresh paper-demo CARLA source render was not attempted in this pass because local `127.0.0.1:2000` refused connection during the optional smoke check. Existing TASK-102 source video was time-warped and used for TASK-111/TASK-113. Evidence: `tickets/TASK-112/artifacts/timewarp-v1/video_timewarp.md`. Next unblock path: restart the graphics-capable CARLA host and run `configs/carla_ood_paper_demo.sample.yaml` for a fresh longer source capture.; 2026-05-06 11:48 +0800 | fail2drive,carla,town13,score,capture | TASK-060 long-score attempt `town13-long-score-attempt-001` started the stock `Generalization_PedestriansOnRoad_1088` route and reached game time `0.600s` at about `0.142x`, then stopped making observable progress. A concurrent route-aligned Alpamayo capture attempt with a 60s CARLA timeout also failed waiting for the simulator. I terminated the route evaluator cleanly to avoid burning the full 1200s timeout on a stalled local Mac/Wine simulation. Evidence: `tickets/TASK-060/artifacts/town13-long-score-attempt-001-evidence/run_evidence.md` and `tickets/TASK-069/artifacts/town13-live-attach-attempt-004/carla_alpamayo_capture.json`. Next unblock path: use a graphics-capable Linux NVIDIA CARLA host for Fail2Drive scoring/capture, or rerun locally only after confirming CARLA can sustain route ticks and serve a second Python client during synchronous mode.; 2026-05-06 11:34 +0800 | fail2drive,carla,town13,score | TASK-071 produced fresh Town13 MP4 evidence from the stock Fail2Drive `Generalization_PedestriansOnRoad_1088` route, but full route score/completion remains open because the run intentionally stops after early video capture. Restarted CARLA improved route speed to about `0.23x`, but the local Mac/Kegworks/Wine path is still not a fast full-suite scoring runtime. Evidence: `tickets/TASK-071/artifacts/town13-early-route-evidence/run_evidence.md`. Next unblock path: rerun without `--stop-after-video` for a long local route scoring attempt, or move the route to a faster graphics-capable Linux NVIDIA CARLA host.; 2026-05-05 17:07 +0800 | h100,carla,vulkan | TASK-020 stock SimLingo H100 route run cannot reach policy execution because CARLA 0.9.15 exits before opening port `20000` on the RunPod H100 container. CUDA is compatible for SimLingo (`sm_90`), but CARLA needs a working graphics/Vulkan runtime; diagnostics show default Vulkan only exposes `llvmpipe`, forcing the NVIDIA ICD fails with `ERROR_INCOMPATIBLE_DRIVER`, and CARLA exits with status `1`. Evidence: `tickets/archive/TASK-020/artifacts/task20-evidence-final/remote_simlingo_evidence.md` and `tickets/archive/TASK-020/artifacts/task20-remote/carla_runtime_diagnostics.md`. Next unblock path: move the stock route to a graphics-capable Ampere host such as RTX 3090 / RTX A6000 / A40 / A10, or rebuild the SimLingo torch stack for the earlier RTX PRO 6000 Blackwell host where CARLA did launch.

## Model And Data Declarations

- Base VLA: nvidia/Alpamayo-1.5-10B, frozen, non-commercial research use.
- No AV-dataset fine-tuning was performed.
- Alpamayo evidence status: passed; open-loop only.
- CARLA video is simulator evidence and is retimed offline for presentation.
- Generated videos, datasets, model weights, remote caches, and credentials are excluded from git.
