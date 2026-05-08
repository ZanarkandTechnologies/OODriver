# TASK-140: Bad-Path Stress Demo Pack

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-131, TASK-135, TASK-136
- location: `src/driverx/pipeline`, `src/driverx/scenarios`, `src/oodrive`, `tests`, `tickets/TASK-140`
- enter when: OODrive has strong happy-path hero/video artifacts, but the user cannot see concrete unsafe edge cases where the vehicle must stop, swerve, slow, and recover.
- leave when: `oodrive stress-demo` produces four bad-path task examples with bad baseline vs guarded response telemetry, pass/fail metrics, HTML/JSON report, and MP4 when local media tooling is available.
- blockers: the stress reel is a local 2D scripted proof, not CARLA visual evidence; CARLA replay remains owned by the generator/runtime lane.
- spawned follow-ups: TASK-141 generator-to-CARLA behavior/object runtime.
- complexity: M

### Description

Create a demo pack made entirely of adversarial driving tasks instead of happy paths. The selected cases are: static object appears in the lane, road hole/pothole forces a swerve and recovery, rolling/moving object crosses into the ego path, and a compound case requiring stop, replan, detour, slow-through, and recovery.

### Goal

Make the submission legible to a real-world autonomy implementer by showing not just "weird scene exists," but the actual safety response: stop, swerve, slow, yield, and continue only when clear.

### Acceptance Criteria

- [x] AC-1: `oodrive stress-demo --help` exists.
- [x] AC-2: The command writes `bad_path_stress_demo.json`, `bad_path_stress_demo.md`, and `bad_path_stress_demo.html`.
- [x] AC-3: The pack includes exactly four default cases: static blocker stop, road hole swerve/recover, rolling collision-course object, and compound obstacle detour.
- [x] AC-4: Each case records bad baseline collision proxy plus guarded response telemetry for speed, throttle, brake, steer, distance, and decision state.
- [x] AC-5: Each guarded case avoids the collision proxy and satisfies its task-specific behavior: stop before blocker, swerve past hole and continue, slow/swerve for rolling object and resume.
- [x] AC-6: MP4 rendering runs when ffmpeg/Pillow are available and blocks cleanly otherwise.
- [x] AC-7: Claim labels remain honest: local scripted stress proof, not closed-loop Alpamayo or real-time VLA control.
- [x] AC-8: Guarded traces cannot pass if they leave the drivable corridor.

### Agent Contract

- Open: `src/driverx/simulators/local_ood_sim.py`, `src/driverx/scenarios/studio_product_cli.py`, `tests/test_oodrive_cli.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_bad_path_stress_demo tests.test_oodrive_cli`
- Stabilize: keep generated videos under ignored `artifacts/`; do not promote as CARLA evidence.
- Inspect: bad baseline collision proxy, guarded response task metrics, claim boundaries, renderer blocker paths.
- Expected artifacts: `artifacts/runs/task140-bad-path-stress-v1/bad_path_stress_demo.json`, `.md`, `.html`, optional `.mp4`

### Build Notes

- Use local deterministic top-down simulation first so the cases can be picked quickly.
- The video should be a stress reel, not a marketing reel: show baseline failure and guarded behavior with controls and distances in frame.
- Correct the rolling-object guarded response before claiming local stress proof: focused tests currently show the rolling object case has `guarded.collision_proxy=true`, `task_pass=false`, and local score `76.6667`.
- Keep CARLA replay separate from the local stress pack; TASK-141 turns the approved behavior/object cases into generator runtime specs and CARLA spawn proof.
- Implemented as `oodrive stress-demo`, defaulting to all four bad-path tasks.
- Generated artifact: `artifacts/runs/task140-bad-path-stress-v3-lane-safe-001/bad_path_stress_demo.mp4`.
- Local score: `bad_path_stress_score=100.0`.
- Lane-safety correction: v3 tightened the road-hole, rolling-object, and compound-detour lateral offsets from off-road-looking values to an adjacent-lane-style corridor and added `lane_departure_proxy` plus `max_abs_y_m` metrics to the manifest.

### Required Evidence

- [x] Focused tests pass.
- [x] `oodrive stress-demo` command output linked.
- [x] MP4 path or renderer blocker recorded.
- [x] Review before completion claim.

### Verification

- PASS: `PYTHONPATH=src python3 -m unittest tests.test_bad_path_stress_demo tests.test_oodrive_cli` ran 14 tests OK for the initial three-case pack.
- PASS: `PYTHONPATH=src python3 -m oodrive stress-demo --run-id task140-bad-path-stress-v1 --target-duration-s 60 --fps 8`
- PASS: `PYTHONPATH=src python3 -m unittest tests.test_bad_path_stress_demo tests.test_oodrive_cli` ran 15 tests OK after the compound case.
- PASS: `PYTHONPATH=src python3 -m oodrive stress-demo --run-id task140-bad-path-stress-v2 --target-duration-s 72 --fps 8`
- PASS: `PYTHONPATH=src python3 -m unittest tests.test_bad_path_stress_demo` ran 6 tests OK after adding lane-departure checks.
- PASS: `PYTHONPATH=src python3 -m oodrive stress-demo --run-id task140-bad-path-stress-v3-lane-safe --target-duration-s 72 --fps 8` emitted `task140-bad-path-stress-v3-lane-safe-001` because the first v3 directory already existed.
- PASS: `python3 -m compileall -q src tests`
- PASS: `bash scripts/pre_push_check.sh` ran 430 tests OK, 5 skipped.
- PASS: review artifact `tickets/TASK-140/artifacts/review/task140-implementation-review.json`
- PASS: lane-safety review artifact `tickets/TASK-140/artifacts/review/task140-lane-safety-review.json`

### Artifact Links

- Manifest: `artifacts/runs/task140-bad-path-stress-v3-lane-safe-001/bad_path_stress_demo.json`
- Report: `artifacts/runs/task140-bad-path-stress-v3-lane-safe-001/bad_path_stress_demo.md`
- HTML: `artifacts/runs/task140-bad-path-stress-v3-lane-safe-001/bad_path_stress_demo.html`
- Video: `artifacts/runs/task140-bad-path-stress-v3-lane-safe-001/bad_path_stress_demo.mp4`
- Lane-safety review: `tickets/TASK-140/artifacts/review/task140-lane-safety-review.json`

### QA Reconciliation

- Static blocker: baseline collision proxy true; guarded response stops before blocker with `3.5m` minimum distance.
- Road hole: baseline collision proxy true; guarded response swerves, clears the hole, returns to lane, continues, and stays within the drivable corridor with `max_abs_y_m=2.736`.
- Rolling object: baseline collision proxy true; guarded response slows, creates lateral separation, resumes, and stays within the drivable corridor with `max_abs_y_m=2.75`.
- Compound obstacle detour: baseline collision proxy true; guarded response stops, replans, finds an alternate route, slows through it, recovers, clears the compound zone, and stays within the drivable corridor with `max_abs_y_m=2.75`.
