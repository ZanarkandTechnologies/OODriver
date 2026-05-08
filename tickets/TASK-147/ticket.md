# TASK-147: Decongested Reasoning Evidence Panel

## Status
- state: building
- phase: documenting
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-145, TASK-146, TASK-131
- location: `src/driverx/simulators/reasoning_timeline_overlay.py`, `src/driverx/pipeline/reasoning_overlay_video.py`, `src/driverx/pipeline`, `tests`, `tickets/TASK-147`
- enter when: the score-gated hero video contains enough RAG/reasoning events, but the HUD is too congested for a human judge to parse quickly.
- leave when: OODrive can render a decongested evidence mode: minimal video HUD plus synchronized chapter cards/HTML panel showing hazard, retrieval principle, Alpamayo diff, action intent, and claim boundary.
- blockers: uses existing video and artifacts; no fresh CARLA or Alpamayo required.
- spawned follow-ups: TASK-144/TASK-148 final packet can link the clearer evidence surface.
- complexity: M

### Summary

Improve reasoning legibility without adding simulator work. Keep the video HUD sparse and move detailed reasoning into chapter cards / HTML evidence panels. The in-video overlay should show at most the current hazard, one retrieved principle, and one action/diff line.

### Scope

- In scope: overlay layout mode, chapter/event schema, HTML evidence panel, report manifest, scorer/metric fields for congestion, tests.
- Out of scope: new frontend app, live browser sync, new model inference, new video footage.

### Gap Analysis

- Current state: [src/driverx/simulators/reasoning_timeline_overlay.py](/Users/kenjipcx/SOTA/0xDriver/src/driverx/simulators/reasoning_timeline_overlay.py) draws a single right-side panel with frame/time, risk, RAG memory, VLA reasoning, action, and claim text.
- Production expectation: RAG/reasoning observability tools expose traces and intermediate steps separately instead of forcing every detail into a HUD. Judges need glanceable video plus inspectable trace.
- Missing gaps: no compact HUD mode, no chapter cards, no congestion metric, no source citations in panel, no separation between immediate driving cue and detailed evidence.
- Recommended boundary: add `--layout compact` / `--evidence-panel` output and keep full trace in HTML/Markdown.

### Plan

#### Change

Add a compact reasoning presentation path:

```bash
PYTHONPATH=src python3 -m oodrive demo-video \
  ... \
  --layout compact \
  --evidence-panel \
  --run-id task147-compact-reasoning-v1
```

If `demo-video` is too broad, add a focused wrapper:

```bash
PYTHONPATH=src python3 -m oodrive evidence-panel \
  --overlay-report artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/hero_demo_video.json \
  --reasoning-diff artifacts/runs/task146-reasoning-diff-v1/alpamayo_reasoning_diff.json \
  --retrieval-ledger artifacts/runs/task145-memory-ledger-v1/retrieval_ledger.json \
  --run-id task147-evidence-panel-v1
```

#### Why

The current overlay can pass a mechanical score while still feeling unreadable. The fix is not more text; it is better information hierarchy.

#### Before -> After

- Before: one crowded HUD tries to show every proof surface.
- After: video shows one short state at a time; HTML/Markdown gives the full evidence trace with citations and reasoning diffs.

#### Touch

- `src/driverx/simulators/reasoning_timeline_overlay.py`
- `src/driverx/pipeline/reasoning_overlay_video.py`
- `src/driverx/pipeline/reasoning_evidence_panel.py` (new)
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/evaluation/hero_demo_score.py` or new `reasoning_presentation_score.py`
- `tests/test_reasoning_timeline_overlay.py`
- `tests/test_reasoning_evidence_panel.py` (new)

#### Inspect

- `src/driverx/scenarios/studio_product_runtime.py` (`run_studio_demo_video`)
- `artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/hero_demo_video.json`
- `tickets/TASK-111/artifacts/reasoning-overlay-v1/reasoning_overlay_video.md`

#### Signature Delta

```python
src/driverx/simulators/reasoning_timeline_overlay.py / ReasoningOverlayConfig(layout: Literal["dense", "compact"] = "dense")
src/driverx/simulators/reasoning_timeline_overlay.py / render_reasoning_overlay_frame(..., layout="dense"): None
src/driverx/pipeline/reasoning_evidence_panel.py / build_reasoning_evidence_panel(overlay_report, reasoning_diff, retrieval_ledgers, output_root, run_id): dict
```

#### Type Sketch

```python
ReasoningChapter = {
  "chapter_id": str,
  "start_s": float,
  "hazard": str,
  "retrieved_principle": str,
  "reasoning_delta": str,
  "action_intent": str,
  "source_refs": list[str],
}

ReasoningPresentationReport = {
  "layout": "compact",
  "max_hud_rows": int,
  "chapter_count": int,
  "citation_count": int,
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example

`hero_demo_video.json + retrieval_ledger.json + alpamayo_reasoning_diff.json`
-> `ReasoningChapter[]`
-> compact overlay frames use `hazard/principle/action`
-> HTML panel renders full chapter cards with source refs
-> presentation score reads `max_hud_rows <= 3`, `chapter_count >= 4`, `citation_count >= 3`.

#### Execution Steps

1. Add compact layout branch to overlay renderer.
2. Add chapter-card builder from existing overlay events and TASK-145/146 artifacts.
3. Write HTML/Markdown panel.
4. Add congestion/presentation metrics to output report.
5. Add tests for row cap, chapter count, citation presence, and claim labels.
6. Render a compact derivative from existing TASK-131 source evidence.

#### Recommendation

Keep the dense overlay as a debug mode; make compact mode the judge-facing default.

#### Options Considered

- Bigger HUD: worse readability.
- Separate slide deck only: loses video connection.
- Sparse video + evidence panel: best judge comprehension.

#### Blast Radius

- Overlay renderer changes risk existing hero-demo tests.
- Default can stay dense until compact artifact passes; then docs can promote compact.

#### Risks

- Compact video may under-count RAG/reasoning events in old scorer. Mitigation: report still records events; score from artifact, not visual text density.

### Acceptance Criteria

- [x] Compact layout limits HUD to at most three content rows plus claim label.
- [x] Evidence panel includes at least four chapters and source/citation refs.
- [x] Existing dense overlay tests still pass.
- [x] Generated evidence panel keeps required claim boundaries.

### Verification

```bash
PYTHONPATH=src python3 -m unittest tests.test_reasoning_timeline_overlay tests.test_reasoning_evidence_panel tests.test_hero_demo_score tests.test_oodrive_cli
bash tickets/TASK-145/autoresearch-m4-m5/autoresearch.sh
```

### Evidence

- Planned compact overlay report: `artifacts/runs/task147-compact-reasoning-v1/hero_demo_video.json`
- Planned evidence panel: `artifacts/runs/task147-evidence-panel-v1/index.html`
- 2026-05-08 08:33 +0800: Implemented compact overlay layout branch plus `build_reasoning_evidence_panel` and additive `oodrive evidence-panel`.
- 2026-05-08 08:33 +0800: Artifact generated: `artifacts/runs/task147-evidence-panel-v1/reasoning_presentation_report.json` with `chapter_count=4`, `max_hud_rows=3`, `citation_count=7`.
- 2026-05-08 08:33 +0800: HTML evidence panel generated: `artifacts/runs/task147-evidence-panel-v1/reasoning_presentation_report.html`.
- 2026-05-08 08:33 +0800: Implementation review: `tickets/TASK-145/artifacts/review/task145-148-impl-review.json`.

### Blockers

- None for existing-artifact rendering.
