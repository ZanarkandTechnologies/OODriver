# Blockers

Live blocker ledger for long-running 0xDriver execution. Add blockers here when
work cannot proceed inside the current ticket, then continue to the next
unblocked ticket when possible.

## Open

- 2026-05-06 04:08 +0800 | fail2drive,carla,town13,performance | TASK-068
  proved local CARLA can load `Town13` and the stock Fail2Drive route starts,
  writes a checkpoint, and emits RGB frames, but the local Kegworks/Wine Mac
  runtime is too slow to finish the route inside the 300s cap. Route logs show
  about `0.075x` simulation speed and the checkpoint remains `entry_status:
  Started`. Evidence:
  `tickets/TASK-068/artifacts/town13-load-probe-after-local-demo/carla_map_inventory.md`,
  `tickets/TASK-068/artifacts/town13-route-run-with-torch/fail2drive_route_run.md`,
  and
  `tickets/TASK-068/artifacts/town13-route-evidence-partial-001/run_evidence.md`.
  Next unblock path: run the same stock route on a faster graphics-capable
  Linux NVIDIA host, or rerun locally with a much longer timeout if cost/time is
  acceptable.

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
