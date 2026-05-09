# TASK-183: Fail2Drive Route Authoring CLI

## Status
- state: building
- owner: OODrive
- assignee: generalPurpose
- dependencies: TASK-181, TASK-182, pinned `third_party/fail2drive`
- location: `/Users/kenjipcx/SOTA/0xDriver`
- enter when: catalog and validation surfaces exist.
- leave when: `oodrive f2d-write-route` converts agent-authored JSON specs into Fail2Drive route XML and validates the result.
- blockers:
- spawned follow-ups:
- complexity: L

### Description
Add an OODrive authoring command that writes Fail2Drive-compatible route XML from a compact JSON spec. Codex can still write XML directly, but JSON authoring gives safer defaults, stable examples, and a friendlier prompt-to-file path for automation.

### Goal
Let a user ask Codex for a weird Fail2Drive scenario, then let Codex create a typed route spec, generate XML, validate it, and hand it to Fail2Drive without opening the GUI.

### Plan
#### Change
Add `oodrive f2d-write-route --spec <route_spec.json> --output <route.xml> --validate`.

#### Why
The Fail2Drive toolbox writes XML from GUI actions. OODrive should provide the non-GUI equivalent for agents while preserving the upstream scenario format.

#### Before -> After
- Before: users must use the toolbox GUI or manually craft XML.
- After: agents can create route specs for scenarios like road blocks, dynamic crossings, accidents, and custom obstacles, then validate generated XML in the same command.

#### Touch
- `src/driverx/fail2drive/route_authoring.py`
- `src/driverx/fail2drive/route_validation.py`
- `src/driverx/scenarios/studio_product_fail2drive_cli.py`
- `tests/fixtures/fail2drive_route_specs/`
- `tests/test_fail2drive_route_authoring.py`
- `README.md`
- `docs/HISTORY.md`

#### Inspect
- `third_party/fail2drive/toolbox/scripts/carla_route.py`
- `third_party/fail2drive/toolbox/scripts/route_manager.py`
- `third_party/fail2drive/toolbox/scripts/custom_obstacle_dialog.py`
- `third_party/fail2drive/toolbox/scripts/road_blocked_layout_dialog.py`
- `third_party/fail2drive/fail2drive_split/*.xml`

#### Signature delta
- `driverx.fail2drive.route_authoring / load_fail2drive_route_spec(path: Path) -> Fail2DriveRouteSpec`
- `driverx.fail2drive.route_authoring / write_fail2drive_route_xml(spec: Fail2DriveRouteSpec, output_path: Path) -> Fail2DriveRouteWriteResult`
- `driverx.fail2drive.route_authoring / example_fail2drive_route_spec(scenario_type: str) -> dict[str, Any]`

#### Type Sketch
```python
@dataclass(frozen=True)
class Fail2DriveRouteSpec:
    route_id: str
    town: str
    waypoints: tuple[XYZ, ...]
    weather: dict[str, str | float]
    scenarios: tuple[Fail2DriveScenarioSpec, ...]
    claim_boundaries: dict[str, bool]

@dataclass(frozen=True)
class Fail2DriveScenarioSpec:
    name: str | None
    type: str
    trigger_point: Transform
    params: dict[str, object]
```

#### Typed flow example
```json
{
  "route_id": "oodrive-roadblocked-001",
  "town": "Town05",
  "waypoints": [{"x": 10, "y": 20, "z": 0}, {"x": 80, "y": 20, "z": 0}],
  "scenarios": [{
    "type": "RoadBlocked",
    "trigger_point": {"x": 45, "y": 20, "z": 0, "yaw": 0},
    "params": {"distance": 60, "wait": 20, "objects": {"vehicle.carlamotors.carlacola": "0,0,0"}}
  }]
}
```
-> `route.xml` -> TASK-182 validation -> Fail2Drive evaluator input.

#### Execution steps
1. Define the route spec JSON contract and examples for `RoadBlocked`, `DynamicObjectCrossing`, `Accident`, and `CustomObstacle`.
2. Generate XML using standard library XML builders; match Fail2Drive tag/attribute shapes from `carla_route.py`.
3. Preserve explicit agent-provided `trigger_point` instead of requiring CARLA snapping in the first pass.
4. Add `--example <scenario-type>` to emit a starter spec.
5. Add `--validate` to run TASK-182 and fail nonzero on validation errors.
6. Include source spec hash and claim boundaries in the write report.
7. Add tests for generated XML shape and validation round trip.

#### Recommendation
Implement this as a JSON-to-XML compiler, not as a natural-language generator. Codex is the generator; OODrive is the compiler and validator.

#### Options considered
- Add natural-language prompt generation inside OODrive: rejected for this slice because it duplicates Codex.
- Drive the PyQt toolbox programmatically: too fragile and not agent-native.
- Compile JSON to Fail2Drive XML: recommended because it is deterministic and easy to validate.

#### Blast radius
New authoring command. Existing OODrive generate/place/reason flow remains unchanged.

#### Risks
- Without live CARLA map snapping, user-supplied waypoints can be structurally valid but poor routes.
- Custom obstacle object encoding may need parity refinement after checking ScenarioRunner handlers.

### Gap Analysis
Prompt-to-environment needs a file compiler. Current OODrive can generate CARLA placement plans and has some Fail2Drive planners, but it cannot author upstream route XML from an agent-owned spec.

### Acceptance Criteria
- [ ] AC-1: `oodrive f2d-write-route --example RoadBlocked` emits a usable JSON spec.
- [ ] AC-2: `oodrive f2d-write-route --spec ... --output ... --validate` writes XML and passes TASK-182 validation.
- [ ] AC-3: Generated XML matches Fail2Drive route structure for route, waypoints, weather, scenarios, and trigger points.
- [ ] AC-4: At least four edge-case examples are fixture-backed: static road block, moving crossing object, accident/rolling hazard, compound custom obstacle.
- [ ] AC-5: The write report records source spec path, output path, validation result, and claim boundaries.

### Agent Contract
- Open: `third_party/fail2drive/toolbox/scripts/carla_route.py`, `tests/fixtures/fail2drive_route_specs`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_route_authoring tests.test_fail2drive_route_validation`
- Stabilize: deterministic XML ordering and stable formatting.
- Inspect: generated XML and validation JSON.
- Key screens/states: none.
- QA cookbook: generate each example, validate, inspect XML snippets.
- Taste refs: small examples that Codex can edit confidently.
- Expected artifacts: route spec JSON, route XML, authoring report.
- Delegate with: explorer for object encoding parity if needed.

### Verification
- `PYTHONPATH=src python3 -m oodrive f2d-write-route --example RoadBlocked --output-root artifacts/runs --run-id task183-example`
- `PYTHONPATH=src python3 -m oodrive f2d-write-route --spec tests/fixtures/fail2drive_route_specs/roadblocked.json --output artifacts/runs/task183-roadblocked/route.xml --validate`
- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_route_authoring tests.test_fail2drive_route_validation tests.test_oodrive_cli`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- Inputs: JSON spec, catalog, validator.
- Permissions: writes XML under requested output path and artifacts.
- Compute: CPU only.
- External services: none.
- Human gates: none.
- QA risks: structural success can still produce weak live route geometry.

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
- Implemented `driverx.fail2drive.route_authoring` and `oodrive f2d-write-route`.
- Smoke metric: `METRIC f2d_route_write_validation_errors=0`.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS

### Blockers
