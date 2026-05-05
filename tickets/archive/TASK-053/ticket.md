# TASK-053: Live Alpamayo Inference Shape Probe

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-052, TASK-045, TASK-047, TASK-051
- location: `scripts/`, `src/driverx/policies`, `tickets/archive/TASK-053/`
- enter when: TASK-052 has a successful RunPod Alpamayo load proof
- leave when: a real Alpamayo inference call records input contracts, output
  keys/shapes, latency, and VRAM without leaking prompts, tokens, or weights
- blockers: none for shape evidence; upstream PhysicalAI sample dataset remains
  gated but synthetic fallback produced the required model I/O shapes
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
- [x] AC-1: Identify the upstream inference entrypoint and required sample data
  path from the local or remote Alpamayo checkout.
- [x] AC-2: Run the smallest live inference path available on the RunPod pod
  with `ALPAMAYO_ATTN_IMPLEMENTATION=eager`, or record a precise external
  blocker if a separate gated dataset/sample is required.
- [x] AC-3: Write a compact shape report containing observed input fields,
  output keys, trajectory shape, reasoning field shape/type when present,
  latency, and peak VRAM.
- [x] AC-4: Update TASK-039 with the exact adapter handoff decision: ready,
  shape-blocked, data-blocked, or memory-blocked.
- [x] AC-5: Keep all model weights, raw datasets, tokens, and heavyweight logs
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
- Expected artifacts: `tickets/archive/TASK-053/artifacts/shape-probe/*`,
  `tickets/archive/TASK-053/artifacts/review/*`, `tickets/archive/TASK-053/artifacts/qa/*`
- Delegate with: reviewer/QA only after shape evidence or blocker is recorded

### Evidence Checklist
- [x] Snapshot: upstream inference entrypoint inventory
- [x] Snapshot: live shape probe report or precise blocker
- [x] Snapshot: updated TASK-039 blocker/readiness note
- [x] QA report linked:

### Build Notes
- Added `scripts/run_remote_alpamayo_shape_probe.sh`, a compact remote runner
  that first tries the upstream `load_physical_aiavdataset` sample path, then
  falls back to synthetic Alpamayo-shaped tensors when the dataset is gated.
- Added `probe-alpamayo-shapes` plus local classifier/reporting tests for shape
  evidence.
- Live RunPod attempt confirmed the upstream sample path is gated by
  `nvidia/PhysicalAI-Autonomous-Vehicles`, then synthetic fallback exercised
  `sample_trajectories_from_data_with_vlm_rollout`.
- Observed input shapes:
  `image_frames=[4,4,3,384,448]`, `camera_indices=[4]`,
  `ego_history_xyz=[1,1,16,3]`, `ego_history_rot=[1,1,16,3,3]`,
  `tokenized_data.input_ids=[1,2894]`, `pixel_values=[10752,1536]`.
- Observed output shapes:
  `pred_xyz=[1,1,1,64,3]`, `pred_rot=[1,1,1,64,3,3]`,
  `extra.cot=[1,1,1]`, `extra.meta_action=[1,1,1]`,
  `extra.answer=[1,1,1]`.
- Live run latency was `96673.62ms` and peak VRAM was `24478.66MB` on the
  RunPod RTX 6000 Ada.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS

### Artifact Links
- Dataset-gated upstream attempt:
  `tickets/archive/TASK-053/artifacts/shape-probe-summary/alpamayo_shape_probe_report.md`
- Synthetic fallback shape proof:
  `tickets/archive/TASK-053/artifacts/shape-probe-synthetic-summary/alpamayo_shape_probe_report.md`
- QA:
  `tickets/archive/TASK-053/artifacts/qa/qa_report.md`
- Review:
  `tickets/archive/TASK-053/artifacts/review/20260506T005200-review.md`

### User Evidence
- Supporting evidence: live RunPod shape probe reports listed above.
- QA report: `tickets/archive/TASK-053/artifacts/qa/qa_report.md`
- Final verdict: TASK-039 can proceed against observed Alpamayo I/O shapes;
  real PhysicalAI sample data remains gated but is not needed to implement the
  DriverX/CARLA adapter path.

### Required Evidence
- [x] Unit/integration/e2e tests pass (as applicable)
- [x] Lint passes
