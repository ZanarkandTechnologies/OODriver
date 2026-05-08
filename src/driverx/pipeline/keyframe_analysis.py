"""Frame-linked Alpamayo keyframe analysis artifacts for OODrive."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios.studio_product_helpers import oodrive_command


REQUIRED_CLAIM_BOUNDARIES = [
    "sampled_open_loop_reasoning=true",
    "closed_loop_vla_control=false",
    "real_time_vla_control=false",
]


def select_carla_keyframes(
    *,
    visual_proof_path: Path,
    run_manifest_path: Path | None = None,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Select keyframes from the same-run CARLA visual proof."""

    visual = _load_json(visual_proof_path)
    manifest_path = run_manifest_path or _optional_path(visual.get("run_manifest_path"))
    run_manifest = _load_json(manifest_path) if manifest_path is not None and manifest_path.exists() else {}
    frame_paths = _frame_paths(visual, run_manifest)
    if not frame_paths:
        return []
    selected = _uniform_sample(frame_paths, max(1, limit))
    fps = _fps_from_manifest(run_manifest)
    keyframes: list[dict[str, Any]] = []
    for index, frame in enumerate(selected):
        frame_index = _frame_index(frame, fallback=index)
        keyframes.append(
            {
                "keyframe_id": f"kf-{index + 1:02d}",
                "frame_index": frame_index,
                "source_time_s": round(frame_index / max(fps, 1.0), 3),
                "image_path": str(frame),
                "selection_reason": "carla_preview" if str(frame) == str(visual.get("preview_image_path")) else "uniform_sample",
                "risk": {
                    "level": "unknown" if not visual.get("same_lineage") else "review_required",
                    "nearest_actor": None,
                    "distance_m": None,
                },
            }
        )
    return keyframes


def build_keyframe_analysis(
    *,
    visual_proof_path: Path,
    db_path: Path,
    run_manifest_path: Path,
    backend: str,
    keyframe_count: int,
    output_root: Path,
    run_id: str,
) -> dict[str, Any]:
    """Build a keyframe analysis manifest with fake, blocked, or real-backend hooks."""

    visual = _load_json(visual_proof_path)
    run_dir = prepare_run_dir(output_root, run_id)
    keyframes = select_carla_keyframes(
        visual_proof_path=visual_proof_path,
        run_manifest_path=run_manifest_path,
        limit=keyframe_count,
    )
    blockers: list[str] = []
    analyses: list[dict[str, Any]] = []
    backend = backend.strip().lower()
    if backend not in {"fake", "blocked", "alpamayo-local"}:
        raise ValueError("backend must be one of: fake, blocked, alpamayo-local")
    if not keyframes:
        blockers.append(
            "No CARLA keyframe images were available. Run `oodrive render-env --live` on the Kasm/CARLA host first."
        )
    elif backend == "fake":
        analyses = [_fake_analysis(frame, visual) for frame in keyframes]
    else:
        blockers.append(_backend_blocker(backend))
        analyses = [_blocked_analysis(frame, backend, blockers[-1]) for frame in keyframes]
    status = "passed" if analyses and backend == "fake" else "blocked" if blockers else "passed"
    payload = {
        "status": status,
        "backend": backend,
        "model_evidence": backend == "alpamayo-local" and status == "passed",
        "visual_proof_path": str(visual_proof_path),
        "db_path": str(db_path),
        "run_manifest_path": str(run_manifest_path),
        "same_lineage": bool(visual.get("same_lineage")) and bool(keyframes),
        "environment_recipe_id": visual.get("environment_recipe_id"),
        "scenario_id": visual.get("scenario_id"),
        "keyframe_count": len(keyframes),
        "reasoned_keyframe_count": sum(1 for item in analyses if item.get("vla_reasoning")),
        "blocked_keyframe_count": sum(1 for item in analyses if item.get("blockers")),
        "keyframes": keyframes,
        "analyses": analyses,
        "claim_boundaries": list(REQUIRED_CLAIM_BOUNDARIES),
        "blockers": blockers,
        "next_commands": [
            oodrive_command(
                f"env-demo-video --visual-proof {visual_proof_path} "
                f"--keyframe-analysis {run_dir / 'keyframe_analysis.json'} "
                f"--run-id task138-env-reasoned-carla-v1"
            )
        ],
    }
    return write_keyframe_analysis(run_dir, payload)


def write_keyframe_analysis(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Write JSON/Markdown/commands for keyframe analysis."""

    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "keyframe_analysis.json"
    report_path = run_dir / "keyframe_analysis.md"
    commands_path = run_dir / "commands.sh"
    payload = {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
        "commands_path": str(commands_path),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    commands_path.write_text(_commands(payload), encoding="utf-8")
    return payload


def _frame_paths(visual: dict[str, Any], run_manifest: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    preview = _optional_path(visual.get("preview_image_path"))
    if preview is not None and preview.exists():
        paths.append(preview)
    artifacts = _mapping(run_manifest.get("artifacts"))
    rgb_folder = _optional_path(artifacts.get("rgb_folder"))
    if rgb_folder is not None and rgb_folder.exists():
        paths.extend(sorted(rgb_folder.glob("frame_*.png")))
        paths.extend(sorted(rgb_folder.glob("*.jpg")))
        paths.extend(sorted(rgb_folder.glob("*.jpeg")))
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if path.is_file() and key not in seen:
            deduped.append(path)
            seen.add(key)
    return deduped


def _uniform_sample(paths: list[Path], limit: int) -> list[Path]:
    if len(paths) <= limit:
        return paths
    if limit <= 1:
        return [paths[len(paths) // 2]]
    indexes = [
        round(index * (len(paths) - 1) / (limit - 1))
        for index in range(limit)
    ]
    return [paths[index] for index in indexes]


def _fake_analysis(frame: dict[str, Any], visual: dict[str, Any]) -> dict[str, Any]:
    family = str(visual.get("family") or "generated OOD environment")
    recipe_id = str(visual.get("environment_recipe_id") or "environment")
    return {
        **frame,
        "backend": "fake",
        "status": "passed",
        "model_evidence": False,
        "vla_reasoning": (
            f"Frame {frame['frame_index']} shows the generated {family} pressure from {recipe_id}. "
            "A cautious policy should slow, hold lane position, and preserve clearance around uncertain objects."
        ),
        "action_intent": "slow, monitor OOD actors, preserve a safe escape path",
        "memory_ids": [f"tag:{family}", "tag:environment_visual_proof"],
        "latency_ms": 4.0,
        "vram_peak_mb": 0.0,
        "blockers": [],
        "claim": "fake_backend_product_proof_not_model_evidence",
    }


def _blocked_analysis(frame: dict[str, Any], backend: str, blocker: str) -> dict[str, Any]:
    return {
        **frame,
        "backend": backend,
        "status": "blocked",
        "model_evidence": False,
        "vla_reasoning": None,
        "action_intent": None,
        "memory_ids": [],
        "latency_ms": None,
        "vram_peak_mb": None,
        "blockers": [blocker],
    }


def _backend_blocker(backend: str) -> str:
    if backend == "alpamayo-local":
        return (
            "Real Alpamayo keyframe inference requires the configured GPU/model environment. "
            "Use the Kasm RunPod Alpamayo venv and avoid sending HF tokens through proxy SSH heredocs."
        )
    return "Keyframe analysis was explicitly requested in blocked backend mode."


def _fps_from_manifest(run_manifest: dict[str, Any]) -> float:
    artifacts = _mapping(run_manifest.get("artifacts"))
    carla_report = _optional_path(artifacts.get("carla_ood_demo_json"))
    if carla_report is not None and carla_report.exists():
        payload = _load_json(carla_report)
        frame_count = _float(payload.get("frame_count"))
        duration_s = _float(payload.get("duration_s"))
        if frame_count > 0 and duration_s > 0:
            return frame_count / duration_s
    return 10.0


def _frame_index(path: Path, *, fallback: int) -> int:
    match = re.search(r"frame_(\d+)", path.name)
    if match:
        return int(match.group(1))
    return fallback


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OODrive Keyframe Analysis",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Backend: `{payload.get('backend')}`",
        f"- Same lineage: `{payload.get('same_lineage')}`",
        f"- Keyframes: `{payload.get('keyframe_count')}`",
        f"- Reasoned keyframes: `{payload.get('reasoned_keyframe_count')}`",
        "",
        "## Analyses",
        "",
    ]
    for item in list(payload.get("analyses", [])):
        lines.append(
            f"- `{item.get('keyframe_id')}` frame `{item.get('frame_index')}` "
            f"at `{item.get('source_time_s')}`s: {item.get('vla_reasoning') or item.get('blockers')}"
        )
    blockers = list(payload.get("blockers", []))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        for blocker in blockers:
            lines.append(f"- {blocker}")
    lines.extend(["", "## Claim Boundaries", ""])
    for claim in list(payload.get("claim_boundaries", [])):
        lines.append(f"- `{claim}`")
    lines.append("")
    return "\n".join(lines)


def _commands(payload: dict[str, Any]) -> str:
    lines = ["#!/usr/bin/env bash", "set -euo pipefail", ""]
    lines.extend(str(command) for command in list(payload.get("next_commands", [])))
    return "\n".join(lines) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _optional_path(value: object) -> Path | None:
    if value in (None, ""):
        return None
    return Path(str(value))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


__all__ = [
    "REQUIRED_CLAIM_BOUNDARIES",
    "build_keyframe_analysis",
    "select_carla_keyframes",
    "write_keyframe_analysis",
]
