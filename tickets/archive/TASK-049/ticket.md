# TASK-049: Alpamayo Offline Policy Rehearsal

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-046, TASK-047
- location: `src/driverx/policies`, tests
- enter when: Alpamayo input and output conversion are available locally
- leave when: DriverX can rehearse the Alpamayo adapter using a saved
  `pred_xyz` JSON and produce a normal policy decision artifact
- blockers: live Alpamayo model execution remains blocked on GPU SSH
- spawned follow-ups: TASK-039 Alpamayo CARLA adapter
- complexity: M

## Summary

Connect the pieces already built: fixture frame -> Alpamayo input manifest ->
saved native `pred_xyz` -> converted DriverX trajectory -> policy decision.
This should prove the policy handoff path before we have a live model output.

## Acceptance Criteria

- [x] Add an offline Alpamayo policy rehearsal runner.
- [x] Write input package, converted trajectory, and policy decision artifacts
  in one run directory.
- [x] Preserve memory ids and nav text in the decision metadata.
- [x] Add CLI and tests using fixture prediction JSON.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_offline tests.test_alpamayo_input tests.test_alpamayo_trajectory`
- `PYTHONPATH=src python3 -m driverx run-alpamayo-offline --prediction-json artifacts/runs/task46-input/pred_xyz.json --with-memory --output-root artifacts/runs --run-id task49-alpamayo-offline-policy`
- `bash scripts/pre_push_check.sh`

## Evidence

- Module: `src/driverx/policies/alpamayo_offline.py`
- CLI: `src/driverx/policies/alpamayo_offline_cli.py`
- Tests: `tests/test_alpamayo_offline.py`
- Offline policy summary:
  `artifacts/runs/task49-alpamayo-offline-policy/alpamayo_offline_policy.json`
- Input package:
  `artifacts/runs/task49-alpamayo-offline-policy/input/alpamayo_input_package.json`
- Converted trajectory:
  `artifacts/runs/task49-alpamayo-offline-policy/trajectory/alpamayo_trajectory.json`
- Policy decision:
  `artifacts/runs/task49-alpamayo-offline-policy/decision/policy_decision.json`
- Review: `tickets/archive/TASK-049/artifacts/review/20260505T230700-review.json`

## Result

DriverX can now rehearse an Alpamayo policy run end-to-end without a GPU: build
the Alpamayo input manifest, convert a saved native `pred_xyz`, and write a
standard `PolicyDecision`. The result explicitly uses
`adapter_kind=alpamayo_saved_prediction` and keeps `offline_replay=true` so this
cannot be mistaken for a live model claim.
