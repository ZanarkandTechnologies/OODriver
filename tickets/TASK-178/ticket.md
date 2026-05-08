# TASK-178: Agent-Facing OODrive Tool Manifest And MCP Surface

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-165, TASK-170, TASK-171, TASK-174, TASK-175, TASK-176, TASK-177
- location: `src/driverx/scenarios`, `src/driverx/tools`, `scripts`, `tests`, `docs`
- enter when: OODrive has many useful CLI commands, but a coding agent still has to infer tool contracts from prose/help text.
- leave when: OODrive exposes machine-readable tool schemas for CARLA composition, OpenSCENARIO validation/run, ScenarioRunner bridge, map/asset import, live run, scoring, and evidence retrieval; optionally wraps them as a local MCP server.
- blockers: MCP wrapper can be deferred if tool manifest and command contracts are stable first.
- spawned follow-ups: agent harness integration docs and smoke demo.
- complexity: M
- assignee: generalPurpose

### Description
Replace the rejected “one command product flow” and rejected internal prompt resolver with the right agent-facing surface: sharp, discoverable CLI/MCP tools that a smarter harness can compose. The product should teach agents what commands exist, what inputs they require, what artifacts they produce, and which claims each command can make.

### Goal
Make OODrive usable by a coding agent without reading the whole README or ticket history.

### Integration Decision
Do not hide OODrive behind a monolithic `make` command, and do not make OODrive infer prompts internally. The correct product surface is a stable set of CLI/MCP-style tools that an agent can compose: validate agent-authored OpenSCENARIO files, configure CARLA/ScenarioRunner, inspect artifacts, and score promotion gates.

### Plan

#### Change
Add a machine-readable tool manifest, artifact index, and optional MCP wrapper for the OODrive CLI surface.

#### Why
The user will operate OODrive through a smarter harness. The harness needs explicit schemas, examples, outputs, side effects, and claim boundaries.

#### Before -> After
- Before: agents infer behavior from README/help text and ticket history.
- After: `oodrive tools-manifest` and `oodrive artifacts-list` expose stable validation/run/probe/score contracts and latest usable artifacts.

#### Touch
- `src/driverx/tools/oodrive_manifest.py` new tool registry.
- `src/driverx/tools/artifact_index.py` new artifact scanner.
- `src/driverx/scenarios/studio_product_tools_cli.py` new CLI registration.
- `src/driverx/scenarios/studio_product_tools_runtime.py` new runtime wrapper.
- `src/driverx/scenarios/studio_product_cli.py` register commands.
- `tests/test_oodrive_tool_manifest.py` new tests.
- `tests/test_oodrive_cli.py` command registration.

#### Inspect
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/scenarios/studio_product_helpers.py`
- `src/driverx/scenarios/studio_product_production_cli.py`
- `src/driverx/scenarios/studio_product_carla_composer_cli.py`
- `src/driverx/scenarios/studio_product_choreography_cli.py`

#### Signature Delta
- `build_oodrive_tools_manifest(include_experimental: bool = True) -> OODriveToolsManifest`
- `write_oodrive_tools_manifest(output_dir: Path) -> dict[str, str]`
- `build_artifact_index(output_root: Path, limit: int = 50) -> ArtifactIndex`
- `run_oodrive_mcp_server(manifest_path: Path | None = None) -> None` optional/deferred

#### Type Sketch
```python
ToolSpec = {
  "name": str,
  "purpose": str,
  "inputs": dict[str, object],
  "outputs": list[str],
  "side_effects": ["writes_artifacts", "may_connect_carla"],
  "claim_boundaries": list[str],
  "examples": list[str],
}
```

#### Typed Flow Example
Manifest entry `validate-osc2` tells an agent it needs an agent-authored `.osc` file and optional sidecar, writes validation artifacts, does not require live CARLA, and cannot claim execution. The agent then chooses `run-osc2` if a ScenarioRunner root is available.

#### Execution Steps
1. Define explicit tool specs for stable OODrive commands instead of scraping argparse.
2. Add artifact index scanner for run manifests, media, score reports, and proof level.
3. Register `tools-manifest` and `artifacts-list`.
4. Add optional MCP server placeholder only after manifest shape is stable.
5. Add schema validation and command registration tests.

#### Recommendation
Land manifest and artifact index first. MCP wrapper is optional follow-up inside the same ticket if the manifest is stable and small.

#### Options Considered
- One command orchestrator: rejected by user; wrong operating model.
- README-only docs: insufficient for coding agents.
- Tool manifest/MCP surface: recommended; composable and agent-native.

#### Blast Radius
Low. Adds discovery surfaces without changing existing command behavior.

#### Risks
- Manifest drift from real CLI behavior; tests must validate command presence and required flags.
- MCP scope creep; keep MCP optional if it delays manifest usefulness.

### Acceptance Criteria
- [ ] AC-1: `oodrive tools-manifest` emits JSON schemas for core commands, inputs, outputs, side effects, claim boundaries, and example invocations.
- [ ] AC-2: Manifest covers OpenSCENARIO validation/run, capability probing, CARLA composition, choreography, ScenarioRunner bridge, custom map import, custom asset packaging, live run, scoring, and artifact listing.
- [ ] AC-3: `oodrive artifacts-list` returns latest run artifacts by kind, proof level, score, and media availability.
- [ ] AC-4: Optional `oodrive mcp-server` exposes the same tool contracts through MCP without requiring CARLA to be running.
- [ ] AC-5: Tests verify schemas stay valid and no command claims unsupported live/custom/closed-loop capabilities.

### Agent Contract
- Open: `src/driverx/scenarios/studio_product_cli.py`, `src/driverx/scenarios/studio_product_helpers.py`, `README.md`, `docs/MEMORY.md`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_oodrive_tool_manifest tests.test_oodrive_cli`
- Stabilize: manifest must be generated from explicit local metadata or stable registry, not scraped from argparse help text at runtime.
- Inspect: `tools_manifest.json`, artifact index JSON, optional MCP smoke transcript.
- QA cookbook: emit manifest, validate JSON schema, run three example commands from the manifest in dry-run/fake mode, verify claim labels.
- Expected artifacts: `tools_manifest.json`, `artifacts_index.json`, optional `mcp_smoke.json`.

### Build Notes
- This is the product-front-door replacement. It should not hide the pipeline behind `oodrive make` or `oodrive resolve-prompt`; it should expose composable primitives.
- Keep command descriptions short and action-oriented for agent planners.

### Verification
- `PYTHONPATH=src python3 -m oodrive tools-manifest --run-id task178-tools`
- `PYTHONPATH=src python3 -m oodrive artifacts-list --output-root artifacts/runs --run-id task178-artifacts`
- `PYTHONPATH=src python3 -m unittest tests.test_oodrive_tool_manifest tests.test_oodrive_cli`
- `bash scripts/pre_push_check.sh`

### Evidence
- Tool manifest
- Artifact index
- Schema validation output
- Optional MCP smoke result
- Planning review: `tickets/TASK-174/artifacts/review/task174-180-integration-plan-review.json`
