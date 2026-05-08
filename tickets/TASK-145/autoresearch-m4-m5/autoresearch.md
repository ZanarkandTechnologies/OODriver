# Autoresearch: Improve M4/M5 Evidence Clarity

## Objective

Maximize the judge-visible strength of OODrive's M4/M5 evidence: memory retrieval, Alpamayo baseline-vs-memory reasoning, decongested explanation surfaces, and scenario ancestry/reference grounding. This session optimizes the evidence layer around already-existing simulator/model artifacts instead of chasing new CARLA or remote inference.

## Metric

- Primary: `m4_m5_evidence_clarity_score` (points, higher is better)
- Verify: `./autoresearch.sh`
- Guard: `./autoresearch.checks.sh`
- Direction: higher
- Target: `>=85`
- Max iterations: `8`
- Noise policy: deterministic artifact score; rerun any gain above 10 points before treating it as durable.

## Scope

- Editable:
  - `src/driverx/memory/`
  - `src/driverx/pipeline/`
  - `src/driverx/scenarios/studio_product_cli.py`
  - `src/driverx/scenarios/studio_product_*runtime.py`
  - `src/driverx/evaluation/`
  - `tests/`
  - `tickets/TASK-145/`
  - `tickets/TASK-146/`
  - `tickets/TASK-147/`
  - `tickets/TASK-148/`
  - `README.md`
  - `docs/HISTORY.md`
- Read-only:
  - existing TASK-104 Alpamayo/RAG comparison artifacts
  - existing TASK-105 Fail2Drive extension artifacts
  - existing TASK-131 hero video/overlay artifacts
  - generated MP4s under `artifacts/runs/`
- Off limits:
  - secrets, HF tokens, model weights, dataset shards, hosted vector DB writes, threshold lowering, and any closed-loop/real-time VLA claim.

## Constraints

- Be honest about retrieval: current backend is lexical/tag memory, not embeddings/vector search.
- Prefer local reproducible evidence over provider/API dependencies.
- Improve judge comprehension by reducing HUD congestion, not by adding more in-video text.
- Preserve claim boundaries: `closed_loop_vla_control=false`, `real_time_vla_control=false`, `sampled_open_loop_reasoning=true`.

## What's Been Tried

- TASK-104 produced 3 passed open-loop Alpamayo+memory comparison records with `reasoning_changed_count=2`, `memory_case_count=3`, mean latency about `92550ms`, and mean VRAM about `23380MB`.
- TASK-131 produced a score-gated hero video with 8 reasoning/RAG events and `hero_demo_score=100`.
- Current retrieval is implemented by token/tag overlap in `src/driverx/memory/bank.py`.
- Current overlay is mechanically complete but visually congested.

## Next Ideas

- TASK-145: add a retrieval ledger with query terms, candidate scores, selected/rejected memories, and source citations.
- TASK-146: add Alpamayo baseline-vs-memory reasoning diff cards.
- TASK-147: render compact HUD plus chaptered HTML evidence panel.
- TASK-148: build scenario ancestry cards linking generated cases to rare-event/failure families and memory principles.
