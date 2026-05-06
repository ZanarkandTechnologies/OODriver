"""Build video evidence from CARLA OOD RGB frames and tracks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.simulators.ood_video_overlay import (
    OodVideoOverlayConfig,
    render_ood_video_overlay,
)
from driverx.simulators.route_video_assembly import (
    wait_for_rgb_frames,
    assemble_route_video_from_watch,
)


@dataclass(frozen=True)
class OodVideoEvidenceInputs:
    rgb_folder: Path
    scenario_id: str
    behavior_id: str
    tracks_path: Path | None = None
    ood_tags: list[str] = field(default_factory=list)
    source_kind: str = "scripted_carla"
    claim_label: str = "scripted_carla_ood_demo"
    output_video: Path | None = None
    fps: int = 10
    min_frames: int = 1
    ffmpeg_path: str | None = None


def build_ood_video_evidence(
    run_dir: Path,
    inputs: OodVideoEvidenceInputs,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    overlay_dir = run_dir / "overlay_rgb"
    overlay = render_ood_video_overlay(
        OodVideoOverlayConfig(
            rgb_folder=inputs.rgb_folder,
            output_frame_dir=overlay_dir,
            scenario_id=inputs.scenario_id,
            behavior_id=inputs.behavior_id,
            ood_tags=inputs.ood_tags,
            tracks_path=inputs.tracks_path,
            claim_label=inputs.claim_label,
        )
    )
    video_path = inputs.output_video or (run_dir / f"{inputs.scenario_id}_ood.mp4")
    if overlay.status == "passed":
        watch = wait_for_rgb_frames(
            overlay_dir,
            min_frames=inputs.min_frames,
            timeout_s=0.0,
            poll_interval_s=0.0,
        )
        assembly = assemble_route_video_from_watch(
            watch,
            video_path,
            fps=inputs.fps,
            ffmpeg_path=inputs.ffmpeg_path,
        )
        assembly_payload = assembly.to_jsonable()
    else:
        assembly_payload = {
            "status": "blocked",
            "plan": {
                "output_video": str(video_path),
                "frame_count": 0,
                "live_blockers": overlay.blockers,
            },
            "executed": False,
        }
    video_exists = video_path.exists()
    payload = {
        "status": _status(overlay.to_jsonable(), assembly_payload, video_exists),
        "scenario_id": inputs.scenario_id,
        "behavior_id": inputs.behavior_id,
        "ood_tags": inputs.ood_tags,
        "source_kind": inputs.source_kind,
        "claim_label": inputs.claim_label,
        "input_rgb_folder": str(inputs.rgb_folder),
        "overlay": overlay.to_jsonable(),
        "assembly": assembly_payload,
        "video_path": str(video_path) if video_exists else None,
        "duration_s": round(overlay.overlay_frame_count / max(inputs.fps, 1), 4),
        "worst_risk": overlay.worst_risk,
        "claim_boundaries": [
            f"{inputs.claim_label}=true",
            "video_overlay_is_evidence_surface=true",
            "closed_loop_vla_control=false",
        ],
    }
    return write_ood_video_evidence(run_dir, payload)


def write_ood_video_evidence(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "ood_video_evidence.json"
    report_path = run_dir / "ood_video_evidence.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _status(overlay: dict[str, Any], assembly: dict[str, Any], video_exists: bool) -> str:
    if overlay.get("status") != "passed":
        return "blocked"
    if assembly.get("status") == "passed" and video_exists:
        return "passed"
    return "partial"


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OOD Video Evidence",
        "",
        f"- status: `{payload['status']}`",
        f"- scenario_id: `{payload['scenario_id']}`",
        f"- behavior_id: `{payload['behavior_id']}`",
        f"- duration_s: `{payload['duration_s']}`",
        f"- video_path: `{payload['video_path']}`",
        f"- overlay_frame_count: `{payload['overlay']['overlay_frame_count']}`",
        f"- worst_risk: `{payload['worst_risk']}`",
        "",
        "## Claim Boundaries",
        "",
    ]
    for boundary in payload["claim_boundaries"]:
        lines.append(f"- `{boundary}`")
    blockers = payload["overlay"].get("blockers", [])
    blockers.extend(payload["assembly"].get("plan", {}).get("live_blockers", []))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        for blocker in blockers:
            lines.append(f"- {blocker}")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "OodVideoEvidenceInputs",
    "build_ood_video_evidence",
    "write_ood_video_evidence",
]
