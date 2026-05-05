# Alpamayo Live Policy Decision

- policy_id: `alpamayo-live`
- adapter_kind: `alpamayo_open_loop`
- open_loop_policy_evaluation: `True`
- model_id: `nvidia/Alpamayo-1.5-10B`
- latency_ms: `96673.62`
- vram_peak_mb: `24478.66`
- pred_xyz_shape: `[1, 1, 1, 64, 3]`
- action_mode: `trajectory_chunk_open_loop`

## Chain Of Causation

Slow down, keep the trajectory centered, and proceed only after checking the generated obstacle corridor.
