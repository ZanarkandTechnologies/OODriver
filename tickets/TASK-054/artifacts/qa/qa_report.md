# TASK-054 QA Report

- verdict: `pass`
- focused tests: `tickets/TASK-054/artifacts/qa/focused_tests.log`
- pre-push gate: `tickets/TASK-054/artifacts/qa/pre_push_check.log`
- real capture proof:
  `tickets/TASK-054/artifacts/real-capture-materialization/alpamayo_tensor_manifest.md`

## Acceptance Criteria

- AC-1: PASS. `materialize_alpamayo_input(...)` validates camera windows, image
  paths, PNG dimensions, camera id alignment, ego history, and rotation shapes.
- AC-2: PASS. Real CARLA capture materialized as
  `image_frames=[3,4,3,90,160]`, `camera_indices=[3]`,
  `ego_history_xyz=[1,1,16,3]`, and `ego_history_rot=[1,1,16,3,3]`.
- AC-3: PASS. CLI wrote `alpamayo_tensor_manifest.json` and Markdown report.
- AC-4: PASS. Focused tests cover happy path, validation failures, CLI output,
  and lazy torch dependency behavior without CUDA.
- AC-5: PASS. Secret scan found no token patterns in the diff and artifact-size
  scan found no files above 1 MB under the ticket.

## Commands

```bash
PYTHONPATH=src python3 -m unittest tests.test_alpamayo_materializer tests.test_alpamayo_input tests.test_carla_alpamayo_capture
bash scripts/pre_push_check.sh
PYTHONPATH=src python3 -m driverx materialize-alpamayo-input --package artifacts/runs/task51-live-alpamayo-capture/alpamayo_carla_input_package.json --output-root tickets/TASK-054/artifacts --run-id real-capture-materialization
```
