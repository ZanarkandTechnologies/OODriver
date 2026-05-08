# driverx.scenarios

## Purpose

Owns Fail2Drive-style scenario seeds, generated OOD recipes, and scenario suite
reports for the 0xDriver closed-loop generalization track. It also owns the
Scenario Studio catalog that indexes generated CARLA evidence, Alpamayo
reasoning artifacts, quality gates, and promotion status for submission curation.

## Public API

- `load_scenario_seeds(path)`
- `generate_scenario_recipes(seeds, mutation_policy, count, random_seed)`
- `write_scenario_suite(run_dir, seeds, recipes)`
- `index_scenario_artifacts(artifact_roots)`
- `filter_catalog(catalog, query)`
- `promote_scenario(catalog, scenario_id, decision)`
- `driverx.scenarios.studio.compile_scenario_prompt(prompt, seed=...)`
- `driverx.scenarios.studio.generate_studio_batch(config)`
- `driverx.scenarios.studio_product.run_studio_quickstart(...)`
- `driverx.scenarios.generated_runtime.build_generated_scenario_runtime_spec(...)`
- `driverx.scenarios.generated_runtime.run_generated_scenario_runtime(...)`
- `driverx.scenarios.production_pack.build_production_scenario_pack(...)`
- `driverx.scenarios.scenario_graph.compile_scenario_graph(...)`
- `driverx.scenarios.studio_product_production_runtime.run_studio_run_scenario(...)`
- `PYTHONPATH=src python3 -m oodrive ...`

## Example

```bash
PYTHONPATH=src python3 -m driverx forge-scenarios \
  --config configs/scenario_forge.sample.yaml

PYTHONPATH=src python3 -m driverx index-scenarios \
  --artifact-root artifacts/runs/scripted-ood-campaign \
  --run-id scenario-catalog

PYTHONPATH=src python3 -m driverx generate-scenario-studio \
  --config configs/scenario_studio.sample.json \
  --run-id scenario-studio-v1

PYTHONPATH=src python3 -m oodrive quickstart \
  --prompt "Malaysian wet roadwork with scooter filtering and unsignaled braking" \
  --run-id oodrive-cli-smoke
```

## OODrive CLI Loop

`oodrive` is the product-facing command. `driverx oodrive`,
`driverx oodriver`, and `driverx studio` remain aliases kept for older tickets
and docs.

```bash
PYTHONPATH=src python3 -m oodrive init --run-id oodrive-demo --force
PYTHONPATH=src python3 -m oodrive ingest-brief \
  --db artifacts/runs/oodrive-demo/scenario_studio_db.json \
  --prompt "Night market scooter shoulder pass with roadside vendor occlusion" \
  --author codex
PYTHONPATH=src python3 -m oodrive compile --db artifacts/runs/oodrive-demo/scenario_studio_db.json --count 6
PYTHONPATH=src python3 -m oodrive queue --db artifacts/runs/oodrive-demo/scenario_studio_db.json --accept top:3
PYTHONPATH=src python3 -m oodrive run --db artifacts/runs/oodrive-demo/scenario_studio_db.json --policy mock
PYTHONPATH=src python3 -m oodrive evaluate --db artifacts/runs/oodrive-demo/scenario_studio_db.json
PYTHONPATH=src python3 -m oodrive replay --db artifacts/runs/oodrive-demo/scenario_studio_db.json
PYTHONPATH=src python3 -m oodrive export --db artifacts/runs/oodrive-demo/scenario_studio_db.json
```

Generated behavior/object runtime proof:

```bash
PYTHONPATH=src python3 -m oodrive carla-catalog

PYTHONPATH=src python3 -m oodrive carla-control \
  --town Town03 \
  --load-map \
  --weather-preset night_rain_fog \
  --capture \
  --run-id town03-control-probe

PYTHONPATH=src python3 -m oodrive carla-compose \
  "Town03 night rain construction lane blocker with a cut-in" \
  --town Town03 \
  --load-map \
  --weather-preset night_rain_fog \
  --template-id construction_lane_closure \
  --behavior-id motorcycle_filtering \
  --behavior-id no_signal_cut_in \
  --object-kind construction_debris \
  --object-kind rolling_object \
  --road-anchor-spawn-index 7 \
  --background-vehicle-count 9 \
  --background-pedestrian-count 3 \
  --backend fake-carla \
  --run-id town03-compose-smoke

PYTHONPATH=src python3 -m oodrive generate-run \
  "wet Malaysian roadwork, scooter cut-in, lane debris" \
  --template-id construction_lane_closure \
  --behavior-id motorcycle_filtering \
  --behavior-id no_signal_cut_in \
  --object-kind construction_debris \
  --object-kind roadside_vendor \
  --backend fake-carla \
  --run-id generated-runtime-smoke

PYTHONPATH=src python3 -m oodrive score-generator-runtime \
  --runtime-manifest artifacts/runs/generated-runtime-smoke/generated_scenario_runtime.json \
  --metric-only
```

On the Kasm CARLA host, switch the same generated runtime to live simulator
proof:

```bash
PY=/workspace/driverx_py312/bin/python
PYTHONPATH=src "$PY" -m oodrive generate-run \
  "wet Malaysian roadwork, scooter cut-in, lane debris" \
  --template-id construction_lane_closure \
  --behavior-id motorcycle_filtering \
  --object-kind construction_debris \
  --object-kind roadside_vendor \
  --object-kind lane_cone \
  --backend carla-live \
  --config configs/carla_ood_demo.runpod.high_fidelity.yaml \
  --run-id task141-runpod-carla-live
```

The live proof is still open-loop with respect to Alpamayo control:
`objects_spawned_in_carla=true`, `closed_loop_vla_control=false`, and
`real_time_vla_control=false`.

`carla-compose` is the preferred agent-facing entrypoint when the goal is
scenario diversity. It composes OODrive scenarios inside existing CARLA towns by
selecting the map, weather, road anchor, stock proxy objects, dynamic behavior
actors, background vehicles, and pedestrians. It does not claim arbitrary Unreal
world generation; use custom asset/import tickets when a new 3D mesh or map is
required.

Production prompt-to-CARLA scenario generator:

```bash
PYTHONPATH=src python3 -m oodrive scenario-pack \
  "wet Malaysian roadwork with scooter filtering around debris and a roadside vendor" \
  --template-id construction_lane_closure \
  --behavior-id motorcycle_filtering \
  --object-kind construction_debris \
  --object-kind roadside_vendor \
  --run-id production-pack

PYTHONPATH=src python3 -m oodrive generate-assets \
  --scenario-pack artifacts/runs/production-pack/scenario_pack.json \
  --provider local-procedural \
  --run-id production-assets

PYTHONPATH=src python3 -m oodrive install-assets \
  --scenario-pack artifacts/runs/production-pack/production-assets/scenario_pack.assets.json \
  --mode plan \
  --run-id production-registry

PYTHONPATH=src python3 -m oodrive compile-scenario \
  --scenario-pack artifacts/runs/production-pack/production-assets/scenario_pack.assets.json \
  --asset-registry artifacts/runs/production-pack/production-assets/production-registry/carla_asset_registry.json \
  --run-id production-graph

PYTHONPATH=src python3 -m oodrive run-scenario \
  --scenario-pack artifacts/runs/production-pack/production-assets/scenario_pack.assets.json \
  --scenario-graph artifacts/runs/production-pack/production-assets/production-graph/scenario_graph.json \
  --backend carla-live \
  --config configs/carla_ood_demo.runpod.high_fidelity.yaml \
  --run-id production-live
```

`score-research-generator` should include prompt-image QA when available. A
partial visual match caps flagship scoring even when the simulator run itself is
live CARLA.

AI-assisted generation:

```bash
PYTHONPATH=src python3 -m oodrive ai-generate \
  --prompt "Malaysian wet night roadwork chaos with scooter filtering" \
  --run-id oodrive-ai-smoke \
  --count 4 \
  --compile \
  --queue
```

The CLI stores durable state in `scenario_studio_db.json`, produces Markdown and
HTML proof packets, and keeps claim boundaries explicit when CARLA or Alpamayo
evidence is missing.

## Flagship Scenario Contract

Use this when preparing the high-quality case study for the final submission
runtime:

```bash
PYTHONPATH=src python3 -m driverx build-flagship-oodrive-scenario \
  --config configs/oodrive_flagship_malaysia.yaml \
  --run-id flagship-malaysia
```

The output pack names the scenario actors, behavior sequence, checkpoint plan,
quality gates, and H100/Kasm runtime commands for the CARLA + Alpamayo loop.

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_scenario_forge tests.test_scenario_catalog tests.test_scenario_studio tests.test_oodrive_cli tests.test_generated_carla_runtime tests.test_production_scenario_generator
```
