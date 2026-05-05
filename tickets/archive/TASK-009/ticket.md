# TASK-009: Ego Spawn, Camera Capture, And Entity Tracks

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-008
- location: `src/driverx/simulators`, `src/driverx/entities`, CLI, scripts, tests
- enter when: CARLA API probe works or degrades with a known runtime blocker
- leave when: one ego actor, one RGB sensor, one frame, and entity tracks are captured with cleanup
- blockers: none; live CARLA ego smoke succeeded
- spawned follow-ups: TASK-010 behavior scripts, TASK-011 script compiler
- complexity: M

## Summary

Prove 0xDriver can create and observe CARLA entities, then clean them up. This
is the bridge from simulator introspection to generated scenario execution.

## Scope

In scope:

- ego vehicle spawn plan and cleanup.
- RGB camera sensor attachment.
- one-frame capture artifact.
- per-tick actor transform logging.
- local tests using fake CARLA objects.

Out of scope:

- full Fail2Drive route following.
- VLA policy control.

## Acceptance Criteria

- [x] Spawn command can run in dry-run/fake mode without CARLA.
- [x] Live command can spawn/destroy actors when CARLA bridge is available.
- [x] Entity tracks include actor id, type, tick, transform, velocity when available.
- [x] Sensor capture writes image metadata and a frame artifact.
- [x] Cleanup runs in `finally` and logs destroyed actor ids.
- [x] Tests prove cleanup on success and failure.

## Verification

- `bash scripts/pre_push_check.sh`
- live Docker proof after TASK-008:
  `bash scripts/run_carla_client_docker.sh python -m driverx spawn-ego-smoke --host host.docker.internal --port 2000 --run-id task9-ego-smoke`

## Blockers

- None after live proof.

## Evidence

- Local tests: `PYTHONPATH=src python3 -m unittest tests.test_carla_ego tests.test_carla_probe tests.test_cli` passed with 18 tests.
- Live Docker command: `bash scripts/run_carla_client_docker.sh python -m driverx spawn-ego-smoke --host host.docker.internal --port 2000 --timeout-s 10 --tick-count 5 --run-id task9-ego-smoke`.
- Live result: map `Carla/Maps/Town10HD_Opt`, ego actor `24`, camera actor `25`, destroyed ids `[25, 24]`, track count `10`.
- Camera artifact: `artifacts/runs/task9-ego-smoke/ego_camera.png`.
- Track artifact: `artifacts/runs/task9-ego-smoke/entity_tracks.json`.
