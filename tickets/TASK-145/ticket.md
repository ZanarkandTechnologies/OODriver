# TASK-145: Memory Retrieval Ledger V2

## Status
- state: building
- phase: documenting
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-103, TASK-104, TASK-131
- location: `src/driverx/memory`, `src/driverx/pipeline`, `src/driverx/scenarios/studio_product_cli.py`, `src/driverx/evaluation`, `tests`, `tickets/TASK-145`
- enter when: M4/M5 evidence uses memory IDs and RAG callouts, but the retrieval method is tag/token overlap without a visible retrieval ledger, candidate scores, citations, or rejected alternatives.
- leave when: OODrive writes a retrieval ledger that shows query terms, scored candidate memories, selected/rejected entries, source scenarios, ranking method, citations, and claim boundaries; the ledger is consumable by Alpamayo package/report/video tooling.
- blockers: none for local lexical/FTS-style retrieval; optional embeddings stay out of scope unless added as a follow-up.
- spawned follow-ups: TASK-146 consumes ledger for Alpamayo memory-diff reporting; TASK-147 renders selected ledger rows in the decongested evidence panel.
- complexity: M

### Summary

Upgrade the current memory/RAG story from "we included a memory ID" to "we can prove exactly what was retrieved, why, and how it influenced the model package." The now-scope is an honest local hybrid lexical ledger: token/tag overlap plus optional SQLite FTS/BM25-style scoring if available through the standard library/runtime. Do not claim semantic vector RAG unless an embedding index exists.

### Scope

- In scope: ledger data model, retrieval scorer, selected/rejected candidates, source citations, JSON/Markdown report, CLI/product wrapper, tests, and integration into Alpamayo package/evaluation metadata.
- In scope: explicit claim labels: `retrieval_backend=lexical_tag_overlap` or `retrieval_backend=sqlite_fts` when implemented.
- Out of scope: hosted vector DB, external embedding API, secrets, online provider calls, re-running Alpamayo.

### Gap Analysis

- Current state: [src/driverx/memory/bank.py](/Users/kenjipcx/SOTA/0xDriver/src/driverx/memory/bank.py) tokenizes recipe fields and memory tags, then sorts by overlap/confidence. It returns entries but not a retrieval trace.
- Production expectation: credible RAG systems expose retrieval substrate, ranked documents, source metadata/citations, and retrieval-vs-generation evaluation. LangChain docs frame RAG around loaders/splitters/embeddings/vector stores or existing search tools; LlamaIndex exposes source/citation nodes; LangSmith/Haystack evaluate retrieval separately from generation.
- Missing gaps: no ledger, no rejected candidates, no score explanations, no source citation table, no query expansion record, no metric for whether retrieval was legible.
- Recommended boundary: ship a reproducible local retrieval ledger before adding embeddings. It answers the judge's "how do you RAG?" question honestly and quickly.

### Plan

#### Change

Add a retrieval ledger V2 around the existing `retrieve_memory` path:

```bash
PYTHONPATH=src python3 -m oodrive memory-ledger \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --scenario-id studio-0128-malaysian-wet-roadwork-a-roadside-food-cart-cons-v00 \
  --memory-bank <memory_bank.json> \
  --run-id task145-memory-ledger-v1
```

#### Why

M4 currently says "RAG" but the artifact does not prove a production-like retrieval step. A ledger makes the retrieval step inspectable without pretending we have vector search.

#### Before -> After

- Before: `memory_ids=["mem-sample-motorcycle-filtering"]` appears in reports/overlays.
- After: `retrieval_ledger.json` explains the query, backend, top-k candidates, selected entries, rejected entries, source scenarios, scores, and principles.

#### Touch

- `src/driverx/memory/types.py`
- `src/driverx/memory/bank.py`
- `src/driverx/memory/README.md`
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/scenarios/studio_product_memory_runtime.py` (new)
- `src/driverx/evaluation/m4_m5_evidence_score.py` (if metric is pulled into product code)
- `tests/test_memory_retrieval_ledger.py` (new)
- `tests/test_oodrive_cli.py`
- `tickets/TASK-145/autoresearch-m4-m5/*`

#### Inspect

- `src/driverx/pipeline/alpamayo_ood_batch.py`
- `src/driverx/pipeline/rag_comparison.py`
- `src/driverx/policies/alpamayo_ood_package.py`
- `tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/alpamayo_ood_batch_summary.json`
- `artifacts/runs/task128-oodrive-live-product/reasoning/evaluations/*/policy_evaluation.json`

#### Signature Delta

```python
src/driverx/memory/types.py / MemoryRetrievalCandidate(...): dict
src/driverx/memory/types.py / MemoryRetrievalLedger(...): dict
src/driverx/memory/bank.py / retrieve_memory_with_ledger(recipe, bank, limit, backend="lexical_tag_overlap"): MemoryRetrievalLedger
src/driverx/memory/bank.py / write_memory_retrieval_ledger(run_dir, ledger): dict[str, str | int]
src/driverx/scenarios/studio_product_memory_runtime.py / run_studio_memory_ledger(...): StudioCommandResult
```

#### Type Sketch

```python
MemoryRetrievalCandidate = {
  "entry_id": str,
  "rank": int,
  "selected": bool,
  "score": float,
  "overlap_terms": list[str],
  "confidence": float,
  "source_scenario": str,
  "principle": str,
  "recommended_behavior": str,
  "rejection_reason": str | None,
}

MemoryRetrievalLedger = {
  "scenario_id": str,
  "query_terms": list[str],
  "backend": "lexical_tag_overlap" | "sqlite_fts",
  "limit": int,
  "selected_memory_ids": list[str],
  "candidates": list[MemoryRetrievalCandidate],
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example

`ScenarioRecipe(memory_query=["motorcycle_filtering", "wet_roadwork"])`
-> query terms normalized
-> all `MemoryEntry.tags` scored
-> top candidates selected with overlap/confidence
-> ledger records `mem-sample-motorcycle-filtering`, rejected lower-overlap entries, source scenario, principle
-> Alpamayo package/report receives `retrieval_ledger_path`.

#### Execution Steps

1. Add ledger dataclasses and JSON serializers.
2. Preserve current `retrieve_memory(...)` behavior by making it call the ledger path and return selected entries.
3. Add Markdown report with query, selected rows, rejected rows, and claim labels.
4. Add `oodrive memory-ledger` wrapper and CLI registration.
5. Add fixture tests for ranking, tie-breakers, empty bank, no-overlap, and report output.
6. Update docs and autoresearch metric inputs.

#### Recommendation

Implement lexical ledger first, then optionally add SQLite FTS as a backend if it can be done without new dependencies.

#### Options Considered

- Full embeddings/vector store: stronger technically, but adds setup/API risk before the deadline.
- Ledger-only over current overlap: fastest and honest.
- SQLite FTS/BM25 plus ledger: best if time permits; still local and reproducible.

#### Blast Radius

- Policy/package callers should keep receiving `list[MemoryEntry]`.
- New CLI is additive.
- Reports/overlays gain provenance fields but should not require them until TASK-147.

#### Risks

- Overclaiming RAG. Mitigation: backend labels must state lexical/FTS, not vector.
- Ledger bloat. Mitigation: cap candidates and keep full raw JSON separate from video/UI.

### Acceptance Criteria

- [x] `retrieve_memory_with_ledger` returns selected and rejected candidates with stable scores.
- [x] Existing `retrieve_memory` tests still pass.
- [x] `oodrive memory-ledger` writes JSON and Markdown artifacts.
- [x] Reports name retrieval backend and claim boundaries.
- [x] Tests cover ranking and selected/rejected ledger behavior.

### Verification

```bash
PYTHONPATH=src python3 -m unittest tests.test_memory_retrieval_ledger tests.test_scenario_forge tests.test_oodrive_cli
bash tickets/TASK-145/autoresearch-m4-m5/autoresearch.sh
bash tickets/TASK-145/autoresearch-m4-m5/autoresearch.checks.sh
```

### Evidence

- Planned ledger artifact: `artifacts/runs/task145-memory-ledger-v1/retrieval_ledger.json`
- Planned report: `artifacts/runs/task145-memory-ledger-v1/retrieval_ledger.md`
- Autoresearch session: `tickets/TASK-145/autoresearch-m4-m5/autoresearch.md`
- Planning review: `tickets/TASK-145/artifacts/review/task145-148-impl-plan-review.json`
- Implementation review: `tickets/TASK-145/artifacts/review/task145-148-impl-review.json`
- 2026-05-08 08:33 +0800: Implemented `MemoryRetrievalLedger`, additive `oodrive memory-ledger`, JSON/Markdown reports, default blocker/occlusion fixture memories, and CLI help coverage.
- 2026-05-08 08:33 +0800: Artifact generated: `artifacts/runs/task145-memory-ledger-v1/retrieval_ledger.json` with selected/rejected candidates and `retrieval_backend=lexical_tag_overlap`.
- 2026-05-08 08:33 +0800: Nested autoresearch after TASK-145..148 implementation: `METRIC m4_m5_evidence_clarity_score=100.0000`.
- 2026-05-08 08:33 +0800: Focused verification passed: `PYTHONPATH=src python3 -m unittest tests.test_memory_retrieval_ledger tests.test_alpamayo_reasoning_diff tests.test_reasoning_evidence_panel tests.test_scenario_ancestry_cards tests.test_reasoning_timeline_overlay tests.test_oodrive_cli` (`15 tests OK`).
- 2026-05-08 08:33 +0800: Nested guard passed: `bash tickets/TASK-145/autoresearch-m4-m5/autoresearch.checks.sh` (`19 tests OK`).
- 2026-05-08 08:33 +0800: Full gate passed: `bash scripts/pre_push_check.sh` (`440 tests OK`, `5 skipped`).

### Blockers

- None for the local lexical ledger.
