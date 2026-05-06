# driverx.behaviors

## Purpose

Owns deterministic OOD actor behavior traces and parameterized behavior
templates for scenario generation. These traces let tests verify the intended
pressure before live CARLA scripts exist.

## Public API

- `default_behavior_plans()`
- `default_behavior_templates()`
- `generate_behavior_variants(template_id, count, random_seed, severity)`
- `simulate_behavior(plan)`
- `summarize_behavior_suite(traces)`
- `validate_behavior_plan(plan, constraints)`
- `write_behavior_suite(run_dir, traces)`

## Example

```bash
PYTHONPATH=src python3 -m driverx generate-behaviors \
  --template-id motorcycle_filtering \
  --count 4 \
  --severity 4 \
  --validate \
  --run-id behavior-suite
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_behaviors tests.test_behavior_dsl
```
