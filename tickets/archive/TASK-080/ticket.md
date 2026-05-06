# TASK-080: Same-Scene Alpamayo CARLA Capture Package

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-078, TASK-074
- location: `src/driverx/simulators`, `src/driverx/policies`, `tickets/TASK-080/artifacts`
- enter when: live CARLA is available or TASK-078 has generated-scene metadata
- leave when: an Alpamayo package for the live/generated OOD scene is materialized as torch-ready or blocked with validation errors
- blockers: none for same-scene package; package uses one ego RGB camera duplicated across three Alpamayo camera slots
- spawned follow-ups: TASK-081
- complexity: M

### Description
Capture three-camera, four-frame Alpamayo input windows from the same generated
CARLA scene used for video evidence. This connects visible simulator evidence
to reasoning VLA evidence.

### Goal
Write `alpamayo_carla_input_package.json`, capture report, and materialization
report for the generated OOD scene.

### Acceptance Criteria
- [x] AC-1: Capture writes 3 camera windows with 4 frames each or precise blocker.
- [x] AC-2: Materializer reports `torch_ready=true` for live package, or lists validation errors.
- [x] AC-3: Package includes scenario/video links where available.
- [x] AC-4: Capture does not destroy attached third-party actors.

### Agent Contract
- Open: `src/driverx/simulators/carla_alpamayo_capture.py`, `src/driverx/policies/alpamayo_materializer.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_carla_alpamayo_capture tests.test_alpamayo_materializer`
- Stabilize: use fallback spawn if no DriverX ego remains available after TASK-078.
- Inspect: `tickets/TASK-078/artifacts`, `tickets/TASK-074/artifacts`
- Expected artifacts: capture JSON/MD, package JSON, materialization JSON/MD.

### Evidence
- Created 2026-05-06 for the live CARLA retry batch.
- Added `build-alpamayo-ood-package`, which converts TASK-078 live RGB frames
  and entity tracks into an Alpamayo input package tied to the TASK-079 video.
- Package evidence:
  `tickets/TASK-080/artifacts/task80-live-same-scene-package-001/alpamayo_ood_input_package.md`.
- Materialization evidence:
  `tickets/TASK-080/artifacts/task80-live-same-scene-materialized-v2/alpamayo_tensor_manifest.md`,
  with `torch_ready=true`, image shape `[3,4,3,360,640]`, and ego history
  shape `[1,1,16,3]`.
- Alpamayo scene report:
  `tickets/TASK-080/artifacts/task80-live-same-scene-alpamayo-scene-v2/alpamayo_ood_scene.md`.

### Blockers
- None for this ticket. Claim boundary: this is single-camera duplicated
  three-slot Alpamayo evidence, not a full multi-camera CARLA capture rig.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
