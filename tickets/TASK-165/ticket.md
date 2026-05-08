# TASK-165: Agent-Friendly CARLA Scenario Composer

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-135, TASK-141
- location: `src/driverx/simulators`, `src/driverx/scenarios`, `src/oodrive`, `tests`
- enter when: the user needs OODrive to stop reusing one boring CARLA scene and expose CARLA towns, weather, props, road anchors, vehicles, pedestrians, and behavior actors through a clear CLI an AI agent can drive.
- leave when: `oodrive carla-catalog` explains available town/environment/behavior/object controls, `oodrive carla-control` exposes direct live map/weather/capture probes, `oodrive carla-compose` writes a runnable CARLA config + generated runtime manifest, live CARLA weather is applied, and tests prove the commands without launching CARLA.
- blockers: arbitrary generated Unreal maps remain out of scope until a real asset import/package/build path exists.
- spawned follow-ups: a live multi-town video reel and prompt-image QA should consume this composer for polished demo media.
- complexity: M
- assignee: generalPurpose

### Description
Build the first explicit OODrive surface for agent-driven CARLA scenario composition. The feature should be honest that OODrive composes scenarios inside existing CARLA towns by selecting maps, weather, road anchors, stock proxy assets, dynamic behaviors, background traffic, and pedestrians.

### Goal
Make it easy for a human or AI agent to generate varied CARLA sims from the CLI instead of repeatedly using the same Town10 roadwork/vendor clip.

### Acceptance Criteria
- [x] AC-1: `oodrive carla-catalog` returns JSON with CARLA town summaries, map aliases, weather presets, environment templates, behavior ids, object kinds, and claim boundaries.
- [x] AC-2: `oodrive carla-compose` accepts town/map, weather preset, road anchor, template, behaviors, object kinds, background vehicle/pedestrian counts, backend, and prompt.
- [x] AC-3: `carla-compose` writes a CARLA config YAML, generated runtime spec/manifest, agent command script, and composition manifest.
- [x] AC-4: live CARLA runner applies configured weather to the CARLA world when available.
- [x] AC-5: docs and tests explain that OODrive composes scenarios in existing CARLA maps; it does not claim arbitrary 3D world generation.

### Agent Contract
- Open: `src/driverx/simulators/carla_catalog.py`, `src/driverx/simulators/carla_control.py`, `src/driverx/scenarios/studio_product_carla_composer_runtime.py`, `src/driverx/scenarios/studio_product_cli.py`, `src/driverx/simulators/carla_ood_demo.py`, `tests/test_carla_scenario_composer.py`, `tests/test_oodrive_cli.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_carla_scenario_composer tests.test_oodrive_cli`
- Stabilize: keep live CARLA optional; fake/dry-run proof must be deterministic.
- Inspect: generated config YAML, composition manifest, generated runtime manifest.
- QA cookbook: run catalog help, compose a fake CARLA Town03 rainy construction scenario, inspect JSON paths and claim boundaries.
- Expected artifacts: `carla_composition_manifest.json`, `carla_ood_demo_config.yaml`, `agent_commands.sh`, generated runtime manifest.

### Evidence Checklist
- [x] CLI help registered.
- [x] Fake compose artifact exists.
- [x] Live multi-town CARLA screenshots exist.
- [x] Focused tests pass.
- [x] Review summary attached.

### Build Notes
- Added `src/driverx/simulators/carla_catalog.py` with agent-facing CARLA town profiles, weather presets, object-kind summaries, and claim boundaries.
- Added `src/driverx/simulators/carla_control.py` for direct live CARLA map/weather/capture probes.
- Added `src/driverx/scenarios/studio_product_carla_composer_runtime.py` with `carla-catalog`, `carla-control`, and `carla-compose` runtime handlers.
- Registered `oodrive carla-catalog`, `oodrive carla-control`, and `oodrive carla-compose`.
- Extended `CarlaOodDemoConfig` with weather config support and applied it through `world.set_weather` in live CARLA runs.
- Generated local fake-CARLA composition evidence under `artifacts/runs/task165-town03-compose-smoke/`.
- Added `driverx control-carla` as a direct agent control surface for live map loading, weather application, screenshot capture, and cleanup-accounted camera actors.
- Ran live Kasm CARLA control probes for Town03 night/rain/fog and Town05 flooded-surface settings; both loaded different maps, applied weather through CARLA, captured screenshots, and cleaned up camera sensors.

### QA Reconciliation
- AC-1: PASS. `oodrive carla-catalog` returns town summaries, map aliases, weather presets, environment templates, behavior templates, object kinds, composition controls, and claim boundaries.
- AC-2: PASS. `oodrive carla-compose` accepts town/map, load-map, weather preset, road anchor, template ids, behavior ids, object kinds, background traffic/pedestrians, backend, and prompt.
- AC-3: PASS. Fake compose smoke writes CARLA config YAML, generated runtime spec/manifest, agent command script, composition manifest, and Markdown report.
- AC-4: PASS. `run_carla_ood_demo` now applies configured weather via `world.set_weather`; unit test covers the API seam without launching CARLA.
- AC-5: PASS. `AGENTS.md`, `docs/MEMORY.md`, scenario README, simulator README, catalog claims, and composition manifest all state existing-map composition rather than arbitrary 3D world generation.

### Artifact Links
- Compose smoke manifest: `artifacts/runs/task165-town03-compose-smoke/carla_composition_manifest.json`
- Compose smoke report: `artifacts/runs/task165-town03-compose-smoke/carla_composition_manifest.md`
- Generated CARLA config: `artifacts/runs/task165-town03-compose-smoke/carla_ood_demo_config.yaml`
- Runtime manifest: `artifacts/runs/task165-town03-compose-smoke/generated-runtime/runtime/generated_scenario_runtime.json`
- Review: `tickets/TASK-165/artifacts/review/task165-impl-review.json`
- Live control review: `tickets/TASK-165/artifacts/review/task165-live-control-review.json`
- Live Town03 control JSON: `artifacts/runs/carla-control-live-pulled/artifacts/runs/carla-control-town03-night-live/carla_control.json`
- Live Town03 screenshot: `artifacts/runs/carla-control-live-pulled/artifacts/runs/carla-control-town03-night-live/carla_control_screenshot.png`
- Live Town05 control JSON: `artifacts/runs/carla-control-live-pulled/artifacts/runs/carla-control-town05-flood-live/carla_control.json`
- Live Town05 screenshot: `artifacts/runs/carla-control-live-pulled/artifacts/runs/carla-control-town05-flood-live/carla_control_screenshot.png`

### User Evidence
- Supporting evidence: `PYTHONPATH=src python3 -m oodrive carla-compose "Town03 night rain construction lane blocker with a cut-in" --town Town03 --load-map --weather-preset night_rain_fog --template-id construction_lane_closure --behavior-id motorcycle_filtering --behavior-id no_signal_cut_in --object-kind construction_debris --object-kind rolling_object --road-anchor-spawn-index 7 --background-vehicle-count 9 --background-pedestrian-count 3 --backend fake-carla --run-id task165-town03-compose-smoke`
- Live control evidence: `PYTHONPATH=src python3 -m driverx control-carla --host 127.0.0.1 --port 2000 --town Town03 --load-map --weather-preset night_rain_fog --capture --spawn-index 7 --camera-width 960 --camera-height 540 --tick-count 8 --run-id carla-control-town03-night-live` passed on Kasm CARLA with `map_before=Carla/Maps/Town10HD_Opt`, `map_after=Carla/Maps/Town03_Opt`, and screenshot capture.
- Live control evidence: `PYTHONPATH=src python3 -m driverx control-carla --host 127.0.0.1 --port 2000 --town Town05 --load-map --weather-preset flooded_surface --capture --spawn-index 15 --camera-width 960 --camera-height 540 --tick-count 8 --run-id carla-control-town05-flood-live` passed on Kasm CARLA with `map_before=Carla/Maps/Town03_Opt`, `map_after=Carla/Maps/Town05_Opt`, and screenshot capture.
- QA report: `PYTHONPATH=src python3 -m unittest tests.test_carla_scenario_composer tests.test_carla_control tests.test_carla_control_cli tests.test_oodrive_cli` passed 18 tests; `python3 -m compileall -q src tests` passed.
- Score evidence: `PYTHONPATH=src python3 -m oodrive score-generator-runtime --runtime-manifest artifacts/runs/task165-town03-compose-smoke/generated-runtime/runtime/generated_scenario_runtime.json --metric-only` emitted `METRIC generator_runtime_score=92.0000`.
- Final verdict: live control review passed at `4.4/5.0`; local tests and live Kasm screenshots prove agent-controllable CARLA maps/weather/captures. Polished multi-town video remains a follow-up render task, not a simulator capability blocker.

### Required Evidence
- [x] Unit/integration/e2e tests pass (as applicable)
- [x] Lint passes
