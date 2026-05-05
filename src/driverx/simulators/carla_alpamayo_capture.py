"""Live CARLA camera capture shaped for Alpamayo input manifests."""

from __future__ import annotations

import importlib
import json
import queue
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.simulators.carla_ego import (
    _find_vehicle_blueprint,
    _rotation_payload,
    _spawn_ego,
    _vector_payload,
)

ALPAMAYO_CARLA_CAMERA_INDICES = [0, 1, 2]
_CAMERA_DISPLAY_NAMES = {
    0: "Front left camera",
    1: "Front camera",
    2: "Front right camera",
}


@dataclass(frozen=True)
class CarlaAlpamayoCaptureConfig:
    host: str
    port: int
    timeout_s: float
    tick_count: int = 4
    camera_width: int = 320
    camera_height: int = 180
    camera_fov: float = 90.0


@dataclass(frozen=True)
class CarlaAlpamayoCaptureResult:
    connected: bool
    host: str
    port: int
    map_name: str | None = None
    ego_actor_id: int | None = None
    camera_actor_ids: list[int] = field(default_factory=list)
    spawned_actor_ids: list[int] = field(default_factory=list)
    destroyed_actor_ids: list[int] = field(default_factory=list)
    image_count: int = 0
    tracks_path: str | None = None
    package_path: str | None = None
    report_path: str | None = None
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "host": self.host,
            "port": self.port,
            "map_name": self.map_name,
            "ego_actor_id": self.ego_actor_id,
            "camera_actor_ids": self.camera_actor_ids,
            "spawned_actor_ids": self.spawned_actor_ids,
            "destroyed_actor_ids": self.destroyed_actor_ids,
            "image_count": self.image_count,
            "tracks_path": self.tracks_path,
            "package_path": self.package_path,
            "report_path": self.report_path,
            "error": self.error,
        }


def run_carla_alpamayo_capture(
    config: CarlaAlpamayoCaptureConfig,
    run_dir: Path,
    *,
    carla_module: object | None = None,
) -> CarlaAlpamayoCaptureResult:
    """Capture RGB windows from CARLA and write an Alpamayo input package."""

    try:
        carla = carla_module or importlib.import_module("carla")
    except ImportError as exc:
        return CarlaAlpamayoCaptureResult(
            connected=False,
            host=config.host,
            port=config.port,
            error=(
                f"CARLA Python package is unavailable: {exc}. "
                "Run through scripts/run_carla_client_docker.sh or install carla==0.9.16."
            ),
        )

    run_dir.mkdir(parents=True, exist_ok=True)
    image_dir = run_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    tracks_path = run_dir / "ego_tracks.json"
    package_path = run_dir / "alpamayo_carla_input_package.json"
    report_path = run_dir / "alpamayo_carla_capture.md"
    spawned: list[object] = []
    destroyed: list[int] = []
    ego_tracks: list[dict[str, Any]] = []
    camera_queues: dict[int, "queue.Queue[object]"] = {}
    camera_actor_ids: list[int] = []
    package: dict[str, Any] | None = None
    map_name: str | None = None
    error: str | None = None

    try:
        client = carla.Client(config.host, config.port)
        client.set_timeout(config.timeout_s)
        world = client.get_world()
        world_map = world.get_map()
        map_name = str(getattr(world_map, "name", "")) or None
        blueprints = world.get_blueprint_library()
        ego_blueprint = _find_vehicle_blueprint(blueprints)
        if hasattr(ego_blueprint, "set_attribute"):
            ego_blueprint.set_attribute("role_name", "driverx_alpamayo_capture")
        spawn_points = list(world_map.get_spawn_points())
        if not spawn_points:
            raise RuntimeError("CARLA map has no spawn points.")
        ego = _spawn_ego(world, ego_blueprint, spawn_points)
        spawned.append(ego)

        camera_blueprint = blueprints.find("sensor.camera.rgb")
        camera_blueprint.set_attribute("image_size_x", str(config.camera_width))
        camera_blueprint.set_attribute("image_size_y", str(config.camera_height))
        camera_blueprint.set_attribute("fov", str(config.camera_fov))
        for camera_index in ALPAMAYO_CARLA_CAMERA_INDICES:
            camera = world.spawn_actor(
                camera_blueprint,
                _camera_transform(carla, camera_index),
                attach_to=ego,
            )
            spawned.append(camera)
            camera_actor_ids.append(int(getattr(camera, "id")))
            images: "queue.Queue[object]" = queue.Queue()
            camera.listen(images.put)
            camera_queues[camera_index] = images

        for tick in range(config.tick_count):
            try:
                world.wait_for_tick(config.timeout_s)
            except TypeError:
                world.wait_for_tick()
            ego_tracks.append(_ego_track(ego, tick))

        camera_windows: list[dict[str, Any]] = []
        image_count = 0
        for camera_index in ALPAMAYO_CARLA_CAMERA_INDICES:
            frames: list[dict[str, Any]] = []
            images = camera_queues[camera_index]
            last_image: object | None = None
            for frame_index in range(config.tick_count):
                try:
                    image = images.get(timeout=config.timeout_s)
                    last_image = image
                except queue.Empty:
                    image = last_image
                if image is None:
                    raise RuntimeError(f"No image received for camera {camera_index}.")
                image_path = image_dir / f"camera_{camera_index}_frame_{frame_index:03d}.png"
                image.save_to_disk(str(image_path))
                frames.append(
                    {
                        "frame_index": frame_index,
                        "path": str(image_path),
                        "width": config.camera_width,
                        "height": config.camera_height,
                    }
                )
                image_count += 1
            camera_windows.append(
                {
                    "camera_index": camera_index,
                    "camera_name": _CAMERA_DISPLAY_NAMES[camera_index],
                    "frames": frames,
                }
            )

        tracks_path.write_text(json.dumps(ego_tracks, indent=2), encoding="utf-8")
        package = {
            "frame_name": "carla_live_alpamayo_capture",
            "map_name": map_name,
            "camera_windows": camera_windows,
            "camera_indices": ALPAMAYO_CARLA_CAMERA_INDICES,
            "ego_history_xyz": _history_xyz_from_tracks(ego_tracks),
            "ego_history_rot": [_identity3() for _ in range(16)],
            "tensor_shapes": {
                "image_frames": f"3 x {config.tick_count} x 3 x {config.camera_height} x {config.camera_width}",
                "camera_indices": "3",
                "ego_history_xyz": "1 x 1 x 16 x 3",
                "ego_history_rot": "1 x 1 x 16 x 3 x 3",
            },
            "notes": [
                "Live CARLA RGB frames are saved as PNG paths; remote Alpamayo code must load them into tensors.",
                "Ego history is backfilled from sampled CARLA ego motion over the capture window.",
            ],
        }
        package_path.write_text(json.dumps(package, indent=2), encoding="utf-8")
        report_path.write_text(_markdown(package, image_count), encoding="utf-8")
    except Exception as exc:
        error = f"CARLA Alpamayo capture failed: {exc}"
    finally:
        for actor in reversed(spawned):
            try:
                actor_id = int(getattr(actor, "id"))
                actor.destroy()
                destroyed.append(actor_id)
            except Exception:
                pass

    spawned_ids = [int(getattr(actor, "id")) for actor in spawned if hasattr(actor, "id")]
    if package is None:
        return CarlaAlpamayoCaptureResult(
            connected=False,
            host=config.host,
            port=config.port,
            map_name=map_name,
            spawned_actor_ids=spawned_ids,
            destroyed_actor_ids=destroyed,
            error=error,
        )
    return CarlaAlpamayoCaptureResult(
        connected=True,
        host=config.host,
        port=config.port,
        map_name=map_name,
        ego_actor_id=int(getattr(spawned[0], "id")),
        camera_actor_ids=camera_actor_ids,
        spawned_actor_ids=spawned_ids,
        destroyed_actor_ids=destroyed,
        image_count=sum(len(window["frames"]) for window in package["camera_windows"]),
        tracks_path=str(tracks_path),
        package_path=str(package_path),
        report_path=str(report_path),
    )


def write_carla_alpamayo_capture(
    run_dir: Path,
    result: CarlaAlpamayoCaptureResult,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "carla_alpamayo_capture.json"
    payload = result.to_jsonable()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {**payload, "json_path": str(json_path)}


def _camera_transform(carla: object, camera_index: int) -> object:
    y_offset = {0: -0.55, 1: 0.0, 2: 0.55}[camera_index]
    yaw = {0: -35.0, 1: 0.0, 2: 35.0}[camera_index]
    return carla.Transform(
        carla.Location(x=1.6, y=y_offset, z=2.3),
        carla.Rotation(pitch=-8.0, yaw=yaw, roll=0.0),
    )


def _ego_track(ego: object, tick: int) -> dict[str, Any]:
    transform = ego.get_transform()
    return {
        "tick": tick,
        "actor_id": int(getattr(ego, "id")),
        "location": _vector_payload(transform.location),
        "rotation": _rotation_payload(transform.rotation),
        "velocity": _vector_payload(ego.get_velocity()),
    }


def _history_xyz_from_tracks(tracks: list[dict[str, Any]]) -> list[list[float]]:
    if len(tracks) < 2:
        return [[0.0, 0.0, 0.0] for _ in range(16)]
    last = tracks[-1]["location"]
    prev = tracks[-2]["location"]
    vx = float(last["x"]) - float(prev["x"])
    vy = float(last["y"]) - float(prev["y"])
    samples: list[list[float]] = []
    for index in range(16):
        steps_before = 15 - index
        samples.append(
            [
                round(float(last["x"]) - vx * steps_before, 4),
                round(float(last["y"]) - vy * steps_before, 4),
                round(float(last["z"]), 4),
            ]
        )
    return samples


def _identity3() -> list[list[float]]:
    return [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]


def _markdown(package: dict[str, Any], image_count: int) -> str:
    return "\n".join(
        [
            "# CARLA Alpamayo Capture",
            "",
            f"- map_name: `{package['map_name']}`",
            f"- camera_indices: `{package['camera_indices']}`",
            f"- image_count: `{image_count}`",
            f"- image_frames: `{package['tensor_shapes']['image_frames']}`",
            f"- ego_history_xyz: `{package['tensor_shapes']['ego_history_xyz']}`",
            "",
        ]
    )


__all__ = [
    "ALPAMAYO_CARLA_CAMERA_INDICES",
    "CarlaAlpamayoCaptureConfig",
    "CarlaAlpamayoCaptureResult",
    "run_carla_alpamayo_capture",
    "write_carla_alpamayo_capture",
]
