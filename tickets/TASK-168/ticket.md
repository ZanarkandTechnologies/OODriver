# TASK-168: Behavior Simulation Videos For Selected CARLA Suite Cases

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-166, TASK-167
- location: `src/driverx/scenarios`, `src/driverx/simulators`, `src/driverx/pipeline`, `artifacts/runs`, `tests`
- enter when: the 10-case suite has live snapshots and at least three cases look visually distinct enough for behavior simulation.
- leave when: at least three selected cases run through CARLA behavior/object simulation, produce MP4s or frame folders, and expose static/moving hazard tracks plus driver response/action overlays.
- blockers: live CARLA and video assembly dependencies; closed-loop Alpamayo remains out of scope unless TASK-160 has passed.
- spawned follow-ups: final submission reel and optional Alpamayo keyframe analysis.
- complexity: M
- assignee: generalPurpose

### Description
Take the best visual suite cases and run them as actual CARLA behavior scenarios: moving cut-in, static lane blocker, rolling object, and compound obstruction. Produce short clips that show what enters, what blocks, and how the scripted/agent driver responds.

### Goal
Move from “here are generated environments” to “here are generated environments with driving behavior simulation.”

### Acceptance Criteria
- [ ] AC-1: At least three selected suite cases run with `backend=carla-live` or a documented local fallback.
- [ ] AC-2: Each run records spawned object ids, dynamic actor ids, entity tracks, RGB frames, and cleanup ids.
- [ ] AC-3: Each case labels static versus moving hazards and expected safe behavior: stop, slow, swerve-within-lane, yield, or replan/detour.
- [ ] AC-4: At least one MP4/contact sequence shows a moving object entering/crossing and one shows a static blocker.
- [ ] AC-5: `closed_loop_vla_control=false` remains unless live Alpamayo controls are actually applied.

### Agent Contract
- Open: `src/driverx/scenarios/studio_product_generated_runtime.py`, `src/driverx/simulators/carla_ood_demo.py`, `src/driverx/simulators/carla_ood_fidelity.py`, `src/driverx/simulators/carla_overlay_evidence.py`, `tests/test_generated_carla_runtime.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_generated_carla_runtime tests.test_carla_scenario_composer`
- Stabilize: keep lane-alignment and visibility gates strict; do not promote off-road-looking videos.
- Inspect: MP4s, frame folders, `entity_tracks.json`, `carla_ood_demo.json`, road alignment report.
- QA cookbook: run one moving and one static case locally/fake, then live on Kasm, score runtime.
- Expected artifacts: per-case MP4, `entity_tracks.json`, `carla_ood_demo.json`, road alignment report, summary reel manifest.

### Plan

#### Change
Add a suite-case-to-live-runtime workflow and select 3-4 cases for behavior video.

#### Why
Judges need to see not only environment appearance but actual scenario dynamics.

#### Before -> After
- Before: snapshots show scene variety.
- After: short videos show moving/static hazards and driver response evidence.

#### Touch
- `src/driverx/scenarios/studio_product_carla_composer_runtime.py`
- `src/driverx/scenarios/studio_product_generated_runtime.py`
- `src/driverx/simulators/carla_ood_demo.py`
- `src/driverx/pipeline/oodrive_suite_video_reel.py` (new if stitching is needed)
- `tests/test_generated_carla_runtime.py`

#### Signature Delta
- `select_suite_cases_for_video(snapshot_manifest: dict, limit: int = 4) -> list[str]`
- `run_studio_carla_suite_videos(suite_manifest_path: Path, case_ids: tuple[str, ...], backend: str, output_root: Path | None, run_id: str) -> StudioCommandResult`

#### Type Sketch
```python
SuiteVideoCase = {
  "case_id": str,
  "runtime_manifest_path": str,
  "video_path": str | None,
  "rgb_folder": str | None,
  "tracks_path": str | None,
  "static_hazard_count": int,
  "moving_actor_count": int,
  "driver_response_labels": list[str],
  "claim_boundaries": list[str]
}
```

#### Typed Flow Example
Snapshot-approved `case-04-static-blocker` -> live generated runtime -> RGB/tracks -> assemble MP4 -> summary row with static blocker and slow/stop label.

#### Execution Steps
1. Select cases from snapshot manifest.
2. Generate live runtime commands from each case manifest.
3. Run Kasm CARLA live behavior simulations.
4. Assemble MP4s from RGB folders.
5. Score runtime artifacts and lane/visibility status.
6. Write suite video manifest.
7. Update docs/tickets with exact artifact links.

#### Recommendation
Use 3-4 best cases, not all 10, for videos. Snapshots cover breadth; videos cover dynamics.

#### Options Considered
- Video all 10: too slow and noisy.
- Video 3-4 best cases: recommended; enough proof for judges.
- Skip videos and use snapshots only: weak for “vehicle navigating” challenge wording.

#### Blast Radius
Live artifact production; source changes mostly orchestration.

#### Risks
- Behavior actors may spawn poorly on some anchors. Use the snapshot score and road alignment to select cases.

### Verification
- `PYTHONPATH=src python3 -m oodrive carla-suite-videos --suite-manifest <...> --case-id <...> --backend carla-live`
- `PYTHONPATH=src python3 -m oodrive score-generator-runtime --runtime-manifest <...> --metric-only`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- External host: Kasm CARLA.
- Runtime dependencies: CARLA Python venv, ffmpeg/Pillow for MP4 assembly.
- Human gate: promote only road-aligned videos.

### Evidence
- Per-case MP4s
- Runtime manifests
- Track files
- Road-alignment reports
- Claim-boundary matrix
- Planning review: `tickets/TASK-166/artifacts/review/task166-169-plan-review.json`
