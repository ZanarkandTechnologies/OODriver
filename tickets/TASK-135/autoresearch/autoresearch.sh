#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

PYTHONPATH=src python3 - <<'PY'
from __future__ import annotations

import contextlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory

from driverx.environments import EnvironmentSuiteConfig, run_environment_forge
from oodrive.cli import main as oodrive_main

repo = Path(".")

with TemporaryDirectory() as tmp:
    summary = run_environment_forge(
        EnvironmentSuiteConfig(
            template_ids=(
                "construction_lane_closure",
                "roadside_market_occlusion",
                "flooded_road",
                "night_rain_fog",
                "dense_regional_traffic",
                "school_zone_unstructured_crossing",
            ),
            severity=4,
            count=6,
            random_seed=31,
            output_root=Path(tmp),
            run_id="env-demo-score",
        )
    )

families = set(summary.get("families", []))
recipes = list(summary.get("recipes", []))
assets = list(summary.get("asset_requests", []))
weather_ready = all(isinstance(recipe.get("weather"), dict) and recipe.get("weather") for recipe in recipes)
traffic_ready = all(isinstance(recipe.get("traffic"), dict) and recipe.get("traffic") for recipe in recipes)
road_local_assets = [
    asset for asset in assets
    if isinstance(asset.get("intended_placement"), dict)
    and asset["intended_placement"].get("coordinate_frame") == "road_local"
]
generation_substance = (
    10.0 * min(len(families) / 6.0, 1.0)
    + 6.0 * min(len(assets) / 10.0, 1.0)
    + 5.0 * bool(weather_ready)
    + 4.0 * bool(traffic_ready)
    + 5.0 * min(len(road_local_assets) / max(len(assets), 1), 1.0)
)

help_stream = io.StringIO()
with contextlib.redirect_stdout(help_stream):
    try:
        oodrive_main(["--help"])
    except SystemExit:
        pass
oodrive_help = help_stream.getvalue()
product_surface = (
    5.0 * ("generate" in oodrive_help)
    + 5.0 * ("generate-envs" in oodrive_help)
    + 5.0 * ("export-env-demo" in oodrive_help)
    + 5.0 * ("score-env-demo" in oodrive_help)
)

demo_pack_path = repo / "src/driverx/pipeline/environment_demo_pack.py"
demo_score_path = repo / "src/driverx/evaluation/environment_demo_score.py"
demo_pack_test = repo / "tests/test_environment_demo_pack.py"
demo_score_test = repo / "tests/test_environment_demo_score.py"
submission_story = (repo / "src/driverx/pipeline/submission_story_pack.py").read_text(encoding="utf-8")
judge_app_legibility = (
    8.0 * demo_pack_path.exists()
    + 5.0 * ("Environment Studio" in demo_pack_path.read_text(encoding="utf-8") if demo_pack_path.exists() else False)
    + 5.0 * demo_pack_test.exists()
    + 4.0 * ("environment_demo" in submission_story or "Environment Studio" in submission_story)
    + 3.0 * ("claim_boundaries" in submission_story)
)

ticket_text = (repo / "tickets/TASK-135/ticket.md").read_text(encoding="utf-8")
video_readiness = (
    5.0 * ("video_storyboard.md" in ticket_text)
    + 5.0 * ("1-5 minute" in ticket_text)
    + 5.0 * ((repo / "artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/oodrive_hero_demo.mp4").exists())
)

reproducibility = (
    2.0 * (repo / "tests/test_environment_generator.py").exists()
    + 2.0 * demo_pack_test.exists()
    + 2.0 * demo_score_test.exists()
    + 2.0 * demo_score_path.exists()
    + 2.0 * ("environment_demo_readiness_score" in ticket_text)
)

score = generation_substance + product_surface + judge_app_legibility + video_readiness + reproducibility
print(f"METRIC environment_demo_readiness_score={score:.4f}")
print(f"METRIC generation_substance={generation_substance:.4f}")
print(f"METRIC product_surface={product_surface:.4f}")
print(f"METRIC judge_app_legibility={judge_app_legibility:.4f}")
print(f"METRIC video_readiness={video_readiness:.4f}")
print(f"METRIC reproducibility={reproducibility:.4f}")
PY
