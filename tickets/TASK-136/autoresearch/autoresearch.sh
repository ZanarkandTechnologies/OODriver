#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT}"

PYTHONPATH=src python3 - <<'PY'
from __future__ import annotations

import json
import math
import os
import subprocess
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def exists(path: str | None) -> bool:
    return bool(path) and Path(path).exists()


def metric_line(name: str, value: float) -> None:
    if not math.isfinite(value):
        value = 0.0
    print(f"METRIC {name}={value:.4f}")


def help_available(command: str) -> bool:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    proc = subprocess.run(
        ["python3", "-m", "oodrive", command, "--help"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.returncode == 0


env_summary = load_json(Path("artifacts/runs/task135-env-demo-v1/environment_suite_summary.json"))
visual = load_json(Path("artifacts/runs/task136-env-c3-proof-v1/env_carla_proof_manifest.json"))
keyframes = load_json(Path("artifacts/runs/task137-keyframe-analysis-v1/keyframe_analysis.json"))
video = load_json(Path("artifacts/runs/task138-env-reasoned-carla-v1/environment_reasoned_carla_demo.json"))
review = Path("tickets/TASK-136/artifacts/review/task136-138-planning-review.json")

families = env_summary.get("families") if isinstance(env_summary.get("families"), list) else []
recipes = env_summary.get("recipes") if isinstance(env_summary.get("recipes"), list) else []
asset_requests = env_summary.get("asset_requests") if isinstance(env_summary.get("asset_requests"), list) else []

cli_generation = 0.0
if help_available("generate-envs"):
    cli_generation += 6.0
if len(families) >= 4:
    cli_generation += 5.0
if len(recipes) >= 6:
    cli_generation += 5.0
if len(asset_requests) >= 6:
    cli_generation += 4.0
cli_generation = min(cli_generation, 20.0)

visual_components = 0.0
if visual.get("same_lineage") is True:
    visual_components += 7.0
if exists(visual.get("preview_image_path")):
    visual_components += 7.0
if exists(visual.get("run_manifest_path")):
    visual_components += 4.0
if exists(visual.get("placement_plan_path")):
    visual_components += 3.0
if visual.get("status") == "passed":
    visual_components += 4.0
same_run_carla_visual = min(visual_components, 25.0)

analyses = keyframes.get("analyses") if isinstance(keyframes.get("analyses"), list) else []
reasoned = [
    item for item in analyses
    if isinstance(item, dict)
    and item.get("image_path")
    and (item.get("vla_reasoning") or item.get("blockers"))
    and item.get("source_time_s") is not None
]
real_reasoned = [item for item in reasoned if item.get("backend") not in {"fake", "blocked"} and item.get("status") == "passed"]
keyframe_reasoning = 0.0
keyframe_reasoning += min(len(reasoned), 5) * 3.0
if keyframes.get("same_lineage") is True:
    keyframe_reasoning += 4.0
if len(real_reasoned) >= 3:
    keyframe_reasoning += 4.0
elif len(reasoned) >= 5:
    keyframe_reasoning += 2.0
if "sampled_open_loop_reasoning=true" in list(keyframes.get("claim_boundaries", [])):
    keyframe_reasoning += 2.0
keyframe_reasoning = min(keyframe_reasoning, 25.0)

video_readiness = 0.0
duration = float(video.get("duration_s") or 0.0)
if exists(video.get("video_path")):
    video_readiness += 6.0
if exists(video.get("overlay_report_path")) or video:
    video_readiness += 4.0
if 60.0 <= duration <= 300.0:
    video_readiness += 4.0
segments = video.get("timeline_segments") if isinstance(video.get("timeline_segments"), list) else []
kinds = {str(item.get("kind")) for item in segments if isinstance(item, dict)}
if {"cli_generation", "carla_preview", "keyframe_reasoning", "claim_boundary"}.issubset(kinds):
    video_readiness += 4.0
if "time_warped_offline_demo=true" in list(video.get("claim_boundaries", [])):
    video_readiness += 2.0
video_readiness = min(video_readiness, 20.0)

reproducibility = 0.0
if Path("tickets/TASK-136/ticket.md").exists() and Path("tickets/TASK-137/ticket.md").exists() and Path("tickets/TASK-138/ticket.md").exists():
    reproducibility += 2.0
if Path("tickets/TASK-136/autoresearch/autoresearch.md").exists():
    reproducibility += 2.0
if Path("tickets/TASK-136/autoresearch/autoresearch.checks.sh").exists():
    reproducibility += 2.0
if review.exists():
    reproducibility += 2.0
if exists(visual.get("commands_path")) or exists(video.get("commands_path")):
    reproducibility += 2.0
reproducibility = min(reproducibility, 10.0)

score = cli_generation + same_run_carla_visual + keyframe_reasoning + video_readiness + reproducibility

metric_line("environment_to_reasoned_carla_score", score)
metric_line("cli_generation", cli_generation)
metric_line("same_run_carla_visual", same_run_carla_visual)
metric_line("keyframe_reasoning", keyframe_reasoning)
metric_line("video_readiness", video_readiness)
metric_line("reproducibility", reproducibility)
PY
