# TASK-078: Live Scripted CARLA OOD Capture Retry

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-072, local CARLA 0.9.16
- location: `src/driverx/simulators`, `configs/`, `tickets/TASK-078/artifacts`
- enter when: CARLA.app is open and the town is loaded
- leave when: `run-carla-ood-demo` writes live RGB frames, entity tracks, and a reproducible report, or records a precise live blocker
- blockers: none for scripted OOD capture; full stock Fail2Drive scoring remains TASK-060
- spawned follow-ups: TASK-079, TASK-080
- complexity: M

### Description
Retry the DriverX scripted CARLA OOD demo against the currently running local
CARLA server. The goal is to replace fixture-only video proof with live CARLA
frames and actor telemetry from a generated OOD scenario.

### Goal
Produce a live or partial `carla_ood_demo` evidence bundle that can feed video
assembly and same-scene Alpamayo packaging.

### Acceptance Criteria
- [x] AC-1: Docker client probe confirms whether CARLA is reachable at `host.docker.internal:2000`.
- [x] AC-2: Live run writes `carla_ood_demo.json`, `carla_ood_demo.md`, `carla_ood_demo_plan.json`, and either RGB frames plus `entity_tracks.json` or a precise blocker.
- [x] AC-3: Actor cleanup is reported with spawned and destroyed actor ids.
- [x] AC-4: Evidence labels the run as DriverX scripted CARLA OOD, not stock Fail2Drive scoring or VLA closed-loop control.

### Agent Contract
- Open: `src/driverx/simulators/carla_ood_demo.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_carla_ood_demo tests.test_carla_asset_mapping`
- Stabilize: prefer runner/config patches over manual simulator poking; keep frame/video outputs ignored.
- Inspect: `blockers.md`, `tickets/TASK-072/artifacts/task72-live-candidate/carla_ood_demo.md`
- Expected artifacts: `tickets/TASK-078/artifacts/*/carla_ood_demo.{json,md}`, RGB folder if live capture works.

### Evidence
- Created 2026-05-06 for the live CARLA retry batch.
- Docker probe passed at
  `tickets/TASK-078/artifacts/task78-docker-carla-probe/carla_probe.md`.
- Live capture passed at
  `tickets/TASK-078/artifacts/task78-live-ood-capture-v3/carla_ood_demo.md`:
  120 frames, 24.0s at 5 FPS, generated stock-proxy assets, entity tracks, and
  full spawned/destroyed actor cleanup.
- The first failed attempt against `static.prop.trafficcone` is preserved for
  diagnosis; TASK-078 corrected local CARLA 0.9.16 proxy mappings to installed
  blueprints.

### Blockers
- None for this ticket.
