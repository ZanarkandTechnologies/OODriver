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
- RunPod CARLA rendering invariant: use the Kasm desktop path from
  `scripts/setup_runpod_carla_0916_graphics.sh`, with per-process NVIDIA
  Vulkan ICD and Python 3.12 CARLA client venv under `/workspace`; avoid the
  old non-desktop RTX 6000 Ada container path for CARLA rendering. See
  `MEM-0025`.
- RunPod evidence video invariant: fresh Kasm pods need `ffmpeg` and Pillow in
  `/workspace/driverx_py312` before judge-facing overlay videos are assembled.
  See `MEM-0026`.
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
- Treat Fail2Drive as the pinned upstream benchmark/runtime submodule at
  `third_party/fail2drive`; OODrive should extend it through agent-authored
  route XML, validation, execution wrappers, evidence capture, reasoning, and
  scoring rather than copying or reimplementing its scenario classes. See
  `MEM-0052`.
- Use `oodrive f2d-*` for agent-operated Fail2Drive workflows in dependency
  order: catalog, validate/write route, run evidence, reason, demo video, then
  model-reaction batch reporting. Dry-run/fake evidence is contract proof only
  until live CARLA/Alpamayo artifacts exist. See `MEM-0053`.
- Use the OODrive Fail2Drive capture agent for evaluator video evidence; the
  upstream `visu_agent.py` is a display-only path and does not write RGB frames.
  Optimized CARLA town routes may need `_Opt` speed-limit aliases before
  evaluator launch. See `MEM-0055`.
- Fail2Drive videos with prompt-named visible assets must pass
  `oodrive f2d-qa-assets` before promotion; route XML/catalog alignment is not
  visual proof without rendered evidence frames. See `MEM-0056`.
- Fail2Drive animal asset proof requires the packaged Fail2Drive CARLA runtime
  plus a matching CARLA 0.9.15 Python client; loose `.uasset` copies into stock
  CARLA do not prove animal spawnability, and duck claims require a passed
  duck blueprint/content probe. See `MEM-0057`.
- Use OODrive as the product-facing scenario generator name. `oodrive ...` and
  `python -m oodrive ...` are the canonical CLI database/control plane;
  `driverx oodrive`, `driverx oodriver`, and `driverx studio` are
  compatibility aliases only. See `MEM-0035`.
- The next live CARLA + Alpamayo sprint should optimize the flagship
  `flagship-malaysia-wet-roadwork` case before adding more scenario breadth.
  See `MEM-0036`.
- Treat `oodrive generate -> oodrive place -> oodrive reason` as the canonical
  product loop: placement plans are CARLA-ready specs, dry-run placement is not
  live object spawning, and Alpamayo reasoning is open-loop unless a live
  model-driven control trace exists. See `MEM-0037`.
- Waymo-to-Fail2Drive reconstruction claims require direction-aware multiview
  object transcription, explicit XML object/actor mappings or written
  exclusions, and render QA. Stock scenario type selection alone is not
  image-grounded reconstruction. See `MEM-0054`.
- Treat prompt-to-3D-assets-inside-CARLA as unproved until the chain has a
  generated/ingested mesh, asset manifest, CARLA import registry or blueprint
  probe, and live spawn evidence. Stock proxies are fallback simulator evidence,
  not custom generated assets. See `MEM-0044`.
- Treat `static.prop.mesh` actor-spawn JSON as insufficient custom-asset proof:
  current packaged CARLA can render already-cooked `/Game/...` mesh paths, but
  raw Meshy FBX/GLB paths stay unproved until visible live frames exist. See
  `MEM-0059`.
- Treat Fail2Drive Scenario Hub as XML and preview-image sharing, not a custom
  mesh upload/cook path; hub scenarios may reference installed simulator assets
  only. See `MEM-0060`.
- Production prompt-to-CARLA generator promotion requires prompt-image QA on
  live CARLA frames. Partial visual matches can prove simulator execution, but
  they cannot be called exact prompt fidelity or flagship proof. See
  `MEM-0046`.
- OODrive CARLA environment generation composes scenarios inside existing CARLA
  towns by selecting maps, weather, road anchors, stock proxy assets, dynamic
  actors, background vehicles, and pedestrians; do not claim arbitrary Unreal
  world generation unless a custom map/mesh import chain is actually proved. See
  `MEM-0047`.
- CARLA generator gallery promotion must be gated by a live capability matrix
  and image-diversity/prompt-visual-match scoring over real CARLA captures;
  prompt-only scenario variation and text/card storyboards are planning
  artifacts, not gallery or submission evidence. See `MEM-0048`.
- TASK-128 proves the Kasm pod can run the canonical loop in open-loop form:
  prompt-generated CARLA placement, live scripted render, and fresh Alpamayo
  reasoning over captured frames. Keep this evidence labeled
  `closed_loop_vla_control=false` and `real_time_vla_control=false` until
  Alpamayo outputs directly drive CARLA controls. See `MEM-0038`.
- Judge-facing OODrive hero videos must pass a mechanical demo-quality score
  before promotion; raw MP4 presence is insufficient without frame/time,
  reasoning, RAG, risk, motion/duration, and claim-boundary evidence. See
  `MEM-0039`.
- Closed-loop CARLA hero videos must show an ego-visible third-person/spectator
  view with dense action-tick source frames and brisk auto-duration rendering;
  sparse checkpoint stills, front-camera-only clips, or over-stretched videos
  must fail promotion even if the trace/control JSON exists. See `MEM-0051`.
- For SoTA Commission I, optimize against the local commission-readiness score
  once hero video quality is saturated. Winning evidence must cover the
  commission criteria: technical excellence, novelty, feasibility, adherence to
  minimal-shot autonomy, randomized scenario generation, navigation evidence,
  compute/latency honesty, motivation, and a failure case. See `MEM-0040`.
- When the requested proof is env-sim/CARLA and the Kasm/GPU host is available,
  attempt live Kasm CARLA evidence before a completion claim; fake-CARLA and
  local scripted traces are contract tests, not final simulator proof. See
  `MEM-0042`.
- Promote closed-loop Alpamayo/CARLA evidence only after scored
  observe-infer-act-observe recurrence, synchronized sensor frame provenance,
  safety-guarded controls, and inference handoff evidence pass; fake/cached
  traces are contract proof until live Kasm evidence passes both closed-loop
  score gates. See `MEM-0045`.
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
- Do not transmit HF tokens or other secrets through Kasm RunPod proxy SSH
  heredocs/base64 streams because the proxy requires a PTY and echoes command
  input; install tokens through the web terminal or direct TCP SSH/SFTP. See
  `MEM-0027`.
- Remote Alpamayo inference commands must preserve the logged-in Hugging Face
  auth home: do not override `HF_HOME` or `XDG_CACHE_HOME` unless the same token
  is installed there; use `HF_HUB_CACHE`/`TRANSFORMERS_CACHE` for workspace
  model caches. See `MEM-0049`.
- Final submission media evidence must distinguish `public_url`, `local_file`,
  `remote_only`, and `missing`; only public or local exported media can be
  marked as proved. See `MEM-0033`.
- Offline/time-warped CARLA video and sampled Alpamayo reasoning checkpoints
  are acceptable for the final demo only when explicitly labeled as not
  real-time VLA control. See `MEM-0034`.
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
