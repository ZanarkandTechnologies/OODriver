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
- 2026-05-10 07:28 +0800 live Kasm/F2D attempt: `artifacts/runs/task170-crane-live-f2d-v5/fail2drive_route_run.json`; route XML validation passed, evaluator launched against CARLA 0.9.15, but the run timed out after `240.143965s` with no RGB folder/video. Blocker is now the Fail2Drive evaluator camera/output hook, not route XML syntax.
- 2026-05-10 07:28 +0800 live CARLA closed-loop proxy proof: `artifacts/runs/task170-crane-proxy-closed-loop-v1/closed_loop_trace.json`; `closed_loop_score=100.0000`, `closed_loop_integration_score=100.0000`, `closed_loop_video_score=90.0000`; video at `artifacts/runs/task170-crane-proxy-closed-loop-v1/task170-crane-proxy-closed-loop-v1-video/closed_loop_hero.mp4`. This is live CARLA + stock-proxy obstacle proof with `closed_loop_policy=fake-trajectory`, not Alpamayo control.
- 2026-05-10 07:28 +0800 judge-visible direct CARLA reaction video: `artifacts/runs/task170-crane-proxy-kinematic-carla-v2/crane_proxy_stop_reaction.mp4`; contact sheet at `artifacts/runs/task170-crane-proxy-kinematic-carla-v2/preview/contact_sheet.jpg`; evidence at `artifacts/runs/task170-crane-proxy-kinematic-carla-v2/crane_proxy_reaction_evidence.json`. The video shows a live Town10HD_Opt ego approaching visible foodcart/barrier/warning-cone proxies, then `GO -> SLOW -> BRAKE -> STOP` overlays with sampled Alpamayo-style reasoning. Claim boundaries: `custom_mesh_spawned_in_carla=false`, `stock_proxy_fallback=true`, `alpamayo_outputs_applied_to_carla_controls=false`, `scripted_kinematic_carla_behavior=true`.
- 2026-05-10 07:28 +0800 review: `tickets/TASK-170/artifacts/review/2026-05-10-0728-crane-proxy-callback-review.json`; verdict `revise` because the artifact is an honest interim CARLA proxy/reaction video, not custom Meshy blueprint proof or Fail2Drive evaluator video proof.
- 2026-05-10 07:38 +0800 correction/probe for the actual Meshy crane: Meshy generated crane files exist at `artifacts/runs/task170-meshy-showcase-assets/meshy-fallen-crane-arm/model.glb`, `.fbx`, `.obj`, with thumbnail `thumbnail.png`; live CARLA probe for expected blueprint `driverx.generated.meshy_fallen_crane_arm` is blocked at `artifacts/runs/task170-meshy-crane-blueprint-probe/blueprint_probe.json`; live spawn attempt is blocked at `artifacts/runs/task170-meshy-crane-custom-spawn/custom_asset_spawn_proof.json`. Both blockers say the blueprint is not registered in CARLA, so no current video can honestly show the Meshy crane placed in CARLA.
- 2026-05-10 07:45 +0800 custom scenario render of the actual Meshy crane mesh: `artifacts/runs/task170-meshy-crane-custom-scenario-render-v1/meshy_crane_custom_scenario.mp4`; contact sheet `artifacts/runs/task170-meshy-crane-custom-scenario-render-v1/preview/contact_sheet.jpg`; manifest `artifacts/runs/task170-meshy-crane-custom-scenario-render-v1/render_manifest.json`. This renders `model.obj` from `meshy-fallen-crane-arm` across a wet-road custom scenario and shows `GO -> SLOW -> BRAKE -> STOP`. Claim boundary: `custom_mesh_rendered_in_custom_scenario=true`, `spawned_in_carla=false`.
- 2026-05-10 10:20 +0800 import/registration investigation implemented in `oodrive package-asset`: it now writes an official CARLA `Import/<Package>/Props/<Prop>/` FBX bundle, package JSON, commands, host capability report, and CARLA prop id `static.prop.meshy_fallen_crane_arm`. RunPod artifact: `artifacts/runs/task170-meshy-crane-carla-import-bundle/asset_package_plan.json`; bundle copied into `/workspace/fail2drive/f2d_carla/Import/OODrive_meshy_fallen_crane_arm` and `ImportAssets.sh` ran, but probe `artifacts/runs/task170-meshy-crane-static-prop-probe/blueprint_probe.json` still blocks because the current Fail2Drive packaged simulator can only unpack already-cooked packages and has no `make import`/editor cook path.
- 2026-05-10 10:20 +0800 review: `tickets/TASK-170/artifacts/review/2026-05-10-1020-carla-asset-import-review.json`; verdict `pass_with_blocker` for the import-bundle tooling and RunPod capability proof, with full CARLA spawn proof blocked on a source/editor cook host.
- 2026-05-10 10:49 +0800 runtime mesh path implemented and tested: `oodrive spawn-runtime-mesh` now exposes CARLA `static.prop.mesh` with `--mesh-path`, `--scale`, `--spawn-index`, and explicit `--x/--y/--z/--yaw` placement. Live RunPod proof shows a cooked CARLA mesh path renders visibly via `static.prop.mesh`: `artifacts/runs/task170-runtime-mesh-cooked-carla-car-corrected-camera/custom_asset_spawn.png`. The same corrected-camera probe for raw Meshy crane files accepts/spawns actors but does not render the crane: `artifacts/runs/task170-runtime-mesh-meshy-fbx-corrected-camera-scale50/custom_asset_spawn.png`, `artifacts/runs/task170-runtime-mesh-meshy-glb-corrected-camera-scale50/custom_asset_spawn.png`. This proves OODrive can place cooked CARLA mesh-path objects by CLI, but raw Meshy `.fbx`/`.glb` still require an Unreal/CARLA cook/import step before they are visible in CARLA.
- 2026-05-10 10:52 +0800 review: `tickets/TASK-170/artifacts/review/2026-05-10-1052-runtime-mesh-review.json`; verdict `pass_with_blocker` for cooked `static.prop.mesh` CLI placement, with full Meshy-in-CARLA proof still blocked on cook/import.
- 2026-05-10 11:15 +0800 programmatic cook preflight implemented and checked: `oodrive cook-asset-package` now inspects an `asset_package_plan.json` and reports the available lane: CARLA source `make import/package`, CARLA Docker `docker_tools.py`, or packaged-CARLA import of a prebuilt cooked `.tar.gz`/`.zip`. RunPod artifact `artifacts/runs/task170-meshy-crane-cook-preflight-runpod-v2/asset_cook_plan.json` is blocked because the current pod has `has_package_import_assets=true`, `has_source_make_import=false`, `has_editor_binary=false`, and `docker_available=false`; no cooked Meshy `.tar.gz` exists to unpack. Scenario Hub inspection confirms its `assets/` folder is preview images only, while route XMLs reference already-installed Fail2Drive/CARLA assets.
- 2026-05-10 11:15 +0800 review: `tickets/TASK-170/artifacts/review/2026-05-10-1115-cook-preflight-review.json`; verdict `pass_with_blocker` for the cook preflight CLI and evidence, with custom Meshy-in-CARLA still blocked until a source/Docker cook host or cooked package is available.
- 2026-05-10 15:43 +0800 Docker-in-Docker attempt on the Ubuntu/x86_64 RunPod: `docker.io` installed and `dockerd` can start only with `--iptables=false --bridge=none --storage-driver=vfs`, but `docker run hello-world` fails with `failed to register layer: unshare: operation not permitted`; `overlay2` fails with `failed to mount overlay: operation not permitted`. Evidence logs: `artifacts/runs/task170-docker-preflight/docker_info_no_bridge.txt`, `hello_world.txt`, `dockerd-no-bridge.log`, `docker_info_overlay2_retry.txt`, `hello_world_overlay2_retry.txt`, `dockerd-overlay2-retry.log`. This pod is not privileged enough for Docker-based CARLA cooking.

### Current Blocker
- TASK-170 is not complete as live CARLA custom asset proof because generated Meshy meshes still need an Unreal/CARLA package/import/cook path that registers `driverx.generated.*` blueprints. Current live simulator proof is stock-proxy CARLA behavior only until a blueprint probe and live custom-asset spawn proof pass.
- Fail2Drive XML route generation/validation is proved, but Fail2Drive evaluator video capture is still blocked on the evaluator RGB/camera output path on the current pod.
- The next required host is a CARLA source/editor or CARLA Docker cook environment that can run `make import` or `Util/Docker/docker_tools.py`; the current RunPod package can run CARLA and unpack cooked `.tar.gz` packages but cannot cook raw Meshy FBX into a runtime blueprint.
- `static.prop.mesh` is useful for agent-controlled placement of already-cooked CARLA assets, but raw filesystem paths to Meshy `.fbx`/`.glb` are not runtime-renderable in the current packaged simulator; actor-spawn JSON alone is not visual proof.
- Fail2Drive Scenario Hub cannot solve raw Meshy import by itself: its contribution contract is collection README + route XML + preview images, not cooked Unreal/CARLA asset packages.
- Installing Docker inside this RunPod is insufficient: nested container execution needs additional namespace/mount privileges. Use a RunPod image/template launched with Docker-in-Docker/privileged support, a normal x86_64 Linux VM with Docker, or a CARLA source build host.
