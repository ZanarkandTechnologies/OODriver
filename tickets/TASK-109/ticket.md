# TASK-109: Agentic OOD Scenario Generation Loop

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-103, TASK-108
- location: `src/driverx/scenarios`, `src/driverx/workbench`, `tickets/TASK-109/artifacts`
- enter when: Scenario Studio can compile prompts but does not yet demonstrate an autonomous dataset-growth loop
- leave when: an agentic loop generates, novelty-scores, rejects/keeps, and queues OOD scenarios with clear curation lineage
- blockers: optional LLM provider remains out of scope; deterministic agent loop must work locally
- spawned follow-ups: TASK-110, TASK-113
- complexity: M

### Summary

Make Scenario Studio feel like a novel simulator/data engine instead of a
static prompt list. This ticket adds an autonomous loop that proposes OOD
scenario briefs, compiles them, scores novelty and pressure, rejects weak or
duplicate cases, and writes a dataset curation queue.

### Scope

- In scope: deterministic OOD brief generator, novelty/pressure scorer,
  duplicate rejection, curation queue, seedable batch command, and gallery.
- Out of scope: live LLM calls, Meshy assets, CARLA execution, model inference.

### Plan

#### Change

Add an "agentic" generation layer above the existing deterministic compiler.

#### Why

The contribution becomes much clearer if the demo shows a loop generating new
chaotic cases and deciding which are worth running.

#### Before -> After

- Before: `generate-scenario-studio` consumes a fixed prompt config.
- After: `run-ood-generation-loop` produces new briefs from seed themes,
  compiles candidates, scores novelty, and creates a dataset queue.

#### Touch

- Add `src/driverx/scenarios/agentic_loop.py`
- Extend `src/driverx/scenarios/studio.py` only where reuse hooks are missing
- Add CLI in `src/driverx/scenarios/agentic_loop_cli.py`
- Register CLI in `src/driverx/cli_extensions.py`
- Add tests in `tests/test_agentic_ood_generation_loop.py`

#### Inspect

- `src/driverx/scenarios/studio.py`
- `src/driverx/scenarios/catalog.py`
- `src/driverx/environments/library.py`
- `src/driverx/behaviors/library.py`

#### Signature Delta

```python
generate_ood_briefs(seed_themes: list[str], count: int, random_seed: int) -> list[ScenarioBrief]
score_ood_novelty(candidate: ScenarioStudioCandidate, prior: list[ScenarioCatalogRecord]) -> OodNoveltyScore
run_agentic_ood_generation_loop(config: AgenticOodLoopConfig) -> dict[str, Any]
```

#### Type Sketch

```python
OodNoveltyScore = {
  "score": float,
  "novel_tags": list[str],
  "duplicate_tags": list[str],
  "pressure_score": float,
  "reason": str,
}

GeneratedDatasetQueue = {
  "accepted": list[ScenarioStudioCandidate],
  "rejected": list[DatasetCurationRecord],
  "next_runtime_targets": list[{"candidate_id": str, "why": str}],
}
```

#### Typed Flow Example

`["Malaysian road chaos", "flooded market street"] + count=20`
-> generated briefs
-> Studio plans/candidates
-> novelty score
-> `accepted_candidate_ids`
-> `dataset_curation_queue.md`.

#### Execution Steps

1. Define seed theme templates for region, environment, behavior, object, and
   risk mechanism.
2. Generate deterministic natural-language briefs with traceable random seeds.
3. Compile each brief through `compile_scenario_prompt`.
4. Expand each valid plan into candidates.
5. Score novelty against catalog/batch records and reject duplicates.
6. Write `agentic_ood_generation_loop.json`, `dataset_curation_queue.md`, and
   `scenario_brief_gallery.html`.

#### Recommendation

Keep the "agent" deterministic for the deadline. The demo can honestly say the
loop is provider-ready while remaining reproducible.

#### Options Considered

- Add live LLM generation now: more magical, but creates API/secrets risk.
- Keep fixed prompts: stable, but does not show the autonomous flywheel.
- Recommended: deterministic agentic generator with optional provider seam later.

#### Blast Radius

Low. Additive scenario module and CLI; no CARLA dependency.

#### Risks

- Generated prompts may feel templated. Mitigation: include multiple risk axes
  and a gallery that shows why each case is OOD.

### Gap Analysis

The current Scenario Studio compiler is a solid backend primitive. The missing
piece is the visible autonomous loop: generate, score, curate, and queue more
cases. This ticket turns it into a product contribution.

### Acceptance Criteria

- [x] AC-1: Command generates at least 20 candidate briefs from seed themes.
- [x] AC-2: Each candidate has novelty/pressure scoring and keep/reject rationale.
- [x] AC-3: Duplicate or weak candidates are rejected with actionable reasons.
- [x] AC-4: Queue identifies which candidates should run in CARLA next.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_agentic_ood_generation_loop`
- `PYTHONPATH=src python3 -m driverx run-ood-generation-loop --run-id task109-agentic-loop`
- JSON validation over generated queue.
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Inputs: existing fixture seeds and optional catalog.
- Compute: local only.
- Human gates: none.

### Evidence

- Built: `tickets/TASK-109/artifacts/agentic-ood-loop-v1/agentic_ood_generation_loop.json`
- Built: `tickets/TASK-109/artifacts/agentic-ood-loop-v1/dataset_curation_queue.md`
- Built: `tickets/TASK-109/artifacts/agentic-ood-loop-v1/scenario_brief_gallery.html`

### Blockers

- None.
