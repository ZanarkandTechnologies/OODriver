# TASK-053: Live Alpamayo Inference Shape Probe

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-052, TASK-045, TASK-047, TASK-051
- location: `scripts/`, `src/driverx/policies`, `tickets/TASK-053/`
- enter when: TASK-052 has a successful RunPod Alpamayo load proof
- leave when: a real Alpamayo inference call records input contracts, output
  keys/shapes, latency, and VRAM without leaking prompts, tokens, or weights
- blockers: none yet; possible upstream dataset gate or missing sample data
- spawned follow-ups: TASK-039 Alpamayo CARLA adapter
- complexity: M

### Description
TASK-052 proves that the model can load on the RunPod RTX 6000 Ada with eager
attention, but TASK-039 still needs observed inference shapes. This ticket runs
the smallest live Alpamayo call that can reveal the trajectory and reasoning
interfaces without attempting closed-loop CARLA control.

### Goal
Turn Alpamayo from "loadable" into "adaptable" by capturing the concrete
sample-call contract needed by the DriverX CARLA adapter.

### Acceptance Criteria
- [ ] AC-1: Identify the upstream inference entrypoint and required sample data
  path from the local or remote Alpamayo checkout.
- [ ] AC-2: Run the smallest live inference path available on the RunPod pod
  with `ALPAMAYO_ATTN_IMPLEMENTATION=eager`, or record a precise external
  blocker if a separate gated dataset/sample is required.
- [ ] AC-3: Write a compact shape report containing observed input fields,
  output keys, trajectory shape, reasoning field shape/type when present,
  latency, and peak VRAM.
- [ ] AC-4: Update TASK-039 with the exact adapter handoff decision: ready,
  shape-blocked, data-blocked, or memory-blocked.
- [ ] AC-5: Keep all model weights, raw datasets, tokens, and heavyweight logs
  out of git.

### Agent Contract
- Open: `../external/alpamayo1.5` if present, `/workspace/alpamayo1.5` through
  SSH, `scripts/run_remote_alpamayo_probe.sh`, `src/driverx/policies`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_probe`
- Stabilize: use existing `/workspace/.cache/driverx` caches; do not re-download
  Alpamayo unless unavoidable; redact secrets; cap probe artifacts to compact
  JSON/Markdown/log excerpts
- Inspect: upstream `test_inference.py`, notebooks, `load_physical_aiavdataset.py`,
  model helper functions, and any callable trajectory sampling methods
- Expected artifacts: `tickets/TASK-053/artifacts/shape-probe/*`,
  `tickets/TASK-053/artifacts/review/*`, `tickets/TASK-053/artifacts/qa/*`
- Delegate with: reviewer/QA only after shape evidence or blocker is recorded

### Evidence Checklist
- [ ] Snapshot: upstream inference entrypoint inventory
- [ ] Snapshot: live shape probe report or precise blocker
- [ ] Snapshot: updated TASK-039 blocker/readiness note
- [ ] QA report linked:

### Build Notes

### QA Reconciliation
- AC-1: NOT PROVABLE
- AC-2: NOT PROVABLE
- AC-3: NOT PROVABLE
- AC-4: NOT PROVABLE
- AC-5: NOT PROVABLE

### Artifact Links

### User Evidence
- Supporting evidence:
- QA report:
- Final verdict:

### Required Evidence
- [ ] Unit/integration/e2e tests pass (as applicable)
- [ ] Lint passes
