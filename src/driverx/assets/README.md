# driverx.assets

## Purpose

Owns generated OOD asset requests, dry-run manifests, provider readiness checks,
and scenario recipe asset references.

## Public API

- `default_asset_requests()`
- `generate_assets_dry_run(requests)`
- `generate_assets_with_provider(requests, provider, api_key)`
- `validate_asset_manifest(manifest)`
- `attach_assets_to_recipes(recipes, manifests)`
- `write_asset_plan(run_dir, manifests, recipes=None)`
- `map_asset_to_carla_spawn(manifest)`
- `map_assets_to_carla_spawns(manifests)`
- `validate_carla_asset_mappings(manifests, blueprint_ids)`

## Example

```bash
PYTHONPATH=src python3 -m driverx plan-assets --run-id task12-assets
```

The first CARLA object-spawn path uses stock proxy blueprints rather than
custom Meshy/GLB imports. Dry-run manifests map deterministically to traffic
cones, street barriers, construction cones, walkers, or motorcycles depending
on their semantic tags.

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_assets tests.test_carla_asset_mapping
```
