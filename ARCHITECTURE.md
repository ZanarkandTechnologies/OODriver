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
    C --> N["Local 2D OOD simulator"]
    C --> O["DriverX scripted CARLA OOD demo"]
    O --> P["RGB frames + entity tracks"]
    P --> Q["OOD overlay video evidence"]
    E["Fail2Drive result records"] --> F["Failure memory builder"]
    F --> G["Retrieval memory bank"]
    C --> H["Memory retrieval"]
    G --> H
    H --> I["Policy prompt or adapter context"]
    I --> N
    I --> R["Alpamayo open-loop scene report"]
    Q --> R
    C --> J["CARLA/Fail2Drive command planner"]
    J --> K["Local Mac smoke path or Linux NVIDIA runtime"]
    L["Waymo E2E support track"] --> M["Open-loop ADE and trajectory evidence"]
```

## Canonical Surfaces

- `docs/prd.md`: current scenario-forge PRD.
- `docs/specs/minimal-shot-vla-roadmap.md`: end-to-end roadmap from live CARLA
  probing through generated assets, behavior scripts, policy adapters, and RAG
  comparison.
- `tickets/TASK-064`, `tickets/TASK-070`, and `tickets/TASK-082`: current
  runnable local OOD demo and submission-pack evidence. TASK-078 through
  TASK-082 now own the live scripted CARLA OOD capture, long OOD video,
  same-scene Alpamayo packaging, same-capture memory comparison, and V4
  submission pack.
  TASK-060/TASK-069 remain live-runtime follow-up work for full Town13 route
  completion and route-aligned Alpamayo capture.
- `src/driverx/scenarios`: scenario seed and OOD recipe generation.
- `src/driverx/memory`: failure-memory creation and retrieval.
- `src/driverx/simulators`: CARLA smoke checks, Fail2Drive command planning,
  overlay injection, sidecar planning, route-video assembly, and the local 2D
  OOD simulator.
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
4. active `tickets/TASK-*/ticket.md`
5. relevant module `README.md`
6. archived tickets for prior Waymo evidence when needed

## Current Limits

- TASK-007 does not run SimLingo, Alpamayo, or live Fail2Drive.
- CARLA on Apple Silicon is treated as an optional smoke path until server,
  Python client, Fail2Drive, and policy execution work together.
- Generated scenarios now export stock-compatible Bench2Drive route XML plus
  DriverX sidecar overlays. Town13 is installed and loadable locally, and a
  stock Fail2Drive Town13 route starts through Docker, writes a checkpoint, and
  emits RGB frames. TASK-071 adds an early-video runner that captured a fresh
  0.5s MP4 from `Generalization_PedestriansOnRoad_1088`; full score/completion
  still needs a longer local run or faster graphics-capable CARLA host.
- TASK-078 proves the DriverX-owned scripted CARLA OOD runner against live local
  CARLA through the Docker client: 120 captured frames, 24.0s substrate, entity
  tracks, generated stock proxy props, and cleanup evidence.
- TASK-079 adds reusable OOD overlays and MP4 assembly for the live generated
  scene. Current video evidence is explicitly `source_kind=live_carla`, but it
  remains a scripted DriverX OOD demo rather than stock Fail2Drive route score.
- TASK-064 provides a dependency-light end-to-end local simulator artifact. It
  is the current primary demo artifact, but it is not a live CARLA route score.
- Regional driving behavior traces and dry-run generated asset manifests are
  shipped as local evidence; real generated mesh import remains a future
  provider/runtime task.
- TASK-080/TASK-081 link that same generated scene to Alpamayo 1.5 open-loop
  reasoning and a memory/no-memory comparison. The package duplicates one live
  ego RGB camera into Alpamayo's three camera slots; this is valid for current
  shape/proof evidence but is not a full multi-camera CARLA autonomy stack.
- Alpamayo CARLA control remains open-loop today: live inference and memory
  comparison are proven, while TASK-062 owns the first cached trajectory replay
  bridge toward closed-loop control.
