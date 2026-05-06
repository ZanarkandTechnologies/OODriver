# 0xDriver Submission Dossier V6

## Thesis

0xDriver is a CARLA OOD scenario forge for minimal-shot autonomy: generate weird-but-plausible road situations, quality-gate them, and measure how VLA-style policies reason about them without AV fine-tuning.

## Current Evidence

- cataloged scenarios: `9`
- scenarios with video: `2`
- scenarios with VLA reasoning: `1`
- policy evaluations by status: passed `0`, planned `9`, blocked `18`
- local decision artifacts attached: `0`

## Hero Candidates

- No submission-grade hero is selected yet. A hero must be manually promoted and pass video plus road-alignment quality gates.

## Failure Candidates

- No quality-passed failure case is selected yet.

## Claim Boundaries

- This is a scenario-generation and open-loop VLA evaluation harness.
- Closed-loop VLA driving remains future work unless a later run explicitly routes model output into CARLA control.
- Custom GLB generation is represented by Meshy-ready prompts and stock CARLA proxies in this version.

## Open Blockers

- 2026-05-06 22:21 +0800 | runpod,carla,vulkan,gpu | TASK-089 installed CARLA 0.9.16 on the RTX 6000 Ada RunPod host at `/workspace/carla/CARLA_0.9.16` and synced DriverX to `/workspace/0xDriver`. Remote Python imports `carla`, and focused DriverX tests pass on the GPU host. Live CARLA server launch is still blocked because the container NVIDIA Vulkan ICD fails with `ERROR_INCOMPATIBLE_DRIVER` for `libGLX_nvidia.so.0`; non-root CARLA launch never opens port `2000`. Evidence: `tickets/TASK-089/artifacts/remote-carla-setup/remote_carla_setup.md`. Next unblock path: use a RunPod template/host with graphics-capable NVIDIA Vulkan exposed, or keep CARLA local for rendering while using the GPU host for Alpamayo inference and repo tests.
- 2026-05-06 11:48 +0800 | fail2drive,carla,town13,score,capture | TASK-060 long-score attempt `town13-long-score-attempt-001` started the stock `Generalization_PedestriansOnRoad_1088` route and reached game time `0.600s` at about `0.142x`, then stopped making observable progress. A concurrent route-aligned Alpamayo capture attempt with a 60s CARLA timeout also failed waiting for the simulator. I terminated the route evaluator cleanly to avoid burning the full 1200s timeout on a stalled local Mac/Wine simulation. Evidence: `tickets/TASK-060/artifacts/town13-long-score-attempt-001-evidence/run_evidence.md` and `tickets/TASK-069/artifacts/town13-live-attach-attempt-004/carla_alpamayo_capture.json`. Next unblock path: use a graphics-capable Linux NVIDIA CARLA host for Fail2Drive scoring/capture, or rerun locally only after confirming CARLA can sustain route ticks and serve a second Python client during synchronous mode.
- 2026-05-06 11:34 +0800 | fail2drive,carla,town13,score | TASK-071 produced fresh Town13 MP4 evidence from the stock Fail2Drive `Generalization_PedestriansOnRoad_1088` route, but full route score/completion remains open because the run intentionally stops after early video capture. Restarted CARLA improved route speed to about `0.23x`, but the local Mac/Kegworks/Wine path is still not a fast full-suite scoring runtime. Evidence: `tickets/TASK-071/artifacts/town13-early-route-evidence/run_evidence.md`. Next unblock path: rerun without `--stop-after-video` for a long local route scoring attempt, or move the route to a faster graphics-capable Linux NVIDIA CARLA host.
- 2026-05-05 17:07 +0800 | h100,carla,vulkan | TASK-020 stock SimLingo H100 route run cannot reach policy execution because CARLA 0.9.15 exits before opening port `20000` on the RunPod H100 container. CUDA is compatible for SimLingo (`sm_90`), but CARLA needs a working graphics/Vulkan runtime; diagnostics show default Vulkan only exposes `llvmpipe`, forcing the NVIDIA ICD fails with `ERROR_INCOMPATIBLE_DRIVER`, and CARLA exits with status `1`. Evidence: `tickets/archive/TASK-020/artifacts/task20-evidence-final/remote_simlingo_evidence.md` and `tickets/archive/TASK-020/artifacts/task20-remote/carla_runtime_diagnostics.md`. Next unblock path: move the stock route to a graphics-capable Ampere host such as RTX 3090 / RTX A6000 / A40 / A10, or rebuild the SimLingo torch stack for the earlier RTX PRO 6000 Blackwell host where CARLA did launch.
