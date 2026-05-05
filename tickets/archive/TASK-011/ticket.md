# TASK-011: Scenario-To-CARLA Script Compiler

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-009, TASK-010
- location: `src/driverx/simulators`, `src/driverx/behaviors`, CLI, tests
- enter when: entity tracks and behavior traces exist
- leave when: scenario recipes compile into CARLA actor script plans
- blockers: live CARLA execution optional; compiler can be tested offline
- spawned follow-ups: Fail2Drive XML export
- complexity: L

## Summary

Compile `ScenarioRecipe` plus `BehaviorPlan` into a CARLA script plan: spawn
blueprints, transforms, per-tick controls, sensors, expected outputs, and
cleanup. This is the executable layer before full Fail2Drive XML export.

## Acceptance Criteria

- [x] Compiler emits deterministic CARLA script plan JSON.
- [x] Actor plans include blueprint filters, spawn transforms, behavior binding,
  and cleanup policy.
- [x] Sensor plans include camera pose, resolution, and output path.
- [x] Plan validator rejects missing route path, unsupported behavior, and
  invalid spawn constraints.
- [x] Tests cover valid compile and invalid configs.

## Verification

- `bash scripts/pre_push_check.sh`
- `PYTHONPATH=src python3 -m driverx compile-carla-script --recipe <recipe> --behavior <behavior> --run-id task11-script`

## Blockers

- TASK-009/TASK-010 supply the spawn and behavior contracts.

## Evidence

- Local tests: `PYTHONPATH=src python3 -m unittest tests.test_carla_script tests.test_behaviors tests.test_cli` passed with 23 tests.
- Compile command: `PYTHONPATH=src python3 -m driverx compile-carla-script --recipe artifacts/runs/task7-scenario-forge/scenario_recipes.json --recipe-id generated-base-animals-0076-visual-noise-000 --behavior-id motorcycle_filtering --run-id task11-carla-script`.
- Plan artifact: `artifacts/runs/task11-carla-script/carla_script_plan.json`.
- Report artifact: `artifacts/runs/task11-carla-script/carla_script_plan.md`.
- Validation errors: `[]`.
