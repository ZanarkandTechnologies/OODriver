# TASK-011 Review: Scenario-To-CARLA Script Compiler

Reviewed: 2026-05-04 19:04 +0800

## Scope

- Changed files: CARLA script compiler, simulator exports, CLI, tests, docs,
  ticket evidence.
- Rubrics: interface clarity, validation, evidence quality.
- Context checked: TASK-009 entity tracks, TASK-010 behavior traces,
  `tickets/archive/TASK-011/ticket.md`.

## Verdict

Overall score: **4.1 / 5.0**

Verdict: **pass**

TASK-011 creates a useful offline compiler from generated recipe + behavior
trace into a validated CARLA script plan. It does not execute the script yet,
which is the right boundary before introducing multi-actor live side effects.

## Findings

No blocking findings.

## Notes

- `src/driverx/cli.py` is now over the warning threshold at 524 lines. It still
  passes the gate, but the next CLI-heavy ticket should split command handlers
  into a command module before the file keeps swelling.
- The compiler's output schema should be the input contract for future live
  multi-actor execution and Fail2Drive XML export.

## Evidence Reviewed

- `bash scripts/pre_push_check.sh`: PASS, 76 tests, with non-blocking CLI size warning.
- `PYTHONPATH=src python3 -m driverx compile-carla-script --recipe artifacts/runs/task7-scenario-forge/scenario_recipes.json --recipe-id generated-base-animals-0076-visual-noise-000 --behavior-id motorcycle_filtering --run-id task11-carla-script`: PASS.
- `artifacts/runs/task11-carla-script/carla_script_plan.json`.

## Next Action

Proceed to TASK-012, but avoid adding much more to `src/driverx/cli.py` without
extracting command handlers.
