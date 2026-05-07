# TASK-126 QA: Prompt-To-CARLA Placement

## Commands

```bash
PYTHONPATH=src python3 -m unittest tests.test_oodrive_cli
PYTHONPATH=src python3 -m unittest tests.test_oodrive_cli tests.test_carla_ood_demo tests.test_alpamayo_ood_package tests.test_alpamayo_ood_evaluation
PYTHONPATH=src python3 -m oodrive --help
PYTHONPATH=src python3 -m oodrive generate \
  "Malaysian wet roadwork with a roadside vendor, cones, and a motorcycle filtering beside ego" \
  --output-root artifacts/runs \
  --run-id oodrive-generate-place-smoke-v2 \
  --count 3 \
  --seed 21 \
  --force
bash scripts/pre_push_check.sh
```

## Result

- Focused product tests: PASS, `8` tests.
- Integration-adjacent tests: PASS, `23` tests.
- Product help smoke: PASS, lists `generate`, `place`, and `reason`.
- Generate smoke: PASS.
- Full pre-push gate: PASS, `400` tests, `3` skipped.

## Evidence

- DB: `artifacts/runs/oodrive-generate-place-smoke-v2/scenario_studio_db.json`
- Placement plan:
  `artifacts/runs/oodrive-generate-place-smoke-v2/placements/oodrive-generate-place-smoke-v2-placement/carla_placement_plan.json`
- Placement report:
  `artifacts/runs/oodrive-generate-place-smoke-v2/placements/oodrive-generate-place-smoke-v2-placement/carla_placement_plan.md`

## Acceptance Reconciliation

- AC-1: PASS. `oodrive generate <description>` created an OODrive Studio DB.
- AC-2: PASS. `carla_placement_plan.json` and `.md` were written.
- AC-3: PASS. The smoke plan contained `2` object spawn specs with CARLA
  blueprint filters and road-local transforms.
- AC-4: PASS. Next commands include `oodrive place` and `oodrive reason`.

## Claim Boundary

This ticket proves prompt-to-placement planning. It does not claim the objects
were placed in a live CARLA world; that belongs to `oodrive place --live` and
TASK-127.
