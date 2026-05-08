#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

PYTHONPATH=src python3 - <<'PY'
import json
from pathlib import Path

from driverx.evaluation.research_scenario_generator_score import (
    score_research_scenario_generator,
    write_research_scenario_generator_score,
)

score_dir = Path("tickets/TASK-156/autoresearch-production-generator")
score_dir.mkdir(parents=True, exist_ok=True)

def first_existing(*values: str) -> Path | None:
    for value in values:
        path = Path(value)
        if path.exists():
            return path
    return None

scenario_pack = first_existing(
    "artifacts/runs/task150-production-assets-proof/scenario_pack.assets.json",
    "artifacts/runs/task149-production-pack-proof/scenario_pack.json",
)
asset_manifest = first_existing(
    "artifacts/runs/task150-production-assets-proof/asset_generation_manifest.json",
)
asset_registry = first_existing(
    "artifacts/runs/task151-production-registry-proof/carla_asset_registry.json",
)
scenario_graph = first_existing(
    "artifacts/runs/task152-production-graph-proof/scenario_graph.json",
)
run_manifest = first_existing(
    "artifacts/runs/task153-live-prompt-to-carla-pulled/artifacts/runs/task153-live-prompt-to-carla-pack/task153-live-prompt-to-carla-assets/task153-live-prompt-to-carla-run/scenario_run_manifest.json",
    "artifacts/runs/task153-production-fake-proof/scenario_run_manifest.json",
)
workbench = first_existing(
    "artifacts/runs/task154-production-workbench-proof/workbench_summary.json",
)
library = first_existing(
    "artifacts/runs/task155-production-library-proof/scenario_library.json",
)
image_qa = first_existing(
    "tickets/TASK-153/artifacts/qa/prompt-to-carla-image-qa.json",
)

report = score_research_scenario_generator(
    scenario_pack_path=scenario_pack,
    asset_manifest_paths=tuple(path for path in (asset_manifest,) if path is not None),
    asset_registry_path=asset_registry,
    scenario_graph_path=scenario_graph,
    run_manifest_paths=tuple(path for path in (run_manifest,) if path is not None),
    workbench_summary_path=workbench,
    library_path=library,
    image_qa_report_path=image_qa,
)
write_research_scenario_generator_score(score_dir, report)
(score_dir / "baseline_score.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"METRIC research_scenario_generator_score={report['score']}")
for key, value in dict(report.get("components", {})).items():
    print(f"METRIC {key}={float(value):.4f}")
print(json.dumps(report, indent=2))
PY
