# TASK-148: M5 Scenario Ancestry Cards

## Status
- state: building
- phase: documenting
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-103, TASK-105, TASK-145
- location: `src/driverx/pipeline`, `src/driverx/scenarios`, `src/driverx/memory`, `tests`, `tickets/TASK-148`
- enter when: M5 Fail2Drive/reference grounding exists, but generated scenarios do not yet have simple ancestry cards that explain which rare-event family they belong to and which prior failure principle they test.
- leave when: OODrive writes scenario ancestry cards for key generated cases, linking prompt, OOD tags, benchmark/failure family, memory principle, evidence paths, and claim boundaries.
- blockers: no official Fail2Drive scoring required; this is reference grounding and presentation.
- spawned follow-ups: final judge packet can include ancestry cards as the M5 proof surface.
- complexity: S

### Summary

Make generated scenarios feel grounded rather than arbitrary. Each card should say: this generated case is a member of this rare-event/failure family, it stresses this behavior, it retrieves this memory principle, and here is the evidence status.

### Scope

- In scope: ancestry card builder, JSON/Markdown/HTML output, links to TASK-105 Fail2Drive extension report and TASK-145 ledger, tests.
- Out of scope: official Fail2Drive leaderboard runs, Waymo episode mining, new simulator captures.

### Gap Analysis

- Current state: TASK-105 links generated cases to Fail2Drive-like references and memory entries, but this is buried in reports.
- Production expectation: dataset/evaluation systems expose lineage: source/seed, mutation, labels, quality status, evidence path, and why the case matters.
- Missing gaps: no one-card-per-case story, no clear rare-event taxonomy for judges, no link from generated scenario to memory principle and artifact status.
- Recommended boundary: cards over existing generated cases and reference report first.

### Plan

#### Change

Add:

```bash
PYTHONPATH=src python3 -m oodrive ancestry-cards \
  --db artifacts/runs/task141-realistic-ood-generation-v1/scenario_studio_db.json \
  --fail2drive-report tickets/TASK-105/artifacts/fail2drive-extension-v1/fail2drive_extension_report.json \
  --retrieval-ledger artifacts/runs/task145-memory-ledger-v1/retrieval_ledger.json \
  --run-id task148-ancestry-cards-v1
```

#### Why

M5 should show that OODrive's randomization targets meaningful autonomy edge-case families, not just random objects.

#### Before -> After

- Before: generated scenario has tags and a memory query.
- After: generated scenario has a judge-readable ancestry card with rare-event family, prior failure principle, evidence status, and claim boundary.

#### Touch

- `src/driverx/pipeline/scenario_ancestry_cards.py` (new)
- `src/driverx/scenarios/studio_product_ancestry_runtime.py` (new)
- `src/driverx/scenarios/studio_product_cli.py`
- `tests/test_scenario_ancestry_cards.py` (new)
- `tests/test_oodrive_cli.py`

#### Inspect

- `src/driverx/pipeline/fail2drive_extension_report.py`
- `tests/test_fail2drive_extension_report.py`
- `artifacts/runs/task141-realistic-ood-generation-v1/scenario_studio_db.json`
- `tickets/TASK-105/artifacts/*`

#### Signature Delta

```python
src/driverx/pipeline/scenario_ancestry_cards.py / build_scenario_ancestry_cards(db_path, fail2drive_report_path=None, retrieval_ledger_paths=(), output_root, run_id, limit=8): dict
src/driverx/scenarios/studio_product_ancestry_runtime.py / run_studio_ancestry_cards(...): StudioCommandResult
```

#### Type Sketch

```python
ScenarioAncestryCard = {
  "scenario_id": str,
  "prompt_family": str,
  "ood_tags": list[str],
  "rare_event_family": str,
  "reference_source": "Fail2Drive-like fixture" | "generated-only",
  "memory_principle": str | None,
  "evidence_status": "proved" | "partial" | "blocked",
  "artifact_refs": list[str],
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example

`scenario_studio_db.json`
-> scenario candidate tags + expected failure mode
-> join TASK-105 reference family and TASK-145 memory principle
-> write `ScenarioAncestryCard[]`
-> HTML gallery shows static blocker, road hole, rolling object, compound detour.

#### Execution Steps

1. Implement family classifier from tags/expected failure text.
2. Join optional Fail2Drive extension report.
3. Join optional retrieval ledger selected principle.
4. Write JSON, Markdown, and HTML cards.
5. Add CLI command `oodrive ancestry-cards`.
6. Add tests for family mapping, missing reference report, and claim boundaries.

#### Recommendation

Ship cards for 4-8 strongest generated cases; do not chase Waymo episode descriptions for this deadline.

#### Options Considered

- Waymo mining: stronger external grounding but too much work now.
- Fail2Drive-only table: technical but not judge-friendly.
- Ancestry cards: fastest way to make M5 visible.

#### Blast Radius

- Additive report command.
- No runtime changes.

#### Risks

- Taxonomy can become hand-wavy. Mitigation: every card must link tags/expected failure text and evidence paths.

### Acceptance Criteria

- [x] At least four ancestry cards generated for the bad-path families.
- [x] Each card includes reference family, memory ids or explicit joined memory state, and artifact refs.
- [x] Output includes JSON/Markdown/HTML.
- [x] Tests cover reference-grounded card generation and claim boundaries.

### Verification

```bash
PYTHONPATH=src python3 -m unittest tests.test_scenario_ancestry_cards tests.test_fail2drive_extension_report tests.test_oodrive_cli
bash tickets/TASK-145/autoresearch-m4-m5/autoresearch.sh
```

### Evidence

- Planned cards: `artifacts/runs/task148-ancestry-cards-v1/scenario_ancestry_cards.json`
- Planned gallery: `artifacts/runs/task148-ancestry-cards-v1/index.html`
- 2026-05-08 08:33 +0800: Implemented `build_scenario_ancestry_cards`, additive `oodrive ancestry-cards`, and focused tests.
- 2026-05-08 08:33 +0800: Artifact generated: `artifacts/runs/task148-ancestry-cards-v1/scenario_ancestry_cards.json` with `card_count=8`.
- 2026-05-08 08:33 +0800: HTML gallery generated: `artifacts/runs/task148-ancestry-cards-v1/scenario_ancestry_cards.html`.
- 2026-05-08 08:33 +0800: Cards are grounded in `artifacts/runs/task141-realistic-ood-generation-v1/scenario_studio_db.json` and `tickets/TASK-105/artifacts/fail2drive-extension-report/fail2drive_extension_report.json`.
- 2026-05-08 08:33 +0800: Implementation review: `tickets/TASK-145/artifacts/review/task145-148-impl-review.json`.

### Blockers

- None for existing-artifact cards.
