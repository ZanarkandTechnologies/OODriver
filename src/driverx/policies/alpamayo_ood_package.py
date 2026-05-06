"""Build Alpamayo packages from DriverX scripted CARLA OOD captures."""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.policies.alpamayo_input import AlpamayoInputPackage
from driverx.policies.alpamayo_release import (
    CAMERA_DISPLAY_NAMES,
    DEFAULT_CAMERA_INDICES,
    DEFAULT_HISTORY_STEPS,
    DEFAULT_NUM_FRAMES_PER_CAMERA,
)


@dataclass(frozen=True)
class AlpamayoOodPackageInputs:
    rgb_folder: Path
    tracks_path: Path
    scenario_report_path: Path | None = None
    video_evidence_path: Path | None = None
    scenario_id: str | None = None
    behavior_id: str | None = None
    center_frame: int | None = None
    nav_text: str | None = None
    memory_context: list[dict[str, Any]] = field(default_factory=list)


def build_alpamayo_package_from_ood_demo(
    inputs: AlpamayoOodPackageInputs,
) -> AlpamayoInputPackage:
    """Create a same-scene Alpamayo input package from OOD demo frames/tracks."""

    frames = sorted(inputs.rgb_folder.expanduser().glob("*.png"))
    if len(frames) < DEFAULT_NUM_FRAMES_PER_CAMERA:
        raise ValueError(
            f"Need at least {DEFAULT_NUM_FRAMES_PER_CAMERA} RGB frames; found {len(frames)} in {inputs.rgb_folder}."
        )
    tracks = _load_tracks(inputs.tracks_path)
    scenario_report = _load_optional_json(inputs.scenario_report_path)
    video_evidence = _load_optional_json(inputs.video_evidence_path)
    scenario_id = (
        inputs.scenario_id
        or str(scenario_report.get("recipe_id") or "")
        or str(video_evidence.get("scenario_id") or "")
        or inputs.rgb_folder.parent.name
    )
    behavior_id = (
        inputs.behavior_id
        or str(scenario_report.get("behavior_id") or "")
        or str(video_evidence.get("behavior_id") or "")
        or "unknown_behavior"
    )
    selected = _select_frame_window(frames, inputs.center_frame, video_evidence)
    width, height = _png_size(selected[0])
    camera_windows = [
        {
            "camera_index": camera_index,
            "camera_name": CAMERA_DISPLAY_NAMES.get(camera_index, f"Camera {camera_index}"),
            "frames": [
                {
                    "frame_index": frame_offset,
                    "path": str(frame),
                    "width": width,
                    "height": height,
                }
                for frame_offset, frame in enumerate(selected)
            ],
        }
        for camera_index in DEFAULT_CAMERA_INDICES[:3]
    ]
    return AlpamayoInputPackage(
        frame_name=f"driverx_ood_{scenario_id}",
        camera_windows=[
            _window_from_payload(window) for window in camera_windows
        ],
        camera_indices=DEFAULT_CAMERA_INDICES[:3],
        ego_history_xyz=_ego_history_xyz(tracks, selected[-1]),
        ego_history_rot=[_identity3() for _ in range(DEFAULT_HISTORY_STEPS)],
        nav_text=inputs.nav_text or _nav_text(scenario_id, behavior_id),
        memory_context=list(inputs.memory_context),
        tensor_shapes={
            "image_frames": f"3 x {DEFAULT_NUM_FRAMES_PER_CAMERA} x 3 x {height} x {width}",
            "camera_indices": "3",
            "ego_history_xyz": "1 x 1 x 16 x 3",
            "ego_history_rot": "1 x 1 x 16 x 3 x 3",
        },
        notes=[
            "Package was built from a live DriverX scripted CARLA OOD demo.",
            "The source capture has one ego RGB camera; the four selected frames are duplicated across Alpamayo front-left/front/front-right camera indices for same-scene open-loop reasoning.",
            "This package is for open-loop VLA reasoning evidence, not calibrated production multi-camera autonomy.",
            f"scenario_report_path={inputs.scenario_report_path}",
            f"video_evidence_path={inputs.video_evidence_path}",
            f"behavior_id={behavior_id}",
        ],
    )


def write_alpamayo_ood_package(
    run_dir: Path,
    package: AlpamayoInputPackage,
    *,
    source: dict[str, Any],
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = package.to_jsonable()
    payload["scenario_id"] = _scenario_id_from_frame_name(package.frame_name)
    payload["behavior_id"] = _behavior_id_from_notes(payload.get("notes", []))
    payload["source"] = source
    json_path = run_dir / "alpamayo_carla_input_package.json"
    report_path = run_dir / "alpamayo_ood_input_package.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _window_from_payload(payload: dict[str, Any]):
    from driverx.policies.alpamayo_input import AlpamayoCameraFrameRef, AlpamayoCameraWindow

    return AlpamayoCameraWindow(
        camera_index=int(payload["camera_index"]),
        camera_name=str(payload["camera_name"]),
        frames=[
            AlpamayoCameraFrameRef(
                frame_index=int(frame["frame_index"]),
                source_name=str(frame["path"]),
                width=int(frame["width"]),
                height=int(frame["height"]),
            )
            for frame in payload["frames"]
        ],
    )


def _select_frame_window(
    frames: list[Path],
    center_frame: int | None,
    video_evidence: dict[str, Any],
) -> list[Path]:
    if center_frame is None:
        worst = video_evidence.get("worst_risk")
        if isinstance(worst, dict) and isinstance(worst.get("tick"), int):
            center_frame = int(worst["tick"])
    if center_frame is None:
        center_frame = len(frames) - 1
    start = max(0, min(len(frames) - DEFAULT_NUM_FRAMES_PER_CAMERA, center_frame - 2))
    return frames[start : start + DEFAULT_NUM_FRAMES_PER_CAMERA]


def _load_tracks(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected track list in {path}")
    return [dict(item) for item in payload if isinstance(item, dict)]


def _load_optional_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    if not path.exists():
        return {}
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, dict) else {}


def _ego_history_xyz(tracks: list[dict[str, Any]], selected_last_frame: Path) -> list[list[float]]:
    last_tick = _frame_number(selected_last_frame)
    ego_tracks = [
        track
        for track in tracks
        if str(track.get("actor_ref")) == "ego" and int(track.get("tick", -1)) <= last_tick
    ]
    ego_tracks = ego_tracks[-DEFAULT_HISTORY_STEPS:]
    if not ego_tracks:
        return [[0.0, 0.0, 0.0] for _ in range(DEFAULT_HISTORY_STEPS)]
    first = ego_tracks[0]
    while len(ego_tracks) < DEFAULT_HISTORY_STEPS:
        ego_tracks.insert(0, first)
    samples: list[list[float]] = []
    for track in ego_tracks[-DEFAULT_HISTORY_STEPS:]:
        location = dict(track.get("location", {}))
        samples.append(
            [
                round(float(location.get("x", 0.0)), 4),
                round(float(location.get("y", 0.0)), 4),
                round(float(location.get("z", 0.0)), 4),
            ]
        )
    return samples


def _frame_number(path: Path) -> int:
    digits = "".join(ch for ch in path.stem if ch.isdigit())
    return int(digits) if digits else 0


def _png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) >= 24 and header[:8] == b"\x89PNG\r\n\x1a\n":
        width, height = struct.unpack(">II", header[16:24])
        return int(width), int(height)
    raise ValueError(f"Image is not a readable PNG: {path}")


def _identity3() -> list[list[float]]:
    return [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]


def _nav_text(scenario_id: str, behavior_id: str) -> str:
    return (
        "Proceed through the generated OOD scene while checking for regional "
        f"traffic behavior: {behavior_id}; scenario: {scenario_id}."
    )


def _scenario_id_from_frame_name(frame_name: str) -> str:
    prefix = "driverx_ood_"
    return frame_name[len(prefix) :] if frame_name.startswith(prefix) else frame_name


def _behavior_id_from_notes(notes: object) -> str | None:
    if not isinstance(notes, list):
        return None
    for note in notes:
        text = str(note)
        if text.startswith("behavior_id="):
            return text.split("=", 1)[1]
    return None


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Alpamayo OOD Input Package",
        "",
        f"- frame_name: `{payload['frame_name']}`",
        f"- camera_indices: `{payload['camera_indices']}`",
        f"- camera_windows: `{len(payload['camera_windows'])}`",
        f"- memory_entries: `{len(payload.get('memory_context', []))}`",
        f"- source: `{payload.get('source', {})}`",
        "",
        "## Notes",
        "",
    ]
    for note in payload.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "AlpamayoOodPackageInputs",
    "build_alpamayo_package_from_ood_demo",
    "write_alpamayo_ood_package",
]
