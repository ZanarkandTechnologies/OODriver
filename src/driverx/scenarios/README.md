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

## Example

```bash
PYTHONPATH=src python3 -m driverx forge-scenarios \
  --config configs/scenario_forge.sample.yaml

PYTHONPATH=src python3 -m driverx index-scenarios \
  --artifact-root artifacts/runs/scripted-ood-campaign \
  --run-id scenario-catalog
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_scenario_forge tests.test_scenario_catalog
```
