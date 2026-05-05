# TASK-047: Alpamayo Input Package Manifest

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-045, TASK-046
- location: `src/driverx/policies`, tests
- enter when: Alpamayo input contract is known but live GPU inference is blocked
- leave when: DriverX can produce a model-input manifest from local frames with
  camera windows, ego history, route/nav text, and retrieved memory context
- blockers: live CARLA-to-Alpamayo tensor capture remains future work; this
  ticket emits a manifest, not torch tensors
- spawned follow-ups: TASK-039 Alpamayo CARLA adapter
- complexity: M

## Summary

Build the model-side input package that sits between CARLA/fixtures and the
eventual Alpamayo runtime. It should transform current DriverX `FrameBundle`
data into a structured manifest matching the release contract: camera-major
windows, camera indices, 16-step ego history, identity rotation scaffold, nav
text, and memory snippets.

## Acceptance Criteria

- [x] Build an Alpamayo input manifest from a fixture frame.
- [x] Include camera ids/names, repeated temporal windows, image dimensions,
  16-step ego history, 16 identity rotations, nav text, and memory context.
- [x] Add CLI artifact writing for a fixture-backed package.
- [x] Tests cover default cameras, history shape, memory context, and CLI
  output.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_input tests.test_alpamayo_trajectory tests.test_alpamayo_release`
- `PYTHONPATH=src python3 -m driverx build-alpamayo-input --fixture construction_merge --with-memory --output-root artifacts/runs --run-id task47-alpamayo-input-package`
- `bash scripts/pre_push_check.sh`

## Evidence

- Module: `src/driverx/policies/alpamayo_input.py`
- CLI: `src/driverx/policies/alpamayo_input_cli.py`
- Tests: `tests/test_alpamayo_input.py`
- Input package JSON:
  `artifacts/runs/task47-alpamayo-input-package/alpamayo_input_package.json`
- Input package report:
  `artifacts/runs/task47-alpamayo-input-package/alpamayo_input_package.md`
- Review: `tickets/archive/TASK-047/artifacts/review/20260505T230000-review.json`

## Result

DriverX can now produce a GPU-free Alpamayo input manifest from a fixture frame.
The manifest records camera-major windows, camera ids `[0, 1, 2]`, four repeated
fixture frames per camera, 16 ego-local xyz history points, 16 identity rotation
matrices, nav text inferred from the route, and retrieved memory snippets. It is
explicitly labeled as a manifest rather than a torch tensor dump so live CARLA
capture can replace repeated fixture frames later.
