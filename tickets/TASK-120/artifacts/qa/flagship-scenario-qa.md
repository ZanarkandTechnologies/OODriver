# TASK-120 Flagship Scenario QA

## Scope

TASK-120 implements the local flagship OODrive scenario contract for the next
H100/Kasm CARLA + Alpamayo sprint.

## Commands Run

```bash
PYTHONPATH=src python3 -m unittest tests.test_oodrive_flagship
PYTHONPATH=src python3 -m unittest tests.test_oodrive_cli tests.test_oodrive_flagship tests.test_scripted_ood_campaign tests.test_carla_ood_demo
PYTHONPATH=src python3 -m driverx build-flagship-oodrive-scenario \
  --config configs/oodrive_flagship_malaysia.yaml \
  --output-root artifacts/runs \
  --run-id flagship-malaysia-smoke
PYTHONPATH=src python3 -m compileall -q src tests
bash scripts/pre_push_check.sh
```

## Result

- Focused tests: passed, `4` tests.
- Integration tests: passed, `20` tests.
- Full gate: passed, `395` tests with `3` skipped.
- CLI smoke: passed and wrote `flagship_scenario.json` plus
  `flagship_scenario.md`.

## Smoke Artifacts

- `artifacts/runs/flagship-malaysia-smoke/flagship_scenario.json`
- `artifacts/runs/flagship-malaysia-smoke/flagship_scenario.md`

## Claim Boundaries Verified

- `flagship_case_study=true`
- `minimal_shot_scenario_generation=true`
- `scripted_carla_ood_demo_until_live_capture=true`
- `sampled_open_loop_reasoning_until_replay=true`
- `closed_loop_alpamayo_control=false_until_TASK_123`
- `real_time_vla_control=false`

## Blockers

No TASK-120 blocker remains. TASK-121 through TASK-124 need the H100/Kasm VM
for live CARLA capture, Alpamayo checkpoint inference, time-warped replay, and
final video packaging.
