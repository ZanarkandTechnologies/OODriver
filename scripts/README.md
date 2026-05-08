# Scripts

Active scripts are the ones a new collaborator should reach for first.

## Active

- `pre_push_check.sh`: local validation gate.
- `sync_runpod_proxy_workspace.sh`: proxy-safe sync to a RunPod/Kasm pod.
- `setup_runpod_carla_0916_graphics.sh`: CARLA 0.9.16 + Python 3.12 setup on a
  graphics-capable Kasm pod.
- `run_remote_alpamayo_carla_inference.sh`: host-driven Alpamayo package runner.
- `remote_gpu_snapshot.sh`, `run_remote_gpu_probe.sh`: remote GPU diagnostics.
- `build_viewer_showcase_videos.py`: assemble short viewer-facing showcase
  clips from existing evidence.
- `build_final_demo_video.sh`, `build_paper_demo_video.sh`: demo video helpers.
- `build_carla_client_docker.sh`, `run_carla_client_docker.sh`: local CARLA
  Python client bridge.
- `build_fail2drive_client_docker.sh`, `run_fail2drive_client_docker.sh`:
  Fail2Drive bridge.

## Archived

- `archive/simlingo/`: older stock SimLingo remote bootstrap/route scripts.
  The code adapters still exist under `src/driverx/simulators` for tests and
  historical reports, but this is no longer the main submission path.
