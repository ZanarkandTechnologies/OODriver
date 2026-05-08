# Project Rules: 0xDriver

This file defines project-specific technical rules, stack choices, validation
expectations, and runtime assumptions.

## Tech Stack

- Language: Python first for scenario generation, simulator control, model
  evidence, and reports; TypeScript only if a later web demo is added.
- Runtime: Python 3.10 or newer locally; the RunPod/Kasm CARLA path uses the
  Python 3.12 CARLA wheel from CARLA 0.9.16.
- Simulator: CARLA 0.9.16 is the main live evidence path; Fail2Drive supplies
  route families and benchmark framing.
- Autonomy/model integration: OODrive packages CARLA observations for Alpamayo
  or other VLA/VLM backends, then keeps model output behind policy adapters and
  safety-bounded controls.
- Support tracks: Waymo and SimLingo/CarLLaVA code remains available for old
  reports and tests, but the friend-facing submission path is OODrive + CARLA +
  Alpamayo/RAG.
- Package manager: stdlib-first Python package; use editable install or
  `PYTHONPATH=src` during local development.

## Folder Structure

- `ARCHITECTURE.md`: top-level system map and canonical surface guide.
- `docs/`: canonical project state, PRD, specs, memory, history, taste, and troubles.
- `docs/specs/`: durable planning specs before tickets are created.
- `qa/`: reusable verification and evidence-capture guidance.
- `tickets/`: future ticket board and archived work.
- `scripts/`: repo-local validation, RunPod/Kasm setup, sync, and demo helpers.
- `src/driverx/`: implementation surface.
- `notebooks/`: analysis notebook placeholders.
- `data/`: local ignored data mount instructions, not checked-in dataset files.

## Conventions

- Keep the README focused on the current OODrive/CARLA/Alpamayo story.
- Archive old setup paths instead of leaving them in the primary reader flow.
- Keep model integrations behind narrow interfaces so cloud GPU, API-backed VLM,
  and mock backends can be swapped.
- Store large datasets, generated videos, submission archives, and model weights
  outside git unless a later ticket adds explicit artifact handling.
- Prefer deterministic trajectory generation and verification around stochastic
  model outputs.
- Public Python APIs should have typed signatures and explicit return types once
  implementation begins.

## Shared Utilities

- Preferred shared utility location: future `src/driverx/common/` for real
  multi-module reuse.
- Keep local when: helper logic belongs to one module, one notebook, or one
  experiment.
- Extract when: the same logic is needed by loader, evaluator, visualizer, and
  submission paths.

## Pre-Push Policy

- Warn on large tracked source files: 500 raw lines.
- Block on oversized tracked source files: 1000 raw lines.
- Required local commands:
  - Lint/syntax: `python3 -m compileall -q src tests`
  - Typecheck: not configured yet.
  - Tests: `PYTHONPATH=src python3 -m unittest discover -s tests`
  - Build: optional unless packaging/distribution is added.
- Optional heavy checks:
  - Desloppify: manual workflow only for v1.
  - CodeRabbit: manual workflow only for v1.

## Runtime / QA Commands

- Authoritative product quickstart:
  `PYTHONPATH=src python3 -m oodrive quickstart --prompt "wet roadwork scooter"`
- Authoritative QA / evidence run path:
  `bash scripts/pre_push_check.sh`
- Required local services: none for docs; future cloud GPU is optional for VLA
  inference and not required for local dataset parsing.
- Launch shape: local Python processes and notebooks first; optional remote
  inference server later.
- Expected local targets / base URLs: none yet.
- Port / env contract:
  - Future service ports must be configurable.
  - Future dataset paths must be controlled by environment variables or config,
    not hardcoded absolute paths.
- Source of truth note: CLI commands run through `python3 -m driverx` until an
  editable install is required.

## Agent QA / Testability

- Reusable QA runbooks live in `qa/cookbook/`.
- Preferred proof surfaces:
  - validation ADE table over a small local sample
  - rendered camera panels with ground-truth and predicted trajectories
  - latency breakdown table by pipeline stage
  - packaged submission dry-run
- Important future probes:
  - raw VLA structured output
  - pre-smooth trajectory
  - post-smooth trajectory
  - scoring/ranking rationale

## Quick Commands

```bash
# Run the product quickstart
PYTHONPATH=src python3 -m oodrive quickstart --prompt "wet roadwork scooter"

# Generate scenario candidates
PYTHONPATH=src python3 -m oodrive generate "wet roadwork scooter filtering"

# Run the old fixture pipeline support track
PYTHONPATH=src python3 -m driverx run-batch --config configs/mock.yaml

# Run tests
PYTHONPATH=src python3 -m unittest discover -s tests

# Exercise reasoner validation fallback
PYTHONPATH=src python3 -m driverx run-scene --config configs/invalid_reasoner.yaml --run-id invalid-smoke

# Run the local pre-push gate
bash scripts/pre_push_check.sh
```
