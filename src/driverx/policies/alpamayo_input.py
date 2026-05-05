"""Build Alpamayo input manifests from DriverX frames."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.core.types import CameraImage, FrameBundle
from driverx.memory import MemoryEntry
from driverx.policies.alpamayo_release import (
    CAMERA_DISPLAY_NAMES,
    DEFAULT_CAMERA_INDICES,
    DEFAULT_HISTORY_STEPS,
    DEFAULT_NUM_FRAMES_PER_CAMERA,
)

_ASSUMED_FRAME_HISTORY_HZ = 4.0
_ALPAMAYO_HISTORY_HZ = 10.0


@dataclass(frozen=True)
class AlpamayoCameraFrameRef:
    frame_index: int
    source_name: str
    width: int
    height: int

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "frame_index": self.frame_index,
            "source_name": self.source_name,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class AlpamayoCameraWindow:
    camera_index: int
    camera_name: str
    frames: list[AlpamayoCameraFrameRef]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "camera_index": self.camera_index,
            "camera_name": self.camera_name,
            "frames": [frame.to_jsonable() for frame in self.frames],
        }


@dataclass(frozen=True)
class AlpamayoInputPackage:
    frame_name: str
    camera_windows: list[AlpamayoCameraWindow]
    camera_indices: list[int]
    ego_history_xyz: list[list[float]]
    ego_history_rot: list[list[list[float]]]
    nav_text: str | None = None
    memory_context: list[dict[str, Any]] = field(default_factory=list)
    tensor_shapes: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "frame_name": self.frame_name,
            "camera_windows": [window.to_jsonable() for window in self.camera_windows],
            "camera_indices": self.camera_indices,
            "ego_history_xyz": self.ego_history_xyz,
            "ego_history_rot": self.ego_history_rot,
            "nav_text": self.nav_text,
            "memory_context": self.memory_context,
            "tensor_shapes": self.tensor_shapes,
            "notes": self.notes,
        }


def build_alpamayo_input_package(
    frame: FrameBundle,
    *,
    nav_text: str | None = None,
    memory_entries: list[MemoryEntry] | None = None,
    camera_indices: list[int] | None = None,
    frames_per_camera: int = DEFAULT_NUM_FRAMES_PER_CAMERA,
    history_steps: int = DEFAULT_HISTORY_STEPS,
) -> AlpamayoInputPackage:
    """Create an Alpamayo-shaped input manifest from a DriverX frame."""

    if frames_per_camera <= 0:
        raise ValueError("frames_per_camera must be positive.")
    if history_steps <= 1:
        raise ValueError("history_steps must be greater than one.")
    selected_indices = _camera_indices_for(frame.front_images, camera_indices)
    windows = [
        _camera_window(image, camera_index, frames_per_camera)
        for image, camera_index in zip(frame.front_images, selected_indices, strict=False)
    ]
    ego_history_xyz = _resample_history_xyz(frame.ego_history_xy, history_steps)
    ego_history_rot = [_identity3() for _ in range(history_steps)]
    memories = [_memory_payload(memory) for memory in (memory_entries or [])]
    return AlpamayoInputPackage(
        frame_name=frame.frame_name,
        camera_windows=windows,
        camera_indices=selected_indices,
        ego_history_xyz=ego_history_xyz,
        ego_history_rot=ego_history_rot,
        nav_text=nav_text or _nav_text_from_frame(frame),
        memory_context=memories,
        tensor_shapes={
            "image_frames": f"{len(windows)} x {frames_per_camera} x 3 x H x W",
            "camera_indices": f"{len(windows)}",
            "ego_history_xyz": f"1 x 1 x {history_steps} x 3",
            "ego_history_rot": f"1 x 1 x {history_steps} x 3 x 3",
        },
        notes=[
            "This is a model-input manifest, not a torch tensor dump.",
            "Fixture images are repeated across the temporal window; live CARLA capture should replace these with real adjacent frames.",
        ],
    )


def write_alpamayo_input_package(
    run_dir: Path,
    package: AlpamayoInputPackage,
) -> dict[str, Any]:
    """Write Alpamayo input package JSON/Markdown artifacts."""

    run_dir.mkdir(parents=True, exist_ok=True)
    payload = package.to_jsonable()
    json_path = run_dir / "alpamayo_input_package.json"
    report_path = run_dir / "alpamayo_input_package.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def _camera_indices_for(
    images: list[CameraImage],
    camera_indices: list[int] | None,
) -> list[int]:
    if camera_indices is not None:
        if len(camera_indices) != len(images):
            raise ValueError("camera_indices length must match frame.front_images length.")
        return camera_indices
    return DEFAULT_CAMERA_INDICES[: len(images)]


def _camera_window(
    image: CameraImage,
    camera_index: int,
    frames_per_camera: int,
) -> AlpamayoCameraWindow:
    frames = [
        AlpamayoCameraFrameRef(
            frame_index=index,
            source_name=image.name,
            width=image.width,
            height=image.height,
        )
        for index in range(frames_per_camera)
    ]
    return AlpamayoCameraWindow(
        camera_index=camera_index,
        camera_name=CAMERA_DISPLAY_NAMES.get(camera_index, f"Camera {camera_index}"),
        frames=frames,
    )


def _resample_history_xyz(
    ego_history_xy: list[tuple[float, float]],
    history_steps: int,
) -> list[list[float]]:
    (x0, y0), (x1, y1) = ego_history_xy[-2], ego_history_xy[-1]
    dt = 1.0 / _ASSUMED_FRAME_HISTORY_HZ
    vx = (x1 - x0) / dt
    vy = (y1 - y0) / dt
    samples: list[list[float]] = []
    for index in range(history_steps):
        seconds_before_now = (history_steps - 1 - index) / _ALPAMAYO_HISTORY_HZ
        samples.append(
            [
                round(x1 - vx * seconds_before_now, 4),
                round(y1 - vy * seconds_before_now, 4),
                0.0,
            ]
        )
    return samples


def _identity3() -> list[list[float]]:
    return [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]


def _nav_text_from_frame(frame: FrameBundle) -> str | None:
    route = frame.metadata.get("route")
    if route is None:
        return None
    return str(route).replace("_", " ")


def _memory_payload(memory: MemoryEntry) -> dict[str, Any]:
    return {
        "entry_id": memory.entry_id,
        "situation": memory.situation,
        "principle": memory.principle,
        "recommended_behavior": memory.recommended_behavior,
        "confidence": memory.confidence,
        "tags": memory.tags,
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Alpamayo Input Package",
        "",
        f"- frame_name: `{payload['frame_name']}`",
        f"- camera_indices: `{payload['camera_indices']}`",
        f"- camera_windows: `{len(payload['camera_windows'])}`",
        f"- nav_text: `{payload.get('nav_text')}`",
        f"- memory_entries: `{len(payload.get('memory_context', []))}`",
        "",
        "## Tensor Shapes",
        "",
    ]
    for name, shape in payload.get("tensor_shapes", {}).items():
        lines.append(f"- `{name}`: `{shape}`")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "AlpamayoCameraFrameRef",
    "AlpamayoCameraWindow",
    "AlpamayoInputPackage",
    "build_alpamayo_input_package",
    "write_alpamayo_input_package",
]
