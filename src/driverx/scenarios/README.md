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
- `PYTHONPATH=src python3 -m driverx oodrive ...`

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

PYTHONPATH=src python3 -m driverx oodrive quickstart \
  --prompt "Malaysian wet roadwork with scooter filtering and unsignaled braking" \
  --run-id oodrive-cli-smoke
```

## OODrive CLI Loop

`oodrive` is the product-facing command group. `studio` is an alias kept for
older tickets and docs.

```bash
PYTHONPATH=src python3 -m driverx oodrive init --run-id oodrive-demo --force
PYTHONPATH=src python3 -m driverx oodrive ingest-brief \
  --db artifacts/runs/oodrive-demo/scenario_studio_db.json \
  --prompt "Night market scooter shoulder pass with roadside vendor occlusion" \
  --author codex
PYTHONPATH=src python3 -m driverx oodrive compile --db artifacts/runs/oodrive-demo/scenario_studio_db.json --count 6
PYTHONPATH=src python3 -m driverx oodrive queue --db artifacts/runs/oodrive-demo/scenario_studio_db.json --accept top:3
PYTHONPATH=src python3 -m driverx oodrive run --db artifacts/runs/oodrive-demo/scenario_studio_db.json --policy mock
PYTHONPATH=src python3 -m driverx oodrive evaluate --db artifacts/runs/oodrive-demo/scenario_studio_db.json
PYTHONPATH=src python3 -m driverx oodrive replay --db artifacts/runs/oodrive-demo/scenario_studio_db.json
PYTHONPATH=src python3 -m driverx oodrive export --db artifacts/runs/oodrive-demo/scenario_studio_db.json
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
PYTHONPATH=src python3 -m unittest tests.test_scenario_forge tests.test_scenario_catalog tests.test_scenario_studio tests.test_oodrive_cli
```
