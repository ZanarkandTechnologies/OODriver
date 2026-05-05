# TASK-014: Retrieval-Augmented VLA Comparison Harness

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-010, TASK-013
- location: `src/driverx/pipeline`, `src/driverx/policies`, `src/driverx/memory`, tests, reports
- enter when: behavior traces and policy adapters exist
- leave when: no-memory vs memory-guided policy comparison reports are generated
- blockers: real VLA needed only for final live claim; mock comparison can prove harness
- spawned follow-ups: final demo and runtime acceleration
- complexity: L

## Summary

Run matched scenarios with and without retrieved safety memory, then compare
success proxies, infractions, entity tracks, reason summaries, and latency.
Until a real VLA is attached, the mock policy proves harness behavior only.

## Acceptance Criteria

- [x] Comparison runner executes `policy` and `policy+memory` modes on the same
  scenario seed.
- [x] Report includes scenario id, retrieved memory ids, behavior metrics,
  policy outputs, latency, and improvement/regression notes.
- [x] Mock policy demonstrates a controlled memory-sensitive outcome without
  claiming real model performance.
- [x] Tests cover deterministic A/B pairing and report aggregation.
- [x] Live-model blockers are logged without blocking local harness tests.

## Verification

- `bash scripts/pre_push_check.sh`
- `PYTHONPATH=src python3 -m driverx run-rag-comparison --policy mock --run-id task14-rag`

## Blockers

- Real VLA comparison requires a selected policy backend and credentials.

## Evidence

- Local tests: `PYTHONPATH=src python3 -m unittest tests.test_rag_comparison tests.test_policies tests.test_cli` passed with 27 tests.
- Mock comparison proof: `PYTHONPATH=src python3 -m driverx run-rag-comparison --policy mock --run-id task14-rag`.
- Alpamayo blocker proof: `PYTHONPATH=src python3 -m driverx run-rag-comparison --policy alpamayo --run-id task14-rag-alpamayo-blocked`.
- Mock report: `artifacts/runs/task14-rag/rag_comparison.md`.
- Mock JSON: `artifacts/runs/task14-rag/rag_comparison.json`.
- Blocker report: `artifacts/runs/task14-rag-alpamayo-blocked/rag_comparison.md`.
- Controlled mock outcome: no-memory proxy score `58.0`; memory-guided proxy
  score `95.0`; `live_model_claim=false`.
