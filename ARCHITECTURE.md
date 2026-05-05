# Architecture

0xDriver is now a CARLA/Fail2Drive-first minimal-shot autonomy harness. The
Waymo E2E pipeline remains a supporting open-loop evidence track.

## Purpose

Build a reproducible environment for testing whether VLA/VLM driving policies
generalize to long-tail closed-loop scenarios with minimal prior examples. The
system generates OOD scenario recipes, stores policy failures as compact safety
memory, and prepares CARLA/Fail2Drive runs without requiring CARLA during local
development.

## System Map

```mermaid
flowchart TD
    A["Fail2Drive route XML or fixture seeds"] --> B["Scenario seed loader"]
    B --> C["Deterministic OOD recipe generator"]
    C --> D["Scenario suite report"]
    E["Fail2Drive result records"] --> F["Failure memory builder"]
    F --> G["Retrieval memory bank"]
    C --> H["Memory retrieval"]
    G --> H
    H --> I["Policy prompt or adapter context"]
    C --> J["CARLA/Fail2Drive command planner"]
    J --> K["Local Mac smoke path or Linux NVIDIA runtime"]
    L["Waymo E2E support track"] --> M["Open-loop ADE and trajectory evidence"]
```

## Canonical Surfaces

- `docs/prd.md`: current scenario-forge PRD.
- `docs/specs/minimal-shot-vla-roadmap.md`: end-to-end roadmap from live CARLA
  probing through generated assets, behavior scripts, policy adapters, and RAG
  comparison.
- `tickets/TASK-039/ticket.md`: active-but-blocked Alpamayo CARLA adapter
  surface.
- `src/driverx/scenarios`: scenario seed and OOD recipe generation.
- `src/driverx/memory`: failure-memory creation and retrieval.
- `src/driverx/simulators`: CARLA smoke checks, Fail2Drive command planning,
  overlay injection, sidecar planning, and route-video assembly.
- `src/driverx/policies`: policy adapters, runtime readiness matrix, and
  Alpamayo probe reporting.
- `src/driverx/pipeline`: generated OOD suite execution, evidence reports, demo
  pack, and submission dossier builders.
- `src/driverx/datasets`, `planning`, `pipeline`, `submission`: preserved
  Waymo/open-loop support track.

## Runtime Direction

Local Mac:

- fixture scenario generation
- memory/report artifacts
- Fail2Drive command dry-runs
- optional Apple Silicon CARLA TCP smoke checks
- Waymo fixture and Docker bridge commands

Remote or Linux NVIDIA runtime:

- reproducible CARLA/Fail2Drive execution
- SimLingo/CarLLaVA policy runs
- Alpamayo inference
- latency-sensitive serving experiments

## Read Order

1. `AGENTS.md`
2. `docs/prd.md`
3. `ARCHITECTURE.md`
4. `tickets/TASK-007/ticket.md`
5. relevant module `README.md`
6. archived tickets for prior Waymo evidence when needed

## Current Limits

- TASK-007 does not run SimLingo, Alpamayo, or live Fail2Drive.
- CARLA on Apple Silicon is treated as an optional smoke path until server,
  Python client, Fail2Drive, and policy execution work together.
- Generated scenarios now export stock-compatible Bench2Drive route XML plus
  DriverX sidecar overlays; live route video is still blocked until the route
  runner produces RGB frames.
- Regional driving behavior traces and dry-run generated asset manifests are
  shipped as local evidence; real generated mesh import remains a future
  provider/runtime task.
- Alpamayo CARLA control is blocked until the offline probe provides observed
  model input/output shapes.
