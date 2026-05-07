# OODriver CLI QA

## Scope

TASK-114 through TASK-119: OODriver CLI database, queue, run manifest,
Alpamayo evaluation record, replay/export pack, and project-local Codex
operator skill.

## Commands Run

```bash
PYTHONPATH=src python3 -m driverx oodriver --help
PYTHONPATH=src python3 -m driverx studio --help
PYTHONPATH=src python3 -m unittest tests.test_oodriver_cli
PYTHONPATH=src python3 -m unittest tests.test_oodriver_cli tests.test_scenario_studio tests.test_scenario_workbench_bundle
PYTHONPATH=src python3 -m driverx oodriver quickstart \
  --prompt "Malaysian wet roadwork: motorbike filters between cars while a lorry brakes without signal" \
  --prompt "Night market scooter shoulder pass with sudden brake and roadside vendor occlusion" \
  --output-root artifacts/runs \
  --run-id oodriver-cli-smoke \
  --count 4 \
  --severity 4 \
  --seed 23
bash scripts/pre_push_check.sh
```

## Result

- Unit tests: passed, `10` focused tests.
- Full pre-push gate: passed, `391` tests with `3` skipped.
- CLI smoke: passed with honest `partial` status because no Alpamayo prediction
  JSON was attached.
- Product name: `OODriver`.
- Canonical command group: `driverx oodriver`.
- Compatibility alias: `driverx studio`.

## Smoke Artifacts

- DB: `artifacts/runs/oodriver-cli-smoke/scenario_studio_db.json`
- Queue: `artifacts/runs/oodriver-cli-smoke/scenario_dataset_queue.json`
- Mock run: `artifacts/runs/oodriver-cli-smoke/runs/oodriver-cli-smoke-mock-run/run_manifest.json`
- Evaluation: `artifacts/runs/oodriver-cli-smoke/evaluations/studio-0023-malaysian-wet-roadwork-motorbike-filters-between-v00-alpamayo-trajectory-eval/policy_evaluation.json`
- Replay bundle: `artifacts/runs/oodriver-cli-smoke/bundles/studio-0023-malaysian-wet-roadwork-motorbike-filters-between-v00-bundle/scenario_run_bundle.html`
- Export pack: `artifacts/runs/oodriver-cli-smoke/exports/oodriver-cli-smoke-export/scenario_generator_cli_pack.html`

## Claim Boundaries Verified

- `closed_loop_carla_execution=false`
- `real_time_vla_control=false`
- `mock_policy=true`
- `sampled_open_loop_reasoning=false`
- `memory_augmented_prompt_context=true`

## Open Runtime Blockers

No implementation blocker remains for the CLI/database path. Live CARLA and
live Alpamayo evidence are separate runtime attachments and must be recorded
through `oodriver run` and `oodriver evaluate` when available.
