# Stock Fail2Drive Full-Score Host Plan

- target_route: `Generalization_PedestriansOnRoad_1088`
- suitability: `blocked`
- graphics_ready: `False`
- cuda_ready: `False`

## Required

- NVIDIA GPU with working Vulkan/OpenGL graphics exposure
- CARLA 0.9.16 server can load Town13 and open the client port
- Python client environment can import carla and numpy
- Enough disk for CARLA, Fail2Drive checkout, logs, and route frames

## Commands

```bash
ssh <ssh-opts> <graphics-host> 'nvidia-smi && vulkaninfo --summary || true'
```
```bash
ssh <ssh-opts> <graphics-host> 'python3 - <<PY\nimport carla, numpy\nprint("carla client ok")\nPY'
```
```bash
bash scripts/sync_remote_gpu.sh <graphics-host> /workspace/0xdriver-artifacts/fail2drive-score # then run stock Fail2Drive route on the graphics host
```
```bash
PYTHONPATH=src python -m driverx run-fail2drive-route --route-id Generalization_PedestriansOnRoad_1088 --run-id full-score-town13
```

## Blockers

- Need a host where CARLA 0.9.16 can render and tick, not just a CUDA-visible inference pod.

## Pullback Policy

- include: `json, md, txt, log`
- exclude: `model weights, datasets, full RGB folders, videos unless explicitly requested`
