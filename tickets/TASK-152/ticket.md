# TASK-152: Research Scenario Graph And OpenSCENARIO Export

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-149, TASK-151
- location: `src/driverx/scenarios`, `src/driverx/behaviors`, `src/driverx/assets`, `tests`, `tickets/TASK-152`
- enter when: OODrive has production packs and asset registry plans, but behavior/environment intent is still OODrive-specific and not exportable as a researcher-friendly scenario graph.
- leave when: scenario packs compile into an explicit scenario graph with actors, actions, triggers, map/weather constraints, asset references, assertions, and an OpenSCENARIO-compatible export where supported.
- blockers: full standards coverage is not required; unsupported OODrive-only fields must remain in a sidecar.
- spawned follow-ups: TASK-153 consumes the graph for live CARLA runs; TASK-155 exports datasets.
- complexity: L

### Summary

Make the generated scenario behave like a research scenario, not a one-off script. The graph should express what actors do, when objects appear, what the ego route is, what counts as success/failure, and how much can be exported into OpenSCENARIO/ScenarioRunner-compatible surfaces.

### Scope

- In scope: scenario graph type, compiler from production pack, OpenSCENARIO-ish XML export, OODrive sidecar for custom assets/RAG/claim fields, validation, tests, and reports.
- Out of scope: official ScenarioRunner execution, full ASAM OpenSCENARIO 2.0 coverage, live CARLA runs, and closed-loop VLA control.

### Gap Analysis

- Current state: behavior traces and placement plans exist, but they are not a unified actor/action/trigger graph.
- Production expectation: researchers can inspect and export scenario structure, compare it across simulators, and use ScenarioRunner/OpenSCENARIO-compatible parts when possible.
- Missing gaps: no graph contract, no trigger/assertion model, no standards export, no sidecar split for OODrive-only metadata.
- Recommended boundary: implement the graph and best-effort export, with explicit unsupported-field reporting.

### Plan

#### Change

Add:

```bash
PYTHONPATH=src python3 -m oodrive compile-scenario \
  --scenario-pack artifacts/runs/prod-pack/scenario_pack.json \
  --asset-registry artifacts/runs/task151-import-plan/carla_asset_registry.json \
  --run-id task152-scenario-graph
```

#### Why

Production researchers need semantics and repeatability, not just videos. A graph/export layer lets generated scenarios become shareable research artifacts.

#### Before -> After

- Before: OODrive knows behavior traces and object spawns, but no explicit action graph exists.
- After: OODrive writes `scenario_graph.json`, `scenario.unknown_coverage.xosc`, and `scenario_sidecar.json`.

#### Touch

- `src/driverx/scenarios/scenario_graph.py` (new)
- `src/driverx/scenarios/scenario_graph_export.py` (new)
- `src/driverx/scenarios/production_pack.py`
- `src/driverx/behaviors/types.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `src/oodrive/cli.py`
- `tests/test_scenario_graph_export.py` (new)
- `tests/test_oodrive_cli.py`
- `docs/HISTORY.md`

#### Inspect

- `src/driverx/behaviors/`
- `src/driverx/scenarios/generated_runtime.py`
- `src/driverx/scenarios/studio_runtime.py`
- `docs/specs/scenario-generator-cli-v1.md`
- `tickets/TASK-149/ticket.md`
- `tickets/TASK-151/ticket.md`

#### Signature Delta

```python
compile_scenario_graph(pack: dict[str, Any], asset_registry: dict[str, Any] | None = None) -> dict[str, Any]
validate_scenario_graph(graph: dict[str, Any]) -> ScenarioGraphValidation
export_open_scenario(graph: dict[str, Any], output_path: Path) -> dict[str, Any]
write_scenario_graph_bundle(graph: dict[str, Any], output_root: Path, run_id: str) -> dict[str, Any]
```

#### Type Sketch

```python
ScenarioGraph = {
  "actors": [{"actor_ref": str, "kind": str, "blueprint_ref": str}],
  "static_objects": [{"asset_id": str, "placement": dict, "blueprint_ref": str}],
  "actions": [{"actor_ref": str, "start_s": float, "end_s": float, "intent": str, "trajectory": list[dict]}],
  "triggers": [{"at_s": float, "condition": str}],
  "assertions": [{"name": str, "metric": str, "operator": str, "threshold": float}],
  "sidecar_refs": {"asset_registry": str | None, "oodrive_metadata": str},
}
```

#### Typed Flow Example

The motorcycle behavior trace becomes a graph actor plus action:

```json
{
  "actor_ref": "generated_behavior_actor_0",
  "intent": "motorcycle_filtering",
  "start_s": 0.0,
  "end_s": 12.0,
  "trajectory": [{"t_s": 0.0, "x_m": 0.0, "y_m": -1.2}]
}
```

The export writes the trajectory when representable and records RAG/claim-boundary metadata in the sidecar.

#### Execution Steps

1. Define the graph schema as plain dictionaries/dataclasses with validators.
2. Compile actors, objects, weather, map constraints, actions, triggers, and assertions from the production pack.
3. Add asset-registry awareness so objects refer to generated blueprints when installed.
4. Implement conservative OpenSCENARIO XML export for actors, storyboard skeleton, route/trajectory entries, and environment fields.
5. Write unsupported OODrive fields into a sidecar and list them in the report.
6. Register CLI and tests for graph validation, XML presence, sidecar coverage, and unsupported-field reporting.

#### Recommendation

Export OpenSCENARIO as a compatibility view, not the canonical OODrive source. The OODrive graph should preserve research metadata that standards exports cannot carry cleanly.

#### Options Considered

- Keep only OODrive JSON: easiest, but less useful for researchers.
- Make OpenSCENARIO the canonical schema: standards-aligned, but loses custom asset provenance and OODrive evidence state.
- OODrive graph plus standards export: recommended for fidelity and interoperability.

#### Blast Radius

Moderate. This introduces a new scenario representation but should not change current runtime behavior until TASK-153 consumes it.

#### Risks

- Overstating standards compatibility; mitigate with `export_coverage` and sidecar unsupported-field lists.
- XML fragility; keep export minimal and covered by snapshot-like tests.

### Acceptance Criteria

- [x] AC-1: `oodrive compile-scenario` writes graph JSON, Markdown report, OpenSCENARIO XML, and sidecar JSON.
- [x] AC-2: Validation catches missing actors, missing route/action timing, invalid object blueprint refs, and absent assertions.
- [x] AC-3: Export coverage lists supported and sidecar-only fields.
- [x] AC-4: No live CARLA dependency in tests.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_scenario_graph_export tests.test_oodrive_cli`
- `PYTHONPATH=src python3 -m oodrive compile-scenario --scenario-pack <pack> --asset-registry <registry> --run-id task152-smoke`
- Inspect `scenario_graph.json`, `.xosc`, `scenario_sidecar.json`, and report.

### Autonomy Readiness

- Inputs: production scenario pack and optional asset registry.
- Compute: local only.
- External services: none.
- Stop gates: none.

### Refs

- CARLA ScenarioRunner/OpenSCENARIO docs: https://scenario-runner.readthedocs.io/en/latest/openscenario_support/
- ASAM OpenSCENARIO standard overview: https://www.asam.net/standards/detail/openscenario/

### Evidence

- Planning review: `tickets/TASK-149/artifacts/review/production-generator-plan-review.json`
- Implementation proof: `artifacts/runs/task152-production-graph-proof/scenario_graph.json`
- OpenSCENARIO proof: `artifacts/runs/task152-production-graph-proof/scenario_graph.xosc`
- Tests: `PYTHONPATH=src python3 -m unittest tests.test_production_scenario_generator tests.test_generated_carla_runtime tests.test_oodrive_cli`

### Blockers

- None.
