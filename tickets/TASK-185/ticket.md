# TASK-185: Fail2Drive Alpamayo Keyframe Reasoning

## Status
- state: building
- owner: OODrive
- assignee: generalPurpose
- dependencies: TASK-184, TASK-128/TASK-130 reasoning contracts
- location: `/Users/kenjipcx/SOTA/0xDriver`
- enter when: route evidence bundle exists from a Fail2Drive run or dry-run fixture.
- leave when: `oodrive f2d-reason` attaches keyframe-by-keyframe Alpamayo or cached reasoning to Fail2Drive evidence.
- blockers: live Alpamayo inference requires remote model/runtime; cached/fake mode must remain available for tests.
- spawned follow-ups:
- complexity: L

### Description
Add a Fail2Drive-specific reasoning command that samples route video frames or saved RGB frames, runs or imports Alpamayo reasoning, and writes a synchronized explanation timeline. Keep labels honest: this is sampled open-loop reasoning unless the model actually controls the Fail2Drive agent.

### Goal
Show judges what the model notices in rare Fail2Drive edge cases: road blocks, pedestrians, crossing objects, accidents, and compound hazards.

### Plan
#### Change
Add `oodrive f2d-reason --evidence <run_evidence.json> --route <route.xml> --mode cached|fake|alpamayo-local|alpamayo-remote`.

#### Why
The current demo story is too opaque. The submission needs explicit frame-level reasoning over hard scenarios, with latency and claim-boundary honesty.

#### Before -> After
- Before: Fail2Drive route results and OODrive Alpamayo reasoning live in separate lanes.
- After: a Fail2Drive route can produce a reasoning timeline with frame ids, source times, scenario context, risk, likely action, and latency.

#### Touch
- `src/driverx/fail2drive/reasoning.py`
- `src/driverx/scenarios/studio_product_fail2drive_cli.py`
- `src/driverx/scenarios/studio_product_keyframe_runtime.py`
- `src/driverx/scenarios/studio_product_runtime.py`
- `src/driverx/simulators/reasoning_timeline_overlay.py`
- `tests/test_fail2drive_reasoning.py`
- `docs/HISTORY.md`

#### Inspect
- `src/driverx/scenarios/studio_product_keyframe_runtime.py`
- `src/driverx/scenarios/studio_product_runtime.py`
- `src/driverx/evaluation/hero_demo_score.py`
- `src/driverx/simulators/reasoning_timeline_overlay.py`
- remote Alpamayo package/run helpers when live mode is attempted.

#### Signature delta
- `driverx.fail2drive.reasoning / build_fail2drive_reasoning_request(...) -> Fail2DriveReasoningRequest`
- `driverx.fail2drive.reasoning / run_fail2drive_reasoning(request: Fail2DriveReasoningRequest) -> Fail2DriveReasoningResult`
- `driverx.fail2drive.reasoning / write_fail2drive_reasoning(run_dir: Path, result: Fail2DriveReasoningResult) -> dict[str, Any]`

#### Type Sketch
```python
@dataclass(frozen=True)
class Fail2DriveKeyframe:
    frame_index: int
    source_time_s: float
    image_path: Path | None
    route_scenario: str | None
    ego_state: dict[str, object]

@dataclass(frozen=True)
class Fail2DriveReasoningEvent:
    keyframe: Fail2DriveKeyframe
    risk_level: str
    observation: str
    predicted_action: str
    rationale: str
    latency_ms: float | None
    source: str  # fake | cached | alpamayo-local | alpamayo-remote
```

#### Typed flow example
`run_evidence.json + RGB frames` -> sample 8 keyframes around hazard windows -> cached/Alpamayo inference -> `f2d_reasoning.json` -> overlay events for TASK-186.

#### Execution steps
1. Read `run_evidence.json` and route XML to recover video/RGB paths and scenario labels.
2. Add deterministic frame sampling from video metadata or RGB folder names.
3. Support `fake` and `cached` modes for local tests; keep live modes behind explicit flags.
4. Reuse existing Alpamayo reasoning payload format when possible.
5. Emit per-frame latency fields and claim boundaries.
6. Include at least three reasoning snippets and three scenario/RAG/memory callouts when source data supports it.
7. Add tests using fixture frames/reasoning payloads.

#### Recommendation
Prioritize clean reasoning reports before live Alpamayo. The live model is valuable, but the submission fails if the explanation timeline is unreadable.

#### Options considered
- Put all reasoning directly in video overlay code: rejected because it makes reuse and testing harder.
- Only use final route result scores: insufficient for minimal-shot reasoning proof.
- Separate reasoning timeline artifact: recommended.

#### Blast radius
Touches reasoning and overlay inputs. Must preserve existing `oodrive reason` behavior.

#### Risks
- Live Alpamayo latency is high; reports must show time-warped/offline status clearly.
- Video/frame paths from Fail2Drive may vary by evaluator settings.

### Gap Analysis
The product currently proves some Alpamayo frame reasoning over CARLA captures, but not cleanly attached to Fail2Drive scenario evidence. This ticket connects benchmark route evidence to the reasoning story judges need to understand.

### Acceptance Criteria
- [ ] AC-1: `oodrive f2d-reason` writes JSON and Markdown reasoning reports from fixture evidence.
- [ ] AC-2: Each event contains frame index, source time, scenario context, risk, observation, predicted action, rationale, source, and latency fields.
- [ ] AC-3: Output claim boundaries include `sampled_open_loop_reasoning=true`, `time_warped_offline_demo=true`, and no false closed-loop claim.
- [ ] AC-4: Cached/fake mode passes locally without model weights.
- [ ] AC-5: Live mode blockers are logged with exact missing path/env/runtime fields.

### Agent Contract
- Open: `src/driverx/scenarios/studio_product_keyframe_runtime.py`, `src/driverx/simulators/reasoning_timeline_overlay.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_reasoning`
- Stabilize: fixture mode must be deterministic.
- Inspect: reasoning JSON/Markdown.
- Key screens/states: keyframe images if available.
- QA cookbook: verify at least 3 events and claim boundary labels.
- Taste refs: concise explanations that fit later video lower-third panels.
- Expected artifacts: `f2d_reasoning.json`, `f2d_reasoning.md`
- Delegate with: runtime-debugging only for live model execution failures.

### Verification
- `PYTHONPATH=src python3 -m oodrive f2d-reason --evidence tests/fixtures/fail2drive_evidence/run_evidence.json --route tests/fixtures/fail2drive_routes/valid_roadblocked.xml --mode fake --run-id task185-f2d-reason-fake`
- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_reasoning tests.test_reasoning_timeline_overlay tests.test_oodrive_cli`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- Inputs: route evidence, route XML, frames/video, optional Alpamayo runtime.
- Permissions: local artifact writes; remote model only when explicitly selected.
- Compute: fixture CPU; live model GPU recommended.
- External services: Hugging Face/model cache may be required for live Alpamayo.
- Human gates: secrets must not be sent through Kasm proxy heredocs.
- QA risks: cached mode can look stronger than live mode; reports must label source.

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
- Implemented `driverx.fail2drive.reasoning` and `oodrive f2d-reason`.
- Smoke metric: `METRIC f2d_reasoning_event_count=3`.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS for missing cached/live inputs; live Alpamayo runtime not executed.

### Blockers
