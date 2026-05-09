---
name: oodrive-cli
version: 1.0.0
description: Use when an agent needs to operate the OODrive product CLI for prompt-to-CARLA scenario generation, Fail2Drive route XML authoring/validation, CARLA/ScenarioRunner runtime proof, Alpamayo reasoning attachment, demo-video/report export, or submission-readiness scoring. Trigger for requests like "generate an OODrive scenario", "make Fail2Drive XML", "run this in CARLA", "show snapshots/video", "attach Alpamayo reasoning", or "score the demo".
allowed-tools: Read, Grep, Glob, Bash
---

# OODrive CLI

## Purpose

Use OODrive as an agent-operable autonomy evidence workbench: agents author scenario intent/files, while OODrive validates, runs, captures, reasons, scores, and packages evidence.

## Source Of Truth

- Repo: `/Users/kenjipcx/SOTA/0xDriver`
- Main CLI: `PYTHONPATH=src python3 -m oodrive ...`
- Product name: `OODrive`; `driverx` is internal/compat.
- Durable project rules: `AGENTS.md`, `README.md`, `docs/MEMORY.md`, `docs/TROUBLES.md`
- Command examples: [command-cookbook.md](references/command-cookbook.md)

## Trigger Conditions

Use this skill when the user asks to:

- Generate or validate OOD driving scenarios for CARLA.
- Write or inspect Fail2Drive route XML.
- Run or dry-run a scenario in CARLA/Fail2Drive/ScenarioRunner.
- Capture snapshots, videos, route evidence, or artifact manifests.
- Attach Alpamayo/keyframe reasoning or RAG/memory evidence.
- Score hero demos, generated environments, closed-loop traces, or submission readiness.
- Show actual media artifacts back to the user.

## Workflow

1. **Enter the repo and read guardrails.**
   `cd /Users/kenjipcx/SOTA/0xDriver`; read `AGENTS.md`, `README.md`, and the relevant ticket/doc if the task is ticketed.
2. **Choose the correct lane.**
   Use canonical OODrive loop for product-generated CARLA evidence; use `f2d-*` for Fail2Drive XML/upstream scenario workflows; use `carla-*`/ScenarioRunner commands for map/weather/assets/probes.
3. **Generate or author the smallest scenario artifact.**
   For OODrive-native, call `oodrive generate`. For Fail2Drive, have the agent write JSON/XML and run `f2d-write-route` or `f2d-validate-route`.
4. **Validate before runtime.**
   Do not launch CARLA/Fail2Drive until XML/OSC2/asset/map validation passes or the blocker is recorded.
5. **Run the cheapest proof first.**
   Start with dry-run/manifests. Escalate to live CARLA only when the user asks for visual/runtime proof or when final promotion requires it.
6. **Capture visible evidence.**
   Prefer local/public images/videos in `artifacts/runs/...`; when media is local, show it with Markdown image/video links using absolute paths.
7. **Attach reasoning and scores.**
   Use `reason`, `analyze-keyframes`, `f2d-reason`, `demo-video`, `f2d-demo-video`, `score-demo`, or relevant score commands. Keep fake/cached/live labels explicit.
8. **Report artifacts, not vibes.**
   Return the exact XML/JSON/report/media paths, metric lines, blockers, and next live-proof step.

## Decision Branches

- **OODrive-native prompt-to-CARLA:** `generate -> place -> reason -> demo-video -> score-demo`.
- **Fail2Drive upstream scenarios:** `f2d-catalog -> f2d-write-route/f2d-validate-route -> f2d-run-route -> f2d-reason -> f2d-demo-video -> f2d-evaluate-model`.
- **Agent-authored OpenSCENARIO 2.0:** `validate-osc2 -> scenario-runner-package -> scenario-runner-run`.
- **Map/weather/object setup:** `carla-catalog`, `carla-control`, `carla-compose`, `prepare-map-import`, `package-asset`, `probe-asset-blueprint`, `spawn-custom-asset`.
- **No GPU/CARLA available:** produce validated XML/manifests and explicit blockers; do not claim live simulator proof.
- **GPU/RunPod available:** use live CARLA for screenshots/video, but still record dry-run/validation artifacts first.

## Claim Boundaries

Use these labels unless live evidence proves otherwise:

- `closed_loop_vla_control=false`
- `real_time_vla_control=false`
- `sampled_open_loop_reasoning=true`
- `time_warped_offline_demo=true`

For Fail2Drive, be explicit:

- Fail2Drive provides upstream route XML/scenario/evaluator behavior.
- OODrive provides the agent-facing CLI, validation, evidence, reasoning, and scoring layer.
- Dry-run/fake/cached artifacts are contract proof, not live runtime proof.

## Top 3 Gotchas

1. **Do not skip validation.**
   Always validate route XML, OSC2, map imports, or asset manifests before claiming runtime readiness.
2. **Do not overclaim closed-loop Alpamayo.**
   Alpamayo reasoning over sampled frames is open-loop unless its outputs actually drive CARLA controls with observe-infer-act-observe evidence.
3. **Do not show only text when media was requested.**
   Pull or render snapshots/videos locally and show them with absolute Markdown media links. If live rendering failed, show the blocker artifact and the best available validated XML/snapshot proof.

## Judgement Questions

Use `advise` when these are not mechanically determined:

- Should this be OODrive-native, Fail2Drive, OpenSCENARIO, or direct CARLA scripting?
- Is this artifact good enough for submission, or only contract/runtime-debug proof?
- Should we spend time on live GPU rendering now, or ship validated XML plus local snapshots first?
- Is a model behavior claim supported by actual controls, or only reasoning/evaluation over frames?

## Outcome Contract

A successful OODrive CLI run leaves at least one of:

- Scenario DB, route XML, OSC2, map/asset manifest, or validation report.
- CARLA/Fail2Drive/ScenarioRunner run evidence JSON/Markdown.
- Snapshot/video media under `artifacts/runs/...` or `artifacts/exported/...`.
- Reasoning/keyframe/RAG report with claim boundaries.
- Metric output such as `METRIC hero_demo_score=...`, `METRIC f2d_demo_readability_score=...`, or `METRIC closed_loop_video_score=...`.
- A concise final summary with absolute artifact paths, what is live-proven, what is only dry-run/fixture-proven, and the next blocker.

## Minimal Command Map

Load [command-cookbook.md](references/command-cookbook.md) when you need exact command syntax. The most common forms are:

```bash
PYTHONPATH=src python3 -m oodrive generate "blocked wet urban lane with pedestrian occlusion"
PYTHONPATH=src python3 -m oodrive f2d-catalog --format both
PYTHONPATH=src python3 -m oodrive f2d-write-route --example RoadBlocked --validate
PYTHONPATH=src python3 -m oodrive f2d-validate-route --route <route.xml>
PYTHONPATH=src python3 -m oodrive f2d-run-route --route <route.xml> --dry-run
PYTHONPATH=src python3 -m oodrive f2d-reason --evidence <run_evidence.json> --route <route.xml> --mode fake
PYTHONPATH=src python3 -m oodrive f2d-demo-video --evidence <run_evidence.json> --reasoning <f2d_reasoning.json> --route <route.xml> --input-video <source.mp4>
```

## Optional References

- [architecture.md](references/architecture.md): why OODrive wraps rather than replaces CARLA/Fail2Drive.
- [workflows.md](references/workflows.md): longer workflow variants for live RunPod, Fail2Drive, and submission scoring.
- [gotchas.md](references/gotchas.md): long-tail runtime failures and recovery patterns.
