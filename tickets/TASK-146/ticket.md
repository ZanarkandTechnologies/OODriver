# TASK-146: M4 Alpamayo Memory Reasoning Diff Report

## Status
- state: building
- phase: documenting
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-104, TASK-145
- location: `src/driverx/pipeline`, `src/driverx/policies`, `src/driverx/scenarios/studio_product_cli.py`, `tests`, `tickets/TASK-146`
- enter when: TASK-104 proves three open-loop Alpamayo+memory comparisons, but the result is summarized as counts and deltas rather than a judge-readable reasoning diff.
- leave when: OODrive writes a baseline-vs-memory reasoning diff report that shows retrieved memory, changed/not-changed reasoning, trajectory delta, safety flags, latency/VRAM, and open-loop claim boundaries per case.
- blockers: no new Alpamayo inference required; uses existing TASK-104 comparison artifacts unless optional fresh decisions are supplied.
- spawned follow-ups: TASK-147 consumes compact diff events for video/HTML presentation.
- complexity: M

### Summary

Turn M4 from "we have Alpamayo/RAG batch metrics" into a clear before/after explanation. The report should answer: what did memory retrieve, did Alpamayo reasoning change, did trajectory intent change, what safety principle was used, and how slow/expensive was the run?

### Scope

- In scope: diff report builder, CLI wrapper, JSON/Markdown output, compact event extraction for TASK-147, tests using existing TASK-104 fixtures.
- Out of scope: fresh remote Alpamayo inference, closed-loop control, model prompt rewrites.

### Gap Analysis

- Current state: [src/driverx/pipeline/alpamayo_ood_batch.py](/Users/kenjipcx/SOTA/0xDriver/src/driverx/pipeline/alpamayo_ood_batch.py) aggregates `reasoning_changed_count`, `memory_case_count`, latency, VRAM, and trajectory deltas.
- Production expectation: a model-comparison artifact should show each pair's inputs, retrieval evidence, output differences, and resource cost. RAG observability guidance separates retrieval quality from generation quality.
- Missing gaps: no per-case diff prose, no compact "what changed" event, no evidence table for trajectory/safety deltas, no obvious M4 slide/report.
- Recommended boundary: report over existing artifacts first; use ledger paths from TASK-145 when available.

### Plan

#### Change

Add:

```bash
PYTHONPATH=src python3 -m oodrive reasoning-diff \
  --alpamayo-batch tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/alpamayo_ood_batch_summary.json \
  --retrieval-ledger artifacts/runs/task145-memory-ledger-v1/retrieval_ledger.json \
  --run-id task146-reasoning-diff-v1
```

#### Why

The current batch proves technical execution, but judges need a compact "memory changed this" artifact.

#### Before -> After

- Before: `reasoning_changed_count=2`, `mean_trajectory_final_l2_m=2.8219`, raw comparison paths.
- After: per-case cards with baseline summary, memory summary, selected principle, trajectory delta, latency/VRAM, and claim label.

#### Touch

- `src/driverx/pipeline/alpamayo_reasoning_diff.py` (new)
- `src/driverx/scenarios/studio_product_reasoning_diff_runtime.py` (new)
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/pipeline/README.md`
- `tests/test_alpamayo_reasoning_diff.py` (new)
- `tests/test_oodrive_cli.py`

#### Inspect

- `src/driverx/pipeline/alpamayo_ood_evaluation.py`
- `src/driverx/pipeline/alpamayo_ood_batch.py`
- `src/driverx/policies/alpamayo_offline.py`
- `tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/alpamayo_ood_batch_summary.json`

#### Signature Delta

```python
src/driverx/pipeline/alpamayo_reasoning_diff.py / build_alpamayo_reasoning_diff(batch_path, retrieval_ledger_paths=(), output_root, run_id): dict
src/driverx/pipeline/alpamayo_reasoning_diff.py / extract_reasoning_diff_events(diff_report): list[dict]
src/driverx/scenarios/studio_product_reasoning_diff_runtime.py / run_studio_reasoning_diff(...): StudioCommandResult
```

#### Type Sketch

```python
ReasoningDiffCase = {
  "scenario_id": str,
  "memory_ids": list[str],
  "retrieval_ledger_path": str | None,
  "reasoning_changed": bool | None,
  "baseline_reasoning": str | None,
  "memory_reasoning": str | None,
  "trajectory_final_l2_m": float | None,
  "latency_ms": list[float],
  "vram_peak_mb": list[float],
  "safety_flags": dict,
  "takeaway": str,
}
```

#### Typed Flow Example

`alpamayo_ood_batch_summary.json`
-> load each record's `comparison_path`
-> extract baseline/memory CoC snippets and trajectory deltas
-> join retrieval ledger by memory id or scenario id
-> write `alpamayo_reasoning_diff.json` plus a Markdown table/card report
-> TASK-147 consumes `reasoning_diff_events`.

#### Execution Steps

1. Implement loaders that tolerate missing comparison files by writing blockers per case.
2. Extract concise baseline/memory reasoning snippets with word limits.
3. Join optional retrieval ledger evidence.
4. Write JSON/Markdown and event list.
5. Add CLI command `oodrive reasoning-diff`.
6. Add tests for passed cases, missing comparison, and claim-boundary preservation.

#### Recommendation

Do not rerun Alpamayo here. Make existing evidence legible first.

#### Options Considered

- Fresh inference: higher prestige but slow and remote-dependent.
- Pure docs summary: fast but weak.
- Structured diff report: best M4 lift under time pressure.

#### Blast Radius

- Additive command and reports.
- No changes to Alpamayo runtime.
- TASK-147 can depend on stable diff event schema.

#### Risks

- CoC text may be too long for video. Mitigation: report stores full-ish snippets; video receives short takeaways only.

### Acceptance Criteria

- [x] Diff report includes all TASK-104 cases.
- [x] Each case records memory ids, reasoning changed/not changed, trajectory delta, latency/VRAM, and open-loop labels.
- [x] Missing files are tolerated through unavailable snippet/default fields.
- [x] CLI command writes JSON/Markdown.

### Verification

```bash
PYTHONPATH=src python3 -m unittest tests.test_alpamayo_reasoning_diff tests.test_alpamayo_ood_evaluation tests.test_oodrive_cli
bash tickets/TASK-145/autoresearch-m4-m5/autoresearch.sh
```

### Evidence

- Planned diff: `artifacts/runs/task146-reasoning-diff-v1/alpamayo_reasoning_diff.json`
- Planned report: `artifacts/runs/task146-reasoning-diff-v1/alpamayo_reasoning_diff.md`
- 2026-05-08 08:33 +0800: Implemented `build_alpamayo_reasoning_diff`, `extract_reasoning_diff_events`, additive `oodrive reasoning-diff`, and focused tests.
- 2026-05-08 08:33 +0800: Artifact generated: `artifacts/runs/task146-reasoning-diff-v1/alpamayo_reasoning_diff.json` with `case_count=3`, `reasoning_changed_count=2`, `memory_case_count=3`.
- 2026-05-08 08:33 +0800: Claim boundaries preserved: `sampled_open_loop_reasoning=true`, `closed_loop_vla_control=false`, `real_time_vla_control=false`.
- 2026-05-08 08:33 +0800: Implementation review: `tickets/TASK-145/artifacts/review/task145-148-impl-review.json`.

### Blockers

- None for existing-artifact diffing.
