# Specs

Canonical product and implementation specs live here once ideas move past
exploration.

Top-level companion docs:

- `ARCHITECTURE.md` - top-level system map and canonical surface guide
- `README.md` - product story and setup
- `docs/prd.md` - product requirements

Current design docs:

- `minimal-shot-vla-roadmap.md` - TASK-008 through TASK-014 roadmap for CARLA,
  generated assets, regional driving behavior, policy adapters, and RAG
  comparison
- `scenario-generator-cli-v1.md` - OODrive prompt-to-scenario CLI contract
- `scenario-studio-data-engine.md` - TASK-103 product/data-engine design for
  prompt-authored OOD scenarios, curation gates, and Alpamayo/RAG handoff

Archived drafts now live under `docs/archive/legacy-docs/`.

Use this folder for:

- execution model specs
- API or data-contract specs
- architecture or workflow decisions that should survive chat history

## Doc Gardening Loop

When the public story changes:

1. Run the repo's structural validators.
2. Re-read `ARCHITECTURE.md`, `README.md`, and the changed specs.
3. Patch only the canonical surfaces that drifted.
4. Re-run the validators.
