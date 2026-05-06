# TASK-007 Review: Scenario Forge And CARLA Smoke Adapter

Reviewed: 2026-05-03 19:50 +0800

## Scope

- Changed files: scenario/memory/simulator modules, CLI, configs, tests, docs, ticket archive move.
- Rubrics: code quality, integration readiness, evidence quality.
- Context checked: `docs/prd.md`, `docs/MEMORY.md`, `ARCHITECTURE.md`, `tickets/archive/TASK-007/ticket.md`, Fail2Drive route/result parser shape.

## Verdict

Overall score: **4.4 / 5.0**

Verdict: **pass**

TASK-007 lands the intended local closed-loop planning surface without pulling CARLA, TensorFlow, SimLingo, or Alpamayo into the dependency-light path. The interfaces are narrow, deterministic, and covered by tests; old Waymo code remains runnable as a support track. The review hardening pass fixed the route-faithfulness gap: multi-recipe planning requires `--recipe-id`, generated recipes carry `route_path`, and Fail2Drive command planning validates the checkout, evaluator, agent, and selected route before emitting a dry-run plan.

## Findings

No blocking findings.

## Notes

- `plan_fail2drive_run` now emits absolute command paths plus a concrete `cwd`, avoiding ambiguity when a human copies the dry-run plan.
- `plan-carla-run` now refuses to choose implicitly from a multi-recipe suite; callers pass `--recipe-id` so the command plan is tied to one selected recipe.
- The regenerated TASK-007 evidence maps `generated-base-animals-0076-visual-noise-000` to `Base_Animals_0076.xml` consistently in both recipe and command-plan artifacts.
- `smoke-carla` intentionally checks TCP reachability only; this is the right boundary before introducing the CARLA Python client.
- Generated recipes are not executable XML yet, and the docs/ticket correctly leave XML export for a follow-up.

## Evidence Reviewed

- `bash scripts/pre_push_check.sh`: PASS, 57 tests.
- `artifacts/runs/task7-scenario-forge/scenario_suite_report.md`.
- `artifacts/runs/task7-memory-bank/memory_bank.md`.
- `artifacts/runs/task7-carla-plan/carla_command_plan.json`.
- `PYTHONPATH=src python3 -m driverx smoke-carla --config configs/carla_local.sample.yaml`: clean unreachable JSON on current machine.

## Next Action

Proceed to QA closeout and commit TASK-007. Follow-up tickets should target executable Fail2Drive XML export, SimLingo runtime, and Alpamayo adapter in that order.
