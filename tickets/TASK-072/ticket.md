# TASK-072: DriverX CARLA Scripted OOD Demo Runner

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-064, TASK-066, TASK-071
- location: `src/driverx/simulators`, `src/driverx/pipeline`, `configs/`, tests,
  `tickets/TASK-072/artifacts`
- enter when: local CARLA 0.9.16 is running and the submission needs a long
  judge-visible OOD simulator artifact
- leave when: one command spawns a generated OOD scene in CARLA, records RGB
  frames and entity tracks for at least 20 simulated seconds or a configured
  frame count, and writes a reproducible evidence bundle
- blockers: live run requires local CARLA responsiveness; implementation can
  proceed with fake-CARLA tests without a running simulator
- spawned follow-ups: TASK-073, TASK-074, TASK-076
- complexity: L

### Summary
Build a DriverX-owned CARLA demo runner that avoids the slow stock Fail2Drive
scoring loop. It should compile generated scenario recipes and regional
behavior traces into live CARLA actors, record camera frames and entity tracks,
and produce a long enough video substrate for the final submission.

### Scope
- In scope: spawned ego vehicle, RGB camera, generated OOD actors from behavior
  traces, simple ego motion/autopilot or conservative scripted controls,
  weather/map selection, entity tracks, RGB frame capture, evidence reports.
- Out of scope: full Fail2Drive score, Alpamayo live inference, Meshy/custom
  asset import, official leaderboard claims.

### Gap Analysis
- Current state: TASK-071 gives a 0.5s stock Fail2Drive video because it stops
  after five frames; TASK-064 gives a complete local 2D simulation but not a
  CARLA scene.
- Production expectation: the submission needs a visible simulation environment
  with randomized OOD cases, not only dry-run plans or partial route frames.
- Missing gaps: long CARLA run control, DriverX-owned actor spawn/tick loop,
  frame recording independent of Fail2Drive evaluator, and per-actor tracks
  aligned to the video.
- Comparable implementations: CARLA ScenarioRunner and Fail2Drive both separate
  scenario definition from execution artifacts; DriverX should mirror that with
  recipe/script/evidence boundaries while using a smaller custom runner.
- Recommendation: implement a lightweight scripted demo runner now and keep
  stock Fail2Drive scoring as TASK-060 follow-up.

### Plan

#### Change
Add `run-carla-ood-demo` that consumes a scenario recipe or generates one from
fixtures, applies a selected regional behavior trace, spawns actors in CARLA,
records RGB frames, writes entity tracks, and produces `carla_ood_demo.json` and
`carla_ood_demo.md`.

#### Why
This unblocks a real 20-30s CARLA video without waiting on the Mac/Wine
Fail2Drive synchronous route evaluator.

#### Before -> After
- Before: visible CARLA evidence is a 0.5s partial stock route MP4; long OOD
  behavior exists only in local 2D artifacts.
- After: a DriverX-generated OOD scene runs directly in CARLA and creates
  enough frames/tracks for a judge-facing long video.

#### Touch
- `src/driverx/simulators/carla_ood_demo.py`: new live/fake runner and result
  writer.
- `src/driverx/simulators/carla_ood_demo_cli.py`: CLI registration helpers.
- `src/driverx/simulators/carla_script.py`: reuse or extend script-plan actor
  conversion.
- `src/driverx/simulators/route_video_assembly.py`: reuse frame assembly.
- `src/driverx/behaviors/library.py`: consume existing behavior traces.
- `src/driverx/pipeline/end_to_end_ood_demo.py`: optional input artifact reuse.
- `src/driverx/cli.py`, `src/driverx/simulators/__init__.py`.
- `configs/carla_ood_demo.local.sample.yaml`.
- `tests/test_carla_ood_demo.py`.
- `README.md`, `ARCHITECTURE.md`, `docs/progress.md`, `blockers.md`.

#### Inspect
- `src/driverx/simulators/carla_alpamayo_capture.py` for CARLA client, sensors,
  image queues, and cleanup patterns.
- `src/driverx/simulators/carla_injection.py` for actor spawn/tick/track
  helpers.
- `src/driverx/simulators/local_ood_sim.py` for risk summaries.
- `tickets/TASK-071/artifacts/town13-early-route-evidence/run_evidence.md` for
  current short-video limit.

#### Signature Delta
```python
src/driverx/simulators/carla_ood_demo.py / run_carla_ood_demo(config: CarlaOodDemoConfig, run_dir: Path, *, carla_module: object | None = None) -> CarlaOodDemoResult
src/driverx/simulators/carla_ood_demo.py / write_carla_ood_demo(run_dir: Path, result: CarlaOodDemoResult) -> dict[str, Any]
src/driverx/simulators/carla_ood_demo.py / build_carla_ood_demo_plan(recipe: ScenarioRecipe, behavior: BehaviorTrace, config: CarlaOodDemoConfig) -> CarlaOodDemoPlan
```

#### Type Sketch
```python
CarlaOodDemoConfig = {
  "host": "host.docker.internal",
  "port": 2000,
  "timeout_s": 20.0,
  "map_name": "Town13",
  "tick_count": 300,
  "fps": 10,
  "camera_width": 1280,
  "camera_height": 720,
  "behavior_id": "motorcycle_filtering",
  "ego_mode": "autopilot" | "scripted",
  "cleanup": True,
}

CarlaOodDemoResult = {
  "status": "passed" | "partial" | "blocked" | "failed",
  "map_name": str | None,
  "recipe_id": str,
  "behavior_id": str,
  "frame_count": int,
  "duration_s": float,
  "tracks_path": str | None,
  "rgb_folder": str | None,
  "spawned_actor_ids": list[int],
  "destroyed_actor_ids": list[int],
  "blockers": list[str],
}
```

#### Typed Flow Example
`generated-base-animals-0076-regional-driving-behavior-000`
-> `motorcycle_filtering` behavior trace
-> `CarlaOodDemoPlan(ego, rgb_sensor, ood_motorcycle)`
-> live CARLA ticks write `rgb/frame_000001.png...`
-> `entity_tracks.json`
-> `carla_ood_demo.md` with duration, min distance, cleanup, and blockers.

#### Execution Steps
1. Implement dataclasses, plan builder, fake-CARLA compatible runner, and
   writer.
2. Reuse camera capture queue logic from Alpamayo capture, but write many frames
   under `rgb/`.
3. Spawn ego and OOD actor from the script plan; apply behavior trace transforms
   per tick.
4. Track ego and OOD actor transforms/velocities every tick.
5. Add CLI command with `--run-id`, `--config`, `--recipe`, `--behavior-id`,
   `--tick-count`, and `--frame-count`.
6. Add fake-CARLA unit tests for spawn, tick, track, frame-save, cleanup, and
   blocked import guidance.
7. Run one live local attempt through `scripts/run_carla_client_docker.sh` if
   CARLA is running; otherwise record a precise blocker and keep tests passing.

#### Recommendation
Prefer a DriverX scripted CARLA runner over another long stock Fail2Drive
attempt. It maximizes submission video value and minimizes dependency on the
slow Mac/Wine benchmark loop.

#### Options Considered
- Stock Fail2Drive long run: highest benchmark purity, but currently stalls or
  progresses too slowly for video production.
- Local 2D sim only: fastest, but not visually strong enough as the final demo.
- DriverX scripted CARLA runner: best balance of real simulator evidence,
  reproducibility, and speed.

#### Blast Radius
- CARLA-facing simulator modules and CLI command registry.
- Generated artifact paths under `artifacts/runs` or ticket artifacts.
- No policy/model behavior changes.

#### Risks
- Local CARLA may hang during live execution; fake-CARLA tests and partial
  evidence must still pass.
- Actor spawn points may collide; runner should fall back to map spawn points or
  record spawn blockers.
- Frame volume can get large; videos/RGB output remain ignored by git.

### Acceptance Criteria
- [ ] AC-1: `run-carla-ood-demo` has a fake-CARLA test path that requires no
  CARLA, Docker, GPU, or model weights.
- [ ] AC-2: Live or fake run writes `carla_ood_demo.json`,
  `carla_ood_demo.md`, `entity_tracks.json`, and an RGB folder or precise
  blocker.
- [ ] AC-3: A successful live run records enough frames for at least 20 seconds
  at the configured FPS, or explicitly reports the lower captured duration.
- [ ] AC-4: All spawned DriverX actors/sensors are destroyed unless
  `cleanup=false`.
- [ ] AC-5: Evidence labels this as DriverX scripted CARLA OOD demo, not stock
  Fail2Drive score and not VLA closed-loop control.

### Verification
- Focused:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_ood_demo`
- Regression:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_injection tests.test_carla_alpamayo_capture tests.test_route_video_assembly`
- Full gate:
  `bash scripts/pre_push_check.sh`
- Optional live proof:
  `bash scripts/run_carla_client_docker.sh python -m driverx run-carla-ood-demo --config configs/carla_ood_demo.local.sample.yaml --run-id task72-live`

### Autonomy Readiness
- Can proceed without user input for implementation and tests.
- Needs local CARLA running only for the optional live proof.
- If CARLA is unavailable or slow, write blocker evidence and continue to
  TASK-073 with fake/saved frame fixtures.

### Refs
- PRD FR-2, FR-3, FR-5, FR-8, FR-9.
- `docs/specs/minimal-shot-vla-roadmap.md` TASK-010 through TASK-014.
- `MEM-0012`, `MEM-0018`, `MEM-0020`.

### Evidence
- Planning created 2026-05-06 18:16 +0800.
- Review: `docs/reviews/TASK-072-077-impl-plan-review.md`.
- Implementation review: `docs/reviews/TASK-072-077-implementation-review.md`.
- Build: `src/driverx/simulators/carla_ood_demo.py`,
  `src/driverx/simulators/carla_ood_demo_cli.py`,
  `configs/carla_ood_demo.local.sample.yaml`, and
  `tests/test_carla_ood_demo.py`.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_ood_demo tests.test_carla_asset_mapping`.
- Live attempt:
  `tickets/TASK-072/artifacts/task72-live-candidate/carla_ood_demo.md`.

### Blockers
- Optional live proof depends on local CARLA staying responsive. The latest
  Docker client attempt timed out waiting for `host.docker.internal:2000`, so
  no live RGB frames were captured.
