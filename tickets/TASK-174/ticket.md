# TASK-174: CARLA ScenarioRunner Integration Bridge

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-152, TASK-153, TASK-171
- location: `src/driverx/scenarios`, `src/driverx/simulators`, `src/driverx/evaluation`, `scripts`, `tests`
- enter when: OODrive can compile scenario graphs and run its own CARLA graph executor, but it still does not use CARLA ScenarioRunner as a native execution target.
- leave when: OODrive can export/run a ScenarioRunner-compatible scenario package, invoke ScenarioRunner when installed, capture criteria/results, and explain unsupported OODrive sidecar fields.
- blockers: requires a ScenarioRunner checkout/runtime on the Kasm or local Linux CARLA environment for live execution proof.
- spawned follow-ups: OpenSCENARIO 2.0 DSL execution hardening; ScenarioRunner criteria-to-score mapping.
- complexity: L
- assignee: generalPurpose

### Description
Integrate with CARLA ScenarioRunner instead of rebuilding every actor/trigger/criteria concept inside OODrive. OODrive remains the prompt/scenario generator, but ScenarioRunner becomes a supported execution backend for scenarios that can be represented as Python scenario classes, route scenarios, or OpenSCENARIO files.

### Goal
Make `scenario_runner` a first-class backend that a coding agent can call through CLI/MCP-style commands, with clear coverage and blockers.

### Integration Decision
Do not rebuild ScenarioRunner's scenario lifecycle. ScenarioRunner already owns Python `BasicScenario` classes, route scenario execution, OpenSCENARIO entrypoints, triggers, criteria, behavior-tree execution, and cleanup. OODrive should only translate its scenario graph into ScenarioRunner-consumable packages, invoke the external runner, and preserve sidecar metadata that ScenarioRunner cannot represent.

### Plan

#### Change
Add a bridge layer that packages OODrive graphs for ScenarioRunner and runs ScenarioRunner when a checkout is available.

#### Why
ScenarioRunner is the CARLA-native scenario execution surface. Integrating it makes OODrive more credible and avoids maintaining a parallel runner for concepts ScenarioRunner already implements.

#### Before -> After
- Before: `oodrive run-scenario` executes through OODrive's own graph/fake/live runner.
- After: `oodrive scenario-runner-package` and `oodrive scenario-runner-run` provide a standards-adjacent backend while keeping OODrive-only data in a sidecar.

#### Touch
- `src/driverx/scenarios/scenario_runner_bridge.py` new package/export helper.
- `src/driverx/scenarios/studio_product_scenario_runner_cli.py` new CLI registration.
- `src/driverx/scenarios/studio_product_scenario_runner_runtime.py` new runtime wrapper.
- `src/driverx/scenarios/studio_product_cli.py` register commands.
- `src/driverx/evaluation/scenario_runner_bridge_score.py` optional coverage score.
- `tests/test_scenario_runner_bridge.py` new contract tests.
- `tests/test_oodrive_cli.py` command registration.

#### Inspect
- `src/driverx/scenarios/scenario_graph.py`
- `src/driverx/scenarios/studio_product_production_runtime.py`
- `src/driverx/simulators/carla_scenario_runner.py`
- `tickets/TASK-152/ticket.md`
- `tickets/TASK-153/ticket.md`

#### Signature Delta
- `build_scenario_runner_package(graph: dict, sidecar: dict | None, output_dir: Path) -> ScenarioRunnerPackage`
- `run_scenario_runner_package(package_path: Path, scenario_runner_root: Path | None, carla_root: Path | None, output_dir: Path) -> ScenarioRunnerRunResult`
- `score_scenario_runner_bridge(package_or_result: dict) -> ScenarioRunnerBridgeScoreReport`

#### Type Sketch
```python
ScenarioRunnerPackage = {
  "schema_version": "oodrive.scenario_runner_package.v1",
  "scenario_runner_entrypoint": "python_class|xosc|osc2|route",
  "files": {"scenario_py": str | None, "xosc": str | None, "route_xml": str | None, "sidecar": str},
  "coverage": {"native_fields": list[str], "sidecar_fields": list[str], "unsupported_fields": list[str]},
  "command": list[str],
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example
`scenario_graph.json` with a cut-in actor -> package writes a minimal ScenarioRunner Python class or `.xosc` plus `oodrive_sidecar.json` -> run wrapper executes `scenario_runner.py` when present -> result records criteria output, stdout/stderr, return code, and coverage.

#### Execution Steps
1. Implement package builder with deterministic local output and no ScenarioRunner dependency.
2. Export the smallest supported ScenarioRunner entrypoint first: Python scenario class or existing `.xosc` compatibility view.
3. Write sidecar with prompt lineage, generated assets, RAG, claims, and unsupported fields.
4. Add runner wrapper that detects missing ScenarioRunner root and writes a precise blocker.
5. Parse result files/stdout/stderr into an OODrive result JSON.
6. Add score/coverage report and tests for package output, missing-runtime blocker, and overclaim guards.

#### Recommendation
Use ScenarioRunner as an optional backend, not as the canonical OODrive schema. OODrive's graph preserves extra evidence/provenance; ScenarioRunner executes the representable subset.

#### Options Considered
- Replace OODrive runner with ScenarioRunner: too risky because OODrive sidecar data and custom asset provenance would be lost.
- Keep only OODrive runner: faster, but duplicates CARLA scenario lifecycle concepts.
- Bridge to ScenarioRunner: recommended; it reuses upstream execution while keeping OODrive-specific evidence.

#### Blast Radius
Moderate. Adds new commands and files, but should not change existing `compile-scenario` or `run-scenario` behavior.

#### Risks
- ScenarioRunner installation drift: local tests must pass without it and emit blockers.
- Partial standards coverage: package must report unsupported fields instead of pretending full execution fidelity.

### Acceptance Criteria
- [ ] AC-1: `oodrive scenario-runner-package` consumes `scenario_graph.json` plus sidecar and writes a ScenarioRunner package directory.
- [ ] AC-2: Package includes either a minimal Python `BasicScenario` subclass, a route/scenario JSON pair, or an OpenSCENARIO file, plus an OODrive sidecar for unsupported fields.
- [ ] AC-3: `oodrive scenario-runner-run` can invoke an installed ScenarioRunner checkout or write a precise blocker when missing.
- [ ] AC-4: Output records ScenarioRunner command, return code, criteria/results file paths, CARLA map, route id if present, and cleanup status.
- [ ] AC-5: Coverage report distinguishes `native_scenario_runner=true|false`, `oodrive_sidecar_required=true|false`, and unsupported actors/actions/assets.

### Agent Contract
- Open: `src/driverx/scenarios/scenario_graph.py`, `src/driverx/scenarios/studio_product_production_runtime.py`, `src/driverx/simulators/carla_scenario_runner.py`, `src/driverx/scenarios/studio_product_cli.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_scenario_runner_bridge tests.test_oodrive_cli`
- Stabilize: do not require ScenarioRunner for local tests; local path must emit deterministic package/blocker artifacts.
- Inspect: package directory, generated Python/XOSC/route files, sidecar, coverage report, command transcript, ScenarioRunner result JSON/XML if available.
- QA cookbook: build package from a TASK-171/TASK-152 graph, run local missing-runtime blocker path, then run live Kasm ScenarioRunner if checkout exists.
- Expected artifacts: `scenario_runner_package.json`, `scenario_runner_command.sh`, `coverage_report.json`, optional `scenario_runner_results.json`.

### Build Notes
- ScenarioRunner already supports Python scenarios, route scenarios, `.xosc`, and `.osc` entrypoints; OODrive should target those surfaces instead of inventing a parallel standard.
- Preserve OODrive-only metadata in a sidecar: RAG, claim labels, generated asset provenance, Meshy/import status, and prompt lineage.

### Verification
- `PYTHONPATH=src python3 -m oodrive scenario-runner-package --scenario-graph <graph> --run-id task174-package`
- `PYTHONPATH=src python3 -m oodrive scenario-runner-run --package <package.json> --scenario-runner-root <path> --run-id task174-run`
- `PYTHONPATH=src python3 -m unittest tests.test_scenario_runner_bridge tests.test_oodrive_cli`
- `bash scripts/pre_push_check.sh`

### Evidence
- Package manifest
- Coverage report
- Command transcript
- Local missing-runtime blocker or live ScenarioRunner results
- Planning review: `tickets/TASK-174/artifacts/review/task174-180-integration-plan-review.json`
