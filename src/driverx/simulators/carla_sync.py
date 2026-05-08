"""Small CARLA synchronous-mode and sensor-barrier helpers."""

from __future__ import annotations

import queue
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CarlaSyncConfig:
    fixed_delta_seconds: float = 0.25
    timeout_s: float = 2.0


@dataclass(frozen=True)
class SyncedCameraFrame:
    camera_index: int
    sensor_frame_id: int
    path: str | None = None
    width: int | None = None
    height: int | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "camera_index": self.camera_index,
            "sensor_frame_id": self.sensor_frame_id,
            "path": self.path,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class SyncedCarlaCheckpoint:
    checkpoint_id: str
    world_frame_id: int
    sim_time_s: float
    min_required_frame_id: int | None
    camera_frames: tuple[SyncedCameraFrame, ...] = field(default_factory=tuple)
    queue_drain_count: int = 0
    settings_restored: bool = False
    blockers: tuple[str, ...] = field(default_factory=tuple)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "world_frame_id": self.world_frame_id,
            "sim_time_s": self.sim_time_s,
            "min_required_frame_id": self.min_required_frame_id,
            "camera_frames": [frame.to_jsonable() for frame in self.camera_frames],
            "sensor_frame_ids": [frame.sensor_frame_id for frame in self.camera_frames],
            "queue_drain_count": self.queue_drain_count,
            "settings_restored": self.settings_restored,
            "blockers": list(self.blockers),
        }


class CarlaSyncSession:
    """Context manager that owns synchronous stepping and restores settings."""

    def __init__(self, world: object, config: CarlaSyncConfig | None = None) -> None:
        self.world = world
        self.config = config or CarlaSyncConfig()
        self._previous_settings: object | None = None
        self.settings_restored = False

    def __enter__(self) -> "CarlaSyncSession":
        if hasattr(self.world, "get_settings"):
            self._previous_settings = self.world.get_settings()
            settings = self.world.get_settings()
            if hasattr(settings, "synchronous_mode"):
                settings.synchronous_mode = True
            if hasattr(settings, "fixed_delta_seconds"):
                settings.fixed_delta_seconds = self.config.fixed_delta_seconds
            if hasattr(self.world, "apply_settings"):
                self.world.apply_settings(settings)
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._previous_settings is not None and hasattr(self.world, "apply_settings"):
            try:
                self.world.apply_settings(self._previous_settings)
                self.settings_restored = True
            except Exception:
                self.settings_restored = False

    def tick(self) -> int:
        if hasattr(self.world, "tick"):
            value = self.world.tick()
            return int(value) if value is not None else _world_frame(self.world)
        if hasattr(self.world, "wait_for_tick"):
            snapshot = self.world.wait_for_tick(self.config.timeout_s)
            return _frame_from_snapshot(snapshot, self.world)
        return _world_frame(self.world) + 1


def capture_aligned_checkpoint(
    session: CarlaSyncSession,
    sensor_queues: dict[int, "queue.Queue[object]"],
    output_dir: Path,
    *,
    checkpoint_id: str,
    min_frame_id: int | None = None,
) -> SyncedCarlaCheckpoint:
    output_dir.mkdir(parents=True, exist_ok=True)
    world_frame = session.tick()
    min_required = min_frame_id if min_frame_id is not None else world_frame
    frames: list[SyncedCameraFrame] = []
    blockers: list[str] = []
    drained_total = 0
    for camera_index, images in sorted(sensor_queues.items()):
        image, drained = _next_fresh_image(images, min_required, session.config.timeout_s)
        drained_total += drained
        if image is None:
            blockers.append(f"camera {camera_index}: no fresh image >= frame {min_required}")
            continue
        frame_id = int(getattr(image, "frame", getattr(image, "frame_number", world_frame)))
        image_path = output_dir / f"camera_{camera_index}_frame_{frame_id}.png"
        if hasattr(image, "save_to_disk"):
            image.save_to_disk(str(image_path))
            path: str | None = str(image_path)
        else:
            path = None
        frames.append(
            SyncedCameraFrame(
                camera_index=camera_index,
                sensor_frame_id=frame_id,
                path=path,
                width=_optional_int(getattr(image, "width", None)),
                height=_optional_int(getattr(image, "height", None)),
            )
        )
    return SyncedCarlaCheckpoint(
        checkpoint_id=checkpoint_id,
        world_frame_id=world_frame,
        sim_time_s=round(world_frame * session.config.fixed_delta_seconds, 4),
        min_required_frame_id=min_required,
        camera_frames=tuple(frames),
        queue_drain_count=drained_total,
        settings_restored=session.settings_restored,
        blockers=tuple(blockers),
    )


def build_alpamayo_package_from_synced_checkpoint(
    checkpoint: SyncedCarlaCheckpoint,
    *,
    route_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    windows = []
    for frame in checkpoint.camera_frames:
        windows.append(
            {
                "camera_index": frame.camera_index,
                "camera_name": {0: "Front left camera", 1: "Front camera", 2: "Front right camera"}.get(
                    frame.camera_index,
                    f"Camera {frame.camera_index}",
                ),
                "frames": [
                    {
                        "frame_index": 0,
                        "path": frame.path,
                        "width": frame.width,
                        "height": frame.height,
                        "sensor_frame_id": frame.sensor_frame_id,
                    }
                ],
            }
        )
    return {
        "frame_name": checkpoint.checkpoint_id,
        "route_context": route_context or {},
        "camera_windows": windows,
        "camera_indices": [frame.camera_index for frame in checkpoint.camera_frames],
        "sensor_frame_ids": [frame.sensor_frame_id for frame in checkpoint.camera_frames],
        "closed_loop_checkpoint": checkpoint.to_jsonable(),
    }


def _next_fresh_image(images: "queue.Queue[object]", min_frame_id: int, timeout_s: float) -> tuple[object | None, int]:
    drained = 0
    last: object | None = None
    while True:
        try:
            image = images.get(timeout=timeout_s if last is None else 0.0)
        except queue.Empty:
            return last, drained
        frame = int(getattr(image, "frame", getattr(image, "frame_number", -1)))
        if frame < min_frame_id:
            drained += 1
            continue
        return image, drained


def _world_frame(world: object) -> int:
    if hasattr(world, "get_snapshot"):
        return _frame_from_snapshot(world.get_snapshot(), world)
    return int(getattr(world, "frame", 0))


def _frame_from_snapshot(snapshot: object, world: object) -> int:
    if snapshot is not None and hasattr(snapshot, "frame"):
        return int(getattr(snapshot, "frame"))
    return int(getattr(world, "frame", 0))


def _optional_int(value: object) -> int | None:
    return int(value) if isinstance(value, int) else None


__all__ = [
    "CarlaSyncConfig",
    "CarlaSyncSession",
    "SyncedCameraFrame",
    "SyncedCarlaCheckpoint",
    "build_alpamayo_package_from_synced_checkpoint",
    "capture_aligned_checkpoint",
]
