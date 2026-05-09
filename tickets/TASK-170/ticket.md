# TASK-170: Meshy Custom Asset To CARLA Blueprint Import

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-149, TASK-150, TASK-151, TASK-165, TASK-166
- location: `src/driverx/assets`, `src/driverx/scenarios`, `src/driverx/simulators`, `scripts`, `tests`, `artifacts/runs`
- enter when: OODrive can compose CARLA scenarios from installed maps/assets, but the user needs custom generated objects such as a crane instead of stock CARLA proxy props.
- leave when: OODrive can request a Meshy-generated asset, store a sanitized asset manifest, either import/register it as a CARLA-spawnable blueprint or block with exact packaging steps, and prove the result with a live CARLA spawn screenshot/video when the Unreal/CARLA packaging lane is available.
- blockers: CARLA/Unreal asset import/cook/package path is still required before generated meshes become registered CARLA blueprints; do not put API keys in repo or Kasm proxy heredocs.
- spawned follow-ups: live Kasm custom asset spawn proof; final generator-gallery refresh after custom blueprint proof.
- complexity: L
- assignee: generalPurpose

### Description
Build the missing lane from "OODrive requested a custom object" to "CARLA can actually spawn this object." The first target object is a construction crane/crane arm blocking or narrowing a lane. Until the Unreal/CARLA import chain is proved, OODrive must label generated Meshy assets as custom asset manifests and use stock proxy spawning only as fallback evidence.

### Goal
Make custom objects honest and productized: generate/ingest a Meshy mesh, validate dimensions/collision/placement, package or register it into CARLA as a blueprint, and prove live spawnability before calling it a real CARLA custom object.

### Acceptance Criteria
- [x] AC-1: `oodrive generate-assets --provider meshy` or equivalent writes a Meshy asset request/manifest for a crane-like object without leaking credentials.
- [x] AC-2: The manifest records mesh files, dimensions, collision proxy, intended road-local placement, license/source metadata, and claim labels.
- [x] AC-3: `oodrive install-assets` or a new import helper can either register a CARLA blueprint id or write a precise blocker explaining the missing Unreal/CARLA packaging step.
- [x] AC-4: Asset resolution distinguishes `custom_mesh_generated=true`, `carla_blueprint_registered=true|false`, and `stock_proxy_fallback=true|false`.
- [ ] AC-5: A live proof artifact exists when possible: CARLA map, blueprint id, spawn transform, screenshot/video, and cleanup ids.
- [x] AC-6: Tests prevent claiming `arbitrary_mesh_spawn=true` unless the manifest includes generated/ingested mesh, import registry, registered blueprint, and live spawn evidence.

### Agent Contract
- Open: `src/driverx/assets/pipeline.py`, `src/driverx/assets/types.py`, `src/driverx/assets/carla_registry.py`, `src/driverx/assets/local_procedural.py`, `src/driverx/scenarios/studio_product_production_cli.py`, `src/driverx/scenarios/studio_product_production_runtime.py`, `src/driverx/simulators/carla_ood_demo.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_production_scenario_generator tests.test_carla_scenario_composer tests.test_oodrive_cli`
- Stabilize: no secrets in repo, no Meshy token through Kasm proxy heredocs, stock proxies stay labeled as proxies.
- Inspect: asset manifest, CARLA registry JSON, import/package report, live spawn screenshot/video if available.
- QA cookbook: run a dry-run Meshy/provider-disabled asset request, run registry resolution, verify custom object remains blocked/proxy-labeled without a registered blueprint, then run live spawn proof only after a blueprint exists.
- Expected artifacts: `asset_manifest.json`, `carla_asset_registry.json`, `carla_asset_import_report.md`, optional `custom_asset_spawn_proof.json`, optional screenshot/video.

### Build Notes
- First target prompt: `construction crane arm fallen across a wet urban lane`.
- Initial provider path can be request/manifest-first if Meshy credentials are not available locally.
- The CARLA claim boundary remains:
  - `arbitrary_mesh_spawn=false` until registered blueprint plus live spawn evidence exists.
  - `stock_proxy_fallback=true` when using debris/cone/foodcart proxies.

### Verification
- `PYTHONPATH=src python3 -m oodrive generate-assets --provider meshy --prompt "construction crane arm fallen across a wet urban lane" --run-id task170-crane-asset`
- `PYTHONPATH=src python3 -m oodrive install-assets --asset-manifest <asset_manifest.json> --run-id task170-crane-install`
- `PYTHONPATH=src python3 -m unittest tests.test_production_scenario_generator tests.test_oodrive_cli`
- `bash scripts/pre_push_check.sh`

### Evidence
- Repo-local Meshy skill: `skills/meshy-to-oodrive-asset/SKILL.md`
- Meshy helper: `skills/meshy-to-oodrive-asset/scripts/meshy_to_oodrive_asset.py`
- Ignored local key file: `my.env`; `.gitignore` now ignores `my.env`.
- Live Meshy smoke asset: `artifacts/runs/task170-meshy-smoke/asset_manifests.json`; generated `glb`, `fbx`, `obj`, and thumbnail for `meshy-fallen-crane-arm-smoke`.
- Live Meshy showcase batch: `artifacts/runs/task170-meshy-showcase-assets/asset_manifests.json`; generated six assets with zero failures: fallen crane arm, overturned cargo cart, flood barrier stack, fallen market canopy, road sinkhole rim, and rolled industrial drum. Each has local `glb`, `fbx`, `obj`, thumbnail, task metadata, and claim labels.
- OODrive scenario pack: `artifacts/runs/task170-meshy-scenario-pack-001/scenario_pack.json`; `validation.passes=true`, `asset_requests` length `7`, `asset_manifests` length `7`.
- OODrive external manifest ingest: `artifacts/runs/task170-meshy-ingest/asset_generation_manifest.json`; `status=passed`, `asset_manifests` length `6`.
- CARLA asset registry plan: `artifacts/runs/task170-meshy-asset-registry/carla_asset_registry.json`; `installed_blueprint_count=0`, `stock_proxy_fallback_count=6`, claim boundary `custom_asset_imported_in_carla=false; stock_proxy_fallback=true`.
- Custom asset package plan: `artifacts/runs/task170-meshy-crane-package/asset_package_plan.json`; expected blueprint `driverx.generated.meshy_fallen_crane_arm`.
- Scenario graph proof: `artifacts/runs/task170-meshy-scenario-graph/scenario_graph.json`; `validation.passes=true`, `static_objects` length `7`, `actors` length `3`, `actions` length `3`.
- Fake backend run: `artifacts/runs/task170-meshy-fake-run/scenario_run_manifest.json`; nested `result.status=passed`, `result.spawned_static_count=7`, `result.spawned_dynamic_count=3`, `result.custom_asset_spawn_count=0`, `result.stock_proxy_spawn_count=7`.
- Research generator score: `METRIC research_scenario_generator_score=63.0000`; score is capped by `live_carla_execution=0`, `prompt_image_match=0`, and `researcher_usability=0` until live custom blueprint/render proof exists.
- High-value Fail2Drive route specs: `artifacts/runs/task170-high-value-f2d-specs/*.route_spec.json`.
- High-value XML suite summary: `artifacts/runs/task170-high-value-f2d-specs/xml_suite_summary.json`; `route_count=3`, `all_ok=true`.
- Generated Fail2Drive XML:
  - `artifacts/runs/task170-vault-fallen-crane-static-blocker-xml/route.xml`
  - `artifacts/runs/task170-vault-sinkhole-swerve-recover-xml/route.xml`
  - `artifacts/runs/task170-vault-rolling-drum-crossing-xml/route.xml`

### Current Blocker
- TASK-170 is not complete as live CARLA custom asset proof because generated Meshy meshes still need an Unreal/CARLA package/import/cook path that registers `driverx.generated.*` blueprints. Current simulator proof remains stock-proxy/fake-backend until a blueprint probe and live spawn proof pass.
