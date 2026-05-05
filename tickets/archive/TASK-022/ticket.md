# TASK-022: Live Companion CARLA Actor Injector

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-021
- location: `src/driverx/simulators`, CLI, tests, docs
- enter when: overlay injection plans compile sidecar overlays into CARLA script plans
- leave when: companion actors can be spawned, ticked, tracked, and cleaned up from a plan without owning the ego route
- blockers: live proof requires CARLA Python API and a running CARLA server; stock SimLingo rerun still needs H100/H200 or rebuilt Blackwell stack
- spawned follow-ups: SimLingo sidecar orchestration wrapper
- complexity: M

### Summary
Implement the first live runner for TASK-021 artifacts. The runner consumes an
`overlay_injection_plan.json`, connects to CARLA when available, spawns only
`companion_actor_*` overlays, applies their planned ticks, writes entity tracks,
and cleans them up. It intentionally does not spawn ego, sensors, or stock
Bench2Drive route actors; those remain owned by SimLingo/Bench2Drive.

### Acceptance Criteria
- [x] Load a TASK-021 overlay injection plan JSON.
- [x] Select companion actors from each route `script_plan`.
- [x] Spawn companion actors with planned blueprints/transforms.
- [x] Apply companion ticks and write entity-track artifacts.
- [x] Clean up spawned actors in reverse order.
- [x] Return clean setup blockers when `carla` is unavailable or the server is unreachable.
- [x] Add CLI entrypoint.
- [x] Add fake-CARLA unit and CLI tests; no live CARLA required.
- [x] Run `bash scripts/pre_push_check.sh`.

### Evidence
- Clean native setup blocker:
  `tickets/TASK-022/artifacts/qa/2026-05-05T051500Z/local-missing-carla/overlay_injection_run.md`
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_injection tests.test_cli_carla_injection`
  passed with `5` tests.
- Local gate: `bash scripts/pre_push_check.sh` passed with `135` tests.
