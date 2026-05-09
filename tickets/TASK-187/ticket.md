# TASK-187: Fail2Drive Model Reaction Batch CLI

## Status
- state: building
- owner: OODrive
- assignee: generalPurpose
- dependencies: TASK-184, TASK-185, TASK-186
- location: `/Users/kenjipcx/SOTA/0xDriver`
- enter when: single-route run, reasoning, and demo export commands exist.
- leave when: `oodrive f2d-evaluate-model` runs or plans a batch of existing/custom Fail2Drive scenarios and summarizes how an agent reacts.
- blockers: live batch evaluation requires CARLA runtime and selected agent/model assets.
- spawned follow-ups:
- complexity: L

### Description
Add a batch-level OODrive command for evaluating a model or agent against a selected set of Fail2Drive routes, then summarizing route results, failure modes, reasoning coverage, video availability, and blockers. This is the endpoint-like surface for "show me how this model reacts to rare scenarios."

### Goal
Give judges and operators a compact matrix over multiple bad-path examples: route blocked, pedestrian crowd, dynamic crossing, accident, custom obstacle, and compound route.

### Plan
#### Change
Add `oodrive f2d-evaluate-model --routes <xml-or-folder> --agent ... --reason --demo-video --limit <n>`.

#### Why
A single hero clip is not enough to show breadth. A 90th-percentile submission should show a repeatable evaluation harness over existing Fail2Drive scenarios and OODrive-authored scenarios.

#### Before -> After
- Before: each route must be run and reasoned manually.
- After: one command produces a ranked matrix of route outcome, scenario type, model reaction, evidence quality, and demo artifact paths.

#### Touch
- `src/driverx/fail2drive/model_reaction.py`
- `src/driverx/fail2drive/run_wrapper.py`
- `src/driverx/fail2drive/reasoning.py`
- `src/driverx/fail2drive/demo_video.py`
- `src/driverx/evaluation/commission_readiness_score.py` if batch evidence should feed final scoring
- `src/driverx/scenarios/studio_product_fail2drive_cli.py`
- `tests/test_fail2drive_model_reaction.py`
- `README.md`
- `docs/HISTORY.md`

#### Inspect
- `third_party/fail2drive/fail2drive_split/`
- `third_party/fail2drive/tools/f2d_result_parser.py`
- `src/driverx/evaluation/commission_readiness_score.py`
- `autoresearch.sh`
- `autoresearch.md`

#### Signature delta
- `driverx.fail2drive.model_reaction / discover_fail2drive_routes(routes: tuple[Path, ...], *, limit: int | None) -> list[Path]`
- `driverx.fail2drive.model_reaction / run_fail2drive_model_reaction_suite(config: Fail2DriveModelReactionConfig) -> Fail2DriveModelReactionSuite`
- `driverx.fail2drive.model_reaction / write_fail2drive_model_reaction_report(run_dir: Path, suite: Fail2DriveModelReactionSuite) -> dict[str, Any]`

#### Type Sketch
```python
@dataclass(frozen=True)
class Fail2DriveModelReactionCase:
    route_path: Path
    scenario_types: tuple[str, ...]
    run_status: str
    driving_score: float | None
    route_completion: float | None
    reasoning_event_count: int
    demo_video_path: Path | None
    blockers: tuple[str, ...]

@dataclass(frozen=True)
class Fail2DriveModelReactionSuite:
    cases: tuple[Fail2DriveModelReactionCase, ...]
    metrics: dict[str, float]
    claim_boundaries: dict[str, bool]
```

#### Typed flow example
`fail2drive_split/RoadBlocked_*.xml + custom OODrive route.xml` -> dry-run or live per-route plan -> evidence bundle -> optional fake/cached/Alpamayo reasoning -> optional demo video -> `model_reaction_matrix.json` and `METRIC f2d_model_reaction_coverage=<score>`.

#### Execution steps
1. Discover route XMLs from files or folders, with include/exclude scenario-type filters.
2. Validate each route and summarize scenario types.
3. For each route, call TASK-184 run wrapper in dry-run or live mode.
4. Optionally call TASK-185 reasoning and TASK-186 demo export when evidence exists.
5. Emit a matrix JSON/Markdown with case status, blockers, metrics, and artifact paths.
6. Add an autoresearch metric for coverage/readiness: validated route count, scenario family diversity, evidence completeness, reasoning coverage, video coverage.
7. Add tests using fixture routes and fake evidence.

#### Recommendation
Make this the final submission harness, but keep it honest: a blocked live route still appears in the matrix with exact blockers instead of disappearing.

#### Options considered
- Only show one hero video: strong but narrow.
- Full Fail2Drive leaderboard run: better benchmark, but too heavy for the immediate submission window.
- Small curated model-reaction suite: recommended because it proves breadth and can run progressively.

#### Blast radius
Batch orchestration touches several new Fail2Drive modules and `autoresearch.sh`. Keep live execution opt-in and default to dry-run/fixture-safe behavior.

#### Risks
- Batch runs can take too long if live by default; require explicit `--live`.
- Metrics can incentivize artifact quantity over clarity; include video/readability and reasoning coverage gates.

### Gap Analysis
The submission needs more than "we can make one scenario." It needs a convincing harness story: generate or select rare scenarios, run an agent, attach reasoning, and produce evidence. This ticket ties the lane together.

### Acceptance Criteria
- [ ] AC-1: `oodrive f2d-evaluate-model` discovers and validates multiple route XML files.
- [ ] AC-2: Dry-run suite emits per-route evaluator plans and blockers without CARLA.
- [ ] AC-3: Optional reasoning/video phases are invoked only when requested and recorded per case.
- [ ] AC-4: Suite report includes scenario diversity, evidence completeness, reasoning coverage, video coverage, and claim boundaries.
- [ ] AC-5: `autoresearch.sh` or `autoresearch.checks.sh` records a Fail2Drive readiness metric once implementation is complete.

### Agent Contract
- Open: `src/driverx/fail2drive/run_wrapper.py`, `src/driverx/evaluation/commission_readiness_score.py`, `autoresearch.sh`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_model_reaction`
- Stabilize: dry-run mode must be deterministic and fast.
- Inspect: model reaction matrix JSON/Markdown.
- Key screens/states: optional demo video contact sheet.
- QA cookbook: run a 3-route fixture suite and verify matrix rows.
- Taste refs: scoreboard with blockers visible, not hidden.
- Expected artifacts: `model_reaction_matrix.json`, `.md`, optional per-case evidence dirs.
- Delegate with: qa-tester for final matrix proof.

### Verification
- `PYTHONPATH=src python3 -m oodrive f2d-evaluate-model --routes tests/fixtures/fail2drive_routes --fail2drive-root third_party/fail2drive --agent pdm-lite --dry-run --limit 3 --run-id task187-f2d-batch-dry --metric-only`
- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_model_reaction tests.test_fail2drive_run_wrapper tests.test_oodrive_cli`
- `./autoresearch.checks.sh`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- Inputs: route folder, Fail2Drive root, optional agent checkpoint, optional CARLA host.
- Permissions: local artifact writes; live evaluator only with `--live`.
- Compute: dry-run CPU; live batch can be GPU/CARLA-heavy and long-running.
- External services: optional Alpamayo/model cache.
- Human gates: live Kasm runtime if local CARLA unavailable; no secrets through proxy heredocs.
- QA risks: batch partial failures are expected and must remain visible.

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
- Implemented `driverx.fail2drive.model_reaction` and `oodrive f2d-evaluate-model`.
- Smoke metric: `METRIC f2d_model_reaction_coverage=45.5` on two fixture routes.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS

### Blockers
