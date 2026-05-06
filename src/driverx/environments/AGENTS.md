# AGENTS.md

Environment generation module for CARLA OOD scenario packs.

- Keep this module deterministic under explicit seeds.
- Use stock CARLA proxy props as the runnable path; generated GLB/Meshy prompts
  are metadata until an import pipeline is explicitly implemented.
- Do not import CARLA, torch, TensorFlow, or provider SDKs here.
- Preserve road-local placement semantics for every generated asset.
