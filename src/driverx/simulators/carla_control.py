"""Agent-friendly direct CARLA world controls."""

from __future__ import annotations

import importlib
import json
import queue
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable

from driverx.simulators.carla_catalog import resolve_map_name, weather_preset
from driverx.simulators.carla_ood_demo import _apply_world_weather


@dataclass(frozen=True)
class CarlaControlConfig:
    host: str = "127.0.0.1"
    port: int = 2000
    timeout_s: float = 30.0
    town: str | None = None
    map_name: str | None = None
    load_map: bool = False
    weather_preset_name: str | None = None
    capture: bool = False
    spawn_index: int = 0
    camera_width: int = 1280
    camera_height: int = 720
    camera_fov: float = 90.0
    tick_count: int = 3


@dataclass(frozen=True)
class CarlaControlResult:
    connected: bool
    host: str
    port: int
    status: str
    requested_map: str | None = None
    map_before: str | None = None
    map_after: str | None = None
    available_maps: list[str] = field(default_factory=list)
    weather_preset_name: str | None = None
    weather_applied: dict[str, float] = field(default_factory=dict)
    weather_after: dict[str, Any] = field(default_factory=dict)
    screenshot_path: str | None = None
    spawned_actor_ids: list[int] = field(default_factory=list)
    destroyed_actor_ids: list[int] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "host": self.host,
            "port": self.port,
            "status": self.status,
            "requested_map": self.requested_map,
            "map_before": self.map_before,
            "map_after": self.map_after,
            "available_maps": self.available_maps,
            "weather_preset_name": self.weather_preset_name,
            "weather_applied": self.weather_applied,
            "weather_after": self.weather_after,
            "screenshot_path": self.screenshot_path,
            "spawned_actor_ids": self.spawned_actor_ids,
            "destroyed_actor_ids": self.destroyed_actor_ids,
            "blockers": self.blockers,
            "error": self.error,
            "claim_boundaries": [
                "carla_existing_maps_only=true",
                "carla_world_generation=false",
                "weather_control_via_carla_api=true",
                "screenshot_is_live_carla_when_connected=true",
            ],
        }


def control_carla_world(
    config: CarlaControlConfig,
    run_dir: Path,
    *,
    carla_module: object | None = None,
    client_factory: Callable[[str, int], Any] | None = None,
) -> CarlaControlResult:
    """Connect to CARLA, optionally load a map, set weather, and capture a frame."""

    run_dir.mkdir(parents=True, exist_ok=True)
    requested_map = resolve_map_name(config.town, config.map_name) if (config.town or config.map_name) else None
    if carla_module is None:
        try:
            carla_module = importlib.import_module("carla")
        except ImportError as exc:
            return CarlaControlResult(
                connected=False,
                host=config.host,
                port=config.port,
                status="blocked",
                requested_map=requested_map,
                weather_preset_name=config.weather_preset_name,
                error=f"CARLA Python package is unavailable: {exc}",
                blockers=["Install/use the CARLA Python package on the CARLA host."],
            )
    client_factory = client_factory or getattr(carla_module, "Client")
    spawned: list[object] = []
    destroyed: list[int] = []
    result: CarlaControlResult | None = None
    try:
        client = client_factory(config.host, config.port)
        if hasattr(client, "set_timeout"):
            client.set_timeout(config.timeout_s)
        world = client.get_world()
        map_before = _world_map_name(world)
        available_maps = _available_maps(client)
        if config.load_map and requested_map:
            world = client.load_world(requested_map)
        map_after_load = _world_map_name(world)
        applied_weather: dict[str, float] = {}
        if config.weather_preset_name:
            applied_weather = weather_preset(config.weather_preset_name)
            _apply_world_weather(world, carla_module, applied_weather)
        screenshot_path = None
        if config.capture:
            screenshot_path, camera = _capture_screenshot(
                world,
                carla_module,
                run_dir,
                config,
            )
            spawned.append(camera)
        result = CarlaControlResult(
            connected=True,
            host=config.host,
            port=config.port,
            status="passed",
            requested_map=requested_map,
            map_before=map_before,
            map_after=map_after_load,
            available_maps=available_maps,
            weather_preset_name=config.weather_preset_name,
            weather_applied=applied_weather,
            weather_after=_weather_payload(world),
            screenshot_path=str(screenshot_path) if screenshot_path else None,
            spawned_actor_ids=[int(getattr(actor, "id")) for actor in spawned if hasattr(actor, "id")],
            destroyed_actor_ids=destroyed,
        )
    except Exception as exc:
        result = CarlaControlResult(
            connected=False,
            host=config.host,
            port=config.port,
            status="blocked",
            requested_map=resolve_map_name(config.town, config.map_name)
            if (config.town or config.map_name)
            else None,
            destroyed_actor_ids=destroyed,
            error=f"CARLA control failed: {exc}",
            blockers=[str(exc)],
        )
    finally:
        for actor in reversed(spawned):
            try:
                actor_id = int(getattr(actor, "id"))
                actor.destroy()
                destroyed.append(actor_id)
            except Exception:
                pass
    if result is None:
        raise RuntimeError("CARLA control finished without a result.")
    return replace(result, destroyed_actor_ids=destroyed)


def write_carla_control_report(run_dir: Path, result: CarlaControlResult) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "carla_control.json"
    report_path = run_dir / "carla_control.md"
    payload = result.to_jsonable()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_control_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _capture_screenshot(
    world: object,
    carla: object,
    run_dir: Path,
    config: CarlaControlConfig,
) -> tuple[Path, object]:
    blueprints = world.get_blueprint_library()
    camera_blueprint = blueprints.find("sensor.camera.rgb")
    if hasattr(camera_blueprint, "set_attribute"):
        camera_blueprint.set_attribute("image_size_x", str(config.camera_width))
        camera_blueprint.set_attribute("image_size_y", str(config.camera_height))
        camera_blueprint.set_attribute("fov", str(config.camera_fov))
    transform = _camera_transform(world, carla, config.spawn_index)
    camera = world.spawn_actor(camera_blueprint, transform)
    try:
        images: "queue.Queue[object]" = queue.Queue()
        camera.listen(images.put)
        for _ in range(max(1, config.tick_count)):
            _wait_for_world_tick(world, config.timeout_s)
        image = images.get(timeout=config.timeout_s)
        path = run_dir / "carla_control_screenshot.png"
        image.save_to_disk(str(path))
        return path, camera
    except Exception:
        try:
            camera.destroy()
        except Exception:
            pass
        raise


def _camera_transform(world: object, carla: object, spawn_index: int) -> object:
    world_map = world.get_map()
    spawn_points = list(world_map.get_spawn_points())
    if not spawn_points:
        raise RuntimeError("CARLA map has no spawn points for camera capture.")
    spawn = spawn_points[max(0, min(int(spawn_index), len(spawn_points) - 1))]
    location = getattr(spawn, "location")
    rotation = getattr(spawn, "rotation")
    return carla.Transform(
        carla.Location(
            x=float(getattr(location, "x", 0.0)),
            y=float(getattr(location, "y", 0.0)),
            z=float(getattr(location, "z", 0.0)) + 8.0,
        ),
        carla.Rotation(
            pitch=-35.0,
            yaw=float(getattr(rotation, "yaw", 0.0)),
            roll=0.0,
        ),
    )


def _wait_for_world_tick(world: object, timeout_s: float) -> None:
    if hasattr(world, "tick"):
        try:
            world.tick()
            return
        except Exception:
            pass
    try:
        world.wait_for_tick(timeout_s)
    except TypeError:
        world.wait_for_tick()


def _world_map_name(world: object) -> str | None:
    try:
        return str(getattr(world.get_map(), "name", "")) or None
    except Exception:
        return None


def _available_maps(client: object) -> list[str]:
    try:
        return [str(item) for item in client.get_available_maps()]
    except Exception:
        return []


def _weather_payload(world: object) -> dict[str, Any]:
    try:
        weather = world.get_weather()
    except Exception:
        return {}
    payload: dict[str, Any] = {}
    for name in (
        "cloudiness",
        "precipitation",
        "precipitation_deposits",
        "wetness",
        "fog_density",
        "sun_altitude_angle",
        "sun_azimuth_angle",
    ):
        if hasattr(weather, name):
            value = getattr(weather, name)
            if isinstance(value, (str, int, float, bool)) or value is None:
                payload[name] = value
    return payload


def _control_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# CARLA Control",
        "",
        f"- status: `{payload.get('status')}`",
        f"- connected: `{payload.get('connected')}`",
        f"- endpoint: `{payload.get('host')}:{payload.get('port')}`",
        f"- map before: `{payload.get('map_before')}`",
        f"- map after: `{payload.get('map_after')}`",
        f"- weather preset: `{payload.get('weather_preset_name')}`",
        f"- screenshot: `{payload.get('screenshot_path')}`",
        "",
        "## Boundaries",
        "",
    ]
    lines.extend(f"- `{item}`" for item in list(payload.get("claim_boundaries", [])))
    if payload.get("blockers"):
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in list(payload.get("blockers", [])))
    return "\n".join(lines) + "\n"


__all__ = [
    "CarlaControlConfig",
    "CarlaControlResult",
    "control_carla_world",
    "write_carla_control_report",
]
