# Alpamayo Probe Report

- model_id: `nvidia/Alpamayo-1.5-10B`
- status: `metadata_observed`
- blocked: `False`
- model_load_state: `not_requested`
- latency_ms: `None`
- vram_peak_mb: `0.0`

## Blockers

- none

## Artifacts

| artifact | present | bytes |
|---|---:|---:|
| `alpamayo_probe.json` | `True` | `542` |
| `gpu_snapshot.txt` | `True` | `66` |
| `package_versions.json` | `True` | `150` |
| `package_versions.txt` | `True` | `60` |
| `memory_usage.json` | `True` | `212` |
| `probe.log` | `True` | `0` |

## Expected Adapter Schema

- status: `unverified_adapter_stub`
- trajectory target: `20 x 2` waypoints for 5 seconds at 4 Hz when available
- TASK-039 must replace this with observed input/output shape evidence before live CARLA control.

## Redacted Excerpt

```text

NVIDIA RTX 6000 Ada Generation, 570.124.06, 49140 MiB, 2 MiB, 8.9

FileNotFoundError: [Errno 2] No such file or directory: 'uv'
{"download_latency_ms": 37230.37, "download_requested": true, "load_requested": false, "model_id": "nvidia/Alpamayo-1.5-10B", "model_info": {"gated": false, "id": "nvidia/Alpamayo-1.5-10B", "private": false, "sha": "f11cd25b758ab560114019b555dde2a8b92d88b4"}, "model_info_latency_ms": 147.96, "model_load_state": "not_requested", "nvidia_smi_exit_code": 0, "snapshot_path": "/workspace/.cache/driverx/huggingface/hub/models--nvidia--Alpamayo-1.5-10B/snapshots/f11cd25b758ab560114019b555dde2a8b92d88b4"}
{"torch": {"allocated_mb": 0.0, "compute_capability": "8.9", "device_name": "NVIDIA RTX 6000 Ada Generation", "reserved_mb": 0.0, "total_memory_mb": 48519.94, "vram_peak_mb": 0.0}}
{"cuda_available": true, "pip_freeze_exit_code": 1, "python": "/workspace/alpamayo1.5/a1_5_venv/bin/python", "torch_version": "2.8.0+cu128"}
```
