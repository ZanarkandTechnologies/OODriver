# TASK-007: Local Scenario Forge And CARLA Smoke Adapter

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: docs/prd.md, external Fail2Drive checkout
- location: `src/driverx/scenarios`, `src/driverx/memory`, `src/driverx/simulators`, CLI, configs, tests, docs
- enter when: project pivots from Waymo-first open-loop evidence to CARLA/Fail2Drive minimal-shot scenario generation
- leave when: local scenario recipes, memory bank, dry-run CARLA command plan, smoke check, tests, docs, review, and QA evidence pass
- blockers: none for local fixture/dry-run scope
- spawned follow-ups: SimLingo/CarLLaVA runtime, Alpamayo adapter, executable XML export, serving acceleration
- complexity: L

## Summary

Implement the first closed-loop generalization surface without requiring CARLA
to run locally. The ticket preserves the Waymo pipeline as a support track,
archives completed ticket records, clones Fail2Drive externally, and adds
dependency-light scenario generation, failure memory, and CARLA/Fail2Drive
command planning.

## Scope

In scope:

- Fail2Drive-style seed ingestion from fixture JSON and external route XML
- deterministic OOD scenario recipe generation
- failure-result loading and compact memory bank generation
- tag-based retrieval of relevant memory for generated recipes
- dry-run Fail2Drive/CARLA command planning
- TCP smoke check for a local CARLA server
- docs/readme/architecture updates
- local tests and QA artifacts

Out of scope:

- live SimLingo/Alpamayo policy execution
- CARLA Python client integration
- exporting generated recipes to executable Fail2Drive XML
- official Fail2Drive leaderboard claims
- model training, fine-tuning, or serving acceleration

## Plan

### Change

Add `driverx.scenarios`, `driverx.memory`, and `driverx.simulators` modules plus
CLI commands:

- `forge-scenarios`
- `build-memory`
- `plan-carla-run`
- `smoke-carla`

### Why

The SoTA commission rewards minimal-shot generalization and randomized
simulation. The repo needs a CARLA/Fail2Drive-oriented testbed before real VLA
runtime work; otherwise Alpamayo/serving work optimizes the wrong center of
gravity.

### Before -> After

- Before: primary runtime is offline Waymo trajectory evaluation.
- After: primary runtime is local scenario generation and CARLA/Fail2Drive
  command planning, with Waymo retained as supporting open-loop evidence.

### Touch

- `src/driverx/scenarios/**`
- `src/driverx/memory/**`
- `src/driverx/simulators/**`
- `src/driverx/cli.py`
- `configs/scenario_forge.sample.yaml`
- `configs/carla_local.sample.yaml`
- `tests/test_scenario_forge.py`
- `tests/test_simulator_adapters.py`
- `tests/test_cli.py`
- `README.md`
- `ARCHITECTURE.md`
- `docs/HISTORY.md`
- `docs/MEMORY.md`
- `tickets/README.md`

### Signature Delta

```python
load_scenario_seeds(path: Path) -> list[ScenarioSeed]
generate_scenario_recipes(seeds: list[ScenarioSeed], mutation_policy: MutationPolicy, count: int, random_seed: int) -> list[ScenarioRecipe]
load_scenario_results(path: Path) -> list[ScenarioResult]
build_memory_bank(results: list[ScenarioResult]) -> MemoryBank
retrieve_memory(recipe: ScenarioRecipe, bank: MemoryBank, limit: int) -> list[MemoryEntry]
plan_fail2drive_run(config: CarlaRunConfig, recipe: ScenarioRecipe) -> CarlaCommandPlan
smoke_carla_server(host: str, port: int, timeout_s: float) -> CarlaSmokeResult
```

### Type Sketch

```python
ScenarioSeed(seed_id, source, split, scenario_class, route_id, route_path, ood_tags)
ScenarioRecipe(recipe_id, parent_seed_id, mutation, actors, environment, expected_failure_mode, memory_query)
ScenarioResult(scenario_id, policy, success, driving_score, route_completion, infractions, failure_summary, latency_ms)
MemoryEntry(entry_id, situation, observed_failure, principle, recommended_behavior, source_scenario, confidence)
CarlaCommandPlan(command, cwd, env, dry_run, expected_outputs)
```

### Typed Flow Example

`Generalization_CustomObstacles_1028.xml`
-> `ScenarioSeed(scenario_class="CustomObstacles", split="Generalization")`
-> `ScenarioRecipe(mutation="occlusion")`
-> failed policy result becomes `MemoryEntry(principle=...)`
-> retrieval attaches relevant memory to recipe
-> `plan_fail2drive_run` writes a dry-run evaluator command
-> `smoke_carla` reports whether local `127.0.0.1:2000` is reachable.

### Execution Steps

1. Clone Fail2Drive into `../external/fail2drive` and keep it uncommitted.
2. Archive completed tickets `TASK-001` through `TASK-006`.
3. Add scenario, memory, simulator modules and module docs.
4. Add fixture seeds/results and sample configs.
5. Add CLI commands and tests.
6. Update top-level docs to make CARLA/Fail2Drive the main path.
7. Run local gate.
8. Add review and QA evidence.
9. Commit in modular slices.

## Acceptance Criteria

- [x] `../external/fail2drive` exists and is not committed.
- [x] Completed ticket folders move to `tickets/archive/`.
- [x] `forge-scenarios` writes `scenario_recipes.json`, `scenario_suite_summary.json`, and `scenario_suite_report.md`.
- [x] `build-memory` writes `memory_bank.json` and `memory_bank.md`.
- [x] `plan-carla-run` writes a dry-run command plan without launching CARLA.
- [x] `smoke-carla` reports reachable/unreachable cleanly without traceback.
- [x] Tests cover fixture parsing, deterministic generation, memory retrieval, command planning, smoke failure, and CLI compatibility.
- [x] Existing Waymo fixture/batch/experiment commands remain compatible.
- [x] README and architecture present CARLA/Fail2Drive as the main path and Waymo as support.

## Agent Contract

- Open: `docs/prd.md`, `ARCHITECTURE.md`, `docs/MEMORY.md`, this ticket, new modules.
- Test hook: `bash scripts/pre_push_check.sh`.
- Stabilize: no CARLA/model imports in local tests; external Fail2Drive is read-only.
- Inspect: scenario suite report, memory bank report, command plan JSON, smoke JSON.
- Key screens/states: no UI surfaces.
- QA cookbook: local CLI proofs and artifact inspection.
- Taste refs: none.
- Expected artifacts: review doc, QA report, generated scenario/memory/plan artifacts.
- Delegate with: reviewer lane for implementation quality, QA lane for evidence.

## Evidence Checklist

- [x] Snapshot: local pre-push check output.
- [x] Snapshot: `forge-scenarios` artifact paths.
- [x] Snapshot: `build-memory` artifact paths.
- [x] Snapshot: `plan-carla-run` dry-run plan.
- [x] Snapshot: `smoke-carla` unreachable result.
- [x] QA report linked.

## Build Notes

- Started 2026-05-03 19:31 +0800.
- Fail2Drive cloned externally at `../external/fail2drive`, commit `69c982b`.
- TASK-001 through TASK-006 archived under `tickets/archive/`.
- Review hardening required route-faithful dry-run planning: generated fixture
  seeds now carry route paths, multi-recipe suites require `--recipe-id`, and
  planner validation fails fast for missing evaluator, agent, or route files.
- Local gate after hardening: `bash scripts/pre_push_check.sh` PASS, 57 tests.

## QA Reconciliation

- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS
- AC-6: PASS
- AC-7: PASS
- AC-8: PASS
- AC-9: PASS

## Artifact Links

- Review: `docs/reviews/TASK-007-scenario-forge-review.md`
- QA: `tickets/TASK-007/artifacts/qa/2026-05-03T114200Z/report.md`
- QA JSON: `tickets/TASK-007/artifacts/qa/2026-05-03T114200Z/result.json`
- Scenario suite: `artifacts/runs/task7-scenario-forge/scenario_suite_report.md`
- Memory bank: `artifacts/runs/task7-memory-bank/memory_bank.md`
- CARLA plan: `artifacts/runs/task7-carla-plan/carla_command_plan.json`

## User Evidence

- Final verdict: PASS for local scenario forge and CARLA smoke adapter.

## Required Evidence

- [x] Unit/integration/e2e tests pass as applicable.
- [x] Lint/syntax gate passes through `scripts/pre_push_check.sh`.
