# Archive

This folder keeps old project material out of the main reader path without
throwing away useful provenance.

## What Moved Here

- `legacy-readme-full.md`: the pre-cleanup README with the full historical
  command inventory and submission notes.
- `legacy-docs/bootstrap-brief.md`: first Waymo-oriented bootstrap brief.
- `legacy-docs/progress.md`: long historical progress ledger, superseded by
  `docs/HISTORY.md`, tickets, and current docs.
- `legacy-docs/submission-milestones.md`: older submission sprint ladder.
- `legacy-docs/test-audit.md`: old test audit notes.
- `legacy-docs/directory-structure-plan.md`: early directory plan.
- `legacy-docs/scenario-workbench-v2-plan.md`: older Scenario Workbench plan.

## Current Canonical Surfaces

- `README.md`
- `ARCHITECTURE.md`
- `PROJECT_RULES.md`
- `docs/prd.md`
- `docs/specs/README.md`
- `docs/submission-thesis.md`
- `docs/runpod-kasm-quickstart.md`
- `docs/MEMORY.md`
- `docs/HISTORY.md`

## Legacy Code Policy

SimLingo/CarLLaVA and Waymo support code remains in `src/driverx` because tests
still cover those adapters and reports. The friend-facing README now labels
them as support tracks rather than the main submission path.
