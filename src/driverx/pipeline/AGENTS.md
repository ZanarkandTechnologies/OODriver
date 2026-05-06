# Pipeline AGENTS.md

- Orchestrate only; do not bury planner, reasoner, renderer, or evaluator logic here.
- Save intermediate artifacts needed for QA and failure analysis.
- Keep batch runs fixture-compatible and deterministic.
- MEM-0009: treat real Waymo `batch_summary.json` and `batch_report.md` as the baseline surface before adding or comparing VLA/GPU backends.
- MEM-0032: promote CARLA video evidence only from the exact seed/config/case
  pair that produced the MP4; do not let stale retry folders or mismatched
  resume summaries become hero evidence.
