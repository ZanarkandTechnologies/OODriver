# driverx.policies

Policy adapter boundary for frozen VLA/VLM, mock, and deterministic fallback
policies.

## Rules

- Real model adapters must fail with setup guidance when credentials,
  checkpoints, or runtime dependencies are missing.
- Local tests must run through mock or deterministic adapters only.
- Adapter outputs must include structured intent/action, latency, reason summary,
  and memory ids when memory was injected.
- For the RunPod RTX 6000 Ada Alpamayo lane, use
  `ALPAMAYO_ATTN_IMPLEMENTATION=eager` unless a later ticket proves a
  flash-attn setup; SDPA is not compatible with the current Alpamayo custom
  architecture. See `MEM-0019`.
