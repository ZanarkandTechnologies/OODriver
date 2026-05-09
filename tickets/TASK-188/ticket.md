# TASK-188: Fail2Drive Asset Catalog And Render Asset QA

## Status
- state: building
- owner: OODrive
- assignee: generalPurpose
- dependencies: TASK-181, TASK-150, TASK-151
- location: `src/driverx/fail2drive`, `src/driverx/scenarios`, `src/driverx/assets`, `tests`
- enter when: Fail2Drive scenarios render without the expected prompt assets visibly present.
- leave when: OODrive exposes Fail2Drive assets through CLI, accepts external mesh manifests, and can gate route/render evidence against prompt-required assets before a video is promoted.
- blockers:
- spawned follow-ups:
- complexity: L

### Summary
Expose Fail2Drive's real simulator asset vocabulary to agents and add a render-promotion QA gate that checks whether route XML and evidence are aligned with the prompt-required assets. This closes the gap between "the scenario says animals/haybales/roadblocks" and "the CARLA run actually used a Fail2Drive simulator with those assets available."

### Scope
In scope:
- Add `oodrive f2d-assets` for agent-readable Fail2Drive asset catalog output.
- Include stock props, animal/walker ids discovered from upstream routes and scenario hub routes, scenario implementation references, and install/source provenance.
- Add `oodrive f2d-qa-assets` to compare prompt requirements, route XML blueprints, catalog availability, and optional rendered evidence paths.
- Extend `oodrive generate-assets` so an external 3D-object pipeline can hand OODrive an asset manifest JSON without pretending the mesh is already installed in CARLA.
- Add focused tests and update OODrive docs/history.

Out of scope:
- Runtime Unreal packaging for arbitrary meshes.
- Automatic visual recognition of assets inside RGB frames.
- Claiming custom generated meshes are spawnable until a CARLA blueprint probe passes.

### Plan

#### Change
Build an asset-proof layer for Fail2Drive and external assets:

```bash
PYTHONPATH=src python3 -m oodrive f2d-assets --format both
PYTHONPATH=src python3 -m oodrive f2d-qa-assets \
  --route third_party/fail2drive/fail2drive_split/Generalization_Animals_1079.xml \
  --prompt "a deer or cow crosses a rural road" \
  --evidence-frame artifacts/.../frame.jpg
PYTHONPATH=src python3 -m oodrive generate-assets \
  --scenario-pack artifacts/.../scenario_pack.json \
  --provider external-manifest \
  --external-manifest artifacts/.../meshy_asset_manifest.json
```

#### Why
Judges and users need to trust that OODrive is not just printing exotic words while CARLA renders an empty road. The product needs an agent-operable path from asset vocabulary to route XML to render QA.

#### Before -> After
- Before: `f2d-catalog` lists scenario types, but agents cannot ask "what assets can I place?"
- After: `f2d-assets` lists `static.prop.*`, `walker.animal.*`, route usage, content provenance, and scenario examples.
- Before: rendered videos can be promoted even if the prompt says animals but the route/video has no animal asset evidence.
- After: `f2d-qa-assets` blocks promotion when prompt-required assets are missing from XML/catalog/evidence.
- Before: external 3D object generation requires ad hoc hand editing.
- After: `generate-assets --provider external-manifest` patches a production scenario pack from a provider-neutral manifest contract.

#### Touch
- `src/driverx/fail2drive/assets.py` (new)
- `src/driverx/scenarios/studio_product_fail2drive_cli.py`
- `src/driverx/scenarios/studio_product_production_cli.py`
- `src/driverx/scenarios/studio_product_production_runtime.py`
- `src/driverx/assets/types.py`
- `src/driverx/assets/README.md`
- `tests/test_fail2drive_assets.py` (new)
- `tests/test_oodrive_cli.py`
- `docs/HISTORY.md`

#### Inspect
- `third_party/fail2drive/toolbox/images/carla_props_0.9.15`
- `third_party/fail2drive/fail2drive_split/*.xml`
- optional local `fail2drive_scenario_hub/*/routes/*.xml`
- `third_party/fail2drive/f2d_carla/CarlaUE4/Content`

#### Signature delta
- `driverx.fail2drive.assets / load_fail2drive_asset_catalog(root, scenario_hub_root=None): Fail2DriveAssetCatalog`
- `driverx.fail2drive.assets / write_fail2drive_asset_catalog_report(run_dir, catalog, fmt): dict[str, Any]`
- `driverx.fail2drive.assets / qa_fail2drive_route_assets(route_path, prompt, catalog, evidence_frames=(), required_assets=()): Fail2DriveAssetQA`
- `studio_product_fail2drive_cli / f2d-assets(...)`
- `studio_product_fail2drive_cli / f2d-qa-assets(...)`
- `studio_product_production_runtime / run_studio_generate_assets(..., external_manifest_path=None)`

#### Type Sketch
```python
Fail2DriveAsset = {
  "blueprint_id": str,
  "kind": "static_prop" | "animal_walker" | "vehicle" | "pedestrian" | "unknown",
  "labels": list[str],
  "sources": list[str],
  "route_usage_count": int,
  "installed_content_hint": bool,
}

Fail2DriveAssetQA = {
  "status": "passed" | "blocked",
  "prompt_requirements": list[str],
  "route_blueprints": list[str],
  "missing_requirements": list[str],
  "evidence_frame_count": int,
  "visual_proof_status": "provided" | "missing",
}
```

#### Typed flow example
Prompt: "cow walking on rural road" -> inferred requirement `animal` -> route contains `walker.animal.1002` -> catalog records animal assets from Fail2Drive route XML and `f2d_carla` content -> QA passes route/catalog proof and requires rendered frame paths before hero promotion.

#### Execution steps
1. Implement the Fail2Drive asset catalog scanner without importing CARLA.
2. Parse route XML and scenario hub XML for blueprint ids and route usage.
3. Add prompt-to-required-asset heuristics for animals, haybales, debris, roadblocks, accident props, pedestrians, and vehicles.
4. Add `f2d-assets` and `f2d-qa-assets` CLI commands.
5. Add `external-manifest` provider mode for production asset generation.
6. Add tests for catalog contents, animal/hay route QA, missing-asset failure, external manifest ingestion, and CLI registration.
7. Run focused checks and record evidence.

#### Recommendation
Use Fail2Drive's installed simulator asset pack as the first-class asset source for near-term demos, while keeping generated external meshes behind an explicit manifest/package/probe chain. This wins fastest because animals/haybales/custom props already exist in the Fail2Drive simulator, and generated meshes still need Unreal packaging before honest CARLA spawn claims.

#### Options considered
- Rebuild an OODrive-only asset generator: rejected because it duplicates Fail2Drive and does not solve live spawn proof.
- Use Scenario Hub only: useful for examples, but the hub is route XML and preview images, not the installed simulator asset pack.
- Recommended: catalog Fail2Drive installed/route assets, integrate hub XML as optional source, and ingest external mesh manifests through the existing custom-asset registry.

#### Blast radius
- CLI parser help/registration.
- Production asset pack generation.
- Fail2Drive route QA reports.
- No generated media or model artifacts enter git.

#### Risks
- Blueprint IDs from routes do not prove a live CARLA server has loaded the matching customized simulator; the QA report must keep this as a claim boundary.
- External mesh manifests can be malformed; validation must block weak manifests instead of patching scenario packs blindly.
- Visual proof remains human/QA evidence until object detection exists.

### Acceptance Criteria
- [x] AC-1: `oodrive f2d-assets` emits JSON/Markdown with stock props and animal walker ids.
- [x] AC-2: `oodrive f2d-qa-assets` passes route/prompt alignment when evidence frames are supplied and blocks prompt/route mismatch.
- [x] AC-3: `generate-assets --provider external-manifest --external-manifest <json>` patches a scenario pack with externally generated asset manifests.
- [x] AC-4: Reports distinguish route/catalog proof from rendered visual proof and preserve claim boundaries.
- [x] AC-5: Focused tests pass.

### Verification
- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_assets tests.test_oodrive_cli tests.test_assets`
- `PYTHONPATH=src python3 -m oodrive f2d-assets --fail2drive-root third_party/fail2drive --format both --run-id task188-f2d-assets`
- `PYTHONPATH=src python3 -m oodrive f2d-qa-assets --route third_party/fail2drive/fail2drive_split/Generalization_Animals_1079.xml --prompt "a deer crosses a rural road" --run-id task188-animal-qa`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- Safe local implementation is unblocked.
- Live CARLA visual QA needs a running Fail2Drive CARLA simulator and rendered frames; this ticket can produce the gate locally and record live proof as missing until frames are provided.
- No secrets, paid API calls, or destructive remote operations are required.

### Evidence
- Planned by `impl-plan` on 2026-05-10.
- Implemented `driverx.fail2drive.assets`, `oodrive f2d-assets`, and `oodrive f2d-qa-assets`.
- Implemented `generate-assets --provider external-manifest --external-manifest <json>` for external 3D pipeline ingestion.
- Focused tests: `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_assets tests.test_oodrive_cli tests.test_assets tests.test_carla_asset_mapping` -> `Ran 25 tests`, `OK`.
- Asset catalog smoke: `PYTHONPATH=src python3 -m oodrive f2d-assets --fail2drive-root third_party/fail2drive --format both --run-id task188-f2d-assets --metric-only` -> `METRIC f2d_asset_count=140`.
- Render QA no-frame smoke: `PYTHONPATH=src python3 -m oodrive f2d-qa-assets --route third_party/fail2drive/fail2drive_split/Generalization_Animals_1079.xml --prompt 'a deer crosses a rural road' --run-id task188-animal-qa-no-frame` -> route matched `walker.animal.1010`, status `blocked` only because rendered visual evidence frame is missing.
- Mismatch smoke: `PYTHONPATH=src python3 -m oodrive f2d-qa-assets --route third_party/fail2drive/fail2drive_split/Generalization_Animals_1079.xml --prompt 'a haybale blocks the lane' --run-id task188-mismatch-qa --metric-only` -> `METRIC f2d_asset_qa_missing_requirements=1`.
- Full gate: `bash scripts/pre_push_check.sh` -> `Ran 521 tests`, `OK (skipped=6)`, `Pre-push checks passed`.
- Review: `tickets/TASK-188/artifacts/review/task188-impl-review.json` -> pass, score `4.1`.
- Live stock-prop CARLA proof: `scripts/run_asset_showcase_carla.py` rendered `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task188-asset-showcase-live-v2/` from RunPod CARLA, spawning haybales, traffic warning, food cart, cones, debris, street barriers, parked vehicles, and a scooter across three MP4s. Each case drove about `94.081m`; claim boundary remains `animal_assets=false_on_current_stock_carla_server`.
- Live Fail2Drive animal proof: installed the packaged Fail2Drive simulator on RunPod, launched it as `kasm-user`, used a matching Miniconda Python 3.10 + `carla-0.9.15` client, and rendered `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task188-animal-showcase-live/animal_assets_crossing_gallery_v2/animal_assets_crossing_gallery_v2.mp4`.
- Animal runtime probe: Fail2Drive CARLA reported `walker.animal.* 18` and no semantic `*duck*` blueprint filter; v2 animal render spawned `12 / 18` requested `walker.animal.*` actors and visibly shows elephant, cow, chicken-like birds, deer/stag, lion-like animals, and other animal walkers in the local frame dump.
- Animal showcase manifest: `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task188-animal-showcase-live/animal_showcase_manifest.json`; v2 case drove `69.133m`, captured `260` frames, and records `duck_assets_available=false`.

### Blockers
- Duck-specific visual proof remains blocked because this Fail2Drive simulator exposes animal walker IDs but no duck-named blueprint or duck content found in the installed package.
