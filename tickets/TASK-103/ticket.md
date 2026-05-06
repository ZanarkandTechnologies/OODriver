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

### Scope

- In scope: prompt schema, deterministic prompt parser, optional provider hook,
  scenario studio batch CLI, validation, markdown report, and examples for
  Malaysian driving, roadwork, occlusion, sudden braking, roadside market, and
  irrelevant visual noise.
- Out of scope: fine-tuning, Meshy GLB generation, arbitrary free-form CARLA map
  editing, and guaranteeing every prompt is solvable.

### Plan

#### Change

Add `driverx.scenario_studio` or a scenario-owned module that turns compact
natural-language briefs into existing `ScenarioRecipe`, `EnvironmentVariant`,
and `BehaviorPlan` objects.

#### Why

The challenge rewards randomized scenario generation. The repo already has
deterministic generators; this ticket makes the generation interface legible and
agentic without betting the deadline on custom assets.

#### Before -> After

- Before: generation is powerful but code/config driven.
- After: a judge can read a prompt, see the compiled scenario recipe, and watch
  the selected generated case run through quality/model evidence.

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

generate_studio_batch(config: ScenarioStudioConfig): dict[str, Any]

validate_studio_plan(plan: ScenarioStudioPlan): StudioValidationReport
```

#### Type Sketch

```python
ScenarioStudioPlan = {
  "prompt": str,
  "scenario_id": str,
  "environment_family": str,
  "behavior_id": str,
  "asset_tags": list[str],
  "ood_tags": list[str],
  "memory_query": str,
  "expected_failure_mode": str,
  "compiled_recipe": ScenarioRecipe,
  "quality_targets": {
    "min_duration_s": float,
    "require_conflict": bool,
    "require_road_alignment": bool,
  },
  "provider": "deterministic" | "llm",
}
```

#### Typed Flow Example

Prompt:
`"Malaysian wet roadwork: motorbike filters between cars while a lorry brakes without signal"`

-> `environment_family="monsoon_roadwork"`
-> `behavior_id="motorcycle_filtering"`
-> `asset_tags=["road_cones", "debris", "lorry_proxy"]`
-> `memory_query="motorcycle filtering sudden brake wet roadwork"`
-> `ScenarioRecipe(...)`
-> batch handoff to TASK-102/TASK-104.

#### Execution Steps

1. Define studio plan dataclasses and JSON serialization.
2. Implement deterministic keyword/rule compiler over existing environment and
   behavior libraries.
3. Add optional provider interface but default it to disabled.
4. Add validation for unknown behavior/environment tags and unsolvable prompts.
5. Add CLI: `python -m driverx generate-scenario-studio --config ...`.
6. Add sample prompts and tests.
7. Produce a batch of 20 scenario plans and a Markdown gallery.

#### Recommendation

Implement deterministic studio first. Optional LLM generation is useful polish,
but the submission needs reliable reproducibility more than novelty theater.

#### Options Considered

- Full LLM scenario generation: attractive, but introduces API/key/flakiness
  risk.
- Pure code/config generation: reliable, but undersells the "agent-generated
  edge cases" contribution.
- Recommended: deterministic prompt compiler with optional provider seam.

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

### Acceptance Criteria

- [ ] AC-1: At least 10 natural-language briefs compile into valid studio
  plans.
- [ ] AC-2: Compiled plans include behavior, environment, assets, memory query,
  expected failure, and quality targets.
- [ ] AC-3: Unknown/unsupported prompts fail with actionable validation errors.
- [ ] AC-4: Studio batch writes JSON/Markdown suitable for the final browser.

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

- `tickets/TASK-103/artifacts/scenario_studio_batch.json`
- `tickets/TASK-103/artifacts/scenario_studio_gallery.md`
- validation report and tests

### Blockers

- None for deterministic studio.
