# TASK-038: Alpamayo Offline Probe

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-037, RTX 6000 Ada or equivalent GPU, Hugging Face access
- location: `src/driverx/policies`, `scripts`, remote artifacts, tests
- enter when: policy runtime matrix identifies Alpamayo as a high-value adapter
- leave when: Alpamayo can be loaded or produces a precise model/runtime
  blocker, with memory and latency evidence
- blockers: live proof still needs a confirmed Alpamayo checkpoint/repo id and
  an explicit remote run using `scripts/run_remote_alpamayo_probe.sh`
- spawned follow-ups: TASK-039 Alpamayo CARLA adapter
- complexity: L

## Summary

Probe Alpamayo offline before trying closed-loop CARLA. The target is model
load, input/output shape discovery, one prepared observation, trajectory output,
latency, and blocker classification.

## Acceptance Criteria

- [x] Remote probe script records GPU, package versions, model load state,
  memory usage, and latency when run.
- [x] Adapter stub records expected Alpamayo input/output schema.
- [x] Failure modes are classified without leaking credentials.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_probe`
- `PYTHONPATH=src python3 -m driverx probe-alpamayo --output-root artifacts/runs --run-id task38-local-probe`
- remote optional: `scripts/run_remote_alpamayo_probe.sh user@host`

## Evidence

- Code: `src/driverx/policies/alpamayo_probe.py`
- CLI: `python -m driverx probe-alpamayo`
- Script: `scripts/run_remote_alpamayo_probe.sh`
- Local dry-run artifact: `artifacts/runs/task38-local-probe/alpamayo_probe_report.json`
- Review: `tickets/TASK-038/artifacts/review/20260505T192400-review.json`

## Blockers

- Live proof was not executed in this local ticket pass. The remaining gate is a
  confirmed Alpamayo model repo/checkpoint plus a remote run. The script defaults
  to metadata inspection and requires `ALPAMAYO_DOWNLOAD=1` or
  `ALPAMAYO_LOAD=1` to perform heavier operations.
