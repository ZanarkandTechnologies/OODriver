# Bootstrap Brief

## Summary

- Project: 0xDriver
- Goal: Build a credible minimal-shot autonomy submission using VLA-inspired
  reasoning and deterministic trajectory planning on Waymo E2E scenes.
- Audience: SoTA Commission judges, autonomy engineers, and the project owner
  evaluating whether deployment engineering can turn slow general reasoning into
  useful long-tail driving predictions.

## Intent

- Why now: SoTA Commission I is open with a May 10, 2026 deadline, and recent
  VLA systems work suggests that real-time behavior is mainly an engineering
  deployment problem rather than a train-from-scratch problem.
- What good looks like: a repo, analysis notebook, short write-up, and 1-5
  minute demo showing the pipeline operating on Waymo E2E examples, including a
  known failure case and honest latency accounting.
- What this scaffold should optimize for first: fast planning, reproducible
  evidence, and a clean future path from PRD to tickets to implementation.

## Recommended Shape

- App type: offline research pipeline with notebook/demo outputs.
- Topology recommendation: single Python package plus notebooks, with an
  optional remote inference service adapter later.
- Why this topology: Waymo E2E evaluation is offline, so local/cloud network
  latency does not block the first deliverable; a separate service can be added
  only when needed for GPU-backed VLA inference.
- Non-goals for v1:
  - no new VLA model training from scratch
  - no real vehicle or closed-loop hardware deployment
  - no production real-time safety claim
  - no checked-in Waymo dataset shards or model weights

## Stack Decisions

- Frontend: none for v1; optional local visualizer or deck later.
- Backend: none for v1; optional inference server adapter later.
- Database: none.
- Runtime / package manager: Python 3.10 or newer; prefer stdlib-first local
  commands unless a Waymo package constraint requires otherwise. On Apple
  Silicon, official Waymo dependencies run through the Linux amd64 Docker
  runtime.
- Deployment target: local Mac for planning, data parsing, and notebooks; rented
  NVIDIA GPU for heavy VLA inference if needed.

## Runtime / QA Commands

- Preferred app-only run path: not created yet.
- Preferred QA / evidence-capture run path: future `pytest` plus notebook/demo
  artifact generation.
- Required local services: none.
- Process vs compose expectation: plain local processes first.
- Expected targets or base URLs: none yet.
- Port / env assumptions agents must honor: future services must use
  configurable ports and dataset/model paths.
- Evidence-capture notes: save camera panels, raw structured VLA output,
  pre-smooth trajectories, post-smooth trajectories, ADE tables, and latency
  breakdowns.

## Validation and Hooks

- Required local checks: `bash scripts/pre_push_check.sh` during bootstrap.
- Optional heavy local checks: manual `desloppify` or CodeRabbit only.
- Hook policy: hooks are scaffolded but opt-in.
- Hook activation choice: do not auto-enable; human may run
  `git config core.hooksPath .githooks`.
- Preferred hook stages: pre-push once code exists; pre-commit remains minimal.
- CodeRabbit policy: manual workflow only for v1.
- Desloppify policy: manual workflow only for v1.
- Separate CI / deployment gate: none defined yet.
- TypeScript typecheck policy: not applicable unless a TypeScript surface is
  added later.

## Agent Experience / Testability

- Important states the agent must reach quickly:
  - parse one Waymo E2E frame
  - render front camera strip with future trajectory overlay
  - run a mock reasoner
  - generate and smooth a 20-point prediction
  - compute ADE on a tiny validation sample
  - package a dry-run submission shard
- Fast-entry surfaces to create or preserve: sample config, tiny-run command,
  mock backend, deterministic fixture path.
- Reset / seed / fixture strategy: keep small synthetic fixtures in git; keep
  real Waymo data external.
- Hidden state that needs probes, HUDs, or DOM mirrors: raw VLA JSON, parser
  validation errors, trajectory ranking scores, latency breakdown.
- Preferred browser proof stack: not needed until UI exists.
- Initial QA cookbook workflows to document: dataset smoke test, visualization
  proof, ADE smoke test, submission packaging dry-run.

## File-Size Policy

- Warn threshold: 500 raw lines.
- Block threshold: 1000 raw lines.
- Measurement: raw line count over tracked source files.
- Source-file scope / exclusions: use `scripts/pre_push_check.sh`.

## Shared Utility Policy

- Preferred shared utility location: future `src/driverx/common/`.
- When to extract vs keep local: extract only after real multi-module reuse.
- Helper naming / placement constraints: avoid catch-all `utils.py` files unless
  the utility surface is intentionally shared and documented.

## Decision Boundaries

- What the scaffold may decide automatically: docs layout, ticket templates,
  QA cookbook shell, artifact policy, and initial offline-first architecture.
- What still requires confirmation: final model/provider choice, cloud GPU
  budget, Waymo dataset subset, submission metadata, and whether to build a web
  demo or deck-only demo.

## Defaults Chosen

- Recommended defaults accepted: docs-first Codexter scaffold, offline-first
  Waymo E2E slice, optional cloud GPU, no training from scratch.
- Explicit overrides: no Next.js/Convex app scaffold for v1 because the first
  deliverable is a research pipeline and notebook/demo package.
