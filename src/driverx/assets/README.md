# driverx.assets

## Purpose

Owns generated OOD asset requests, dry-run manifests, provider readiness checks,
scenario recipe asset references, local procedural mesh artifacts, asset QA, and
CARLA registry/proxy fallback records.

## Public API

- `default_asset_requests()`
- `generate_assets_dry_run(requests)`
- `generate_assets_with_provider(requests, provider, api_key)`
- `generate_local_procedural_assets(requests, output_dir)`
- `validate_generated_asset_artifact(manifest)`
- `build_carla_asset_registry(manifests)`
- `write_carla_asset_registry(run_dir, registry)`
- `validate_asset_manifest(manifest)`
- `attach_assets_to_recipes(recipes, manifests)`
- `write_asset_plan(run_dir, manifests, recipes=None)`
- `map_asset_to_carla_spawn(manifest)`
- `map_assets_to_carla_spawns(manifests)`
- `validate_carla_asset_mappings(manifests, blueprint_ids)`

## Example

```bash
PYTHONPATH=src python3 -m driverx plan-assets --run-id task12-assets

PYTHONPATH=src python3 -m oodrive generate-assets \
  --scenario-pack artifacts/runs/pack/scenario_pack.json \
  --provider local-procedural \
  --run-id assets

PYTHONPATH=src python3 -m oodrive install-assets \
  --scenario-pack artifacts/runs/pack/assets/scenario_pack.assets.json \
  --mode plan \
  --run-id registry
```

The first CARLA object-spawn path still uses stock proxy blueprints unless a
target install probes generated blueprint ids successfully. Local procedural
assets write real OBJ/thumbnail artifacts and quality metadata; they do not
become custom CARLA actors until the registry/import path proves installed
blueprints. Stock proxies map deterministically to `static.prop.dirtdebris01`,
`static.prop.foodcart`, `static.prop.constructioncone`, walkers, or motorcycles
depending on semantic tags.

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_assets tests.test_carla_asset_mapping tests.test_production_scenario_generator
```
