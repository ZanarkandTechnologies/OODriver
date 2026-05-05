# Blockers

Live blocker ledger for long-running 0xDriver execution. Add blockers here when
work cannot proceed inside the current ticket, then continue to the next
unblocked ticket when possible.

## Open

- 2026-05-05 19:24 +0800 | alpamayo,probe,gpu | TASK-038 shipped the
  local Alpamayo probe classifier and remote probe script, but live Alpamayo
  model proof still needs a confirmed checkpoint/repo id and an explicit remote
  run of `scripts/run_remote_alpamayo_probe.sh`. The script is intentionally
  download/load gated with `ALPAMAYO_DOWNLOAD=1` and `ALPAMAYO_LOAD=1` so a
  default run does not unexpectedly pull a large model.

- 2026-05-05 18:58 +0800 | fail2drive,video | TASK-033 route-video
  smoke planning is implemented, but the external Fail2Drive checkout does not
  include `tools/generate_video.py`. The plan still writes the expected command
  and output contract, and live route execution can produce `SAVE_PATH`
  visualizations first. TASK-034 should accept an externally generated video or
  add a DriverX-owned video assembler so this does not block evidence
  normalization.

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

- 2026-05-05 15:19 +0800 | runpod,ssh | RunPod SSH initially rejected
  local keys because `/root/.ssh/authorized_keys` split the public key over two
  lines. Fixed by replacing it with one single-line `ssh-ed25519 ... runpod`
  entry; direct TCP SSH now works.
