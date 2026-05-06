# Blockers

Live blocker ledger for long-running 0xDriver execution. Add blockers here when
work cannot proceed inside the current ticket, then continue to the next
unblocked ticket when possible.

## Open

- 2026-05-06 11:48 +0800 | fail2drive,carla,town13,score,capture | TASK-060
  long-score attempt `town13-long-score-attempt-001` started the stock
  `Generalization_PedestriansOnRoad_1088` route and reached game time `0.600s`
  at about `0.142x`, then stopped making observable progress. A concurrent
  route-aligned Alpamayo capture attempt with a 60s CARLA timeout also failed
  waiting for the simulator. I terminated the route evaluator cleanly to avoid
  burning the full 1200s timeout on a stalled local Mac/Wine simulation.
  Evidence:
  `tickets/TASK-060/artifacts/town13-long-score-attempt-001-evidence/run_evidence.md`
  and
  `tickets/TASK-069/artifacts/town13-live-attach-attempt-004/carla_alpamayo_capture.json`.
  Next unblock path: use a graphics-capable Linux NVIDIA CARLA host for
  Fail2Drive scoring/capture, or rerun locally only after confirming CARLA can
  sustain route ticks and serve a second Python client during synchronous mode.

- 2026-05-06 11:34 +0800 | fail2drive,carla,town13,score | TASK-071 produced
  fresh Town13 MP4 evidence from the stock Fail2Drive
  `Generalization_PedestriansOnRoad_1088` route, but full route
  score/completion remains open because the run intentionally stops after early
  video capture. Restarted CARLA improved route speed to about `0.23x`, but the
  local Mac/Kegworks/Wine path is still not a fast full-suite scoring runtime.
  Evidence:
  `tickets/TASK-071/artifacts/town13-early-route-evidence/run_evidence.md`.
  Next unblock path: rerun without `--stop-after-video` for a long local route
  scoring attempt, or move the route to a faster graphics-capable Linux NVIDIA
  CARLA host.

- 2026-05-05 17:07 +0800 | h100,carla,vulkan | TASK-020 stock
  SimLingo H100 route run cannot reach policy execution because CARLA 0.9.15
  exits before opening port `20000` on the RunPod H100 container. CUDA is
  compatible for SimLingo (`sm_90`), but CARLA needs a working graphics/Vulkan
  runtime; diagnostics show default Vulkan only exposes `llvmpipe`, forcing the
  NVIDIA ICD fails with `ERROR_INCOMPATIBLE_DRIVER`, and CARLA exits with
  status `1`. Evidence:
  `tickets/archive/TASK-020/artifacts/task20-evidence-final/remote_simlingo_evidence.md`
  and `tickets/archive/TASK-020/artifacts/task20-remote/carla_runtime_diagnostics.md`.
  Next unblock path: move the stock route to a graphics-capable Ampere host
  such as RTX 3090 / RTX A6000 / A40 / A10, or rebuild the SimLingo torch stack
  for the earlier RTX PRO 6000 Blackwell host where CARLA did launch.

## Resolved

- 2026-05-07 02:04 +0800 | alpamayo,runpod,kasm,huggingface |
  TASK-100 resolved the TASK-099 live Alpamayo blocker. The Kasm RunPod lane ran
  Alpamayo 1.5 on the hero CARLA OOD package and produced CoC reasoning,
  trajectory tensor shapes, 111765.05ms latency, and 23559.71MB peak VRAM.
  Evidence: `tickets/archive/TASK-100/ticket.md`.

- 2026-05-07 05:42 +0800 | carla,runpod,video,scenario-quality |
  TASK-102 resolved the "better video" blocker for the submission path. The
  RunPod Kasm CARLA host produced `task102-high-fidelity-hero-v6`, a
  420-frame / 84.0s / 1280x720 high-fidelity scripted OOD video candidate on
  Town10HD_Opt, and the strict quality pass checked video presence, road
  alignment, conflict distance, actor density, and OOD actor smoothness. The
  MP4 is kept remote by artifact policy at
  `/workspace/0xDriver/artifacts/runs/task102-high-fidelity-hero-v6/cases/000-generated-base-animals-0076-regional-driving-behavior-000-motorcycle_filtering/video/task102_high_fidelity_hero_v6_full.mp4`.
  Evidence:
  `tickets/TASK-102/artifacts/task102-high-fidelity-hero-v6/scripted_ood_campaign_summary.md`.

- 2026-05-07 01:22 +0800 | runpod,carla,campaign,video,catalog |
  TASK-097/TASK-098 resolved the "credible long video" blocker. The Kasm
  RunPod CARLA host ran a quality-gated scripted OOD campaign, selected one
  road-aligned live case, produced 300 frames / 60.0s of video substrate, and
  regenerated an overlay MP4 after installing Pillow in `/workspace/driverx_py312`.
  The pulled evidence now indexes as a `hero` scenario in the submission
  browser. Evidence: `tickets/TASK-097/ticket.md` and
  `tickets/TASK-098/ticket.md`.

- 2026-05-07 00:52 +0800 | runpod,carla,vulkan,gpu | TASK-096 resolved the
  prior RTX 6000 Ada container graphics blocker by moving to a RunPod Kasm
  desktop pod, using a per-process NVIDIA Vulkan ICD, installing CARLA 0.9.16
  on `/workspace/carla`, launching CARLA headlessly on port `2000`, and
  connecting with a Python 3.12 CARLA client. Evidence:
  `tickets/TASK-096/ticket.md`.

- 2026-05-06 20:41 +0800 | carla,docker,video,campaign | TASK-085 live
  campaign captured two 24.0s CARLA cases through Docker. Docker-side video
  assembly initially lacked Pillow/ffmpeg, so DriverX now falls back to copying
  raw frames when Pillow is absent and the host assembled local MP4 evidence
  from the captured RGB folders. Evidence:
  `tickets/TASK-085/artifacts/task85-live-campaign-2b/scripted_ood_campaign_summary.md`.

- 2026-05-06 23:18 +0800 | carla,docker,scripted-ood,video | TASK-078
  resolved the live DriverX scripted OOD capture blocker. Docker reached local
  CARLA at `host.docker.internal:2000`; after replacing unavailable
  `static.prop.trafficcone` with installed CARLA 0.9.16 proxy props, the runner
  captured 120 RGB frames, 24.0s of scripted OOD video substrate, entity
  tracks, generated stock props, and full cleanup evidence. Evidence:
  `tickets/TASK-078/artifacts/task78-live-ood-capture-v3/carla_ood_demo.md`
  and
  `tickets/TASK-079/artifacts/task79-live-ood-video/ood_video_evidence.md`.

- 2026-05-06 19:20 +0800 | carla,docker,scripted-ood,video | TASK-072
  original live Docker client timeout against local CARLA is superseded by
  TASK-078. The old blocked report remains preserved at
  `tickets/TASK-072/artifacts/task72-live-candidate/carla_ood_demo.md`.

- 2026-05-06 11:34 +0800 | fail2drive,carla,town13,video | TASK-071 resolved
  the immediate "how far until we get a video" blocker. The runner now watches
  RGB frames, stops after early video capture, and the host assembler produced
  `tickets/TASK-071/artifacts/town13-early-video-after-restart/Generalization_PedestriansOnRoad_1088_early.mp4`.

- 2026-05-06 04:08 +0800 | fail2drive,carla,map,restart | TASK-068 resolved
  the post-install CARLA relaunch/readiness blocker. Docker client probes now
  connect to local CARLA 0.9.16, list `Town13`, and successfully load
  `Carla/Maps/Town13/Town13`. Evidence:
  `tickets/TASK-068/artifacts/town13-load-probe-after-local-demo/carla_map_inventory.md`.

- 2026-05-06 04:08 +0800 | fail2drive,docker,torch | The first TASK-068 route
  attempt failed immediately because the Fail2Drive Docker client lacked
  `torch`. Rebuilding the existing optional torch path with
  `DRIVERX_FAIL2DRIVE_INSTALL_TORCH=1 bash scripts/build_fail2drive_client_docker.sh`
  resolved the dependency blocker and allowed the route to start.

- 2026-05-06 03:34 +0800 | fail2drive,carla,map | TASK-058 resolved the
  original "Town13 not installed" blocker. The official Windows
  `AdditionalMaps_0.9.16.zip` package downloaded successfully, extracted
  23,647 files into the local Kegworks CARLA root, and `Town13` appears in
  `available_maps`. Remaining blocker is now only the simulator restart/readiness
  step above.

- 2026-05-06 03:22 +0800 | alpamayo,huggingface,physical-ai,dataset | TASK-059
  resolved the upstream `nvidia/PhysicalAI-Autonomous-Vehicles` dataset gate.
  The dataset-forced RunPod shape probe used real PhysicalAI sample frames
  (`shape_source_used=dataset`) and observed `pred_xyz=[1,1,1,64,3]`,
  `pred_rot=[1,1,1,64,3,3]`, CoC output, `124987.44ms` latency, and
  `24881.65MB` peak VRAM. Evidence:
  `tickets/TASK-059/artifacts/physicalai-shape-probe-summary/alpamayo_shape_probe_report.md`.

- 2026-05-06 01:50 +0800 | fail2drive,docker,video | TASK-054B resolved the
  TASK-041/TASK-042/TASK-043 local route blockers. The Docker image now builds,
  imports `carla`, `numpy`, `torch`, and CARLA PythonAPI `agents`, reaches
  live local CARLA through `host.docker.internal:2000`, and a Town10 fallback
  route produced 41 RGB frames plus a DriverX-assembled MP4. Evidence:
  `tickets/archive/TASK-054B/artifacts/qa_report.md`.

- 2026-05-06 00:05 +0800 | alpamayo,huggingface,cosmos,attention | The
  TASK-052 nested Cosmos access blocker is resolved. After the user accepted
  the gated agreement, the RunPod probe downloaded the nested files and loaded
  `nvidia/Alpamayo-1.5-10B` on RTX 6000 Ada with
  `ALPAMAYO_ATTN_IMPLEMENTATION=eager`. SDPA mode is incompatible with
  Alpamayo's custom architecture, so future live probes should use `eager` or
  install the upstream flash-attn path instead. Evidence:
  `tickets/archive/TASK-052/artifacts/probe-load-eager-after-cosmos-summary/alpamayo_probe_report.md`.

- 2026-05-05 23:50 +0800 | alpamayo,probe,gpu | The TASK-038 generic
  "needs live Alpamayo probe" blocker is resolved by TASK-052 evidence:
  model metadata was observed, the 21GB Alpamayo snapshot downloaded, CUDA is
  available, and the remaining live-load blocker is specifically gated access
  to the nested Cosmos backbone.

- 2026-05-05 23:35 +0800 | runpod,ssh,alpamayo | The apparent A6000 SSH
  blocker on `195.26.233.80:36723` was a stale RunPod direct TCP mapping.
  RunPod REST metadata resolved the current SSH target as
  `root@195.26.233.80 -p 55050` with `~/.ssh/id_ed25519_runpod`, and live SSH
  reached the RTX 6000 Ada pod. Future runs should resolve RunPod SSH metadata
  first instead of reusing old Connect-tab ports.

- 2026-05-05 19:42 +0800 | fail2drive,video | The TASK-033 missing
  `tools/generate_video.py` helper is mitigated by TASK-041's DriverX-owned
  ffmpeg route-video assembler. Remaining live blocker is now missing RGB
  frames, not missing assembler code.

- 2026-05-05 15:19 +0800 | runpod,ssh | RunPod SSH initially rejected
  local keys because `/root/.ssh/authorized_keys` split the public key over two
  lines. Fixed by replacing it with one single-line `ssh-ed25519 ... runpod`
  entry; direct TCP SSH now works.
