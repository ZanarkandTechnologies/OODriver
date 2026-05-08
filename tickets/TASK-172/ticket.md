# TASK-172: Live CARLA Choreography Video Gate

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-167, TASK-171
- location: `src/driverx/scenarios`, `src/driverx/simulators`, `src/driverx/pipeline`, `tests`, `artifacts/runs`
- enter when: TASK-171 has a replayable choreography manifest and TASK-167 has live snapshot proof.
- leave when: at least three choreography cases run in live CARLA, produce videos/tracks, and pass a video/evidence score without closed-loop overclaims.
- blockers: requires Kasm CARLA host, ffmpeg/Pillow, and stable road anchors.
- spawned follow-ups: TASK-173 final judge demo pack.
- complexity: L
- assignee: generalPurpose

### Summary
Promote choreography from local/fake proof to live CARLA behavior videos. The videos should show bad-path dynamics: static blocker, moving cut-in, rolling object, and compound obstruction.

### Scope
In scope:
- Product commands: `oodrive choreograph-video` and `oodrive score-choreography-video`.
- Consumption of a TASK-171 `choreography_manifest.json` as the single source of truth.
- Live CARLA execution when the Kasm host is available, with a deterministic `fake-carla` fallback only for local contract tests.
- Per-case MP4/frame folders, entity tracks, cleanup ids, contact sheet, and video manifest.
- A mechanical `choreography_video_score` gate that rejects missing media, invisible hazards, off-road-looking routes, weak duration, and claim-boundary drift.

Out of scope:
- Meshy/custom blueprint import. That remains TASK-170.
- Closed-loop Alpamayo claim upgrades. TASK-172 may show scripted safe responses unless a true model-driven recurrence is attached by a separate closed-loop ticket.
- Final narrative packaging. That is TASK-173.

### Plan

#### Change
Build a video runner that turns a choreography manifest into selected live CARLA case captures and a scorer that decides whether those captures are judge-visible enough to promote.

#### Why
The submission needs to show concrete bad-path examples, not only a scenario JSON. A real-world implementer wants to see the car/hazard relationship frame by frame: stop for a blocker, slow/yield for a cut-in, recover from a rolling object, and replan around a compound obstruction.

#### Before -> After
- Before: TASK-171 proves the timed bad-path contract locally with fake-CARLA tracks.
- After: TASK-172 produces live CARLA media and a scored manifest for at least three cases, while preserving honest non-closed-loop labels unless model control is actually wired.

#### Touch
- `src/driverx/scenarios/studio_product_choreography_video_runtime.py` new runtime.
- `src/driverx/scenarios/studio_product_choreography_video_cli.py` new CLI registration.
- `src/driverx/scenarios/studio_product_cli.py` register commands.
- `src/driverx/simulators/carla_scenario_runner.py` or `src/driverx/simulators/carla_control.py` consume per-case map/weather/anchor/object specs.
- `src/driverx/evaluation/choreography_video_score.py` new score.
- `tests/test_choreography_video.py` contract tests.
- `tests/test_oodrive_cli.py` command registration.

#### Inspect
- `src/driverx/scenarios/choreography.py`
- `src/driverx/scenarios/generated_runtime.py`
- `src/driverx/simulators/carla_scenario_runner.py`
- `src/driverx/simulators/carla_control.py`
- `src/driverx/evaluation/closed_loop_video_score.py`
- `src/driverx/evaluation/environment_reasoned_carla_score.py`

#### Signature Delta
- `run_studio_choreography_video(choreography_manifest_path: Path, case_ids: tuple[str, ...], backend: str, run_id: str, output_root: Path | None) -> StudioCommandResult`
- `render_choreography_case_video(case: dict, backend: Literal["carla-live", "fake-carla"], output_dir: Path) -> dict`
- `score_choreography_video(inputs: ChoreographyVideoScoreInputs, threshold: float = 90.0) -> ChoreographyVideoScoreReport`

#### Type Sketch
```python
ChoreographyVideoManifest = {
  "schema_version": "oodrive.choreography_video.v1",
  "source_choreography_manifest": str,
  "backend": "carla-live|fake-carla",
  "cases": [{
    "case_id": str,
    "video_path": str,
    "frame_dir": str,
    "track_path": str,
    "visible_hazard": bool,
    "static_hazard": bool,
    "moving_hazard": bool,
    "response_labels": list[str],
    "cleanup_ids": list[int],
    "claim_boundaries": list[str]
  }],
  "contact_sheet_path": str,
  "claim_boundaries": list[str]
}
```

#### Typed Flow Example
`task171-choreography-v2/choreography_manifest.json` -> select `static-blocker-stop-creep`, `moving-cut-in-slow-yield`, `rolling-object-avoid` -> run CARLA map/weather/anchor capture -> write MP4/frame folders/tracks -> score `visible_hazard`, `duration`, `motion`, `road_alignment`, `cleanup`, and claims -> pass at `>=90`.

#### Execution Steps
1. Add CLI/runtime skeleton and fake-CARLA contract path.
2. Map TASK-171 case records to CARLA runner inputs without introducing a second scenario schema.
3. Write a video manifest with per-case media, tracks, cleanup ids, and claim labels.
4. Add score module with hard blockers for missing MP4/frame evidence, fewer than three cases, missing static+moving hazards, missing response labels, off-road/lane-departure flags, and closed-loop overclaims.
5. Add unit tests for contract path, score pass/fail, and CLI registration.
6. Run local fake-CARLA contract tests.
7. Run Kasm live CARLA for at least three cases when host is available.
8. Attach MP4/contact-sheet/score evidence to this ticket.

#### Recommendation
Implement the local manifest/score contract first, then immediately run the Kasm live backend. The live backend is the completion gate; the fake backend is only a regression harness.

#### Options Considered
- Build a hand-edited video reel: visually fast, but not agent-operable or reproducible.
- Extend `carla-suite`: good for static diversity, but weak for timed behaviors.
- New `choreograph-video` command: recommended because it preserves the TASK-171 contract and gives judges concrete bad-path clips.

#### Blast Radius
Adds new CLI/evaluation paths and consumes CARLA runner modules. Existing `choreograph`, `carla-suite`, and closed-loop commands should remain unchanged.

#### Risks
- Kasm CARLA proxy may drop sessions; write outputs incrementally and pull artifacts case-by-case.
- Installed CARLA blueprints may vary; use capability-matrix-probed stock proxies and label proxy fallback.
- Live videos may look weak if camera framing is poor; scorer must block invisible hazards instead of accepting metadata-only proof.

### Acceptance Criteria
- [ ] AC-1: `oodrive choreograph-video` consumes a TASK-171 manifest and selected case ids.
- [ ] AC-2: At least three cases produce live CARLA video or frame folders, entity tracks, and cleanup ids.
- [ ] AC-3: Video score verifies visible hazard, moving/static actor evidence, response label, duration, road alignment, and claim boundaries.
- [ ] AC-4: Claims preserve `closed_loop_vla_control=false` unless a true model-driven loop is attached.

### Verification
- `PYTHONPATH=src python3 -m oodrive choreograph-video --choreography-manifest <...> --backend carla-live`
- `PYTHONPATH=src python3 -m oodrive score-choreography-video --video-manifest <...> --metric-only`
- `bash scripts/pre_push_check.sh`

### Evidence
- MP4/frame folders
- Entity tracks
- Video score JSON
- Contact sheet/reel
- Review artifact
