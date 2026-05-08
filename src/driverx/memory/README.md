# driverx.memory

## Purpose

Turns closed-loop scenario results into compact safety memory and retrieves
relevant entries for generated OOD recipes.

## Public API

- `build_memory_bank(results)`
- `retrieve_memory(recipe, bank, limit)`
- `retrieve_memory_with_ledger(recipe, bank, limit)`
- `write_memory_bank(run_dir, bank)`
- `write_memory_retrieval_ledger(run_dir, ledger)`

## Example

```bash
PYTHONPATH=src python3 -m driverx build-memory \
  --results tests/fixtures/fail2drive_like/results.json
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_memory_retrieval_ledger tests.test_scenario_forge
```

## Retrieval Ledger

`retrieve_memory_with_ledger` wraps the deterministic tag/token overlap backend
and records query tokens, ranked candidates, selected/rejected rows, source
scenarios, scores, and claim boundaries. It is a local lexical retrieval
surface, not semantic vector RAG; generated reports must keep
`retrieval_backend=lexical_tag_overlap`, `semantic_vector_rag=false`, and
`embedding_rag=false` unless a real embedding index is added.
