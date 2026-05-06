"""Render lightweight explanatory overlays onto OOD demo video frames."""

from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class OodVideoOverlayConfig:
    rgb_folder: Path
    output_frame_dir: Path
    scenario_id: str
    behavior_id: str
    ood_tags: list[str] = field(default_factory=list)
    tracks_path: Path | None = None
    claim_label: str = "scripted_carla_ood_demo"


@dataclass(frozen=True)
class OodVideoOverlayResult:
    status: str
    input_frame_count: int
    overlay_frame_count: int
    output_frame_dir: str
    scenario_id: str
    behavior_id: str
    worst_risk: dict[str, Any] | None = None
    blockers: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "input_frame_count": self.input_frame_count,
            "overlay_frame_count": self.overlay_frame_count,
            "output_frame_dir": self.output_frame_dir,
            "scenario_id": self.scenario_id,
            "behavior_id": self.behavior_id,
            "worst_risk": self.worst_risk,
            "blockers": self.blockers,
        }


def render_ood_video_overlay(config: OodVideoOverlayConfig) -> OodVideoOverlayResult:
    frames = _frame_paths(config.rgb_folder)
    blockers: list[str] = []
    if not frames:
        blockers.append(f"No RGB frames found in {config.rgb_folder}.")
        return OodVideoOverlayResult(
            status="blocked",
            input_frame_count=0,
            overlay_frame_count=0,
            output_frame_dir=str(config.output_frame_dir),
            scenario_id=config.scenario_id,
            behavior_id=config.behavior_id,
            blockers=blockers,
        )
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        copied = copy_overlay_frames_without_text(config.rgb_folder, config.output_frame_dir)
        blockers.append(
            f"Pillow is unavailable for text overlay rendering: {exc}. Copied raw frames as fallback."
        )
        return OodVideoOverlayResult(
            status="passed" if copied else "blocked",
            input_frame_count=len(frames),
            overlay_frame_count=copied,
            output_frame_dir=str(config.output_frame_dir),
            scenario_id=config.scenario_id,
            behavior_id=config.behavior_id,
            blockers=blockers,
        )

    config.output_frame_dir.mkdir(parents=True, exist_ok=True)
    risk_by_tick, worst_risk = _risk_by_tick(config.tracks_path)
    font = ImageFont.load_default()
    for index, frame in enumerate(frames):
        target = config.output_frame_dir / f"overlay_{index:06d}{frame.suffix.lower() or '.png'}"
        with Image.open(frame) as image:
            image = image.convert("RGB")
            draw = ImageDraw.Draw(image, "RGBA")
            risk = risk_by_tick.get(index)
            lines = [
                f"0xDriver OOD: {config.scenario_id}",
                f"behavior: {config.behavior_id}",
                f"tags: {', '.join(config.ood_tags[:4]) if config.ood_tags else 'none'}",
                f"claim: {config.claim_label}",
            ]
            if risk is not None:
                lines.append(f"nearest actor: {risk['distance_m']:.2f}m")
            _draw_panel(draw, lines, font)
            image.save(target)
    return OodVideoOverlayResult(
        status="passed",
        input_frame_count=len(frames),
        overlay_frame_count=len(frames),
        output_frame_dir=str(config.output_frame_dir),
        scenario_id=config.scenario_id,
        behavior_id=config.behavior_id,
        worst_risk=worst_risk,
        blockers=blockers,
    )


def _frame_paths(folder: Path) -> list[Path]:
    root = folder.expanduser()
    frames: list[Path] = []
    for pattern in ("*.png", "*.jpg", "*.jpeg"):
        frames.extend(root.glob(pattern))
    return sorted(frames)


def _risk_by_tick(tracks_path: Path | None) -> tuple[dict[int, dict[str, float]], dict[str, Any] | None]:
    if tracks_path is None or not tracks_path.exists():
        return {}, None
    try:
        tracks = json.loads(tracks_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, None
    by_tick: dict[int, list[dict[str, Any]]] = {}
    for track in tracks if isinstance(tracks, list) else []:
        if isinstance(track, dict):
            by_tick.setdefault(int(track.get("tick", 0)), []).append(track)
    risk: dict[int, dict[str, float]] = {}
    worst: dict[str, Any] | None = None
    for tick, records in by_tick.items():
        ego = next((record for record in records if record.get("actor_ref") == "ego"), None)
        if ego is None:
            continue
        ego_loc = dict(ego.get("location", {}))
        best_distance = math.inf
        best_ref = None
        for record in records:
            actor_ref = str(record.get("actor_ref", ""))
            if actor_ref in {"ego", "ego_rgb"}:
                continue
            distance = _distance(ego_loc, dict(record.get("location", {})))
            if distance < best_distance:
                best_distance = distance
                best_ref = actor_ref
        if math.isfinite(best_distance):
            risk[tick] = {"distance_m": best_distance}
            candidate = {"tick": tick, "actor_ref": best_ref, "distance_m": round(best_distance, 4)}
            if worst is None or candidate["distance_m"] < float(worst["distance_m"]):
                worst = candidate
    return risk, worst


def _distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    dx = float(left.get("x", 0.0)) - float(right.get("x", 0.0))
    dy = float(left.get("y", 0.0)) - float(right.get("y", 0.0))
    dz = float(left.get("z", 0.0)) - float(right.get("z", 0.0))
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _draw_panel(draw: Any, lines: list[str], font: Any) -> None:
    line_height = 16
    width = max(260, max(len(line) for line in lines) * 7 + 20)
    height = 12 + line_height * len(lines)
    draw.rounded_rectangle((12, 12, width, height), radius=4, fill=(0, 0, 0, 150))
    y = 20
    for line in lines:
        draw.text((22, y), line, fill=(255, 255, 255, 235), font=font)
        y += line_height


def copy_overlay_frames_without_text(rgb_folder: Path, output_frame_dir: Path) -> int:
    """Small helper for fallback tests and manual recovery."""

    output_frame_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for index, frame in enumerate(_frame_paths(rgb_folder)):
        shutil.copy2(frame, output_frame_dir / f"overlay_{index:06d}{frame.suffix.lower()}")
        count += 1
    return count


__all__ = [
    "OodVideoOverlayConfig",
    "OodVideoOverlayResult",
    "copy_overlay_frames_without_text",
    "render_ood_video_overlay",
]
