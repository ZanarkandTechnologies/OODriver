# TASK-181: Fail2Drive Scenario Catalog CLI

## Status
- state: building
- owner: OODrive
- assignee: generalPurpose
- dependencies: TASK-174, TASK-180, pinned `third_party/fail2drive`
- location: `/Users/kenjipcx/SOTA/0xDriver`
- enter when: Fail2Drive submodule is available and OODrive needs an agent-readable scenario surface.
- leave when: `oodrive f2d-catalog` emits a stable JSON/Markdown catalog from upstream Fail2Drive metadata.
- blockers:
- spawned follow-ups:
- complexity: M

### Description
Expose Fail2Drive's scenario taxonomy, parameters, defaults, and route-authoring hints as an OODrive CLI surface designed for coding agents. This avoids duplicating the Fail2Drive toolbox GUI while making the same scenario vocabulary visible to Codex, MCP, and automation harnesses.

### Goal
Give an agent enough structured information to choose Fail2Drive scenario types and write valid route specs without opening the PyQt toolbox.

### Plan
#### Change
Add `oodrive f2d-catalog` with JSON and Markdown output, defaulting to `third_party/fail2drive`.

#### Why
Fail2Drive already has the hard scenario library. OODrive's useful contribution is making it inspectable, scriptable, and auditable from an agent CLI.

#### Before -> After
- Before: scenario knowledge is buried in `third_party/fail2drive/toolbox/scripts/config.py` and GUI dialogs.
- After: agents can call one command and receive scenario groups, parameter names/types/defaults, graphical-layout support, source file paths, upstream commit, and OODrive claim boundaries.

#### Touch
- `src/driverx/fail2drive/catalog.py`
- `src/driverx/fail2drive/__init__.py`
- `src/driverx/scenarios/studio_product_fail2drive_cli.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/tools/oodrive_manifest.py`
- `tests/test_fail2drive_catalog.py`
- `docs/HISTORY.md`

#### Inspect
- `third_party/fail2drive/toolbox/scripts/config.py`
- `third_party/fail2drive/toolbox/README.md`
- `third_party/fail2drive/toolbox/scripts/scenario_editor_registry.py`
- `third_party/fail2drive/scenario_runner/srunner/scenarios/`
- `src/driverx/scenarios/studio_product_tools_cli.py`

#### Signature delta
- `driverx.fail2drive.catalog / load_fail2drive_catalog(root: Path) -> Fail2DriveCatalog`
- `driverx.fail2drive.catalog / write_fail2drive_catalog_report(run_dir: Path, catalog: Fail2DriveCatalog, *, fmt: str) -> dict[str, Any]`
- `driverx.scenarios.studio_product_fail2drive_cli / register_fail2drive_commands(subparsers: Any) -> None`

#### Type Sketch
```python
@dataclass(frozen=True)
class Fail2DriveScenarioParam:
    name: str
    kind: str  # value | choice | bool | interval | transform | location | objects
    default: object | None
    tooltip: str | None
    placement_hint: str | None

@dataclass(frozen=True)
class Fail2DriveScenarioType:
    name: str
    group: str
    params: tuple[Fail2DriveScenarioParam, ...]
    graphical_editor: bool
    implementation_path: str | None

@dataclass(frozen=True)
class Fail2DriveCatalog:
    fail2drive_root: Path
    upstream_commit: str | None
    scenario_types: tuple[Fail2DriveScenarioType, ...]
    towns_with_toolbox_data: tuple[str, ...]
```

#### Typed flow example
`third_party/fail2drive/toolbox/scripts/config.py` -> static metadata loader -> `Fail2DriveCatalog` -> `artifacts/runs/task181-f2d-catalog/fail2drive_catalog.json` -> Codex chooses `RoadBlocked`, `DynamicObjectCrossing`, or `Accident` with valid parameter names.

#### Execution steps
1. Create a small Fail2Drive module that reads catalog constants without launching CARLA or PyQt.
2. Prefer AST/static loading if direct import drags GUI dependencies.
3. Classify scenario groups from `toolbox/README.md` headings and known scenario names.
4. Add the `oodrive f2d-catalog` parser with `--fail2drive-root`, `--format json|md|both`, `--output-root`, and `--run-id`.
5. Include upstream source paths and submodule commit in output.
6. Add command visibility to the OODrive tools manifest.
7. Add fixture-backed tests proving core scenario families and layout-editor scenarios are present.

#### Recommendation
Build this first. Every later Fail2Drive CLI feature should consume this catalog instead of copying scenario names by hand.

#### Options considered
- Import the GUI toolbox directly: richer but fragile due PyQt and CARLA imports.
- Parse only README text: easy but loses defaults and parameter kinds.
- Static-read `config.py` constants: recommended because it is deterministic, fast, and close to upstream truth.

#### Blast radius
New read-only command surface. Main risk is accidentally importing GUI/CARLA modules during normal CLI use.

#### Risks
- Upstream `config.py` may contain expressions that are awkward to parse statically.
- Scenario group classification may need a maintained mapping when Fail2Drive updates.

### Gap Analysis
Current OODrive has Fail2Drive run planners, but no agent-readable catalog. Production-grade agent use needs discoverable scenario names, parameter schemas, route examples, and source provenance before route authoring is reliable.

### Acceptance Criteria
- [ ] AC-1: `oodrive f2d-catalog --fail2drive-root third_party/fail2drive --format json` writes a JSON catalog.
- [ ] AC-2: Catalog includes Fail2Drive scenario groups, at least `RoadBlocked`, `DynamicObjectCrossing`, `Accident`, `CustomObstacle`, and `PedestrianCrowd`.
- [ ] AC-3: Catalog output includes parameter kinds/defaults and graphical-editor support where upstream exposes it.
- [ ] AC-4: Command appears in the OODrive tools manifest with an agent-facing usage example.

### Agent Contract
- Open: `third_party/fail2drive/toolbox/scripts/config.py`, `src/driverx/scenarios/studio_product_cli.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_catalog`
- Stabilize: do not import CARLA or PyQt at CLI startup.
- Inspect: catalog JSON and Markdown output.
- Key screens/states: none.
- QA cookbook: compare emitted scenario count and a few canonical params against upstream config.
- Taste refs: agent-readable terse JSON, provenance-first Markdown.
- Expected artifacts: `artifacts/runs/task181-f2d-catalog/fail2drive_catalog.json`, `.md`
- Delegate with: generalPurpose or explorer for upstream metadata mapping.

### Evidence Checklist
- [ ] Snapshot: catalog JSON path
- [ ] Snapshot: catalog Markdown path
- [ ] QA report linked:

### Verification
- `PYTHONPATH=src python3 -m oodrive f2d-catalog --fail2drive-root third_party/fail2drive --format both --run-id task181-f2d-catalog`
- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_catalog tests.test_oodrive_cli`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- Inputs: local Fail2Drive submodule.
- Permissions: read-only.
- Compute: CPU only.
- External services: none.
- Human gates: none.
- QA risks: false completeness if metadata parser silently drops unusual param types.

### Artifact Links
- Planning review: `tickets/TASK-181/artifacts/review/task181-187-plan-review.json`
- Implementation review: `tickets/TASK-181/artifacts/review/task181-187-impl-review.json`

### User Evidence
- Hero screenshot:
- Supporting evidence:
- QA report:
- Final verdict:

### Required Evidence
- [ ] Unit/integration/e2e tests pass (as applicable)
- [ ] Typecheck passes
- [ ] Lint passes

### Build Notes
- Implemented `driverx.fail2drive.catalog` and `oodrive f2d-catalog`.
- Smoke metric: `METRIC f2d_catalog_scenario_count=56`.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS

### Blockers
