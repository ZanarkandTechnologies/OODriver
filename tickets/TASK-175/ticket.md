# TASK-175: Agent-Written ASAM OpenSCENARIO 2.0 Validation And Execution Gate

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-152, TASK-174
- location: `src/driverx/scenarios`, `src/driverx/simulators`, `src/driverx/evaluation`, `tests`, `skills`
- enter when: Codex/the coding harness can author OpenSCENARIO 2.0 files, but OODrive lacks a validator/run gate that accepts those externally authored `.osc` files.
- leave when: an agent can write `scenario.osc`, pass it to OODrive for validation, run it through ScenarioRunner `--openscenario2` when available, and get coverage/claim-boundary evidence.
- blockers: ScenarioRunner OpenSCENARIO 2.0 support may not cover every OODrive feature; unsupported fields must stay sidecar-only.
- spawned follow-ups: broader ASAM coverage only after the first three bad-path cases run; Codex skill implementation in TASK-179.
- complexity: M
- assignee: generalPurpose

### Description
Treat ASAM OpenSCENARIO 2.0 as an agent-authored interoperability target, not an internal OODrive prompt generator. Codex can write the DSL; OODrive should validate, run, score, and preserve sidecar metadata.

### Goal
Let judges and agents inspect and execute a standards-shaped scenario description that Codex wrote from the user's prompt.

### Integration Decision
Do not invent an OODrive-only DSL or an internal prompt resolver for scenario semantics that ASAM OpenSCENARIO 2.0 and Codex authoring can cover. OODrive should accept agent-written `.osc` files, validate coverage, run them, and keep non-standard evidence/provenance in a sidecar. Graph-to-OSC2 export can remain a helper, but it is not the primary authoring path.

### Plan

#### Change
Add explicit `.osc` OpenSCENARIO 2.0 validation, optional helper export, and ScenarioRunner `--openscenario2` execution for agent-authored scenario files.

#### Why
The coding harness is the generator. OODrive should provide the simulator-facing guardrails: check the file, explain coverage, run it when possible, and produce evidence. That keeps intelligence in Codex and keeps OODrive as a reliable tool layer.

#### Before -> After
- Before: `compile-scenario` writes an OpenSCENARIO-ish XML skeleton.
- After: Codex writes `scenario.osc`; `validate-osc2` and `run-osc2` turn it into coverage, execution, and blocker artifacts. `export-osc2` is available only as a helper for graph-derived drafts.

#### Touch
- `src/driverx/scenarios/openscenario2_export.py` new exporter/validator.
- `src/driverx/scenarios/studio_product_osc2_cli.py` new CLI registration.
- `src/driverx/scenarios/studio_product_osc2_runtime.py` new runtime.
- `src/driverx/scenarios/studio_product_cli.py` register commands.
- `src/driverx/evaluation/openscenario2_score.py` optional coverage score.
- `tests/test_openscenario2_export.py` new tests.
- `tests/test_oodrive_cli.py` command registration.

#### Inspect
- `src/driverx/scenarios/scenario_graph.py`
- `src/driverx/scenarios/production_pack.py`
- `tickets/TASK-152/ticket.md`
- `tickets/TASK-174/ticket.md`

#### Signature Delta
- `validate_openscenario2(osc_path: Path, sidecar_path: Path | None = None) -> OpenScenario2Validation`
- `run_openscenario2(osc_path: Path, scenario_runner_root: Path | None, output_dir: Path) -> OpenScenario2RunResult`
- `export_openscenario2_draft(graph: dict, output_dir: Path) -> OpenScenario2Export`

#### Type Sketch
```python
OpenScenario2Export = {
  "osc_path": str,
  "sidecar_path": str,
  "coverage": {"supported": list[str], "unsupported": list[str], "coverage_ratio": float},
  "executable_claim": "not_run|blocked|passed",
  "claim_boundaries": ["asam_openscenario2_export=true", "asam_openscenario2_executable=false"],
}
```

#### Typed Flow Example
Codex writes `scenario.osc` for “rainy roadwork with a stopped object and a scooter cut-in” -> OODrive validates actors/actions/parallel timing/map refs and reads optional `scenario_sidecar.json` -> `run-osc2` invokes ScenarioRunner when present -> result records stdout/stderr, criteria, blocker/execution status, and claim labels.

#### Execution Steps
1. Add validator for externally authored `.osc` files: file presence, extension, basic structure, known unsupported markers, and sidecar linkage.
2. Add sidecar schema for prompt lineage, assets, RAG, claim boundaries, and media expectations.
3. Add run wrapper around ScenarioRunner `--openscenario2` with missing-runtime blocker.
4. Keep graph-to-OSC2 export as a draft helper, not as the main product workflow.
5. Add tests proving `.xosc` and `.osc` are not conflated and executable claims require execution evidence.

#### Recommendation
Make agent-authored `.osc` the main path. OODrive validates and runs it; Codex skill guidance teaches the authoring workflow.

#### Options Considered
- Retain only `.xosc`: insufficient because the user explicitly wants ASAM 2.0.
- Convert OODrive graph completely into OSC2: too generator-centric and can lose data.
- Let Codex freehand `.osc` with no validation: fast but fragile.
- Agent-authored `.osc` plus OODrive validation/run sidecar: recommended.

#### Blast Radius
Moderate. Adds commands/exporters without replacing existing graph compilation.

#### Risks
- ScenarioRunner OSC2 support may reject valid-looking DSL; keep `validate` and `run` claims separate.
- Coverage can be gamed; validation must list unsupported features explicitly.

### Acceptance Criteria
- [x] AC-1: `oodrive validate-osc2 --osc2 scenario.osc` accepts agent-authored `.osc` files and emits coverage, supported features, unsupported features, pass/block status, and claim labels.
- [x] AC-2: Validator accepts an optional sidecar with prompt lineage, assets, RAG, claim boundaries, and media expectations.
- [ ] AC-3: `oodrive export-osc2 --scenario-graph <graph>` remains available as a draft helper but is not required for the agent-authored workflow.
- [x] AC-4: `oodrive run-osc2` invokes ScenarioRunner `--openscenario2` when available or writes a precise blocker.
- [x] AC-5: Tests prevent claiming `asam_openscenario2_executable=true` unless export validation and ScenarioRunner execution evidence exist.

### Agent Contract
- Open: `src/driverx/scenarios/scenario_graph.py`, `src/driverx/scenarios/scenario_graph_export.py`, `src/driverx/scenarios/studio_product_production_cli.py`, `src/driverx/scenarios/studio_product_production_runtime.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_openscenario2_export tests.test_oodrive_cli`
- Stabilize: keep `.xosc` legacy export and `.osc` DSL export separate; do not relabel old XML output as ASAM 2.0.
- Inspect: `.osc` output, validation JSON/Markdown, sidecar, optional ScenarioRunner execution result.
- QA cookbook: write a tiny fixture `.osc`, validate supported modifiers, run missing-runtime blocker locally, then Kasm execution if ScenarioRunner is installed.
- Expected artifacts: `scenario.osc`, `osc2_validation.json`, `osc2_sidecar.json`, optional `osc2_execution_result.json`.

### Build Notes
- Use ASAM 2.0 concepts only where supported: actors, actions, serial/parallel composition, speed, position, lane, acceleration/change-speed/change-lane modifiers.
- Keep OODrive graph canonical until ASAM coverage is high enough to avoid data loss.

### Verification
- `PYTHONPATH=src python3 -m oodrive validate-osc2 --osc2 tests/fixtures/osc2/static_blocker.osc --metric-only`
- `PYTHONPATH=src python3 -m oodrive run-osc2 --osc2 <scenario.osc> --scenario-runner-root <path>`
- `bash scripts/pre_push_check.sh`

### Evidence
- OSC2 file
- Coverage/validation report
- Sidecar
- Execution result or precise blocker
- Planning review: `tickets/TASK-174/artifacts/review/task174-180-integration-plan-review.json`
- Build evidence: `PYTHONPATH=src python3 -m unittest tests.test_openscenario2_export tests.test_oodrive_cli` passed as part of the focused integration batch.
- Smoke output: `PYTHONPATH=src python3 -m oodrive validate-osc2 --osc2 tests/fixtures/osc2/static_blocker.osc --sidecar tests/fixtures/osc2/static_blocker_sidecar.json --run-id task175-osc2-smoke --metric-only` emitted `METRIC osc2_coverage_ratio=1.0000` and `METRIC osc2_status_passed=1.0000`.
- Build review: `tickets/TASK-174/artifacts/review/task174-180-impl-review.json`
