# TASK-151: CARLA Custom Asset Import Registry

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-150
- location: `src/driverx/assets`, `src/driverx/simulators`, `scripts`, `tests`, `tickets/TASK-151`
- enter when: OODrive can produce mesh artifacts, but CARLA still only receives stock proxy blueprint filters.
- leave when: OODrive can build an import/install plan, record a CARLA asset registry, probe a target CARLA installation for installed generated blueprints, and fall back honestly to stock proxies when custom import is not installed.
- blockers: actual Unreal package build requires a CARLA/Unreal-capable host; local tests use fixtures and blocked/probe modes.
- spawned follow-ups: TASK-153 uses the registry to spawn custom assets in live CARLA.
- complexity: L

### Summary

Bridge generated mesh files into CARLA without pretending the Python API can hot-import arbitrary GLBs at runtime. CARLA custom assets need an import/package/install step that produces spawnable blueprints or a precise blocker.

### Scope

- In scope: import plan schema, CARLA asset registry, blueprint-id resolver, target-install probe, install command wrapper, Kasm/CARLA run instructions, stock-proxy fallback with claim labels, and tests with fake CARLA blueprint libraries.
- Out of scope: rebuilding CARLA itself, checking in generated packages, hiding failed custom imports behind stock proxies, or requiring live CARLA for unit tests.

### Gap Analysis

- Current state: `map_asset_to_carla_spawn` maps semantic tags to installed stock proxies like `static.prop.foodcart`.
- Production expectation: generated assets are packaged or installed into the simulator, assigned blueprint ids, probed, and spawned by registry reference.
- Missing gaps: no import plan, no registry, no installed-blueprint probe, no package/install command, and no artifact separating generated mesh success from CARLA import success.
- Recommended boundary: plan and probe import/install locally; perform live packaging on Kasm/Unreal host when available.

### Plan

#### Change

Add:

```bash
PYTHONPATH=src python3 -m oodrive install-assets \
  --scenario-pack artifacts/runs/task150-assets/scenario_pack.assets.json \
  --mode plan \
  --run-id task151-import-plan

PYTHONPATH=src python3 -m oodrive probe-assets \
  --asset-registry artifacts/runs/task151-import-plan/carla_asset_registry.json \
  --config configs/carla_ood_demo.runpod.high_fidelity.yaml
```

#### Why

Researchers will not accept "prompt-to-3D inside CARLA" unless the generated asset has a simulator-installed identity. This ticket makes that identity explicit and testable.

#### Before -> After

- Before: a generated asset maps to a stock CARLA proxy blueprint.
- After: an asset maps first to a generated blueprint registry entry when installed, otherwise to a labeled fallback proxy.

#### Touch

- `src/driverx/assets/carla_import.py` (new)
- `src/driverx/assets/carla_registry.py` (new)
- `src/driverx/assets/carla_mapping.py`
- `src/driverx/assets/pipeline.py`
- `src/driverx/simulators/carla_asset_probe.py` (new)
- `src/driverx/scenarios/studio_product_cli.py`
- `src/oodrive/cli.py`
- `scripts/run_carla_asset_probe.py` (new, optional wrapper)
- `tests/test_carla_asset_import_registry.py` (new)
- `tests/test_carla_asset_mapping.py`
- `docs/HISTORY.md`

#### Inspect

- `src/driverx/assets/types.py`
- `src/driverx/assets/carla_mapping.py`
- `src/driverx/simulators/carla_ood_demo.py`
- `scripts/setup_runpod_carla_0916_graphics.sh`
- `docs/MEMORY.md` MEM-0021, MEM-0025, MEM-0042
- `tickets/TASK-141/ticket.md`
- `tickets/TASK-150/ticket.md`

#### Signature Delta

```python
build_carla_asset_import_plan(pack_path: Path, output_root: Path, run_id: str) -> dict[str, Any]
build_carla_asset_registry(import_plan: dict[str, Any], installed_blueprints: list[str] = ()) -> dict[str, Any]
resolve_carla_blueprint_for_asset(manifest: AssetManifest, registry: dict[str, Any] | None, available_blueprints: list[str]) -> CarlaBlueprintResolution
probe_carla_asset_registry(config_path: Path, registry_path: Path, carla_module: object | None = None) -> dict[str, Any]
```

#### Type Sketch

```python
CarlaAssetRegistryEntry = {
  "asset_id": str,
  "mesh_path": str,
  "expected_blueprint_id": str,
  "installed": bool,
  "fallback_blueprint": str,
  "import_status": "planned" | "installed" | "blocked",
  "claim_boundary": str,
}
```

#### Typed Flow Example

`asset-roadside-vendor` resolves as:

```json
{
  "expected_blueprint_id": "driverx.generated.asset_roadside_vendor",
  "installed": false,
  "fallback_blueprint": "static.prop.foodcart",
  "claim_boundary": "custom_asset_imported_in_carla=false; stock_proxy_fallback=true"
}
```

After a Kasm install/probe, `installed=true` and the spawn spec uses `driverx.generated.asset_roadside_vendor`.

#### Execution Steps

1. Define import-plan and registry schemas.
2. Build deterministic expected blueprint ids from asset ids.
3. Update mapping resolution to prefer installed registry entries and fall back to MEM-0021 stock proxies.
4. Add a CARLA blueprint probe that imports `carla` only inside the live edge.
5. Add CLI commands for `install-assets --mode plan` and `probe-assets`.
6. Add Kasm setup guidance in the generated report, including where package outputs should live and what remains blocked locally.
7. Add tests with fake blueprint libraries for installed, missing, wildcard, and fallback paths.

#### Recommendation

Do not promise runtime GLB hot-import. Treat CARLA custom asset support as a package/install/probe workflow with explicit registry evidence.

#### Options Considered

- Runtime mesh import from Python: rejected because CARLA spawning uses installed blueprints.
- Always use stock proxies: acceptable fallback, not production prompt-to-3D.
- Registry plus install/probe lane: recommended because it is honest and matches CARLA's installed-blueprint model.

#### Blast Radius

High around asset-to-CARLA mapping. Guard existing proxy behavior with tests.

#### Risks

- Unreal packaging may require a heavier host than the current Python client; the plan mode must still be useful and precise.
- Generated blueprint ids can drift from packaged asset names; registry probe must be authoritative.

### Acceptance Criteria

- [x] AC-1: Import plan and registry artifacts are written from a generated-asset scenario pack.
- [x] AC-2: Mapping prefers installed generated blueprints when the registry/probe says they exist.
- [x] AC-3: Missing custom blueprints fall back to stock proxies with explicit claim boundaries.
- [ ] AC-4: Live CARLA probe records available generated blueprints or a precise blocker.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_carla_asset_import_registry tests.test_carla_asset_mapping`
- `PYTHONPATH=src python3 -m oodrive install-assets --scenario-pack <pack> --mode plan --run-id task151-smoke`
- Optional Kasm proof: run `oodrive probe-assets` against a configured CARLA host and attach probe JSON.

### Autonomy Readiness

- Inputs: asset-generated scenario pack.
- Compute: local for plan/probe tests; Kasm/Unreal host for real package install.
- External services: none.
- Stop gates: do not rebuild CARLA or install packages into a shared host without explicit operator approval.

### Refs

- CARLA actor blueprint model: https://carla.readthedocs.io/en/latest/core_actors/
- CARLA custom prop authoring: https://carla.readthedocs.io/en/latest/content_authoring_props/

### Evidence

- Planning review: `tickets/TASK-149/artifacts/review/production-generator-plan-review.json`
- Implementation proof: `artifacts/runs/task151-production-registry-proof/carla_asset_registry.json`
- Current boundary: generated OBJ meshes exist, but installed generated CARLA blueprints are still `0`; live CARLA proof uses stock proxies.

### Blockers

- Real custom asset install proof needs a CARLA/Unreal-capable host.
- Generated CARLA blueprint packaging/import is not implemented yet; stock proxy fallback remains the honest simulator path.
