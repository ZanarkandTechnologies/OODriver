# TASK-021: DriverX Overlay Injection Plan

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-018, TASK-011
- location: `src/driverx/simulators`, CLI, tests, docs
- enter when: generated Bench2Drive route packs include DriverX sidecar overlays
- leave when: overlays compile into per-route CARLA actor/sensor/tick plans without launching CARLA
- blockers: live injection still requires a future CARLA runner beside SimLingo
- spawned follow-ups: live companion actor injector
- complexity: M

### Summary
Turn TASK-018 sidecar overlays into a concrete companion-injection plan. This
keeps the current ticket dependency-light: it compiles per-route actor scripts,
behavior ticks, memory queries, and expected outputs, but does not claim to
modify stock SimLingo behavior until a live runner exists.

### Acceptance Criteria
- [x] Load a route-pack manifest and resolve per-route XML/overlay paths.
- [x] Compile each overlay into a CARLA script plan using the selected regional behavior trace.
- [x] Preserve memory query, mutation, expected failure mode, and runtime contract.
- [x] Write JSON/Markdown plan artifacts.
- [x] Add CLI entrypoint.
- [x] Add unit and CLI tests without CARLA or SimLingo.
- [x] Run `bash scripts/pre_push_check.sh`.

### Evidence
- Overlay injection report:
  `tickets/TASK-021/artifacts/qa/2026-05-04T220000Z/overlay-injection/overlay_injection_plan.md`
- Overlay injection JSON:
  `tickets/TASK-021/artifacts/qa/2026-05-04T220000Z/overlay-injection/overlay_injection_plan.json`
- Proof result: `2` routes, `25` behavior samples plus `1` companion spawn
  tick per route (`26` ticks total), zero validation errors, distinct
  route-specific overlay actor roles `occluder` and `distractor`, companion
  blueprints `static.prop.streetbarrier` and `static.prop.trafficwarning`,
  preserved `driverx_runtime_contract`, and cleanup order `ego_rgb`,
  `ood_actor_0`, `companion_actor_0`, `ego`.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_overlay_injection tests.test_cli`
- Local gate: `bash scripts/pre_push_check.sh` passed with `130` tests.
