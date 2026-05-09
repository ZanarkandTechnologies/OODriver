# TASK-186: Fail2Drive Judge Demo Video Export

## Status
- state: building
- owner: OODrive
- assignee: generalPurpose
- dependencies: TASK-184, TASK-185, TASK-130
- location: `/Users/kenjipcx/SOTA/0xDriver`
- enter when: Fail2Drive run evidence and reasoning timeline exist.
- leave when: `oodrive f2d-demo-video` exports a judge-visible MP4/report that explains the route, behavior, reasoning, and claim boundaries.
- blockers: source RGB frames or video required for real MP4; local tests may use fixture video.
- spawned follow-ups:
- complexity: L

### Description
Create a Fail2Drive-specific demo video exporter that overlays route context, scenario type, frame/time, route result, risk, Alpamayo reasoning, and claim labels. The output should make bad-path examples understandable without a narrator.

### Goal
Produce a 1-5 minute submission-ready clip segment or reel from Fail2Drive route evidence, with a scoring report that prevents unreadable HUD clutter.

### Plan
#### Change
Add `oodrive f2d-demo-video --evidence <run_evidence.json> --reasoning <f2d_reasoning.json> --route <route.xml>`.

#### Why
The current videos can be visually confusing. For a 90th-percentile submission, judges need to see the scenario, the vehicle response, and model reasoning at the same time without decoding raw logs.

#### Before -> After
- Before: route video, evaluator results, and reasoning snippets are separate artifacts.
- After: one MP4 plus JSON report shows the Fail2Drive scenario and model explanation timeline clearly.

#### Touch
- `src/driverx/fail2drive/demo_video.py`
- `src/driverx/simulators/reasoning_timeline_overlay.py`
- `src/driverx/simulators/video_timewarp.py`
- `src/driverx/evaluation/hero_demo_score.py`
- `src/driverx/scenarios/studio_product_fail2drive_cli.py`
- `tests/test_fail2drive_demo_video.py`
- `docs/HISTORY.md`

#### Inspect
- `src/driverx/simulators/reasoning_timeline_overlay.py`
- `src/driverx/scenarios/studio_product_runtime.py`
- `src/driverx/evaluation/hero_demo_score.py`
- `artifacts/exported/task102_high_fidelity_hero_v6_full.mp4` as visual reference only.

#### Signature delta
- `driverx.fail2drive.demo_video / build_fail2drive_overlay_events(evidence: dict[str, Any], reasoning: dict[str, Any], route: ElementTree) -> list[ReasoningOverlayEvent]`
- `driverx.fail2drive.demo_video / run_fail2drive_demo_video(config: Fail2DriveDemoVideoConfig) -> dict[str, Any]`
- `driverx.fail2drive.demo_video / score_fail2drive_demo_report(report_path: Path) -> dict[str, Any]`

#### Type Sketch
```python
@dataclass(frozen=True)
class Fail2DriveDemoVideoConfig:
    evidence_path: Path
    reasoning_path: Path
    route_path: Path
    input_video_path: Path | None
    rgb_folder: Path | None
    speed_factor: float
    target_duration_s: float
    output_dir: Path

@dataclass(frozen=True)
class Fail2DriveDemoReport:
    video_path: Path
    overlay_report_path: Path
    scenario_count: int
    reasoning_event_count: int
    claim_boundaries: dict[str, bool]
    readability_score: float
```

#### Typed flow example
`run_evidence.json + f2d_reasoning.json + route.xml + source.mp4` -> time-warp video -> overlay events -> `f2d_hero_demo.mp4` + `f2d_demo_video.json` -> `METRIC f2d_demo_readability_score=...`.

#### Execution steps
1. Build overlay event conversion from Fail2Drive reasoning to existing OODrive overlay primitives.
2. Add a less-congested layout preset for Fail2Drive: route/scenario ribbon, one reasoning card, one risk/action line, claim footer.
3. Support both source MP4 and RGB folder inputs.
4. Emit a report with event coverage, frame/time coverage, duration, claim labels, and route result status.
5. Add a local fixture video/RGB test path that avoids heavy CARLA.
6. Add a mechanical readability metric: duration in range, event count, text density cap, frame/time coverage, claim-label presence.
7. Keep existing TASK-130 score-demo thresholds unchanged; add Fail2Drive-specific metric as additional gate, not replacement.

#### Recommendation
Make the overlay less busy than the current hero HUD. Judges should understand one thing per second: hazard, response, reasoning, evidence.

#### Options considered
- Use existing `demo-video` unchanged: too generic and currently congested for Fail2Drive route stories.
- Build a new video stack: unnecessary; reuse timewarp and overlay modules.
- Add Fail2Drive overlay profile: recommended.

#### Blast radius
Touches video overlay code. Must preserve existing `oodrive demo-video` outputs.

#### Risks
- Text readability is subjective; use mechanical proxies and sample screenshots.
- Missing video frames should produce a blocker report, not fake evidence.

### Gap Analysis
Winning submission evidence needs understandable bad-path demonstrations. Current artifacts often show motion without enough causal explanation. This ticket creates the judge-visible bridge from benchmark route to model reasoning.

### Acceptance Criteria
- [ ] AC-1: `oodrive f2d-demo-video` writes MP4 and JSON report from fixture video/RGB plus reasoning.
- [ ] AC-2: Report includes duration, frame/time coverage, scenario labels, reasoning event count, risk/action coverage, and claim boundaries.
- [ ] AC-3: MP4 overlay contains at least three reasoning snippets and three route/scenario context callouts when inputs contain them.
- [ ] AC-4: Readability metric emits `METRIC f2d_demo_readability_score=<score>`.
- [ ] AC-5: Missing video/RGB inputs produce a precise blocker instead of a promoted artifact.

### Agent Contract
- Open: `src/driverx/simulators/reasoning_timeline_overlay.py`, `src/driverx/simulators/video_timewarp.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_demo_video tests.test_reasoning_timeline_overlay`
- Stabilize: video tests should use tiny fixture frames.
- Inspect: MP4, overlay report, sampled screenshots.
- Key screens/states: start/mid/hazard/end frames.
- QA cookbook: inspect generated frames for legibility and non-overlap.
- Taste refs: low-density lower-third, persistent claim footer, no clutter wall.
- Expected artifacts: `f2d_hero_demo.mp4`, `f2d_demo_video.json`, `f2d_demo_readability.md`
- Delegate with: visual-qa if overlay layout changes substantially.

### Verification
- `PYTHONPATH=src python3 -m oodrive f2d-demo-video --evidence tests/fixtures/fail2drive_evidence/run_evidence.json --reasoning tests/fixtures/fail2drive_reasoning/f2d_reasoning.json --route tests/fixtures/fail2drive_routes/valid_roadblocked.xml --run-id task186-f2d-demo-fixture --metric-only`
- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_demo_video tests.test_reasoning_timeline_overlay tests.test_oodrive_cli`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- Inputs: run evidence, route XML, reasoning JSON, source video or RGB folder.
- Permissions: artifact writes and ffmpeg execution.
- Compute: CPU video encoding; live-quality exports can be slow.
- External services: none.
- Human gates: visual inspection before submission promotion.
- QA risks: automated readability does not replace checking actual rendered media.

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
- Implemented `driverx.fail2drive.demo_video` and `oodrive f2d-demo-video`.
- Smoke metric: `METRIC f2d_demo_readability_score=100.0` on fixture source video/reasoning.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS

### Blockers
