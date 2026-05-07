# Scenario Workbench

Scenario Workbench owns the end-to-end evidence object for the final minimal-shot
submission. It links a Scenario Studio candidate, CARLA video/tracks,
Alpamayo/RAG evidence, risk timeline, and dataset curation into one
`ScenarioRunBundle`.

## Entrypoints

- `build_scenario_run_bundle(inputs)` builds the in-memory lineage bundle.
- `write_scenario_run_bundle(run_dir, bundle)` writes JSON, Markdown, and HTML.
- CLI: `python -m driverx build-scenario-workbench-bundle ...`

## Example

```bash
PYTHONPATH=src python3 -m driverx build-scenario-workbench-bundle \
  --studio-batch tickets/TASK-103/artifacts/scenario-studio-v1/scenario_studio_batch.json \
  --video-evidence tickets/TASK-102/artifacts/task102-high-fidelity-hero-v6/ood_video_evidence.json \
  --alpamayo-batch tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/alpamayo_ood_batch_summary.json \
  --output-root tickets/TASK-108/artifacts \
  --run-id workbench-bundle-v1
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_scenario_workbench_bundle
```
