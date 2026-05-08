# TASK-154: Researcher Scenario Workbench

## Status
- state: building
- owner: Codex
- assignee: frontend-designer
- dependencies: TASK-149, TASK-153
- location: `src/driverx/workbench`, `src/driverx/pipeline`, `src/driverx/scenarios`, `tests`, `tickets/TASK-154`
- enter when: scenario packs and live/fake run artifacts exist, but researchers still have to read raw JSON and shell output to inspect, edit, curate, and rerun scenarios.
- leave when: OODrive can generate a local researcher workbench that lets users inspect prompt, assets, graph, CARLA run evidence, video/keyframes, metrics, claim boundaries, and curation decisions from one artifact.
- blockers: no web server or cloud deployment required; UI proof uses generated local HTML and screenshot/visual QA.
- spawned follow-ups: TASK-155 exports accepted workbench cases into datasets.
- complexity: L

### Summary

Build the usable researcher surface. It should not be a landing page: first screen should be the scenario cockpit with prompt, asset readiness, CARLA evidence, metrics, and curation controls/report links.

### Scope

- In scope: static/local workbench generator, scenario/run detail pages, asset cards with thumbnails/proxy/import status, video/keyframe panel, graph/timeline panel, metrics panel, curation decision file, visual QA, and tests.
- Out of scope: hosted multi-user app, database migrations, live editing server, and billing/auth.

### Gap Analysis

- Current state: reports and HTML packs exist for submission, but not a researcher workflow for scenario generation.
- Production expectation: researchers can inspect what was generated, see whether assets truly appeared in CARLA, compare runs, accept/reject cases, and rerun exact commands.
- Missing gaps: no workbench index, no asset readiness view, no graph timeline, no run evidence status, no curation sidecar, no visual proof gate for the product workflow.
- Recommended boundary: static artifact workbench first, generated from packs/runs, with curation JSON persisted.

### Plan

#### Change

Add:

```bash
PYTHONPATH=src python3 -m oodrive workbench \
  --scenario-pack artifacts/runs/prod-pack/scenario_pack.json \
  --run-manifest artifacts/runs/task153-live-generated-scenario/run_manifest.json \
  --score-report artifacts/runs/task156-score/research_scenario_generator_score.json \
  --run-id task154-workbench
```

#### Why

Researchers will use the generator only if they can quickly judge whether a prompt produced a meaningful simulator case and whether the evidence is honest.

#### Before -> After

- Before: useful artifacts exist but require hunting across directories.
- After: one local HTML workbench makes generation, assets, simulator evidence, scoring, and curation visible.

#### Touch

- `src/driverx/workbench/scenario_workbench.py` (new)
- `src/driverx/workbench/README.md` and `AGENTS.md` if absent
- `src/driverx/pipeline/html_helpers.py` or local helpers if existing
- `src/driverx/scenarios/studio_product_cli.py`
- `src/oodrive/cli.py`
- `tests/test_scenario_workbench.py` (new)
- `tests/test_oodrive_cli.py`
- `tickets/TASK-154/artifacts/visual-qa/`
- `docs/HISTORY.md`

#### Inspect

- `src/driverx/pipeline/submission_scenario_browser.py`
- `src/driverx/pipeline/environment_demo_pack.py`
- `src/driverx/pipeline/reasoning_video_pack.py`
- `src/driverx/workbench/` if present
- `tickets/TASK-135/ticket.md`
- `tickets/TASK-141/ticket.md`
- `tickets/TASK-153/ticket.md`
- `docs/TASTE.md`

#### Signature Delta

```python
build_research_scenario_workbench(
    *,
    scenario_pack_path: Path,
    run_manifest_paths: tuple[Path, ...],
    score_report_paths: tuple[Path, ...],
    output_root: Path,
    run_id: str,
) -> dict[str, Any]

write_curation_decision(workbench_dir: Path, scenario_id: str, decision: str, notes: str) -> dict[str, Any]
run_studio_workbench(...) -> StudioCommandResult
```

#### Type Sketch

```python
WorkbenchScenarioCard = {
  "scenario_id": str,
  "prompt": str,
  "asset_status": {"generated": int, "custom_imported": int, "stock_proxy": int},
  "run_status": str,
  "video_path": str | None,
  "score": float | None,
  "claim_boundaries": list[str],
  "next_commands": list[str],
}
```

#### Typed Flow Example

The TASK-153 run becomes a card showing `custom_imported=0`, `stock_proxy=2`, a video path, score `research_scenario_generator_score=...`, and curation default `needs_review`.

#### Execution Steps

1. Reuse existing HTML/report helpers and create a focused workbench module.
2. Build a scenario overview with asset readiness, run evidence, metric status, claim boundaries, and exact rerun commands.
3. Add detail sections for asset cards, behavior timeline, graph summary, video/keyframes, and artifacts.
4. Persist curation decisions as JSON/Markdown sidecars without mutating source runs.
5. Register `oodrive workbench`.
6. Add tests for generated HTML content, missing optional video, curation output, and CLI registration.
7. Run visual QA screenshots for desktop/mobile layouts.

#### Recommendation

Generate a static local workbench first. A hosted app can follow after researchers are already getting useful artifacts.

#### Options Considered

- Raw reports only: too hard to use.
- Full web app now: more work and deployment overhead before the data contract stabilizes.
- Static workbench: recommended because it is usable, shareable, and easy to verify.

#### Blast Radius

Mostly additive. UI artifacts are generated under ignored run directories.

#### Risks

- UI can become a submission page instead of a tool; keep first screen dense and operational.
- Visual proof can be skipped; require screenshot/visual QA evidence before completion.

### Acceptance Criteria

- [x] AC-1: `oodrive workbench` writes a local HTML workbench plus JSON summary.
- [x] AC-2: Workbench exposes prompt, assets, graph/timeline, live/fake run evidence, metrics, claim boundaries, and next commands.
- [x] AC-3: Curation decision artifact can mark scenarios accepted/rejected/needs-review.
- [ ] AC-4: Visual QA proves desktop and mobile do not overlap text or hide core status.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_scenario_workbench tests.test_oodrive_cli`
- Generate a workbench from a fake or live TASK-153 run.
- Visual QA screenshot pass with generated artifact links in the ticket.

### Autonomy Readiness

- Inputs: scenario pack, run manifest, optional score reports/videos.
- Compute: local only.
- External services: none.
- Stop gates: visual QA is required because this is UI-bearing work.

### Refs

- Existing scenario browser: `src/driverx/pipeline/submission_scenario_browser.py`
- Taste rules: `docs/TASTE.md`

### Evidence

- Planning review: `tickets/TASK-149/artifacts/review/production-generator-plan-review.json`
- Implementation proof: `artifacts/runs/task154-production-workbench-proof/scenario_workbench.html`
- Summary proof: `artifacts/runs/task154-production-workbench-proof/workbench_summary.json`

### Blockers

- Browser visual-QA screenshots are still pending for the static workbench; no UI promotion claim is made yet.
