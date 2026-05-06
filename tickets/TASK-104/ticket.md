# TASK-104: Alpamayo Plus RAG Evaluation Batch Over Generated OOD

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-100, TASK-101, TASK-102, TASK-103
- location: `src/driverx/pipeline/alpamayo_ood_batch.py`, `src/driverx/pipeline/alpamayo_ood_evaluation.py`, `scripts`, `tickets/TASK-104/artifacts`
- enter when: selected generated scenarios have Alpamayo packages or video/capture frames
- leave when: at least 3 selected scenarios have baseline-vs-memory Alpamayo comparison artifacts, or precise live model blockers are recorded per case
- blockers: RunPod Kasm Alpamayo environment and HF auth must remain available for live inference; fallback uses existing TASK-100 proof plus planned commands
- spawned follow-ups: TASK-106
- complexity: M
- assignee: generalPurpose

### Summary

Run the actual minimal-shot model comparison: frozen Alpamayo on generated OOD
cases with and without retrieved DriverX safety memory. This is the clearest
research contribution: does prompt-side memory change reasoning and trajectory
intent without fine-tuning?

### Scope

- In scope: batch Alpamayo package generation from selected videos/captures,
  baseline inference, memory-augmented package generation, memory inference,
  comparison aggregation, latency/VRAM reporting, and evidence warnings.
- Out of scope: model fine-tuning, real-time serving optimization, and claiming
  closed-loop success unless replay/control artifacts are explicitly generated.

### Plan

#### Change

Extend the existing Alpamayo OOD batch flow into a final-evidence batch over
selected generated scenarios.

#### Why

The challenge is minimal-shot autonomy. A model+RAG comparison over generated
OOD cases is higher signal than more setup, more maps, or a single pretty video.

#### Before -> After

- Before: one hero Alpamayo open-loop proof exists.
- After: multiple generated OOD scenarios show baseline vs memory CoC,
  trajectory deltas, latency, VRAM, and safety flags.

#### Touch

- `src/driverx/pipeline/alpamayo_ood_batch.py`: ensure selected cases can run
  baseline and memory pairs, not only plan one package.
- `src/driverx/pipeline/alpamayo_ood_evaluation.py`: aggregate stronger
  reasoning/trajectory/safety deltas.
- `scripts/run_remote_alpamayo_carla_inference.sh`: reuse, do not rewrite.
- `tickets/TASK-104/artifacts`: batch output and pulled remote payloads.

#### Inspect

- `tickets/archive/TASK-100/artifacts/hero-alpamayo-live/alpamayo_live_prediction.json`
- `tickets/archive/TASK-100/artifacts/task100-hero-alpamayo-policy/alpamayo_policy_decision.json`
- `src/driverx/policies/alpamayo_materializer.py`
- `src/driverx/policies/alpamayo_live.py`
- `src/driverx/pipeline/alpamayo_ood_batch.py`
- `src/driverx/pipeline/alpamayo_ood_evaluation.py`

#### Signature Delta

```python
AlpamayoOodBatchConfig(...,
  run_memory_pairs: bool = False,
  memory_entries_path: Path | None = None,
  selected_matrix_path: Path | None = None,
)

run_alpamayo_ood_batch(config): dict[str, Any]

build_alpamayo_ood_evaluation(run_dir, inputs): dict[str, Any]
```

#### Type Sketch

```python
AlpamayoRagCase = {
  "scenario_id": str,
  "package_path": str,
  "baseline_prediction": str | None,
  "memory_prediction": str | None,
  "baseline_decision": str | None,
  "memory_decision": str | None,
  "comparison_path": str | None,
  "reasoning_changed": bool | None,
  "trajectory_final_l2_m": float | None,
  "latency_ms": [float | None, float | None],
  "vram_peak_mb": [float | None, float | None],
  "status": "passed" | "planned" | "blocked",
}
```

#### Typed Flow Example

`TASK-102 video/capture package`
-> baseline remote Alpamayo inference
-> `run-alpamayo-live` baseline decision
-> memory-augmented package
-> memory remote Alpamayo inference
-> `build-alpamayo-ood-comparison`
-> `alpamayo_rag_batch_summary.md`.

#### Execution Steps

1. Use TASK-101 matrix to select 3 cases: hero, failure/edge, and one diverse
   generated scenario.
2. Build or reuse Alpamayo packages for each case.
3. Run baseline inference on RunPod for missing cases.
4. Build memory-augmented packages from existing memory bank.
5. Run memory inference on RunPod.
6. Convert predictions into policy decisions.
7. Build comparisons and aggregate deltas.
8. Mark every case as passed/planned/blocked with exact missing artifact.

#### Recommendation

Run 3 cases first, not 20. The final video/write-up needs interpretable deltas,
not a huge table of slow inferences.

#### Options Considered

- One hero-only comparison: safe but too thin.
- Large batch over all generated cases: impressive, but too slow and likely to
  burn the remaining schedule.
- Recommended: 3-case batch with rich reports and one failure analysis.

#### Blast Radius

Medium. Touches batch orchestration and remote command handling. Existing
single-case conversion must keep passing.

#### Risks

- Alpamayo latency is about 112s/case on current settings. Three baseline plus
  memory pairs can take 10-20 minutes plus overhead, acceptable if the pod is
  stable.
- Kasm proxy logs are awkward. Continue avoiding secret transmission and pull
  compact artifacts only.

### Gap Analysis

Current proof shows Alpamayo can react to one generated case. The submission
needs a minimal-shot claim: memory retrieved from prior failures changes
reasoning/trajectory on novel generated cases. This ticket supplies that claim
with measured caveats.

### Acceptance Criteria

- [x] AC-1: At least 3 selected cases have baseline-vs-memory records, or each
  blocked case records an actionable blocker.
- [x] AC-2: Reports include memory ids, trajectory deltas,
  latency, VRAM, and open-loop claim boundaries.
- [x] AC-3: Batch summary separates model failure, artifact gap, and simulator
  gap.
- [x] AC-4: No secrets, model weights, datasets, or large videos are committed.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_alpamayo_ood_batch tests.test_alpamayo_ood_evaluation`
- `python3 -m compileall -q src tests`
- CLI smoke over three existing baseline-vs-memory comparison artifacts.
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Inputs available: RunPod Kasm Alpamayo env, HF auth, TASK-100 proof.
- Human gates: if HF token expires or pod is killed, user must refresh.
- Compute: RunPod Kasm GPU for live inference; local for conversion/reporting.
- Stop condition: 3-case batch evidence or precise blockers.

### Evidence

- `tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/alpamayo_ood_batch_summary.json`
- `tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/alpamayo_ood_batch_summary.md`
- `tickets/TASK-104/artifacts/review/task104-implementation-review.json`
- Batch summary: 3 passed open-loop Alpamayo+memory comparison records,
  `reasoning_changed_count=2`, `memory_case_count=3`,
  `mean_trajectory_final_l2_m=2.8219`, `mean_latency_ms=92550.1317`,
  `max_vram_peak_mb=23557.31`.

### Blockers

- None for replaying the existing comparison batch. Live RunPod availability is
  only required for generating additional missing comparisons.
