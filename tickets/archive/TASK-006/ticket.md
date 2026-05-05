# TASK-006: Motion-Prior Hybrid Planner

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-005
- location: `src/driverx/planning`, `src/driverx/pipeline`, tests, docs
- enter when: TASK-005 shows deterministic ego-history baselines outperform the
  mock semantic planner on the first real Waymo slice
- leave when: the main `run-scene`/`run-batch` planner uses a deployable hybrid
  candidate set and real 10-frame Waymo ADE is close to the strongest rule
  baseline
- blockers: none
- spawned follow-ups: VLA/cloud backend should feed the hybrid intent layer after
  this local action layer is stable
- complexity: M

## Summary

Implement the first Realtime-VLA-inspired runtime improvement: keep the VLA/VLM
as a slower semantic reasoner, but give the local planner a strong fast action
prior from ego history. This makes the main pipeline a hybrid planner rather
than a pure mock-intent planner, so future cloud/GPU VLA work must beat a
credible local control layer instead of a weak placeholder.

## Scope

In scope:

- hybrid candidate generation that combines semantic intent candidates with
  deterministic rule baselines
- deployable ranking that does not read future labels
- artifacts that expose candidate families and the selected source
- tests proving the hybrid planner is used by the main pipeline
- real Waymo 10-frame batch evidence comparing TASK-006 against the TASK-005
  baseline

Out of scope:

- cloud GPU model serving
- FlashDrive CUDA kernels, quantization, speculative decoding, or streaming KV
  cache implementation
- official aggregate Waymo submission shards
- training or fine-tuning model weights

## Plan

### Change

Before:

- `run-scene` generates only semantic candidates from structured mock intent.
- deterministic baselines are available only in `run-experiment`.
- the real 10-frame batch selected `intent_planner` mean ADE was `6.204769`,
  while the deployable `constant_acceleration` baseline was `3.73323`.

After:

- `run-scene` and `run-batch` generate hybrid candidates:
  - semantic intent candidates
  - local ego-history motion-prior candidates
- the ranker remains deployable and label-free.
- `run-batch` can select the motion prior when semantic intent is weak, while
  still preserving semantic candidates for future VLA overrides.

### Why This Matches The Papers

FlashDrive is mostly about making VLA inference stages faster once the real VLA
backend exists. Realtime-VLA V2 is also about the rest of the deployment stack:
action chunking, local smoothing/MPC, aligned logs, and making model output
usable by fast hardware-facing control. TASK-006 implements that second family
now: a fast local action layer that the later GPU VLA path can steer but does
not have to replace.

### Touch

- `src/driverx/planning/hybrid.py`: hybrid candidate generator.
- `src/driverx/planning/baselines.py`: deployable baseline score ordering.
- `src/driverx/planning/__init__.py`, `src/driverx/planning/README.md`,
  `src/driverx/planning/AGENTS.md`: public API and invariant update.
- `src/driverx/pipeline/scene_run.py`: use hybrid candidates in the main path.
- `tests/test_trajectory.py`, `tests/test_pipeline_mock.py`,
  `tests/test_batch.py`: shape, artifact, and batch selection coverage.
- `README.md`, `docs/progress.md`, `docs/HISTORY.md`, `docs/MEMORY.md`,
  `tickets/TASK-006/ticket.md`: usage and durable evidence.

### Signature Delta

```python
# planning
generate_hybrid_candidates(frame: FrameBundle, intent: DrivingIntent) -> list[TrajectoryCandidate]
```

Existing runtime APIs stay stable:

```python
run_scene(config: DriverConfig) -> SceneRunResult
run_batch(config: DriverConfig, ...) -> dict[str, Any]
run_experiment(config: DriverConfig, ...) -> dict[str, Any]
```

### Typed Flow Example

`configs/waymo_local.sample.yaml + frame_count=10`
-> `iter_waymo_frames(...)` streams real validation frames
-> mock reasoner emits structured semantic intent
-> `generate_hybrid_candidates(frame, intent)` adds semantic and motion-prior
candidates
-> smoothing/ranking selects the lowest deployable rank cost
-> `run_batch(...)` reports selected source, ADE, latency, and worst failure SVG.

### Execution Steps

1. Add hybrid candidate generator and wire the main scene pipeline to it.
2. Reorder deployable rule baseline scores so the empirically stronger
   constant-acceleration prior can win without reading labels.
3. Add/adjust tests for hybrid candidate families, selected source artifacts,
   fixture batch behavior, and CLI compatibility.
4. Run local unit/syntax checks.
5. Run real 10-frame Waymo batch through Docker and record mean ADE.
6. Update README/progress/history/memory/ticket evidence.
7. Run review and QA, then commit the completed slice.

## Acceptance Criteria

- [x] AC-1: Main `run-scene`/`run-batch` uses hybrid candidates by default.
- [x] AC-2: Hybrid candidate generation includes semantic and motion-prior
  sources and all trajectories contain exactly 20 points.
- [x] AC-3: Ranking remains deployable and does not inspect `future_xy`.
- [x] AC-4: Real 10-frame Waymo batch evidence is captured with mean ADE and
  selected source table.
- [x] AC-5: Existing fixture, batch, experiment, CLI, and packaging behavior
  remains compatible.
- [x] AC-6: Docs, history, memory, review, and QA evidence are updated.

## Agent Contract

- Open: `docs/prd.md`, `ARCHITECTURE.md`, `docs/MEMORY.md`,
  `tickets/TASK-005/ticket.md`, planning/pipeline modules.
- Test hook: `bash scripts/pre_push_check.sh`.
- Real-data hook: `scripts/run_waymo_docker.sh python -m driverx run-batch
  --config configs/waymo_local.sample.yaml --run-id waymo-hybrid-batch-10
  --frame-start 0 --frame-count 10`.
- Stabilize: keep the planner label-free; compare ADE only in evaluation/report
  surfaces.
- Inspect: `raw_candidates.json`, `smoothed_candidates.json`,
  `selected_trajectory.json`, `batch_summary.json`, `batch_report.md`.
- Key screens/states: no UI surfaces.
- QA cookbook: local checks plus real Docker batch; inspect selected source and
  worst-scene SVG path.
- Taste refs: none.
- Expected artifacts: review doc, QA report, batch summary/report paths.
- Delegate with: code reviewer for implementation quality; QA tester for
  evidence reconciliation.

## Evidence Checklist

- [x] Snapshot: local pre-push check output.
- [x] Snapshot: real 10-frame Waymo Docker batch summary/report.
- [x] Snapshot: worst-scene SVG path from batch report.
- [x] QA report linked.

## Build Notes

- Started 2026-05-03 14:24 +0800.
- Added `generate_hybrid_candidates(frame, intent)` and routed the main
  `run-scene`/`run-batch` path through it.
- Motion-prior candidates now carry `candidate_family=motion_prior`; semantic
  candidates carry `candidate_family=semantic_intent`.
- `run-experiment` now labels the current main planner as `hybrid_planner`
  rather than the stale `intent_planner` name.
- The deployable rule score ordering now allows `constant_acceleration` to win
  when no safety/ranking penalty outweighs it.
- Local gate passed with 40 unit tests.
- Real Docker proof `waymo-hybrid-batch-10` produced mean ADE `3.73323`; all
  10 selected sources were `constant_acceleration_smooth`.
- Fresh Docker experiment `waymo-hybrid-experiment-10` records the current main
  strategy as `hybrid_planner` with mean ADE `3.73323`.

## QA Reconciliation

- AC-1: PASS - `run-scene` calls `generate_hybrid_candidates`.
- AC-2: PASS - tests cover semantic and motion-prior families with 20-point
  trajectories.
- AC-3: PASS - ranking still consumes only candidates, metadata, and frame
  metadata; ADE/future labels remain in evaluation/report surfaces.
- AC-4: PASS - `waymo-hybrid-batch-10` captured `batch_summary.json`,
  `batch_report.md`, and worst-scene SVG path.
- AC-5: PASS - local pre-push check passed with existing fixture, batch,
  experiment, CLI, packaging, and optional-dependency tests.
- AC-6: PASS - docs, history, memory, review, and QA evidence are linked below.

## Artifact Links

- Review: `docs/reviews/TASK-006-hybrid-planner-review.md`
- QA: `tickets/TASK-006/artifacts/qa/2026-05-03T063433Z/report.md`
- Real batch summary:
  `artifacts/runs/waymo-hybrid-batch-10/batch_summary.json`
- Real batch report: `artifacts/runs/waymo-hybrid-batch-10/batch_report.md`
- Real experiment summary:
  `artifacts/runs/waymo-hybrid-experiment-10/experiment_summary.json`
- Real experiment report:
  `artifacts/runs/waymo-hybrid-experiment-10/experiment_report.md`
- Worst-scene SVG:
  `artifacts/runs/waymo-hybrid-batch-10/frame-000006/scene_prediction.svg`

## User Evidence

- Supporting evidence: hybrid batch mean ADE `3.73323`, best ADE `0.012684`
  at frame index `4`, worst ADE `9.15508` at frame index `6`.
- QA report: `tickets/TASK-006/artifacts/qa/2026-05-03T063433Z/report.md`
- Final verdict: PASS - main planner is now hybrid and ready for the next
  VLA/GPU backend ticket.

## Required Evidence

- [x] Unit/integration/e2e tests pass
- [x] Typecheck passes or remains not configured
- [x] Lint/syntax passes
