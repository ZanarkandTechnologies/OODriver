# TASK-076: CARLA Prop And Object Spawn Pack V1

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-012, TASK-072
- location: `src/driverx/assets`, `src/driverx/simulators`, tests,
  `tickets/TASK-076/artifacts`
- enter when: TASK-072 can spawn basic actors or fake-CARLA tests are ready
- leave when: generated asset manifests can map to existing CARLA blueprints and
  spawn static/vehicle/walker OOD objects in scripted demos
- blockers: real Meshy/GLB import is out of scope; live prop proof needs CARLA
- spawned follow-ups: optional Meshy-to-CARLA asset import prototype
- complexity: M

### Summary
Use existing CARLA blueprints to make generated OOD objects visible in the demo
now. Meshy/custom GLB import stays a follow-up because packaged CARLA assets
require the Unreal content pipeline.

### Scope
- In scope: map dry-run asset manifests to existing CARLA static props,
  vehicles, walkers, barriers/cones/debris proxies, spawn transforms, collision
  proxies, and evidence.
- Out of scope: Meshy API calls, GLB/FBX import, Unreal packaging, new CARLA
  blueprints.

### Gap Analysis
- Current state: TASK-012 creates asset manifests and placeholder blueprint
  metadata, but the live CARLA demo does not spawn those objects.
- Production expectation: randomized scenario generation should visibly affect
  the simulated environment, even if v1 uses stock prop proxies.
- Missing gaps: blueprint mapping registry, prop spawn plan, validation that
  chosen blueprints exist, and track/evidence linkage.
- Recommendation: implement stock blueprint object spawning first; keep Meshy as
  a later visual-novelty ticket.

### Plan

#### Change
Add a CARLA prop/object mapping layer that turns `AssetManifest` objects into
spawnable `CarlaObjectSpawnSpec`s for TASK-072.

#### Why
This lets the demo show object novelty and road artifacts without fighting the
Unreal asset import path before submission.

#### Before -> After
- Before: asset generation is manifest-only/dry-run.
- After: generated scenarios can spawn stock CARLA proxies for debris, barriers,
  occluders, roadside objects, and unusual parked actors.

#### Touch
- `src/driverx/assets/pipeline.py`: expose blueprint mapping if not already
  enough.
- `src/driverx/assets/carla_mapping.py`: new stock blueprint registry and
  validation.
- `src/driverx/simulators/carla_ood_demo.py`: consume object spawn specs.
- `src/driverx/simulators/carla_script.py`: optional static asset actor refs.
- `tests/test_carla_asset_mapping.py`, `tests/test_carla_ood_demo.py`.
- `README.md`, `docs/progress.md`.

#### Inspect
- `src/driverx/assets/types.py`
- `src/driverx/assets/pipeline.py`
- `src/driverx/simulators/carla_injection.py`
- CARLA blueprint library behavior through fake objects.

#### Signature Delta
```python
src/driverx/assets/carla_mapping.py / map_asset_to_carla_spawn(manifest: AssetManifest, *, index: int = 0) -> CarlaObjectSpawnSpec
src/driverx/assets/carla_mapping.py / validate_carla_asset_mappings(manifests: list[AssetManifest], blueprint_ids: list[str]) -> dict[str, list[str]]
```

#### Type Sketch
```python
CarlaObjectSpawnSpec = {
  "asset_id": str,
  "actor_ref": "generated_asset_asset-roadside-food-cart",
  "blueprint_filter": "static.prop.streetbarrier",
  "spawn_transform": {"location": dict, "rotation": dict},
  "collision_proxy": dict,
  "semantic_tags": list[str],
}
```

#### Typed Flow Example
`asset-roadside-food-cart` manifest
-> `static.prop.streetbarrier` proxy
-> spawn at shoulder-relative transform
-> TASK-072 tracks include `generated_asset_asset-roadside-food-cart`
-> video overlay tags include `roadside_vendor, occlusion`.

#### Execution Steps
1. Add stock blueprint registry keyed by semantic tags.
2. Convert asset intended placements into simple CARLA transforms.
3. Validate blueprint availability in fake-CARLA and live-CARLA modes.
4. Wire spawn specs into TASK-072 runner.
5. Add evidence fields for spawned generated assets and unresolved asset
   mappings.

#### Recommendation
Prioritize stock CARLA prop proxies now. Meshy assets are useful later, but not
needed to demonstrate generated OOD scenarios.

#### Options Considered
- Meshy first: visually novel but high import/cooking risk.
- Overlays only: easy but not actually in CARLA.
- Stock CARLA prop proxies: realistic enough and runnable now.

#### Blast Radius
- Asset mapping and CARLA demo runner.
- No external API calls or secrets.

#### Risks
- Blueprint names vary by CARLA package; validation must list alternatives and
  degrade cleanly.
- Static prop spawn may fail on some maps; record per-object blockers.

### Acceptance Criteria
- [ ] AC-1: Asset manifests map to deterministic CARLA object spawn specs.
- [ ] AC-2: Fake-CARLA tests prove generated objects are included in spawn and
  cleanup.
- [ ] AC-3: Live runner reports generated asset ids, blueprint filters, spawn
  success/failure, and object blockers.
- [ ] AC-4: Docs clearly say v1 uses stock CARLA proxies, not custom Meshy
  imported meshes.

### Verification
- Focused:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_asset_mapping tests.test_carla_ood_demo`
- Full gate:
  `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- Can implement locally without CARLA or Meshy.
- Live proof only needs local CARLA running.

### Refs
- PRD US-002, FR-2, FR-3, FR-9.
- `docs/specs/minimal-shot-vla-roadmap.md` TASK-012.

### Evidence
- Planning created 2026-05-06 18:16 +0800.
- Review: `docs/reviews/TASK-072-077-impl-plan-review.md`.
- Implementation review: `docs/reviews/TASK-072-077-implementation-review.md`.
- Build: `src/driverx/assets/carla_mapping.py`,
  `src/driverx/simulators/carla_ood_demo_cli.py`, and
  `tests/test_carla_asset_mapping.py`.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_asset_mapping tests.test_carla_ood_demo`.
- Asset plan:
  `tickets/TASK-076/artifacts/stock-proxy-assets/asset_report.md`.

### Blockers
- None for stock-proxy implementation. Real Meshy/custom GLB import remains an
  explicit follow-up outside this ticket.
