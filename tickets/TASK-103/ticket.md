# TASK-103: AI Scenario Studio Prompt-To-OOD DSL

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-090, TASK-091, TASK-092, TASK-101
- location: `src/driverx/scenarios`, `src/driverx/environments`, `src/driverx/behaviors`, `src/driverx/pipeline`, `configs`, `tickets/TASK-103/artifacts`
- enter when: core deterministic scenario/environment/behavior generators exist and the submission needs an "AI generates edge cases" surface
- leave when: natural-language scenario briefs compile into validated DriverX scenario recipes and batch artifacts without requiring a live LLM
- blockers: optional LLM API key only for provider-backed generation; deterministic compiler path has no blocker
- spawned follow-ups: TASK-102, TASK-104
- complexity: M
- assignee: generalPurpose

### Summary

Build the scenario-generation contribution judges can understand: a small
Scenario Studio where prompts like "Malaysian motorbike filtering through wet
construction traffic" compile into environment packs, behavior DSL variants,
stock CARLA proxy assets, memory queries, and quality-gate expectations.

Planning update: Scenario Studio is the sprint's product contribution. It
should behave like a small autonomy data engine, not a thin prompt-to-config
helper. The durable design target is captured in
`docs/specs/scenario-studio-data-engine.md`.

### Scope

- In scope: prompt schema, deterministic prompt parser, optional provider hook,
  scenario studio batch CLI, validation, curation scoring, dataset-candidate
  records, markdown report, and examples for Malaysian driving, roadwork,
  occlusion, sudden braking, roadside market, and irrelevant visual noise.
- Out of scope: fine-tuning, Meshy GLB generation, arbitrary free-form CARLA map
  editing, and guaranteeing every prompt is solvable.

### Plan

#### Change

Add `driverx.scenario_studio` or a scenario-owned module that turns compact
natural-language briefs into existing `ScenarioRecipe`, `EnvironmentRecipe`,
and `BehaviorPlan` objects, then scores whether each generated case is worth
keeping as a dataset/evaluation point.

#### Why

The challenge rewards randomized scenario generation. The repo already has
deterministic generators; this ticket makes the generation interface legible and
agentic without betting the deadline on custom assets.

#### Before -> After

- Before: generation is powerful but code/config driven.
- After: a judge can read a prompt, see the compiled scenario recipe, and watch
  the selected generated case run through quality/model evidence.
- After: the batch also explains whether each generated data point is accepted,
  partial, rejected, blocked, or queued for CARLA/Alpamayo work.

#### Touch

- `src/driverx/scenarios/studio.py`: prompt compiler and batch planner.
- `src/driverx/scenarios/studio_cli.py`: CLI command registration.
- `src/driverx/scenarios/types.py`: only if a new studio-specific record earns
  a type.
- `src/driverx/environments/library.py`: reuse existing environment families.
- `src/driverx/behaviors/library.py`: reuse existing behavior variants.
- `configs/scenario_studio.sample.yaml`: prompt batch examples.
- Tests: `tests/test_scenario_studio.py`, CLI coverage.

#### Inspect

- `src/driverx/scenarios/generator.py`
- `src/driverx/scenarios/catalog.py`
- `src/driverx/environments/library.py`
- `src/driverx/behaviors/dsl.py`
- `src/driverx/behaviors/validators.py`
- `src/driverx/assets/pipeline.py`

#### Signature Delta

```python
compile_scenario_prompt(prompt: str, *, seed: int, catalog: StudioCatalog | None = None): ScenarioStudioPlan

expand_studio_plan(plan: ScenarioStudioPlan, *, count: int, random_seed: int): list[ScenarioStudioCandidate]

score_studio_candidate(candidate: ScenarioStudioCandidate, existing_records: list[ScenarioCatalogRecord]): DatasetCurationRecord

generate_studio_batch(config: ScenarioStudioConfig): dict[str, Any]

validate_studio_plan(plan: ScenarioStudioPlan): StudioValidationReport
```

#### Type Sketch

```python
ScenarioStudioPlan = {
  "prompt": str,
  "brief_id": str,
  "scenario_id": str,
  "environment_family": str,
  "environment_template_id": str,
  "behavior_id": str,
  "asset_tags": list[str],
  "ood_tags": list[str],
  "memory_query": list[str],
  "expected_failure_mode": str,
  "safe_behavior_principle": str,
  "compiled_recipe": ScenarioRecipe,
  "quality_targets": {
    "min_duration_s": float,
    "require_conflict": bool,
    "require_road_alignment": bool,
  },
  "provider": "deterministic" | "llm",
}

ScenarioStudioCandidate = {
  "candidate_id": str,
  "plan_id": str,
  "variant_index": int,
  "random_seed": int,
  "compiled_recipe": ScenarioRecipe,
  "environment_recipe": EnvironmentRecipe,
  "behavior_plan": BehaviorPlan,
  "asset_requests": list[dict],
}

DatasetCurationRecord = {
  "candidate_id": str,
  "curation_status": "accept" | "accept_partial" | "needs_rerun" | "reject_duplicate" | "reject_invalid" | "blocked_runtime",
  "score": float,
  "gate_results": dict[str, bool | str | float | None],
  "evidence_paths": dict[str, str | None],
  "why_keep": str,
  "next_action": str,
}
```

#### Typed Flow Example

Prompt:
`"Malaysian wet roadwork: motorbike filters between cars while a lorry brakes without signal"`

-> `environment_template_id="construction_lane_closure"`
-> `behavior_id="motorcycle_filtering"`
-> `asset_tags=["road_cones", "debris", "lorry_proxy"]`
-> `memory_query=["motorcycle_filtering", "sudden_brake", "wet_roadwork"]`
-> `ScenarioRecipe(...)`
-> `DatasetCurationRecord(next_action="run high-fidelity CARLA and Alpamayo+memory")`
-> batch handoff to TASK-102/TASK-104/TASK-105.

#### Execution Steps

1. Define studio plan dataclasses and JSON serialization.
2. Implement deterministic keyword/rule compiler over existing environment and
   behavior libraries.
3. Add optional provider interface but default it to disabled.
4. Expand plans into deterministic concrete candidates using existing
   environment and behavior variant generators.
5. Add curation scoring for validity, OOD pressure, novelty, solvability,
   evidence readiness, and model-evaluation value.
6. Add validation for unknown behavior/environment tags and unsolvable prompts.
7. Add CLI: `python -m driverx generate-scenario-studio --config ...`.
8. Add sample prompts and tests.
9. Produce a batch of 20 scenario candidates and a Markdown gallery.

#### Recommendation

Implement deterministic studio first. Optional LLM generation is useful polish,
but the submission needs reliable reproducibility more than novelty theater.

#### Options Considered

- Full LLM scenario generation: attractive, but introduces API/key/flakiness
  risk.
- Pure code/config generation: reliable, but undersells the "agent-generated
  edge cases" contribution.
- Recommended: deterministic prompt compiler with optional provider seam.
- Full self-running active-learning loop: best long-term product, but too much
  for the final sprint. This ticket should emit the curation queue that a later
  loop could execute.

#### Blast Radius

Low to medium. Adds a user-facing generation layer on top of existing modules;
should not mutate lower-level generator contracts unless necessary.

#### Risks

- Overclaiming "AI generated" if provider is deterministic. Mitigate by calling
  it "Scenario Studio prompt compiler" unless a live LLM provider is used.

### Gap Analysis

The repo currently generates scenarios, environments, and behaviors, but the
interface is not demo-friendly. A production-grade stress-test environment needs
scenario authoring that is understandable to a non-code judge. This ticket
creates that bridge while preserving deterministic reproducibility.

Parity research shows the credible shape is a data flywheel: author intent,
expand parameterized cases, run or plan simulation, quality-gate evidence,
curate useful data points, evaluate model behavior, and feed failures back into
memory. See `docs/specs/scenario-studio-data-engine.md`.

### Acceptance Criteria

- [ ] AC-1: At least 10 natural-language briefs compile into valid studio
  plans.
- [ ] AC-2: Compiled plans include behavior, environment, assets, memory query,
  expected failure, and quality targets.
- [ ] AC-3: Unknown/unsupported prompts fail with actionable validation errors.
- [ ] AC-4: Studio batch writes JSON/Markdown suitable for the final browser.
- [ ] AC-5: Each generated candidate has a curation status, score, gate
  results, and `next_action` for TASK-102/TASK-104/TASK-105.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_scenario_studio`
- CLI smoke over `configs/scenario_studio.sample.yaml`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Inputs available: no API key required for deterministic path.
- Human gates: optional LLM provider key only if user wants live LLM generation.
- Compute: local only.
- Stop condition: prompt batch compiled and validated.

### Evidence

- `docs/specs/scenario-studio-data-engine.md`
- `tickets/TASK-103/artifacts/review/task103-scenario-studio-plan-review.json`
- `tickets/TASK-103/artifacts/scenario_studio_batch.json`
- `tickets/TASK-103/artifacts/scenario_studio_gallery.md`
- validation report and tests

### Blockers

- None for deterministic studio.
