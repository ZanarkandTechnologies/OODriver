# TASK-009 Review: Ego Spawn, Camera Capture, And Entity Tracks

Reviewed: 2026-05-04 19:00 +0800

## Scope

- Changed files: CARLA ego smoke module, simulator exports, CLI, tests, docs,
  ticket evidence.
- Rubrics: code quality, cleanup safety, evidence quality.
- Context checked: TASK-008 bridge, `src/driverx/simulators/AGENTS.md`,
  `tickets/archive/TASK-009/ticket.md`, live output artifacts.

## Verdict

Overall score: **4.3 / 5.0**

Verdict: **pass**

TASK-009 safely proves 0xDriver can create and observe CARLA entities. The live
path spawned one ego actor and one RGB camera, captured a frame, wrote transform
tracks, and destroyed both actors in `finally`.

## Findings

No blocking findings.

## Notes

- The first side-effect path is intentionally tiny: no traffic manager, no
  route following, and no policy loop.
- The cleanup contract is tested with fake CARLA actors and proven in live
  evidence by destroyed ids `[25, 24]`.
- Behavior scripts should build on the track format rather than inventing a new
  entity-log schema.

## Evidence Reviewed

- `bash scripts/pre_push_check.sh`: PASS, 65 tests.
- `bash scripts/run_carla_client_docker.sh python -m driverx spawn-ego-smoke --host host.docker.internal --port 2000 --timeout-s 10 --tick-count 5 --run-id task9-ego-smoke`: PASS.
- `artifacts/runs/task9-ego-smoke/ego_camera.png`.
- `artifacts/runs/task9-ego-smoke/entity_tracks.json`.

## Next Action

Proceed to TASK-010 regional driving behavior traces and metrics.
