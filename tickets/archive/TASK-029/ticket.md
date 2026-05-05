# TASK-029: Remote GPU Probe Script

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-028
- location: `scripts`, `tests`, docs,
  `tickets/TASK-029/artifacts`
- enter when: TASK-028 can assess host suitability from artifacts, but the next
  GPU host still needs a repeatable way to collect those artifacts
- leave when: one script can SSH to a GPU host, write compact snapshot/CUDA/CARLA
  graphics probe artifacts remotely, and pull them back without copying heavy
  files
- blockers: none for local implementation
- spawned follow-ups: none
- complexity: S

## Summary

Add a remote probe script for future GPU rentals. It should collect the exact
small artifacts that `assess-gpu-host` needs before running expensive
SimLingo/CARLA jobs: GPU snapshot, torch CUDA architecture compatibility, and
Vulkan/CARLA graphics diagnostics.

## Acceptance Criteria

- [x] AC-1: Script writes `gpu_snapshot.txt`, `torch_cuda_compatibility.json`,
  and `carla_runtime_diagnostics.md` under a remote probe directory.
- [x] AC-2: Script pulls compact probe artifacts into a local directory.
- [x] AC-3: Script avoids model weights, CARLA installs, caches, media, and
  archives.
- [x] AC-4: Tests inspect the script contract without requiring SSH or GPU.
- [x] AC-5: README documents the probe-to-assessment flow.

## Evidence

- Script: `scripts/run_remote_gpu_probe.sh`
- Live H100 probe artifacts:
  `tickets/TASK-029/artifacts/h100-probe-live/gpu_snapshot.txt`,
  `tickets/TASK-029/artifacts/h100-probe-live/torch_cuda_compatibility.json`,
  and
  `tickets/TASK-029/artifacts/h100-probe-live/carla_runtime_diagnostics.md`
- Live H100 probe suitability report:
  `tickets/TASK-029/artifacts/h100-probe-live-suitability/gpu_host_suitability.json`
  and
  `tickets/TASK-029/artifacts/h100-probe-live-suitability/gpu_host_suitability.md`
- Live H100 probe verdict: `cuda_model=ready`, `carla_graphics=blocked`, and
  `host_storage=warning`.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_docker_scripts` passed
  with `14` tests.
- Syntax check: `bash -n scripts/run_remote_gpu_probe.sh` passed.
- Local gate: `bash scripts/pre_push_check.sh` passed with `166` tests.
- Review:
  `tickets/TASK-029/artifacts/review/2026-05-05_172900_review.md`
  passed with overall score `4.0`.
- Live probe evidence review:
  `tickets/TASK-029/artifacts/review/2026-05-05_173100_live_probe_review.md`
  passed with overall score `4.0`.

## Blockers

- None currently.
