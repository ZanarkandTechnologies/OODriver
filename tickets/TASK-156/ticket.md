# TASK-156: Production Generator Score And Autoresearch Loop

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-149, TASK-150, TASK-151, TASK-152, TASK-153, TASK-154, TASK-155
- location: `src/driverx/evaluation`, `src/driverx/scenarios`, `src/oodrive`, `tests`, `tickets/TASK-156`
- enter when: the production scenario-generator ticket train exists, but there is no single mechanical score that optimizes toward researcher-grade prompt-to-CARLA utility.
- leave when: OODrive exposes `score-research-generator`, the nested autoresearch session can run it, and the metric rewards real prompt-to-asset-to-CARLA evidence while penalizing proxies, missing imports, bad videos, weak curation, and overclaims.
- blockers: final high scores depend on upstream tickets; baseline scoring can run against current TASK-141 evidence.
- spawned follow-ups: autoresearch-exec can run once one or more implementation tickets land.
- complexity: M

### Summary

Create the metric spine for the full production generator. The score should make it mechanically obvious whether OODrive is becoming useful to researchers: prompt fidelity, generated assets, CARLA import/spawn proof, behavior realism, evidence quality, reproducibility, workbench usability, and export completeness.

### Scope

- In scope: metric design, scorer command, fixtures, nested autoresearch session, guard checks, thresholds, and reports.
- Out of scope: optimizing the score in this planning pass, live CARLA runs, or replacing the existing SoTA submission readiness metric.

### Gap Analysis

- Current state: `submission_readiness_score`, `hero_demo_score`, and generator-runtime scoring serve challenge/demo goals.
- Production expectation: a researcher-grade generator score should reward actual prompt-to-scenario-pack-to-asset-to-CARLA-to-library utility and punish stock-proxy-only overclaims.
- Missing gaps: no composite metric across custom assets, CARLA import, live spawn, video quality, curation, export, and claim honesty.
- Recommended boundary: add a scorer and autoresearch contract now; use upstream ticket evidence to move it later.

### Plan

#### Change

Add:

```bash
PYTHONPATH=src python3 -m oodrive score-research-generator \
  --scenario-pack <pack> \
  --asset-manifest <asset_generation_manifest> \
  --asset-registry <carla_asset_registry> \
  --scenario-graph <scenario_graph> \
  --run-manifest <run_manifest> \
  --workbench <workbench_summary> \
  --library <scenario_library.json> \
  --metric-only
```

The nested session under `tickets/TASK-156/autoresearch-production-generator/` runs the current baseline safely without overwriting root `autoresearch.*`.

#### Why

Without a score, the project will drift toward nice-looking videos or JSON count inflation. The metric keeps us aimed at real researcher usefulness.

#### Before -> After

- Before: generator runtime score proves parts of TASK-141 but not production research utility.
- After: `research_scenario_generator_score` gives a 0-100 higher-is-better signal with component breakdown and strict claim-boundary penalties.

#### Touch

- `src/driverx/evaluation/research_scenario_generator_score.py` (new)
- `src/driverx/scenarios/studio_product_cli.py`
- `src/oodrive/cli.py`
- `tests/test_research_scenario_generator_score.py` (new)
- `tests/test_oodrive_cli.py`
- `tickets/TASK-156/autoresearch-production-generator/`
- `docs/HISTORY.md`

#### Inspect

- `src/driverx/evaluation/submission_readiness_score.py`
- `src/driverx/evaluation/hero_demo_score.py`
- `src/driverx/scenarios/studio_product_generated_runtime.py`
- `tickets/TASK-141/ticket.md`
- `tickets/TASK-149/ticket.md` through `tickets/TASK-155/ticket.md`
- root `autoresearch.md` and `autoresearch.jsonl`

#### Signature Delta

```python
score_research_scenario_generator(inputs: ResearchGeneratorScoreInputs) -> dict[str, Any]
run_studio_score_research_generator(...) -> StudioCommandResult

ResearchGeneratorScoreInputs = {
  "scenario_pack_path": Path | None,
  "asset_manifest_paths": tuple[Path, ...],
  "asset_registry_path": Path | None,
  "scenario_graph_path": Path | None,
  "run_manifest_paths": tuple[Path, ...],
  "workbench_summary_path": Path | None,
  "library_path": Path | None,
}
```

#### Type Sketch

```python
ResearchGeneratorScore = {
  "metric_name": "research_scenario_generator_score",
  "score": float,
  "components": {
    "scenario_contract": float,
    "asset_generation": float,
    "carla_asset_import": float,
    "live_carla_execution": float,
    "behavior_realism": float,
    "evidence_quality": float,
    "researcher_usability": float,
    "export_reproducibility": float,
    "claim_honesty": float,
  },
  "blockers": list[str],
  "recommendations": list[str],
}
```

#### Typed Flow Example

Current TASK-141 evidence earns live-CARLA and behavior credit but little/no custom-asset-import or workbench/export credit. After TASK-150/TASK-151/TASK-153, the same metric should rise only if generated assets actually become installed/spawned or honestly fall back with lower points.

#### Execution Steps

1. Define component weights and hard penalties for overclaiming custom assets, closed-loop VLA, or media availability.
2. Implement scorer loading optional artifacts independently so partial baselines are valid.
3. Add CLI with `--metric-only`.
4. Add fixture tests for current-proxy baseline, full target fixture, overclaim penalty, and missing artifact blockers.
5. Create and validate the nested autoresearch session.
6. Document target thresholds: `>=85` production-research useful, `>=95` flagship proof.

#### Recommendation

Use one composite score with transparent components and blockers. Keep `submission_readiness_score` for challenge packaging, but use this metric for production generator quality.

#### Options Considered

- Reuse `submission_readiness_score`: too challenge-specific.
- Use only live CARLA video score: misses asset generation, export, and workbench usability.
- Composite research-generator score: recommended because it matches the actual product goal.

#### Blast Radius

Moderate but additive. It reads artifacts and registers a new score command.

#### Risks

- Metric can reward artifact-count gaming; include claim-honesty penalties and validation blockers.
- Some components depend on upstream tickets; partial scoring must stay explicit.

### Acceptance Criteria

- [x] AC-1: `oodrive score-research-generator --metric-only` emits `METRIC research_scenario_generator_score=<number>`.
- [x] AC-2: Score components distinguish custom generated assets, CARLA custom import, stock-proxy fallback, live spawn proof, workbench usability, and library export.
- [x] AC-3: Overclaims lower score or block promotion.
- [x] AC-4: Nested autoresearch session runs without overwriting root `autoresearch.*`.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_research_scenario_generator_score tests.test_oodrive_cli`
- `bash tickets/TASK-156/autoresearch-production-generator/autoresearch.sh`
- `bash tickets/TASK-156/autoresearch-production-generator/autoresearch.checks.sh`

### Autonomy Readiness

- Inputs: optional artifact paths.
- Compute: local for scorer and autoresearch baseline.
- External services: none.
- Stop gates: autoresearch-plan only; do not execute iterative experiments until requested through `autoresearch-exec`.

### Refs

- Root session preserved: `autoresearch.md`
- Production ticket train: TASK-149 through TASK-155

### Evidence

- Nested autoresearch baseline: `tickets/TASK-156/autoresearch-production-generator/autoresearch.md`
- Planning review: `tickets/TASK-149/artifacts/review/production-generator-plan-review.json`
- Current scored proof: `artifacts/runs/task156-production-score-with-live-workbench-library-imageqa/research_scenario_generator_score.json`
- Current metric: `research_scenario_generator_score=92.0`, `status=partial`, capped by prompt-image QA.
- Autoresearch verify: `tickets/TASK-156/autoresearch-production-generator/baseline_score.json`
- Implementation review: `tickets/TASK-156/artifacts/review/production-generator-implementation-review.json`

### Blockers

- Flagship score is capped by partial prompt-image QA and stock-proxy-only CARLA asset import.
