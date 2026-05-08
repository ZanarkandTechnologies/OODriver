# TASK-149: Production Scenario Pack Contract

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-141
- location: `src/driverx/scenarios`, `src/driverx/assets`, `src/oodrive`, `tests`, `tickets/TASK-149`
- enter when: TASK-141 proves prompt-generated behaviors and stock-proxy object spawns in live CARLA, but there is no production-grade scenario pack contract that researchers can inspect, edit, rerun, and trust.
- leave when: OODrive writes one typed scenario pack that captures prompt, scenario graph, generated asset requests, behavior timelines, CARLA placement constraints, evidence requirements, claim boundaries, and next commands.
- blockers: none for local contract work; later live CARLA proof remains owned by TASK-153.
- spawned follow-ups: TASK-150, TASK-151, TASK-152, TASK-153, TASK-154, TASK-155, TASK-156
- complexity: M

### Summary

Make the production scenario generator explicit before adding more runtime machinery. A researcher should be able to run one command from a prompt and get a durable pack that says what will appear in CARLA, which assets still need generation/import, which vehicles will behave how, which map/route/weather constraints apply, and what proof is required before promotion.

### Scope

- In scope: scenario-pack schema, loader/writer, validation, CLI command, Markdown report, test fixtures, and migration from TASK-141 runtime specs into the new pack shape.
- Out of scope: generating real mesh files, installing Unreal/CARLA packages, live simulation execution, and workbench UI.

### Gap Analysis

- Current state: `oodrive generate-run` emits a runtime manifest with behavior cases, dry-run asset manifests, and CARLA stock-proxy spawn specs.
- Production expectation: a scenario pack is a stable research artifact with explicit scenario intent, editable constraints, asset provenance, behavior schedule, simulator assumptions, evidence requirements, and export hooks.
- Missing gaps: no first-class pack type, no schema version, no claim-boundary gate for custom assets versus stock proxies, no asset-import readiness state, and no one-file input for later runner/workbench/export commands.
- Recommended boundary: build the pack contract now and keep execution in later tickets.

### Plan

#### Change

Add a product command:

```bash
PYTHONPATH=src python3 -m oodrive scenario-pack \
  "wet Malaysian roadwork with scooter filtering around debris and a roadside vendor" \
  --behavior-id motorcycle_filtering \
  --object-kind construction_debris \
  --object-kind roadside_vendor \
  --seed 41 \
  --run-id prod-pack-wet-roadwork
```

#### Why

The current system has proof surfaces, but they are not a researcher-facing contract. The pack becomes the handoff object for prompt-to-assets, prompt-to-CARLA, replay, scoring, and export.

#### Before -> After

- Before: runtime data is split across generated-runtime specs, placement plans, DB rows, and reports.
- After: one `scenario_pack.json` captures the scenario graph and points to derived runtime artifacts without overclaiming live execution.

#### Touch

- `src/driverx/scenarios/production_pack.py` (new)
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/scenarios/studio_product_generated_runtime.py`
- `src/oodrive/cli.py`
- `tests/test_production_scenario_pack.py` (new)
- `tests/test_oodrive_cli.py`
- `docs/HISTORY.md`
- `tickets/TASK-149/ticket.md`

#### Inspect

- `src/driverx/scenarios/generated_runtime.py`
- `src/driverx/scenarios/studio_runtime.py`
- `src/driverx/assets/types.py`
- `src/driverx/assets/carla_mapping.py`
- `docs/specs/scenario-generator-cli-v1.md`
- `tickets/TASK-141/ticket.md`
- `docs/MEMORY.md`
- `docs/TROUBLES.md`

#### Signature Delta

```python
build_production_scenario_pack(
    prompt: str,
    *,
    behavior_ids: tuple[str, ...],
    object_kinds: tuple[str, ...],
    seed: int,
    severity: int,
    output_root: Path,
    run_id: str,
) -> dict[str, Any]

load_production_scenario_pack(path: Path) -> dict[str, Any]
validate_production_scenario_pack(pack: dict[str, Any]) -> ScenarioPackValidation
run_studio_scenario_pack(...) -> StudioCommandResult
```

#### Type Sketch

```python
ProductionScenarioPack = {
  "schema_version": "oodrive.scenario_pack.v1",
  "scenario_id": str,
  "source_prompt": str,
  "seed": int,
  "map_constraints": {"town": str | None, "road_features": list[str]},
  "weather": dict[str, float | str],
  "asset_requests": list[AssetRequestJson],
  "asset_readiness": {"stock_proxy": bool, "custom_mesh": bool, "carla_import": bool},
  "behavior_timelines": list[BehaviorTimelineJson],
  "placement_constraints": list[RoadLocalPlacementJson],
  "evidence_requirements": list[str],
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example

Prompt `wet roadwork scooter and food cart` compiles to a pack with one motorcycle timeline, two asset requests, road-local placement constraints, and claim boundaries:

```json
{
  "asset_readiness": {
    "stock_proxy": true,
    "custom_mesh": false,
    "carla_import": false
  },
  "evidence_requirements": [
    "custom_asset_generation_manifest",
    "carla_live_spawn_manifest",
    "mp4_or_rgb_frames"
  ]
}
```

#### Execution Steps

1. Define the scenario pack schema and validation result dataclasses in a focused module.
2. Adapt `build_generated_scenario_runtime_spec` output into the pack builder instead of duplicating behavior/object selection logic.
3. Add a Markdown report with the exact next commands for asset generation, import/install, live run, score, and export.
4. Register `oodrive scenario-pack` and compatibility aliases.
5. Add fixtures and tests covering valid packs, missing prompt, missing behavior, missing asset readiness, and claim-boundary text.
6. Update docs/history with the new production planning surface.

#### Recommendation

Use a versioned OODrive JSON pack as the authoritative source of truth, with OpenSCENARIO export added later in TASK-152. This keeps local tests dependency-light while still giving researchers a durable artifact.

#### Options Considered

- Reuse TASK-141 generated-runtime JSON only: fastest, but it mixes runtime proof with authoring intent.
- Make OpenSCENARIO the only contract now: standards-friendly, but CARLA custom assets and OODrive evidence state do not map cleanly on day one.
- Add OODrive pack first, export standards later: recommended because it preserves all research metadata and lets later tickets emit standards-compatible views.

#### Blast Radius

Touches CLI registration, tests, and scenario-generation packaging only. Existing `oodrive generate-run` behavior should stay compatible.

#### Risks

- Pack/schema drift from existing runtime specs; mitigate with adapter tests from a TASK-141 fixture.
- Over-broad schema; keep fields tied to required downstream tickets and validation.

### Acceptance Criteria

- [x] AC-1: `oodrive scenario-pack` writes `scenario_pack.json` and `.md` from a prompt with selected behaviors/assets.
- [x] AC-2: Validation fails fast for missing prompt, no behaviors, no asset requests, or absent claim boundaries.
- [x] AC-3: The pack distinguishes stock-proxy readiness from custom-mesh and CARLA-import readiness.
- [x] AC-4: Existing generated-runtime flow can reference or derive from the pack without breaking TASK-141 tests.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_production_scenario_pack tests.test_oodrive_cli`
- `PYTHONPATH=src python3 -m oodrive scenario-pack "wet roadwork scooter filtering" --object-kind construction_debris --behavior-id motorcycle_filtering --run-id task149-smoke`
- Inspect `artifacts/runs/task149-smoke/scenario_pack.json` for claim boundaries and evidence requirements.

### Autonomy Readiness

- Inputs: prompt, seed, built-in object/behavior ids.
- Compute: local only.
- External services: none.
- Stop gates: none unless schema contradicts an existing runtime contract.

### Refs

- CARLA custom prop authoring: https://carla.readthedocs.io/en/latest/content_authoring_props/
- CARLA actor blueprint model: https://carla.readthedocs.io/en/latest/core_actors/
- OODrive CLI spec: `docs/specs/scenario-generator-cli-v1.md`

### Evidence

- Planning review: `tickets/TASK-149/artifacts/review/production-generator-plan-review.json`
- Implementation proof: `artifacts/runs/task149-production-pack-proof/scenario_pack.json`
- Tests: `PYTHONPATH=src python3 -m unittest tests.test_production_scenario_generator tests.test_generated_carla_runtime tests.test_oodrive_cli`

### Blockers

- None.
