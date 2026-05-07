# TASK-126: OODrive Prompt-To-CARLA Placement Path

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-125
- location: `src/driverx/scenarios`, `src/oodrive`, `tests`, `docs`
- enter when: `oodrive ai-generate` exists but the product lacks `oodrive generate <scenario>` and a concrete CARLA placement plan
- leave when: `oodrive generate <describe scenario>` writes a Studio DB, queued candidate, CARLA placement plan, and next command that can place the objects in CARLA
- blockers: none for local dry-run placement planning
- spawned follow-ups: TASK-127
- complexity: M

### Summary

Build the missing product bridge from an English OOD prompt to explicit CARLA
objects and actor behavior. This ticket does not claim live CARLA execution; it
must create a runnable placement plan that names the stock CARLA blueprint
filters, road-local transforms, dynamic behavior trace, and next command.

### Scope

- In scope: `oodrive generate`, prompt positional UX, candidate selection,
  dry-run asset-to-CARLA mapping, placement JSON/Markdown artifacts, DB
  artifact indexing, next-command handoff.
- Out of scope: live CARLA spawning and Alpamayo inference, handled by
  TASK-127.

### Plan

#### Change

Add a high-level product command:

```bash
PYTHONPATH=src python3 -m oodrive generate \
  "Malaysian wet roadwork with a motorbike filtering around cones"
```

It should run the existing deterministic AI generator, compile and queue a
candidate, then materialize a CARLA placement plan from the chosen candidate.

#### Why

The submission needs to demonstrate the new contribution as a simulator product,
not a pile of internal scripts. The judge-facing primitive is: describe an
edge case, get a concrete scenario to place in CARLA.

#### Before -> After

- Before: user must know `ai-generate`, `compile`, `queue`, asset mapping, and
  CARLA demo internals.
- After: user runs `oodrive generate <prompt>` and gets a DB plus
  `carla_placement_plan.json` that lists spawnable CARLA objects and behavior.

#### Touch

- `src/driverx/scenarios/studio_runtime.py`
- `src/driverx/scenarios/studio_product.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `tests/test_oodrive_cli.py`
- `README.md`, `docs/HISTORY.md`

#### Inspect

- `src/driverx/scenarios/studio_product.py`
- `src/driverx/scenarios/studio_product_helpers.py`
- `src/driverx/simulators/carla_ood_demo.py`
- `src/driverx/assets/*`
- `src/driverx/behaviors/*`

#### Signature Delta

```python
build_studio_placement_plan(
    db_path: Path,
    *,
    scenario_id: str | None,
    config_path: Path,
    output_root: Path | None,
    run_id: str | None,
) -> dict[str, Any]

run_studio_generate(
    *,
    prompt: str,
    db_path: Path | None,
    output_root: Path,
    run_id: str,
    count: int,
    seed: int,
    severity: int,
    accept: str,
    config_path: Path,
    force: bool,
) -> StudioCommandResult
```

#### Type Sketch

```python
CarlaPlacementPlan = {
  "placement_id": str,
  "scenario_id": str,
  "candidate_id": str,
  "recipe": dict,
  "behavior_plan": dict,
  "behavior_metrics": dict,
  "asset_manifests": list[dict],
  "object_spawn_specs": list[dict],
  "carla_plan": dict,
  "next_commands": list[str],
}
```

#### Typed Flow Example

`oodrive generate "wet KL roadwork scooter filtering" --run-id kl-chaos`
-> generated DB brief
-> compiled candidate with `asset_requests`
-> dry-run `AssetManifest`s
-> stock CARLA spawn specs such as `static.prop.foodcart`,
`vehicle.kawasaki.ninja`
-> `carla_placement_plan.json`
-> next command: `oodrive place --db ... --placement ... --live`.

#### Execution Steps

1. Add runtime helpers that reconstruct `ScenarioRecipe`, `BehaviorPlan`, and
   dry-run `AssetManifest`s from a DB candidate.
2. Write placement JSON/Markdown artifacts with explicit CARLA transforms.
3. Add `run_studio_generate` to orchestrate AI generation, compile, queue, and
   placement-plan writing.
4. Add product CLI parser and tests for positional prompt UX.
5. Update docs and evidence.

### Acceptance Criteria

- [x] AC-1: `oodrive generate <description>` creates/updates a Studio DB.
- [x] AC-2: The generated result writes `carla_placement_plan.json` and `.md`.
- [x] AC-3: Placement plan includes at least one `object_spawn_specs` entry with
  blueprint filter and road-local transform.
- [x] AC-4: Next commands point to `oodrive place` and `oodrive reason`.

### Verification

- Focused unit tests for `oodrive generate`.
- CLI smoke with a Malaysian OOD prompt.
- `bash scripts/pre_push_check.sh`.

### Evidence

- QA report: `tickets/TASK-126/artifacts/qa/generate-placement-qa.md`.
- Review: `docs/reviews/TASK-126-127-oodrive-product-loop-review.md`.
- Smoke DB: `artifacts/runs/oodrive-generate-place-smoke-v2/scenario_studio_db.json`.
- Placement plan:
  `artifacts/runs/oodrive-generate-place-smoke-v2/placements/oodrive-generate-place-smoke-v2-placement/carla_placement_plan.json`.
- Tests: `PYTHONPATH=src python3 -m unittest tests.test_oodrive_cli`.
- Full gate: `bash scripts/pre_push_check.sh`.

### Blockers

- None.
