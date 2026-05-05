# TASK-013: Policy Adapter Interface

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-011
- location: `src/driverx/policies`, `src/driverx/memory`, tests
- enter when: compiled scenarios need policy execution surfaces
- leave when: mock/rule/VLM-ready policy adapters share one contract
- blockers: real SimLingo/Alpamayo credentials needed only for live adapters
- spawned follow-ups: TASK-014 RAG comparison
- complexity: L

## Summary

Define the policy adapter boundary for frozen reasoning VLA/VLM policies. The
first implementation includes deterministic mock and local hybrid adapters so
the harness can be tested before real model access.

## Acceptance Criteria

- [x] `PolicyAdapter` interface returns structured intent/action, latency, and
  reason summary.
- [x] Mock adapter supports no-memory and memory-aware behavior.
- [x] Local hybrid planner adapter can act as fallback.
- [x] VLM/API, SimLingo, and Alpamayo adapters exist as setup-checked stubs with
  clear blockers.
- [x] Tests cover adapter selection, memory injection, and missing dependency
  guidance.

## Verification

- `bash scripts/pre_push_check.sh`
- `PYTHONPATH=src python3 -m driverx run-policy-fixture --policy mock --run-id task13-policy`

## Blockers

- Real model checkpoints/API keys are not required for the adapter contract.

## Evidence

- Local tests: `PYTHONPATH=src python3 -m unittest tests.test_policies tests.test_cli` passed with 23 tests.
- No-memory proof: `PYTHONPATH=src python3 -m driverx run-policy-fixture --policy mock --run-id task13-policy`.
- Memory-aware proof: `PYTHONPATH=src python3 -m driverx run-policy-fixture --policy mock --with-memory --run-id task13-policy-memory`.
- Stub blocker proof: `PYTHONPATH=src python3 -m driverx run-policy-fixture --policy alpamayo --run-id task13-policy-alpamayo-blocked`.
- Decision artifacts:
  - `artifacts/runs/task13-policy/policy_decision.json`
  - `artifacts/runs/task13-policy-memory/policy_decision.json`
  - `artifacts/runs/task13-policy-alpamayo-blocked/policy_setup_blocker.json`
- External blockers retained: live VLM/SimLingo/Alpamayo require credentials,
  checkpoints, and/or Linux NVIDIA runtime setup.
