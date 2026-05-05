# TASK-054: Alpamayo Tensor Materializer From DriverX/CARLA Captures

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-051, TASK-053
- location: `src/driverx/policies`, tests, `tickets/archive/TASK-054/`
- enter when: TASK-053 has observed live Alpamayo inference shapes
- leave when: a CARLA Alpamayo capture package can be validated and converted
  into a torch-ready tensor contract for the remote Alpamayo runner
- blockers: none
- spawned follow-ups: TASK-039 Alpamayo CARLA adapter
- complexity: M

### Description
TASK-051 writes live CARLA RGB capture packages and TASK-053 proves Alpamayo's
real inference tensor shapes. This ticket bridges them by validating CARLA
capture PNG windows, ego history, camera ids, and memory/nav metadata into a
remote-ready Alpamayo tensor manifest.

### Goal
Make DriverX/CARLA captures mechanically consumable by the Alpamayo runner
without guessing tensor ranks or requiring CUDA on the local machine.

### Acceptance Criteria
- [x] AC-1: `materialize_alpamayo_input(package_path, image_root)` validates
  camera windows, image files, camera ids, ego history, and rotation shapes.
- [x] AC-2: Materialization emits Alpamayo-compatible tensor shapes:
  `image_frames=[N,4,3,H,W]`, `camera_indices=[N]`,
  `ego_history_xyz=[1,1,16,3]`, and `ego_history_rot=[1,1,16,3,3]`.
- [x] AC-3: CLI writes `alpamayo_tensor_manifest.json` and Markdown report with
  validation errors, camera ids, image paths, and the remote torch loader
  contract.
- [x] AC-4: Unit tests cover fixture PNG materialization, validation failures,
  and CLI output without requiring torch or CUDA.
- [x] AC-5: No generated tensors, datasets, model weights, credentials, or live
  image artifacts are committed.

### Agent Contract
- Open: `src/driverx/policies/alpamayo_input.py`,
  `src/driverx/simulators/carla_alpamayo_capture.py`, TASK-053 shape reports
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_materializer`
- Stabilize: keep torch/PIL imports optional at runtime; local checks should
  prove the payload contract even when CUDA is absent
- Inspect: CARLA capture package shape and TASK-053 observed shapes
- Expected artifacts: `tickets/archive/TASK-054/artifacts/qa/*`,
  `tickets/archive/TASK-054/artifacts/review/*`, optional local materialization proof
- Delegate with: reviewer/QA after focused tests pass

### Evidence Checklist
- [x] Snapshot: materializer JSON/Markdown from fixture package
- [x] Snapshot: focused test log
- [x] Snapshot: pre-push log
- [x] QA report linked:

### Build Notes
- Added `driverx.policies.alpamayo_materializer`, including
  `materialize_alpamayo_input(...)`, `write_alpamayo_tensor_materialization(...)`,
  and lazy `load_alpamayo_torch_tensors(...)` for the remote Alpamayo runtime.
- Added `materialize-alpamayo-input` CLI registration.
- Real TASK-051 CARLA capture materialized successfully with
  `image_frames=[3,4,3,90,160]`, `camera_indices=[3]`,
  `ego_history_xyz=[1,1,16,3]`, and `ego_history_rot=[1,1,16,3,3]`.
- Torch and Pillow are lazy dependencies for the tensor loader; local validation
  and reports do not require CUDA.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS

### Artifact Links
- Real capture materialization:
  `tickets/archive/TASK-054/artifacts/real-capture-materialization/alpamayo_tensor_manifest.md`
- Focused tests: `tickets/archive/TASK-054/artifacts/qa/focused_tests.log`
- Pre-push gate: `tickets/archive/TASK-054/artifacts/qa/pre_push_check.log`
- QA report: `tickets/archive/TASK-054/artifacts/qa/qa_report.md`
- Review: `tickets/archive/TASK-054/artifacts/review/20260506T010324-review.md`

### User Evidence
- Supporting evidence:
  `tickets/archive/TASK-054/artifacts/real-capture-materialization/alpamayo_tensor_manifest.md`
- QA report: `tickets/archive/TASK-054/artifacts/qa/qa_report.md`
- Final verdict: TASK-054 is complete; TASK-039 can now call the lazy tensor
  loader or use the manifest contract to execute Alpamayo on CARLA captures.

### Required Evidence
- [x] Unit/integration/e2e tests pass (as applicable)
- [x] Lint passes
