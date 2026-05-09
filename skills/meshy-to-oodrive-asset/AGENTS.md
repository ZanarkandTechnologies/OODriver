# AGENTS.md

## Purpose

This skill is an agent-side bridge from Meshy API outputs to OODrive external
asset manifests.

## Rules

- Never commit Meshy API keys, generated meshes, thumbnails, or downloaded
  provider payloads.
- Read `MESHY_API_KEY` from environment or ignored `my.env`.
- Write generated assets under ignored `artifacts/runs/...`.
- Emit OODrive external manifests only after a local mesh file exists.
- Do not claim CARLA spawnability from Meshy generation alone. CARLA proof still
  requires OODrive `package-asset`, `probe-asset-blueprint`, and rendered spawn
  evidence. See `MEM-0058`.
