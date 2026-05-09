# TASK-184: Fail2Drive Route Run Wrapper And Evidence Bundle

## Status
- state: building
- owner: OODrive
- assignee: generalPurpose
- dependencies: TASK-182, TASK-183, pinned `third_party/fail2drive`
- location: `/Users/kenjipcx/SOTA/0xDriver`
- enter when: OODrive can validate or author Fail2Drive route XML.
- leave when: `oodrive f2d-run-route` plans or executes a Fail2Drive evaluator run and bundles route evidence.
- blockers: live CARLA runtime may be unavailable locally; dry-run and Kasm paths must remain valid.
- spawned follow-ups:
- complexity: L

### Description
Wrap Fail2Drive's existing evaluator scripts in an OODrive CLI that understands the local submodule, route XML, agent selection, output evidence, and failure reporting. This ticket must reuse upstream evaluator commands rather than copying the benchmark.

### Goal
Turn a validated route XML into a runnable command plan or live Fail2Drive run with result/video/log evidence ready for reasoning and demo export.

### Plan
#### Change
Add `oodrive f2d-run-route --route <xml> --agent pdm-lite|human|transfuser|custom --dry-run|--live`.

#### Why
Fail2Drive has evaluator CLIs, but OODrive needs a product-level wrapper that agents can call with predictable defaults, artifact locations, and blocker summaries.

#### Before -> After
- Before: operators manually assemble `leaderboard_evaluator_local.py` commands and evidence paths.
- After: OODrive produces a run plan, optional execution record, expected outputs, and route-evidence bundle from one command.

#### Touch
- `src/driverx/fail2drive/run_wrapper.py`
- `src/driverx/simulators/fail2drive.py`
- `src/driverx/simulators/fail2drive_video.py`
- `src/driverx/simulators/fail2drive_route_runner.py`
- `src/driverx/pipeline/route_evidence.py`
- `src/driverx/scenarios/studio_product_fail2drive_cli.py`
- `tests/test_fail2drive_run_wrapper.py`
- `docs/HISTORY.md`

#### Inspect
- `third_party/fail2drive/leaderboard/leaderboard/leaderboard_evaluator_local.py`
- `third_party/fail2drive/team_code/visu_agent.py`
- `third_party/fail2drive/team_code/sensor_agent.py`
- `third_party/fail2drive/tools/f2d_result_parser.py`
- `scripts/run_fail2drive_client_docker.sh`

#### Signature delta
- `driverx.fail2drive.run_wrapper / build_fail2drive_route_run_request(args: argparse.Namespace) -> Fail2DriveRouteRunRequest`
- `driverx.fail2drive.run_wrapper / plan_fail2drive_route_run(request: Fail2DriveRouteRunRequest) -> Fail2DriveRouteRunPlan`
- `driverx.fail2drive.run_wrapper / write_fail2drive_route_run_bundle(run_dir: Path, plan: Fail2DriveRouteRunPlan, run_result: dict[str, Any] | None) -> dict[str, Any]`

#### Type Sketch
```python
@dataclass(frozen=True)
class Fail2DriveRouteRunRequest:
    route_path: Path
    fail2drive_root: Path
    carla_root: Path | None
    agent_kind: str
    agent_path: Path
    agent_config: Path | None
    host: str
    port: int
    live: bool
    capture_video: bool

@dataclass(frozen=True)
class Fail2DriveRouteRunPlan:
    evaluator_command: tuple[str, ...]
    env: dict[str, str]
    expected_outputs: dict[str, Path]
    blockers: tuple[str, ...]
```

#### Typed flow example
`validated route.xml` -> `f2d-run-route --agent pdm-lite --dry-run` -> evaluator command + env + blockers -> `run_evidence.json` -> downstream `f2d-reason`.

#### Execution steps
1. Reuse existing `plan_fail2drive_run`, `plan_fail2drive_video_smoke`, and `run_fail2drive_route` where possible.
2. Add agent-kind resolver defaults for `human`, `pdm-lite`, `transfuser`, and `custom`.
3. Validate route XML before planning unless `--skip-validate` is set.
4. Produce dry-run plans even when CARLA is not available.
5. In `--live`, execute through existing route runner with timeouts, logs, video polling, and nonzero blocker evidence instead of crashing.
6. Bundle results through `build_route_evidence`.
7. Add tests for command construction, default paths, blocker handling, and evidence summary.

#### Recommendation
Treat this as the runtime hinge for the submission: it should not be clever, just reliable and obvious.

#### Options considered
- Use Fail2Drive commands directly in docs only: too much manual wiring for agents.
- Reimplement evaluator behavior: rejected; upstream owns benchmark execution.
- Wrap upstream evaluator with OODrive evidence contracts: recommended.

#### Blast radius
This touches live execution surfaces. Dry-run must stay the default in tests to avoid CARLA dependency.

#### Risks
- `tools/generate_video.py` may be missing or differ in pinned Fail2Drive; wrapper must detect and report instead of assuming.
- Live Kasm/CARLA setup can fail independently of OODrive code.

### Gap Analysis
The product can author planned scenarios, but winning evidence needs repeatable runtime proof. The missing piece is a command that turns an XML route into a traceable Fail2Drive run without requiring the user to memorize evaluator flags.

### Acceptance Criteria
- [ ] AC-1: Dry-run command emits evaluator command, env, expected outputs, and validation summary.
- [ ] AC-2: Agent resolver supports `pdm-lite`, `human`, `transfuser`, and explicit `--agent-path`.
- [ ] AC-3: Missing CARLA, missing route, missing agent, and missing video tool are reported as blockers.
- [ ] AC-4: Live execution path reuses existing route runner and writes logs/result evidence when available.
- [ ] AC-5: Evidence bundle includes route validation, evaluator plan, result JSON status, video path status, and claim boundaries.

### Agent Contract
- Open: `src/driverx/simulators/fail2drive_video.py`, `src/driverx/pipeline/route_evidence.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_run_wrapper`
- Stabilize: no live CARLA in unit tests.
- Inspect: run plan JSON, run evidence JSON.
- Key screens/states: live route video only when CARLA available.
- QA cookbook: run dry-run locally; live Kasm proof if available.
- Taste refs: clear blocker messages that tell a human exactly what is missing.
- Expected artifacts: `fail2drive_route_run_plan.json`, `run_evidence.json`, logs.
- Delegate with: runtime-debugging for live CARLA failures.

### Verification
- `PYTHONPATH=src python3 -m oodrive f2d-run-route --route tests/fixtures/fail2drive_routes/valid_roadblocked.xml --fail2drive-root third_party/fail2drive --agent pdm-lite --dry-run --run-id task184-f2d-run-dry`
- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_run_wrapper tests.test_fail2drive_route_validation tests.test_oodrive_cli`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- Inputs: route XML, Fail2Drive root, optional CARLA host, optional model checkpoint.
- Permissions: may launch long-running evaluator only with `--live`.
- Compute: dry-run CPU; live needs CARLA/GPU host.
- External services: none by default.
- Human gates: live Kasm only if credentials/runtime unavailable.
- QA risks: evaluator can fail for upstream/runtime reasons; failures must be preserved as evidence, not hidden.

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
- Implemented `driverx.fail2drive.run_wrapper` and `oodrive f2d-run-route`.
- Smoke metric: `METRIC f2d_route_run_blockers=6` on local dry-run because no live Fail2Drive video helper/RGB/result artifacts exist locally; route validation and evaluator plan are produced.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: NOT PROVABLE locally - live CARLA/Fail2Drive was not run in this pass.
- AC-5: PASS

### Blockers
