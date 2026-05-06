# TASK-090: Scenario Studio Catalog And Management CLI

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-007, TASK-085, TASK-089
- location: `src/driverx/scenarios`, `src/driverx/pipeline`, `src/driverx/cli.py`, docs, `tickets/TASK-090/artifacts`
- enter when: DriverX can generate recipes and campaign artifacts but has no durable scenario catalog for managing, filtering, promoting, or rerunning them
- leave when: generated scenarios and evidence can be indexed, searched, selected, promoted, and summarized from one CLI surface
- blockers: none
- spawned follow-ups: TASK-095 submission browser consumes the catalog
- complexity: M

### Summary

Turn scenario generation from one-off artifact folders into a small "scenario
studio" management layer. The submission needs to show that we can generate and
curate many OOD cases, not only run whichever case happened to be first.

### Scope

- In scope: scenario catalog records, artifact indexing, filtering, promotion
  status, run/evidence links, CLI commands, and Markdown/JSON reports.
- Out of scope: web UI, live CARLA execution, new behavior generation, or model
  inference.

### Gap Analysis

- Current state: generated recipes, campaign summaries, and Alpamayo reports
  live in artifact directories with no shared index.
- Production expectation: a tester should ask "show me construction + motorbike
  cases that passed road alignment and have video + reasoning evidence" and get
  a deterministic answer.
- Missing gaps: catalog schema, ingestion from existing outputs, quality status,
  scenario promotion, and rerun manifests.
- Recommendation: build a CLI-first catalog now, then render it as a static
  browser in TASK-095.

### Plan

#### Change

Add `driverx.scenarios.catalog` plus CLI commands for indexing, listing,
selecting, and promoting scenarios.

#### Why

The core contribution is a generator/evaluation harness. A harness needs
management primitives so the judging story is "we can produce a suite," not
"we have a folder of videos."

#### Before -> After

- Before: scenario evidence is discoverable only by knowing artifact paths.
- After: scenario evidence is discoverable by tags, quality, video status,
  model evidence status, behavior family, and promotion decision.

#### Touch

- `src/driverx/scenarios/catalog.py`: new catalog model and indexer.
- `src/driverx/scenarios/reports.py`: catalog Markdown renderer.
- `src/driverx/pipeline/scripted_ood_campaign.py`: emit catalog-compatible case
  records.
- `src/driverx/cli.py`: add `index-scenarios`, `list-scenarios`,
  `promote-scenario`, `export-scenario-selection`.
- `tests/test_scenario_catalog.py`.
- `README.md`, `ARCHITECTURE.md`, `docs/progress.md`.

#### Inspect

- `src/driverx/scenarios/types.py`
- `src/driverx/scenarios/reports.py`
- `src/driverx/pipeline/scripted_ood_campaign.py`
- `tickets/TASK-085/artifacts/task85-live-campaign-2b/scripted_ood_campaign_summary.json`
- `tickets/TASK-086/artifacts/task86-plan-cache/alpamayo_ood_batch_summary.json`

#### Signature Delta

```python
load_scenario_catalog(path: Path) -> ScenarioCatalog
index_scenario_artifacts(artifact_roots: list[Path]) -> ScenarioCatalog
filter_catalog(catalog: ScenarioCatalog, query: ScenarioQuery) -> list[ScenarioCatalogRecord]
promote_scenario(catalog: ScenarioCatalog, scenario_id: str, decision: PromotionDecision) -> ScenarioCatalog
write_scenario_catalog_outputs(catalog: ScenarioCatalog, output_dir: Path) -> dict[str, Path]
```

#### Type Sketch

```python
ScenarioCatalogRecord = {
  "scenario_id": str,
  "recipe_id": str | None,
  "family": str,
  "behavior_id": str | None,
  "environment_tags": list[str],
  "ood_tags": list[str],
  "quality": {"road_aligned": bool | None, "has_conflict": bool | None, "has_video": bool, "has_model_reasoning": bool},
  "artifacts": {"video": str | None, "tracks": str | None, "reasoning": str | None, "quality_report": str | None},
  "promotion": {"status": "candidate" | "hero" | "failure_case" | "rejected", "reason": str | None},
}
```

#### Typed Flow Example

`tickets/TASK-085/artifacts + tickets/TASK-086/artifacts`
-> `index-scenarios`
-> `artifacts/scenario-catalog/scenario_catalog.json`
-> `list-scenarios --tag construction --requires-video`
-> `export-scenario-selection --status hero`.

#### Execution Steps

1. Define catalog schema and strict JSON loading/writing.
2. Add indexers for existing campaign summary, video evidence, Alpamayo batch
   comparison, and future road-alignment reports.
3. Add CLI commands with text tables and Markdown output.
4. Add deterministic fixture tests.
5. Use the catalog to mark old off-road videos as rejected/failed evidence once
   TASK-089 quality reports exist.

#### Recommendation

Keep this CLI-first. A web UI is tempting, but a searchable JSON/Markdown
catalog gives us real management value immediately and feeds a later browser.

#### Options Considered

- Build a frontend first: higher polish, too much surface before the data model.
- Keep artifact folders only: not enough for "generate lots of scenarios."
- Build catalog-first: best; it creates the backbone for generator, policy, and
  demo selection.

#### Blast Radius

- Low to moderate: new read-only indexing layer plus optional campaign emit
  field additions.

#### Risks

- Existing artifact schemas are inconsistent; indexers must tolerate missing
  files and classify partial evidence instead of crashing.

### Acceptance Criteria

- [x] AC-1: Catalog can index at least the latest scripted campaign and
  Alpamayo comparison artifacts.
- [x] AC-2: CLI can list scenarios by tag, behavior, quality status, and
  evidence availability.
- [x] AC-3: CLI can promote/reject scenarios and write a durable selection
  manifest.
- [x] AC-4: Catalog report distinguishes hero candidates, failure cases,
  rejected evidence, and blocked/partial runs.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_scenario_catalog`
- `PYTHONPATH=src python3 -m driverx index-scenarios --artifact-root tickets/TASK-085/artifacts --artifact-root tickets/TASK-086/artifacts --run-id task90-catalog`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Fully local and independent of CARLA/GPU.
- If artifact schemas are missing fields, create tolerant adapters and continue.

### Evidence

- Planned 2026-05-06 as the first scenario-management layer after road-frame
  correction.
- Plan review: `docs/reviews/TASK-089-095-impl-plan-review.md`.
- Implemented `driverx.scenarios.catalog` and CLI commands
  `index-scenarios`, `list-scenarios`, `promote-scenario`, and
  `export-scenario-selection`.
- Focused tests passed:
  `PYTHONPATH=src python3 -m unittest tests.test_scenario_catalog tests.test_scripted_ood_campaign tests.test_cli`.
- Generated catalog evidence:
  `tickets/TASK-090/artifacts/scenario-catalog-v4/scenario_catalog.md`.

### Blockers

- None.
