# AGENTS.md

Project operational contract for 0xDriver. Keep this file lightweight; put
stack-specific details and commands in `PROJECT_RULES.md`.

## Build & Run

- Current phase: first fixture-backed implementation.
- Install: optional `python3 -m pip install -e .`; local commands use `PYTHONPATH=src`.
- Dev: `PYTHONPATH=src python3 -m driverx run-scene --config configs/mock.yaml`
- QA path: `bash scripts/pre_push_check.sh`
- Docker path invariant: `scripts/run_carla_client_docker.sh` writes repo
  outputs under `/workspace`, while `scripts/run_fail2drive_client_docker.sh`
  writes under `/workspace/0xDriver`; keep output roots aligned with the wrapper
  in use. See `MEM-0020`.
- The CARLA Docker client is intentionally minimal; capture can run there, but
  video overlays/MP4 assembly may need host fallback when Pillow or ffmpeg is
  absent. See `MEM-0022`.

## Validation

- Bootstrap/full local gate: `bash scripts/pre_push_check.sh`
- Tests: `PYTHONPATH=src python3 -m unittest discover -s tests`
- Typecheck: not configured yet.
- Lint/syntax: `python3 -m compileall -q src tests`
- Build: not applicable yet.

## Docs State

- Architecture: `ARCHITECTURE.md`
- PRD: `docs/prd.md`
- Bootstrap: `docs/bootstrap-brief.md`
- Specs index: `docs/specs/README.md`
- History: `docs/HISTORY.md`
- Memory: `docs/MEMORY.md`
- Troubles: `docs/TROUBLES.md`
- Taste: `docs/TASTE.md`
- Tickets: active `tickets/TASK-*/ticket.md`, completed `tickets/archive/TASK-*/ticket.md`

## Context First

- Read `docs/prd.md`, `ARCHITECTURE.md`, and relevant specs before code edits.
- Search for existing patterns before adding modules.
- Keep Waymo dataset files, model weights, generated videos, and submission
  archives out of git unless a ticket explicitly changes artifact policy.
- No blind edits.

## Operating Modes

- Discovery mode: clarify product/research scope before PRD/spec changes.
- Planning mode: create or refresh durable specs/tickets before implementation.
- Build mode: execute approved tickets, then test and review.

## Project Bias

- Start with the smallest complete Waymo E2E offline pipeline.
- Treat VLA/VLM output as structured intent, not direct control.
- Prefer deterministic planners, smoothing, and safety checks around model output.
- Keep cloud GPU acceleration optional and swappable.
- Keep generated Bench2Drive route XML stock-compatible; DriverX OOD actor,
  asset, behavior, and memory intent belongs in sidecar overlays until a real
  companion injector is running. See `MEM-0018`.
- For local CARLA 0.9.16 scripted OOD props, use probed stock proxy
  blueprints (`static.prop.dirtdebris01`, `static.prop.foodcart`,
  `static.prop.constructioncone`) and do not rely on absent `trafficcone`
  placeholders. See `MEM-0021`.
- Promote CARLA OOD evidence only after road-alignment, visibility, conflict,
  duration, and artifact-completeness checks pass; setup-only or off-road
  videos are partial/legacy evidence, not hero artifacts. See `MEM-0023`.
- Scenario catalog promotion, policy evaluation, and submission browser hero
  selection must honor propagated `quality_status`; legacy/open-loop artifacts
  can support context but cannot become hero or closed-loop policy proof. See
  `MEM-0024`.
- For stock SimLingo/CARLA 0.9.15 live runs, prefer H100/H200-class `sm_90`
  hosts; Blackwell `sm_120` requires a separate PyTorch/CARLA rebuild path
  before it can run the upstream Python 3.8 + torch 2.2 stack. See `MEM-0017`.

## Delegation Guardrails

- Use review before completion claims after meaningful docs or build passes.
- Use visual QA only when UI/demo surfaces change.
- Use runtime debugging for reproducible runtime/model/dataset failures once
  implementation begins.

## Notes

- Update the active ticket once tickets exist; do not keep task state only in chat.
- If repeated mistakes or operator corrections happen, append them to
  `docs/TROUBLES.md` before promoting durable lessons.
