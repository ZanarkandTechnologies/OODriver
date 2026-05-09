# TASK-182: Agent-Written Fail2Drive Route XML Validator

## Status
- state: building
- owner: OODrive
- assignee: generalPurpose
- dependencies: TASK-181, pinned `third_party/fail2drive`
- location: `/Users/kenjipcx/SOTA/0xDriver`
- enter when: agents can inspect the Fail2Drive scenario catalog.
- leave when: `oodrive f2d-validate-route` gives actionable validation for Codex-authored Fail2Drive XML.
- blockers:
- spawned follow-ups:
- complexity: M

### Description
Add an OODrive validator for Fail2Drive route XML so a coding agent can write or edit route files and immediately get precise, fixable errors. The validator should check route structure, scenario type names, expected parameter shapes, trigger points, and basic provenance without launching CARLA.

### Goal
Make route XML authoring safe enough that Codex can iteratively write Fail2Drive scenarios from a user prompt and prove the file is structurally runnable before runtime.

### Plan
#### Change
Add `oodrive f2d-validate-route --route <xml>` and a reusable validator module.

#### Why
Fail2Drive provides evaluator scripts, but an agent-native edit/validate loop needs fast, local, structured feedback before expensive CARLA runs.

#### Before -> After
- Before: invalid XML is discovered late through ScenarioRunner or evaluator failures.
- After: agents receive JSON diagnostics with paths, scenario names, param issues, and suggested repairs.

#### Touch
- `src/driverx/fail2drive/route_validation.py`
- `src/driverx/fail2drive/catalog.py`
- `src/driverx/scenarios/studio_product_fail2drive_cli.py`
- `tests/fixtures/fail2drive_routes/`
- `tests/test_fail2drive_route_validation.py`
- `docs/HISTORY.md`

#### Inspect
- `third_party/fail2drive/fail2drive_split/*.xml`
- `third_party/fail2drive/toolbox/scripts/carla_route.py`
- `third_party/fail2drive/scenario_runner/srunner/tools/route_parser.py`
- `src/driverx/simulators/fail2drive.py`

#### Signature delta
- `driverx.fail2drive.route_validation / validate_fail2drive_route(route_path: Path, catalog: Fail2DriveCatalog, *, strict: bool = False) -> Fail2DriveRouteValidation`
- `driverx.fail2drive.route_validation / write_fail2drive_route_validation(run_dir: Path, validation: Fail2DriveRouteValidation) -> dict[str, Any]`

#### Type Sketch
```python
@dataclass(frozen=True)
class RouteIssue:
    severity: Literal["error", "warning", "info"]
    code: str
    xml_path: str
    message: str
    suggestion: str | None

@dataclass(frozen=True)
class Fail2DriveRouteValidation:
    route_path: Path
    ok: bool
    route_count: int
    town_names: tuple[str, ...]
    scenario_counts: dict[str, int]
    issues: tuple[RouteIssue, ...]
```

#### Typed flow example
`Codex-authored route.xml` -> XML parse -> route/waypoint/scenario walk -> catalog param check -> `ok=false` with `missing trigger_point for scenario RoadBlocked_0` -> Codex patches XML -> `ok=true`.

#### Execution steps
1. Create positive and negative route fixtures from minimal Fail2Drive-style XML.
2. Parse XML with `xml.etree.ElementTree` and never execute upstream code.
3. Validate root `<routes>`, route `id`/`town`, waypoint positions, scenario name/type, trigger point transform, and param tag shapes.
4. Use TASK-181 catalog for scenario type and param kind checks.
5. Treat extra params as warnings by default and errors under `--strict`.
6. Emit JSON and Markdown reports under `artifacts/runs/<run-id>/`.
7. Add `--metric-only` output such as `METRIC f2d_route_validation_errors=<n>`.

#### Recommendation
Build this immediately after catalog. It is the core guardrail that lets agent-authored XML be useful instead of brittle.

#### Options considered
- Shell out to Fail2Drive evaluator for validation: too slow and requires CARLA context.
- Rely on XML schema: upstream scenario params are Python-defined rather than XSD-defined.
- Local semantic validator: recommended for fast agent edit loops.

#### Blast radius
New validation path only. It should not mutate routes or run CARLA.

#### Risks
- Some upstream scenarios accept undocumented params; validator must avoid over-rejecting valid routes unless `--strict`.
- Route topology correctness still needs CARLA map snapping or upstream route parser; this ticket validates structure, not drivable geometry.

### Gap Analysis
The product needs prompt -> scenario file -> proof. OODrive has generator and CARLA placement surfaces, but the Fail2Drive route-XML leg lacks the fast validation layer that real agent workflows require.

### Acceptance Criteria
- [ ] AC-1: Valid Fail2Drive fixture route passes with `ok=true`.
- [ ] AC-2: Unknown scenario types produce precise errors with suggestions from the catalog when possible.
- [ ] AC-3: Missing or malformed `trigger_point`, `interval`, `value`, `transform`, and `objects` params are reported with XML paths.
- [ ] AC-4: `--strict` upgrades unknown extra params from warnings to errors.
- [ ] AC-5: CLI emits machine-readable JSON and `METRIC f2d_route_validation_errors=<n>`.

### Agent Contract
- Open: `src/driverx/fail2drive/catalog.py`, `third_party/fail2drive/fail2drive_split`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_route_validation`
- Stabilize: keep diagnostics deterministic and sorted.
- Inspect: validation report JSON/Markdown.
- Key screens/states: none.
- QA cookbook: run good/bad fixtures and verify issue codes.
- Taste refs: compiler-style diagnostics, not vague prose.
- Expected artifacts: `fail2drive_route_validation.json`, `.md`
- Delegate with: qa-tester after implementation for fixture reconciliation.

### Verification
- `PYTHONPATH=src python3 -m oodrive f2d-validate-route --route tests/fixtures/fail2drive_routes/valid_roadblocked.xml --fail2drive-root third_party/fail2drive --metric-only`
- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_route_validation tests.test_oodrive_cli`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- Inputs: route XML and Fail2Drive catalog.
- Permissions: read-only route inspection, write reports under artifacts.
- Compute: CPU only.
- External services: none.
- Human gates: none.
- QA risks: semantic parity gaps versus ScenarioRunner runtime.

### Artifact Links
- Planning review: `tickets/TASK-181/artifacts/review/task181-187-plan-review.json`
- Implementation review: `tickets/TASK-181/artifacts/review/task181-187-impl-review.json`

### User Evidence
- Supporting evidence:
- QA report:
- Final verdict:

### Required Evidence
- [ ] Unit/integration/e2e tests pass (as applicable)
- [ ] Typecheck passes
- [ ] Lint passes

### Build Notes
- Implemented `driverx.fail2drive.route_validation` and `oodrive f2d-validate-route`.
- Smoke metric: `METRIC f2d_route_validation_errors=0`.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS

### Blockers
