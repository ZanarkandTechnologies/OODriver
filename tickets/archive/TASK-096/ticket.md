# TASK-096: RunPod Kasm Desktop CARLA Graphics Runtime

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-089, TASK-093, TASK-095
- location: `scripts`, `tickets/TASK-096/artifacts`, `blockers.md`, remote `/workspace`
- enter when: local/fake simulator generation is done but final hero evidence still needs a graphics-capable Linux CARLA host
- leave when: the RunPod Kasm desktop pod either runs CARLA 0.9.16 with NVIDIA Vulkan or records a precise residual blocker and the repo has a repeatable proxy-sync/setup path
- blockers: none
- spawned follow-ups: TASK-097 live quality-passed CARLA campaign on the GPU desktop
- complexity: M

### Summary

Convert the new KasmVNC RunPod pod from a manual setup experiment into a
repeatable graphics-host runtime for DriverX. This ticket owns the practical
unblocker for the final submission path: make NVIDIA Vulkan visible to CARLA,
install CARLA 0.9.16 on the persistent workspace, sync the current repo despite
RunPod proxy SSH limitations, and prove a CARLA Python client can connect.

### Scope

- In scope: RunPod SSH smoke, NVIDIA Vulkan ICD workaround, CARLA 0.9.16
  download/extract/install, repo sync through proxy SSH, focused remote tests,
  setup logs, and blocker updates.
- Out of scope: Alpamayo inference, SimLingo, full Fail2Drive route scoring,
  custom Meshy assets, and final submission video rendering.

### Acceptance Criteria

- [x] AC-1: RunPod Kasm pod is reachable over SSH and exposes RTX 6000 Ada.
- [x] AC-2: NVIDIA Vulkan is visible through a per-process ICD file.
- [x] AC-3: Repo has a repeatable proxy-safe sync script for Kasm templates
  where scp/rsync fail.
- [x] AC-4: CARLA 0.9.16 launches on the pod and opens port `2000`.
- [x] AC-5: Python client connects to CARLA and records map/actor evidence.

### Build Notes

- New pod SSH:
  `poz4gv6ryu2571-644111cc@ssh.runpod.io` with
  `~/.ssh/id_ed25519_runpod`.
- Kasm desktop proxy:
  `https://poz4gv6ryu2571-6901.proxy.runpod.net/`.
- `vulkaninfo --summary` is not supported by the Ubuntu 20.04 package; use
  `vulkaninfo` with `DISPLAY=` and `VK_ICD_FILENAMES=/workspace/carla/nvidia_icd.json`.
- `/etc/vulkan/icd.d` is read-only in this template, so the NVIDIA ICD must be
  passed per process instead of globally installed.

### Evidence

- SSH smoke passed with user `kasm-user`, `DISPLAY=:1`, `80G` container disk,
  `/workspace` mounted, and GPU `NVIDIA RTX 6000 Ada Generation`.
- Kasm web port `6901` returned HTTP `401`, proving the desktop service is up.
- Default OpenGL is software llvmpipe, but explicit NVIDIA Vulkan ICD sees the
  RTX 6000 Ada as a discrete GPU.
- Remote CARLA setup script started:
  `/workspace/setup_carla_0916_driverx.sh`.
- Remote setup log:
  `/workspace/driverx_remote_artifacts/setup_carla_0916_driverx.log`.
- CARLA 0.9.16 Linux tarball download completed from the Backblaze release
  mirror. The first extraction used the wrong strip depth, so the launcher was
  repaired by re-extracting without `--strip-components=1`; the tracked setup
  script now preserves top-level launchers.
- CARLA server launched on the GPU desktop with:
  `DISPLAY= VK_ICD_FILENAMES=/workspace/carla/nvidia_icd.json ./CarlaUE4.sh -RenderOffScreen -nosound -quality-level=Low -carla-port=2000`.
- Port `2000` opened after five 2-second polling attempts.
- Python client smoke passed in `/workspace/driverx_py312` using the official
  CARLA `cp312` wheel:
  `connected_map Carla/Maps/Town10HD_Opt`, `actors 23`.
- Local proxy sync script added:
  `scripts/sync_runpod_proxy_workspace.sh`.
- RunPod-local configs added:
  `configs/carla_ood_demo.runpod.sample.yaml` and
  `configs/scripted_ood_campaign.runpod.sample.yaml`.
- Focused local tests passed:
  `PYTHONPATH=src python3 -m unittest tests.test_runpod_remote tests.test_carla_road_frame tests.test_carla_ood_demo tests.test_scripted_ood_campaign`.

### Blockers

- None.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
