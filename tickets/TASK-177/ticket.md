# TASK-177: CARLA Custom Asset Packaging And Blueprint Probe

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-170
- location: `src/driverx/assets`, `src/driverx/simulators`, `scripts`, `tests`
- enter when: TASK-170 can create Meshy/custom asset manifests, but OODrive still lacks a concrete packaging/probe lane for CARLA blueprint registration.
- leave when: OODrive can turn an ingested/generated mesh manifest into a CARLA asset import/package plan, probe installed blueprint ids, and prove or block live spawning with exact evidence.
- blockers: Unreal/CARLA packaging may require source build tooling and manual editor/cook steps.
- spawned follow-ups: custom asset gallery refresh after first live registered blueprint spawn.
- complexity: L
- assignee: generalPurpose

### Description
Move custom assets from “manifest exists” to “CARLA blueprint can be probed/spawned or the exact packaging gap is known.” This complements TASK-170 by focusing on CARLA registration and live spawn proof.

### Goal
Make custom objects such as cranes real CARLA spawn targets, not just stock proxy substitutions.

### Integration Decision
Do not implement a new asset runtime inside OODrive. CARLA spawns registered blueprints. Meshy or local generators can create mesh assets, but OODrive's job is packaging/probing: prove the mesh became a registered CARLA blueprint, or use a labeled stock proxy fallback.

### Plan

#### Change
Add asset packaging plans, live blueprint probes, and custom asset spawn proof commands.

#### Why
The gap is not mesh creation alone. The product is only honest when a generated object can be resolved to a CARLA blueprint and spawned visibly.

#### Before -> After
- Before: TASK-170 requests/generated asset manifests and plans fallback.
- After: TASK-177 proves whether the asset is registered/spawnable in CARLA or records the exact packaging blocker.

#### Touch
- `src/driverx/assets/carla_packaging.py` new package/probe/spawn contract.
- `src/driverx/scenarios/studio_product_asset_cli.py` new CLI registration.
- `src/driverx/scenarios/studio_product_asset_runtime.py` new runtime wrapper.
- `src/driverx/scenarios/studio_product_cli.py` register commands.
- `src/driverx/evaluation/custom_asset_spawn_score.py` optional score.
- `tests/test_custom_asset_packaging.py` new tests.
- `tests/test_oodrive_cli.py` command registration.

#### Inspect
- `src/driverx/assets/pipeline.py`
- `src/driverx/assets/types.py`
- `src/driverx/assets/carla_registry.py`
- `src/driverx/simulators/carla_control.py`
- `tickets/TASK-170/ticket.md`

#### Signature Delta
- `build_asset_package_plan(asset_manifest: dict, output_dir: Path) -> AssetPackagePlan`
- `probe_asset_blueprint(blueprint_id: str, carla_client: object | None, output_dir: Path) -> BlueprintProbeResult`
- `spawn_custom_asset(blueprint_id: str, transform: dict, output_dir: Path, carla_client: object | None) -> CustomAssetSpawnProof`

#### Type Sketch
```python
CustomAssetSpawnProof = {
  "blueprint_id": str,
  "blueprint_registered": bool,
  "spawned_actor_id": int | None,
  "screenshot_path": str | None,
  "stock_proxy_fallback": bool,
  "claim_boundaries": ["arbitrary_mesh_spawn=false|true"],
}
```

#### Typed Flow Example
Meshy crane manifest -> package plan lists Unreal/CARLA import steps -> blueprint probe searches `static.prop.oodrive_crane` -> if found, spawn and capture frame -> if missing, use `static.prop.dirtdebris01` fallback and record `arbitrary_mesh_spawn=false`.

#### Execution Steps
1. Add asset package plan writer with expected source/build/package paths.
2. Add blueprint probe using CARLA blueprint library when live; local mode emits blocker.
3. Add spawn proof command with screenshot/capture and cleanup ids.
4. Add score/claim guard requiring package + probe + spawn for arbitrary mesh claims.
5. Add tests for missing blueprint, stock proxy fallback, and overclaim prevention.

#### Recommendation
Build the CARLA packaging/probe lane separately from Meshy generation. It keeps provider work and simulator registration work clean.

#### Options Considered
- Treat mesh manifest as spawnable: rejected, false claim.
- Use stock proxies only: fast but not custom asset product viability.
- Package/probe/spawn lane: recommended; it exposes the real integration boundary.

#### Blast Radius
Moderate around assets and live CARLA probes. Existing stock proxy behavior should remain unchanged.

#### Risks
- Unreal packaging may be manual or unavailable; output must be a precise blocker, not a failure spiral.
- Large generated assets must stay out of git.

### Acceptance Criteria
- [ ] AC-1: `oodrive package-asset` consumes a Meshy/local asset manifest and writes CARLA packaging inputs plus command plan.
- [ ] AC-2: `oodrive probe-asset-blueprint` searches a live CARLA blueprint library for expected custom ids and writes proof/blocker output.
- [ ] AC-3: `oodrive spawn-custom-asset` spawns a registered blueprint in CARLA, captures a screenshot/frame proof, and records cleanup ids.
- [ ] AC-4: Stock proxy fallback remains available but labeled `stock_proxy_fallback=true`.
- [ ] AC-5: Tests prevent `arbitrary_mesh_spawn=true` unless packaging, blueprint probe, and live spawn evidence all pass.

### Agent Contract
- Open: `src/driverx/assets/pipeline.py`, `src/driverx/assets/types.py`, `src/driverx/assets/carla_registry.py`, `src/driverx/simulators/carla_control.py`, `src/driverx/scenarios/studio_product_production_cli.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_custom_asset_packaging tests.test_production_scenario_generator tests.test_oodrive_cli`
- Stabilize: no Meshy secrets in repo or proxy SSH heredocs; no generated large mesh commits.
- Inspect: package plan, blueprint probe JSON, spawn proof JSON, screenshot/video.
- QA cookbook: run local no-blueprint blocker, run live blueprint probe on installed stock proxy, then run custom blueprint proof when packaging exists.
- Expected artifacts: `asset_package_plan.json`, `blueprint_probe.json`, `custom_asset_spawn_proof.json`, optional screenshot/video.

### Build Notes
- TASK-170 owns provider/request manifest generation. TASK-177 owns CARLA packaging/probing/spawning.
- Do not conflate “mesh file exists” with “CARLA blueprint registered.”

### Verification
- `PYTHONPATH=src python3 -m oodrive package-asset --asset-manifest <asset_manifest.json> --run-id task177-package`
- `PYTHONPATH=src python3 -m oodrive probe-asset-blueprint --blueprint-id static.prop.oodrive_crane --run-id task177-probe`
- `PYTHONPATH=src python3 -m oodrive spawn-custom-asset --blueprint-id static.prop.oodrive_crane --run-id task177-spawn`
- `bash scripts/pre_push_check.sh`

### Evidence
- Package plan
- Blueprint probe
- Live spawn proof or precise blocker
- Overclaim guard test output
- Planning review: `tickets/TASK-174/artifacts/review/task174-180-integration-plan-review.json`
