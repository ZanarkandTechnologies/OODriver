# driverx.environments

## Purpose

Own deterministic CARLA environment packs for OOD scenario generation:
construction, roadside market occlusion, flooded roads, night rain/fog, and
dense regional traffic, plus school-zone pedestrian occlusion.

## Public API

- `load_environment_pack(path=None)`
- `generate_environment_recipe(template_id, severity, random_seed)`
- `generate_environment_suite(template_ids, severity, count, random_seed)`
- `environment_to_asset_requests(recipe, road_frame_hint=None)`
- `environment_to_carla_weather(recipe)`
- `write_environment_suite_report(recipes, output_dir)`

## Example

```bash
PYTHONPATH=src python3 -m driverx forge-environments \
  --config configs/environment_forge.sample.yaml
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_environment_generator
```
