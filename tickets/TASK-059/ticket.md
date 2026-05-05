# TASK-059: PhysicalAI Dataset Alpamayo Sample Probe

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-052, TASK-053
- location: `scripts/`, `src/driverx/policies`, tests, `tickets/TASK-059/artifacts`
- enter when: user confirms Hugging Face access to
  `nvidia/PhysicalAI-Autonomous-Vehicles` is approved and RunPod stays alive
- leave when: the upstream dataset-backed Alpamayo inference sample runs or
  produces a new precise non-access blocker
- blockers: live RunPod SSH mapping may need refresh if the pod port changes
- spawned follow-ups: TASK-061 route-aligned Alpamayo comparison
- complexity: M

### Description
TASK-053 got the model I/O shapes through a synthetic fallback because the
PhysicalAI dataset was gated. The user has now approved that dataset, so this
ticket reruns the real upstream sample path and replaces synthetic fallback
evidence with dataset-backed evidence.

### Goal
Prove the exact NVIDIA sample inference path using real PhysicalAI sample data,
not synthetic tensors.

## Plan

### Change
Rerun and harden `scripts/run_remote_alpamayo_shape_probe.sh` with
`ALPAMAYO_SHAPE_SOURCE=dataset`, then classify the artifact as
`dataset_shape_observed` when `shape_source_used == "dataset"`.

### Why
This removes the last "synthetic shape" caveat from the Alpamayo adapter proof
and makes the model declaration more defensible for judges.

### Before -> After
- Before: Alpamayo live inference is proven, but real PhysicalAI sample access
  is still listed as open.
- After: `blockers.md` moves the PhysicalAI gate to resolved, or records a fresh
  runtime issue such as missing dataset key, bad clip id, or OOM.

### Touch
- `scripts/run_remote_alpamayo_shape_probe.sh`: dataset-first run settings and
  better dataset-source logging if needed.
- `src/driverx/policies/alpamayo_shape_probe.py`: classify dataset-backed
  evidence separately from synthetic fallback.
- `tests/test_alpamayo_shape_probe.py`: dataset vs synthetic status tests.
- `README.md`, `blockers.md`, `docs/progress.md`: update the evidence story.

### Inspect
- `tickets/archive/TASK-053/artifacts/shape-probe-synthetic-summary/`
- `scripts/run_remote_alpamayo_shape_probe.sh`
- `src/driverx/policies/alpamayo_shape_probe.py`
- RunPod SSH resolver docs and `README.md` command block.

### Signature Delta
```python
src/driverx/policies/alpamayo_shape_probe.py / classify_alpamayo_shape_probe_artifacts(artifact_root, model_id=...) -> dict[str, Any]
```

Add/report fields:

```python
{
  "status": "dataset_shape_observed" | "shape_observed" | "dataset_gate_blocked" | "runtime_blocked",
  "shape_source_used": "dataset" | "synthetic_after_dataset_blocker" | "synthetic",
  "clip_id": str,
  "t0_us": int,
}
```

### Type Sketch
```python
DatasetShapeProbeEvidence = {
  "input_shapes": dict[str, list[int] | dict],
  "output_shapes": {"pred_xyz": [1, 1, 1, 64, 3], "pred_rot": [1, 1, 1, 64, 3, 3], "extra.cot": list[int] | None},
  "latency_ms": float,
  "vram_peak_mb": float,
  "shape_source_used": "dataset",
}
```

### Typed Flow Example
`.env HF_TOKEN + RunPod target`
-> `ALPAMAYO_SHAPE_SOURCE=dataset scripts/run_remote_alpamayo_shape_probe.sh ...`
-> remote `load_physical_aiavdataset(clip_id, t0_us)`
-> `sample_trajectories_from_data_with_vlm_rollout`
-> pulled `alpamayo_shape_probe.json`
-> local report classifies `dataset_shape_observed`.

### Execution Steps
1. Resolve the current RunPod SSH mapping if needed.
2. Rerun the remote shape probe with dataset source forced.
3. If access still fails, inspect whether the token, dataset agreement, or clip id
   is the issue and update blockers precisely.
4. If it succeeds, update the classifier/report to surface dataset-backed state.
5. Refresh demo/model declaration inputs that previously mentioned synthetic
   fallback.

### Recommendation
Run this before new Alpamayo evaluation work. It is cheap compared with route
work and makes every later Alpamayo claim stronger.

### Options Considered
- Keep synthetic fallback only: already works but leaves a credibility caveat.
- Run full upstream `test_inference.py`: useful, but noisier/heavier than the
  current compact shape probe.
- Dataset-forced shape probe: best balance of real data, small artifacts, and
  direct adapter relevance.

### Blast Radius
Remote scripts, Alpamayo shape report, docs, and blockers. No local data shards,
HF cache, model weights, or raw image samples should be committed.

### Risks
- The approved dataset may still have delayed access propagation.
- The hard-coded sample `clip_id`/`t0_us` may no longer exist in the current
  dataset version.
- Dataset-backed inference may use more memory than the synthetic sample.

## Acceptance Criteria
- [ ] AC-1: Dataset-forced probe produces a report with
  `shape_source_used=dataset`, or a precise non-access blocker.
- [ ] AC-2: Report includes input shapes, output shapes, CoC type/shape, latency,
  VRAM, clip id, and t0.
- [ ] AC-3: PhysicalAI blocker is resolved or replaced in `blockers.md`.
- [ ] AC-4: Secret scan shows no HF token in artifacts.
- [ ] AC-5: Heavy caches/model/data remain outside git.

## Verification
- Unit: `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_shape_probe`
- Remote proof:
  `ALPAMAYO_SHAPE_SOURCE=dataset scripts/run_remote_alpamayo_shape_probe.sh ...`
- Gate: `bash scripts/pre_push_check.sh`
- Evidence:
  `tickets/TASK-059/artifacts/physicalai-shape-probe/alpamayo_shape_probe_report.md`

## Autonomy Readiness
- I can run this on the kept-alive RunPod pod.
- Human gate only if Hugging Face still returns 403 after the user's approval.

## Evidence
- Pending implementation.

## Blockers
- Pending live dataset-backed probe.
