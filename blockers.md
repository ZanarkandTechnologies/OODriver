# Blockers

Live blocker ledger for long-running 0xDriver execution. Add blockers here when
work cannot proceed inside the current ticket, then continue to the next
unblocked ticket when possible.

## Open

- 2026-05-05 23:50 +0800 | alpamayo,huggingface,cosmos | TASK-052
  bootstrapped Alpamayo 1.5 on the RunPod RTX 6000 Ada pod, downloaded the
  `nvidia/Alpamayo-1.5-10B` snapshot to `/workspace`, and verified CUDA
  availability. Load-only inference is blocked because Alpamayo imports its
  gated base model `nvidia/Cosmos-Reason2-8B`, and Hugging Face returned
  `403 Forbidden` for `https://huggingface.co/nvidia/Cosmos-Reason2-8B/...`.
  Next unblock path: request/accept access for
  `https://hf.co/nvidia/Cosmos-Reason2-8B` on the same Hugging Face account
  backing `HF_TOKEN`, then rerun the TASK-052 load probe.

- 2026-05-05 22:33 +0800 | fail2drive,docker,network | TASK-043
  added the Dockerized Fail2Drive client path, but local image build stalled
  during the pip wheel download layer after the apt layer succeeded. The image
  is intentionally lightweight by default and keeps torch gated behind
  `DRIVERX_FAIL2DRIVE_INSTALL_TORCH=1`. Next unblock path: rerun
  `scripts/build_fail2drive_client_docker.sh` on a faster network or the A6000
  host.

- 2026-05-05 22:10 +0800 | fail2drive,local-deps | TASK-042 local
  Fail2Drive route runner reached the evaluator, but native macOS Python failed
  before CARLA connection with `ModuleNotFoundError: No module named 'numpy'`.
  Evidence: `artifacts/runs/task42-route-run-numpy-blocker/fail2drive_route_run.md`.
  Next unblock path: run Fail2Drive inside a Docker client environment that
  mounts both `0xDriver` and `../external/fail2drive`.

- 2026-05-05 19:42 +0800 | fail2drive,video | TASK-041 removes the
  hard dependency on Fail2Drive's missing `tools/generate_video.py` by adding
  `python -m driverx assemble-route-video`, but live video evidence still needs
  a route run to create the RGB frame folder under `SAVE_PATH`.

- 2026-05-05 17:07 +0800 | h100,carla,vulkan | TASK-020 stock
  SimLingo H100 route run cannot reach policy execution because CARLA 0.9.15
  exits before opening port `20000` on the RunPod H100 container. CUDA is
  compatible for SimLingo (`sm_90`), but CARLA needs a working graphics/Vulkan
  runtime; diagnostics show default Vulkan only exposes `llvmpipe`, forcing the
  NVIDIA ICD fails with `ERROR_INCOMPATIBLE_DRIVER`, and CARLA exits with
  status `1`. Evidence:
  `tickets/TASK-020/artifacts/task20-evidence-final/remote_simlingo_evidence.md`
  and `tickets/TASK-020/artifacts/task20-remote/carla_runtime_diagnostics.md`.
  Next unblock path: move the stock route to a graphics-capable Ampere host
  such as RTX 3090 / RTX A6000 / A40 / A10, or rebuild the SimLingo torch stack
  for the earlier RTX PRO 6000 Blackwell host where CARLA did launch.

## Resolved

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
