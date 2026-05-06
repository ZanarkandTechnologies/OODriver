# TASK-099: Alpamayo Package From RunPod Hero Video

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-097, TASK-098
- location: `src/driverx/policies/alpamayo_ood_package.py`, `scripts`, `tickets/TASK-097/artifacts`, `tickets/TASK-099/artifacts`
- enter when: RunPod has produced one quality-passed hero CARLA OOD video and the submission needs latest-VLA reaction evidence for that exact scenario
- leave when: the hero MP4 can be converted into a torch-ready Alpamayo package, the RunPod Alpamayo environment is probed on the Kasm pod, and live inference is either attempted or blocked only by a concrete secret/access gate
- blockers: none; live inference was completed in TASK-100 after user installed Hugging Face auth through the Kasm web terminal
- spawned follow-ups: TASK-100 live Alpamayo reasoning on the hero scenario, TASK-101 high-fidelity CARLA scenario runner, TASK-102 AI scenario studio
- complexity: M

### Summary

Connect the new simulator contribution to the VLA track. The first hero
scenario is now a real 60s RunPod CARLA video, so this ticket converts that
video into an Alpamayo-compatible open-loop input package, validates tensor
materialization locally, and probes the Kasm pod's Alpamayo runtime without
leaking Hugging Face credentials through the PTY-only SSH proxy.

### Scope

- In scope: build an Alpamayo package from the hero MP4 when raw RGB frames are
  not available locally, validate materialization, plan the remote Alpamayo
  batch command, probe the RunPod Alpamayo env, and record the remaining live
  inference blocker precisely.
- Out of scope: closed-loop VLA steering, CARLA control from Alpamayo outputs,
  Meshy/custom GLB import, SimLingo, and token handling that would echo secrets
  into terminal logs.

### Acceptance Criteria

- [x] AC-1: `build-alpamayo-ood-package` can extract frames from MP4 evidence
  when `rgb_folder` does not already contain enough PNGs.
- [x] AC-2: The RunPod hero overlay MP4 writes an
  `alpamayo_carla_input_package.json` with scenario id, behavior id, memory
  context, nav text, and four selected frames.
- [x] AC-3: `materialize-alpamayo-input` validates the package as
  `torch_ready=true` with no validation errors.
- [x] AC-4: `run-alpamayo-ood-batch` produces a rerunnable open-loop plan for
  the hero package.
- [x] AC-5: The Kasm RunPod Alpamayo runtime is probed with CUDA visible on
  RTX 6000 Ada, and the follow-up TASK-100 records live inference after
  Hugging Face auth was installed through the Kasm web terminal.

### Build Notes

- Added MP4 extraction support to `driverx.policies.alpamayo_ood_package` and
  exposed it through `--video` / `--ffmpeg-bin`.
- The package uses one ego RGB camera from the CARLA video and duplicates the
  four selected frames across Alpamayo front-left/front/front-right indices.
  This is explicitly open-loop VLA reasoning evidence, not calibrated
  production multi-camera autonomy.
- The selected frame window is centered near the overlay `worst_risk.tick` when
  present, including nested `overlay.worst_risk` payloads.
- Existing Kasm proxy SSH requires a PTY and echoes submitted command text, so
  Codex should not paste or base64-wrap Hugging Face tokens through that path.

### Evidence

- Hero source video:
  `tickets/TASK-097/artifacts/pulled/artifacts/runs/task97-runpod-overlay-v2/generated-base-animals-0076-visual-noise-000_ood.mp4`.
- Alpamayo package:
  `tickets/TASK-097/artifacts/task99-hero-alpamayo-package/alpamayo_carla_input_package.json`.
- Package report:
  `tickets/TASK-097/artifacts/task99-hero-alpamayo-package/alpamayo_ood_input_package.md`.
- Tensor materialization:
  `tickets/TASK-097/artifacts/task99-hero-alpamayo-materialized/alpamayo_tensor_manifest.json`.
- Tensor report:
  `tickets/TASK-097/artifacts/task99-hero-alpamayo-materialized/alpamayo_tensor_manifest.md`.
- Batch plan:
  `tickets/TASK-097/artifacts/task99-hero-alpamayo-batch-plan/alpamayo_ood_batch_summary.json`.
- Verification materialization rerun:
  `tickets/TASK-099/artifacts/verify-task99-materialized/alpamayo_tensor_manifest.json`.
- Verification batch plan rerun:
  `tickets/TASK-099/artifacts/verify-task99-batch-plan/alpamayo_ood_batch_summary.json`.
- RunPod Kasm Alpamayo env probe:
  `tickets/TASK-099/artifacts/runpod-kasm-alpamayo-env/alpamayo_env_probe.json`.
- RunPod Kasm Alpamayo env report:
  `tickets/TASK-099/artifacts/runpod-kasm-alpamayo-env/alpamayo_env_probe.md`.
- Follow-up live Alpamayo proof:
  `tickets/TASK-100/artifacts/hero-alpamayo-live/alpamayo_live_prediction.json`.
- Follow-up live Alpamayo policy conversion:
  `tickets/TASK-100/artifacts/task100-hero-alpamayo-policy/alpamayo_policy_decision.json`.
- Final RunPod proxy sync:
  `DRIVERX_REMOTE_TEST=1 scripts/sync_runpod_proxy_workspace.sh
  poz4gv6ryu2571-644111cc@ssh.runpod.io ~/.ssh/id_ed25519_runpod
  /workspace/0xDriver` passed, with `17` focused remote tests on
  `/workspace/driverx_py312`.
- Focused local tests:
  `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_ood_package
  tests.test_submission_scenario_browser tests.test_scenario_catalog
  tests.test_carla_ood_demo` passed with `15` tests.
- Full local gate:
  `bash scripts/pre_push_check.sh` passed with `358` tests, `2` skips, and
  compileall lint.
- Secret scan:
  `rg -n "hf_[A-Za-z0-9]{20,}|RUNPOD_[A-Z_]*=.+[A-Za-z0-9]{16,}|MESHY_API_KEY=.+[A-Za-z0-9]" ...`
  found no live secret values in the active work surface; the only hit is a
  literal regex example in an older QA report.
- Review:
  `tickets/TASK-099/artifacts/review/task99-review.json` passes with
  overall score `4.1`.

### Blockers

- Resolved. User installed Hugging Face auth through the Kasm web terminal, and
  TASK-100 records live Alpamayo inference plus DriverX policy conversion.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
