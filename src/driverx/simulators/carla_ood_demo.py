"""DriverX-owned scripted CARLA OOD demo runner."""

from __future__ import annotations

import importlib
import json
import queue
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from driverx.assets import (
    AssetManifest,
    CarlaObjectSpawnSpec,
    map_assets_to_carla_spawns,
)
from driverx.behaviors import BehaviorTrace
from driverx.core.config import read_config_mapping
from driverx.scenarios import ScenarioRecipe
from driverx.simulators.carla_ego import _find_vehicle_blueprint, _rotation_payload, _vector_payload
from driverx.simulators.carla_script import _blueprint_for, _transform
from driverx.simulators.carla_ood_fidelity import (
    ROAD_ACTOR_SPAWN_Z_M,
    fidelity_metrics as build_fidelity_metrics,
    camera_transform,
    smoothed_ood_pose,
    spawn_background_actors,
)
from driverx.simulators.carla_road_frame import (
    RoadFrame,
    RoadFrameSelector,
    local_pose_to_payload,
    resolve_road_frame,
    transform_payload_to_road_frame,
    validate_road_aligned_track,
)


@dataclass(frozen=True)
class CarlaOodDemoConfig:
    host: str = "host.docker.internal"
    port: int = 2000
    timeout_s: float = 20.0
    map_name: str | None = None
    load_map: bool = False
    tick_count: int = 240
    fps: int = 10
    camera_width: int = 1280
    camera_height: int = 720
    camera_fov: float = 90.0
    behavior_id: str = "motorcycle_filtering"
    ego_mode: str = "scripted"
    ego_speed_mps: float = 4.0
    coordinate_frame: str = "road_local"
    road_anchor_spawn_index: int = 0
    road_anchor_forward_m: float = 0.0
    road_anchor_lateral_m: float = 0.0
    road_anchor_yaw_delta_deg: float = 0.0
    road_lane_width_m: float = 3.5
    road_max_lateral_offset_m: float = 6.0
    fidelity_mode: str = "scripted"
    background_vehicle_count: int = 0
    background_pedestrian_count: int = 0
    camera_preset: str = "ego_front"
    ood_motion_smoothing: str = "linear"
    ood_max_step_m: float = 3.0
    cleanup: bool = True
    weather: dict[str, float | str] = field(default_factory=dict)

    def road_frame_selector(self) -> RoadFrameSelector:
        return RoadFrameSelector(
            spawn_index=self.road_anchor_spawn_index,
            forward_offset_m=self.road_anchor_forward_m,
            lateral_offset_m=self.road_anchor_lateral_m,
            yaw_delta_deg=self.road_anchor_yaw_delta_deg,
            lane_width_m=self.road_lane_width_m,
            max_lateral_offset_m=self.road_max_lateral_offset_m,
        )


@dataclass(frozen=True)
class CarlaOodDemoPlan:
    recipe_id: str
    behavior_id: str
    tick_count: int
    fps: int
    actor_refs: list[str]
    coordinate_frame: str = "road_local"
    road_frame_selector: RoadFrameSelector = field(default_factory=RoadFrameSelector)
    object_spawn_specs: list[CarlaObjectSpawnSpec] = field(default_factory=list)
    fidelity_mode: str = "scripted"
    camera_preset: str = "ego_front"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "behavior_id": self.behavior_id,
            "tick_count": self.tick_count,
            "fps": self.fps,
            "actor_refs": self.actor_refs,
            "coordinate_frame": self.coordinate_frame,
            "road_frame_selector": self.road_frame_selector.to_jsonable(),
            "object_spawn_specs": [
                spec.to_jsonable() for spec in self.object_spawn_specs
            ],
            "fidelity_mode": self.fidelity_mode,
            "camera_preset": self.camera_preset,
        }


@dataclass(frozen=True)
class CarlaOodDemoResult:
    status: str
    host: str
    port: int
    recipe_id: str
    behavior_id: str
    map_name: str | None = None
    frame_count: int = 0
    duration_s: float = 0.0
    tracks_path: str | None = None
    rgb_folder: str | None = None
    plan_path: str | None = None
    road_alignment_path: str | None = None
    spawned_actor_ids: list[int] = field(default_factory=list)
    destroyed_actor_ids: list[int] = field(default_factory=list)
    background_actor_ids: list[int] = field(default_factory=list)
    fidelity_metrics: dict[str, Any] = field(default_factory=dict)
    generated_asset_ids: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def connected(self) -> bool:
        return self.status in {"passed", "partial"}

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "connected": self.connected,
            "host": self.host,
            "port": self.port,
            "recipe_id": self.recipe_id,
            "behavior_id": self.behavior_id,
            "map_name": self.map_name,
            "frame_count": self.frame_count,
            "duration_s": self.duration_s,
            "tracks_path": self.tracks_path,
            "rgb_folder": self.rgb_folder,
            "plan_path": self.plan_path,
            "road_alignment_path": self.road_alignment_path,
            "spawned_actor_ids": self.spawned_actor_ids,
            "destroyed_actor_ids": self.destroyed_actor_ids,
            "background_actor_ids": self.background_actor_ids,
            "fidelity_metrics": self.fidelity_metrics,
            "generated_asset_ids": self.generated_asset_ids,
            "blockers": self.blockers,
            "error": self.error,
            "claim_boundaries": [
                "scripted_carla_ood_demo=true",
                "stock_fail2drive_score=false",
                "closed_loop_vla_control=false",
            ],
        }


def load_carla_ood_demo_config(path: Path) -> CarlaOodDemoConfig:
    raw = read_config_mapping(path)
    demo = raw.get("carla_ood_demo", raw)
    if not isinstance(demo, dict):
        raise ValueError("Config field 'carla_ood_demo' must be a mapping.")
    return CarlaOodDemoConfig(
        host=str(demo.get("host", "host.docker.internal")),
        port=int(demo.get("port", 2000)),
        timeout_s=float(demo.get("timeout_s", 20.0)),
        map_name=str(demo["map_name"]) if demo.get("map_name") not in (None, "") else None,
        load_map=bool(demo.get("load_map", False)),
        tick_count=int(demo.get("tick_count", 240)),
        fps=max(1, int(demo.get("fps", 10))),
        camera_width=int(demo.get("camera_width", 1280)),
        camera_height=int(demo.get("camera_height", 720)),
        camera_fov=float(demo.get("camera_fov", 90.0)),
        behavior_id=str(demo.get("behavior_id", "motorcycle_filtering")),
        ego_mode=str(demo.get("ego_mode", "scripted")),
        ego_speed_mps=float(demo.get("ego_speed_mps", 4.0)),
        coordinate_frame=str(demo.get("coordinate_frame", "road_local")),
        road_anchor_spawn_index=int(demo.get("road_anchor_spawn_index", 0)),
        road_anchor_forward_m=float(demo.get("road_anchor_forward_m", 0.0)),
        road_anchor_lateral_m=float(demo.get("road_anchor_lateral_m", 0.0)),
        road_anchor_yaw_delta_deg=float(demo.get("road_anchor_yaw_delta_deg", 0.0)),
        road_lane_width_m=float(demo.get("road_lane_width_m", 3.5)),
        road_max_lateral_offset_m=float(demo.get("road_max_lateral_offset_m", 6.0)),
        fidelity_mode=str(demo.get("fidelity_mode", "scripted")),
        background_vehicle_count=max(0, int(demo.get("background_vehicle_count", 0))),
        background_pedestrian_count=max(0, int(demo.get("background_pedestrian_count", 0))),
        camera_preset=str(demo.get("camera_preset", "ego_front")),
        ood_motion_smoothing=str(demo.get("ood_motion_smoothing", "linear")),
        ood_max_step_m=max(0.1, float(demo.get("ood_max_step_m", 3.0))),
        cleanup=bool(demo.get("cleanup", True)),
        weather=_weather_from_config(demo),
    )


def build_carla_ood_demo_plan(
    recipe: ScenarioRecipe,
    behavior: BehaviorTrace,
    config: CarlaOodDemoConfig,
    *,
    asset_manifests: list[AssetManifest] | None = None,
) -> CarlaOodDemoPlan:
    object_specs = map_assets_to_carla_spawns(asset_manifests or [])
    return CarlaOodDemoPlan(
        recipe_id=recipe.recipe_id,
        behavior_id=behavior.plan.behavior_id,
        tick_count=max(1, config.tick_count),
        fps=config.fps,
        actor_refs=[
            "ego",
            "ego_rgb",
            "ood_actor_0",
            *[spec.actor_ref for spec in object_specs],
        ],
        coordinate_frame=config.coordinate_frame,
        road_frame_selector=config.road_frame_selector(),
        object_spawn_specs=object_specs,
        fidelity_mode=config.fidelity_mode,
        camera_preset=config.camera_preset,
    )


def run_carla_ood_demo(
    config: CarlaOodDemoConfig,
    run_dir: Path,
    *,
    recipe: ScenarioRecipe,
    behavior: BehaviorTrace,
    asset_manifests: list[AssetManifest] | None = None,
    carla_module: object | None = None,
    ego_control_trace: object | None = None,
) -> CarlaOodDemoResult:
    try:
        carla = carla_module or importlib.import_module("carla")
    except ImportError as exc:
        return CarlaOodDemoResult(
            status="blocked",
            host=config.host,
            port=config.port,
            recipe_id=recipe.recipe_id,
            behavior_id=behavior.plan.behavior_id,
            blockers=[
                f"CARLA Python package is unavailable: {exc}. Run through scripts/run_carla_client_docker.sh or install carla==0.9.16."
            ],
            error=str(exc),
        )

    run_dir.mkdir(parents=True, exist_ok=True)
    rgb_folder = run_dir / "rgb"
    rgb_folder.mkdir(parents=True, exist_ok=True)
    tracks_path = run_dir / "entity_tracks.json"
    plan_path = run_dir / "carla_ood_demo_plan.json"
    road_alignment_path = run_dir / "road_alignment_report.json"
    checkpoint_path = run_dir / "carla_ood_demo_live_checkpoint.json"
    plan = build_carla_ood_demo_plan(
        recipe,
        behavior,
        config,
        asset_manifests=asset_manifests,
    )
    plan_path.write_text(json.dumps(plan.to_jsonable(), indent=2), encoding="utf-8")

    spawned: list[object] = []
    destroyed: list[int] = []
    tracks: list[dict[str, Any]] = []
    frame_count = 0
    blockers: list[str] = []
    map_name: str | None = None
    camera_queue: "queue.Queue[object]" = queue.Queue()
    last_image: object | None = None
    actor_by_ref: dict[str, object] = {}
    road_frame: RoadFrame | None = None
    background_actor_ids: list[int] = []
    fidelity_metrics: dict[str, Any] = {}
    alignment_transforms: dict[str, list[dict[str, dict[str, float]]]] = {
        "ego": [],
        "ood_actor_0": [],
    }
    try:
        client = carla.Client(config.host, config.port)
        client.set_timeout(config.timeout_s)
        world = _world_for_config(client, config)
        _apply_world_weather(world, carla, config.weather)
        world_map = world.get_map()
        map_name = str(getattr(world_map, "name", "")) or None
        blueprints = world.get_blueprint_library()
        ego_blueprint = _find_vehicle_blueprint(blueprints)
        if hasattr(ego_blueprint, "set_attribute"):
            ego_blueprint.set_attribute("role_name", "driverx_ood_ego")
        ego, road_frame, ego_spawn_payload = _spawn_ego_with_retry(
            world,
            world_map,
            carla,
            config,
            ego_blueprint,
        )
        spawned.append(ego)
        actor_by_ref["ego"] = ego
        alignment_transforms["ego"].append(ego_spawn_payload)
        if ego_control_trace is None and config.ego_mode == "scripted":
            _disable_actor_physics(ego)

        camera_blueprint = blueprints.find("sensor.camera.rgb")
        camera_blueprint.set_attribute("image_size_x", str(config.camera_width))
        camera_blueprint.set_attribute("image_size_y", str(config.camera_height))
        camera_blueprint.set_attribute("fov", str(config.camera_fov))
        camera = world.spawn_actor(
            camera_blueprint,
            camera_transform(carla, config.camera_preset),
            attach_to=ego,
        )
        spawned.append(camera)
        actor_by_ref["ego_rgb"] = camera
        camera.listen(camera_queue.put)

        ood_blueprint = _find_blueprint(blueprints, _blueprint_for(behavior.plan.actor_kind))
        ood_spawn = _spawn_road_actor_with_offsets(
            world,
            ood_blueprint,
            carla,
            config,
            road_frame,
            behavior.samples[0].x_m,
            behavior.samples[0].y_m,
            ROAD_ACTOR_SPAWN_Z_M,
            behavior.samples[0].heading_deg,
            offsets=_ood_spawn_offsets(config),
        )
        if ood_spawn is None:
            raise RuntimeError("Unable to spawn OOD actor without a collision.")
        ood_actor, ood_spawn_payload, ood_spawn_local_pose = ood_spawn
        _disable_actor_physics(ood_actor)
        spawned.append(ood_actor)
        actor_by_ref["ood_actor_0"] = ood_actor
        alignment_transforms["ood_actor_0"].append(ood_spawn_payload)

        for spec in plan.object_spawn_specs:
            blueprint = _find_blueprint(blueprints, spec.blueprint_filter)
            spawn_transform = _spawn_transform_for_spec(config, road_frame, spec)
            actor = _spawn_actor_safely(world, blueprint, _carla_transform(carla, spawn_transform))
            if actor is None:
                blockers.append(f"Skipped generated asset {spec.asset_id}: spawn collided.")
                continue
            _disable_actor_physics(actor)
            spawned.append(actor)
            actor_by_ref[spec.actor_ref] = actor
            alignment_transforms[spec.actor_ref] = [spawn_transform]

        background_actor_ids = spawn_background_actors(
            world,
            blueprints,
            carla,
            config,
            road_frame,
            spawned,
            actor_by_ref,
            alignment_transforms,
            find_vehicle_blueprint=_find_vehicle_blueprint,
            find_blueprint=_find_blueprint,
            road_transform=_road_transform,
            carla_transform=_carla_transform,
            spawn_actor_safely=_spawn_actor_safely,
            disable_actor_physics=_disable_actor_physics,
        )
        last_ood_local_pose: tuple[float, float, float] | None = (
            ood_spawn_local_pose if config.ood_motion_smoothing != "linear" else None
        )
        for tick in range(plan.tick_count):
            sample = behavior.samples[min(tick, len(behavior.samples) - 1)]
            if ego_control_trace is not None and tick < len(ego_control_trace.commands):
                _safe_apply_control_command(ego, ego_control_trace.commands[tick], carla)
                ego_payload = _payload_from_actor(ego)
            elif config.ego_mode == "scripted":
                ego_payload = _road_transform(
                    config,
                    road_frame,
                    config.ego_speed_mps * tick / max(config.fps, 1),
                    0.0,
                    ROAD_ACTOR_SPAWN_Z_M,
                    0.0,
                )
                _safe_set_transform(
                    ego,
                    _carla_transform(carla, ego_payload),
                )
            else:
                ego_payload = _payload_from_actor(ego)
            alignment_transforms["ego"].append(ego_payload)
            local_x, local_y, local_heading = smoothed_ood_pose(
                sample.x_m,
                sample.y_m,
                sample.heading_deg,
                last_ood_local_pose,
                config,
            )
            last_ood_local_pose = (local_x, local_y, local_heading)
            ood_payload = _road_transform(
                config,
                road_frame,
                local_x,
                local_y,
                ROAD_ACTOR_SPAWN_Z_M,
                local_heading,
            )
            _safe_set_transform(
                ood_actor,
                _carla_transform(carla, ood_payload),
            )
            alignment_transforms["ood_actor_0"].append(ood_payload)
            try:
                world.wait_for_tick(config.timeout_s)
            except TypeError:
                world.wait_for_tick()
            tracks.extend(_tracks_for(actor_by_ref, tick, sample.t_s))
            image = _next_image(camera_queue, config.timeout_s, last_image)
            if image is not None:
                last_image = image
                image.save_to_disk(str(rgb_folder / f"frame_{frame_count:06d}.png"))
                frame_count += 1
            _write_live_checkpoint(
                checkpoint_path,
                config=config,
                plan=plan,
                map_name=map_name,
                frame_count=frame_count,
                tracks_path=tracks_path,
                rgb_folder=rgb_folder,
                road_alignment_path=road_alignment_path,
                spawned=spawned,
                destroyed=destroyed,
                blockers=blockers,
            )
        if frame_count == 0:
            blockers.append("No RGB frames were captured from the CARLA camera.")
        tracks_path.write_text(json.dumps(tracks, indent=2), encoding="utf-8")
        alignment_payload = _write_road_alignment_report(
            road_alignment_path,
            road_frame=road_frame,
            alignment_transforms=alignment_transforms,
            config=config,
        )
        for actor_ref in ("ego", "ood_actor_0"):
            report = alignment_payload.get("actors", {}).get(actor_ref, {})
            if report and not report.get("starts_on_road", False):
                blockers.append(f"{actor_ref} did not start inside the road-aligned corridor.")
        fidelity_metrics = build_fidelity_metrics(
            config,
            tracks,
            background_actor_ids=background_actor_ids,
        )
        _write_live_checkpoint(
            checkpoint_path,
            config=config,
            plan=plan,
            map_name=map_name,
            frame_count=frame_count,
            tracks_path=tracks_path,
            rgb_folder=rgb_folder,
            road_alignment_path=road_alignment_path,
            spawned=spawned,
            destroyed=destroyed,
            blockers=blockers,
        )
    except Exception as exc:
        blockers.append(f"CARLA OOD demo failed: {exc}")
        status = "partial" if frame_count > 0 else "blocked"
        return CarlaOodDemoResult(
            status=status,
            host=config.host,
            port=config.port,
            recipe_id=recipe.recipe_id,
            behavior_id=behavior.plan.behavior_id,
            map_name=map_name,
            frame_count=frame_count,
            duration_s=round(frame_count / max(config.fps, 1), 4),
            tracks_path=str(tracks_path) if tracks_path.exists() else None,
            rgb_folder=str(rgb_folder),
            plan_path=str(plan_path),
            road_alignment_path=str(road_alignment_path) if road_alignment_path.exists() else None,
            spawned_actor_ids=_actor_ids(spawned),
            destroyed_actor_ids=destroyed,
            background_actor_ids=background_actor_ids,
            fidelity_metrics=build_fidelity_metrics(config, tracks, background_actor_ids=background_actor_ids),
            generated_asset_ids=[spec.asset_id for spec in plan.object_spawn_specs],
            blockers=blockers,
            error=str(exc),
        )
    finally:
        if config.cleanup:
            for actor in reversed(spawned):
                try:
                    actor_id = int(getattr(actor, "id"))
                    actor.destroy()
                    destroyed.append(actor_id)
                except Exception:
                    pass

    return CarlaOodDemoResult(
        status="passed" if not blockers else "partial",
        host=config.host,
        port=config.port,
        recipe_id=recipe.recipe_id,
        behavior_id=behavior.plan.behavior_id,
        map_name=map_name,
        frame_count=frame_count,
        duration_s=round(frame_count / max(config.fps, 1), 4),
        tracks_path=str(tracks_path),
        rgb_folder=str(rgb_folder),
        plan_path=str(plan_path),
        road_alignment_path=str(road_alignment_path),
        spawned_actor_ids=_actor_ids(spawned),
        destroyed_actor_ids=destroyed,
        background_actor_ids=background_actor_ids,
        fidelity_metrics=fidelity_metrics,
        generated_asset_ids=[spec.asset_id for spec in plan.object_spawn_specs],
        blockers=blockers,
    )


def write_carla_ood_demo(run_dir: Path, result: CarlaOodDemoResult) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = result.to_jsonable()
    json_path = run_dir / "carla_ood_demo.json"
    report_path = run_dir / "carla_ood_demo.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _world_for_config(client: object, config: CarlaOodDemoConfig) -> object:
    if config.load_map and config.map_name and hasattr(client, "load_world"):
        return client.load_world(config.map_name)
    return client.get_world()


def _weather_from_config(demo: dict[str, Any]) -> dict[str, float | str]:
    nested = demo.get("weather", {})
    if isinstance(nested, dict) and nested:
        return dict(nested)
    prefixed: dict[str, float | str] = {}
    for key, value in demo.items():
        if key.startswith("weather_"):
            prefixed[key.removeprefix("weather_")] = value
    return prefixed


def _apply_world_weather(world: object, carla: object, weather: dict[str, float | str]) -> None:
    if not weather or not hasattr(world, "set_weather"):
        return
    weather_parameters = getattr(carla, "WeatherParameters", None)
    if weather_parameters is None:
        return
    try:
        current = world.get_weather() if hasattr(world, "get_weather") else weather_parameters()
    except Exception:
        current = weather_parameters()
    for key, value in weather.items():
        if hasattr(current, key):
            try:
                setattr(current, key, float(value))
            except (TypeError, ValueError):
                setattr(current, key, value)
    world.set_weather(current)


def _find_blueprint(blueprints: object, blueprint_filter: str) -> object:
    if "*" not in blueprint_filter:
        try:
            return blueprints.find(blueprint_filter)
        except Exception:
            pass
    matches = list(blueprints.filter(blueprint_filter))
    if not matches:
        raise ValueError(f"No CARLA blueprints matched {blueprint_filter}.")
    return matches[0]


def _spawn_actor(world: object, blueprint: object, transform: object) -> object:
    if hasattr(world, "try_spawn_actor"):
        actor = world.try_spawn_actor(blueprint, transform)
        if actor is not None:
            return actor
    return world.spawn_actor(blueprint, transform)


def _spawn_actor_safely(world: object, blueprint: object, transform: object) -> object | None:
    try:
        if hasattr(world, "try_spawn_actor"):
            return world.try_spawn_actor(blueprint, transform)
        return world.spawn_actor(blueprint, transform)
    except Exception:
        return None


def _disable_actor_physics(actor: object) -> None:
    if hasattr(actor, "set_autopilot"):
        try:
            actor.set_autopilot(False)
        except Exception:
            pass
    if hasattr(actor, "set_simulate_physics"):
        try:
            actor.set_simulate_physics(False)
        except Exception:
            pass


def _spawn_ego_with_retry(
    world: object,
    world_map: object,
    carla: object,
    config: CarlaOodDemoConfig,
    blueprint: object,
) -> tuple[object, RoadFrame, dict[str, dict[str, float]]]:
    selector = config.road_frame_selector()
    spawn_points = list(world_map.get_spawn_points())
    if not spawn_points:
        raise RuntimeError("CARLA map has no spawn points.")
    start_index = max(0, min(selector.spawn_index, len(spawn_points) - 1))
    candidate_indices = [
        (start_index + offset) % len(spawn_points)
        for offset in range(min(len(spawn_points), 40))
    ]
    last_error: Exception | None = None
    for spawn_index in candidate_indices:
        candidate_selector = replace(selector, spawn_index=spawn_index)
        road_frame = resolve_road_frame(world_map, candidate_selector)
        spawn_payload = _road_transform(
            config,
            road_frame,
            0.0,
            0.0,
            ROAD_ACTOR_SPAWN_Z_M,
            0.0,
        )
        transform = _carla_transform(carla, spawn_payload)
        try:
            if hasattr(world, "try_spawn_actor"):
                actor = world.try_spawn_actor(blueprint, transform)
                if actor is not None:
                    return actor, road_frame, spawn_payload
            else:
                actor = world.spawn_actor(blueprint, transform)
                return actor, road_frame, spawn_payload
        except Exception as exc:
            last_error = exc
    detail = f": {last_error}" if last_error is not None else ""
    raise RuntimeError(
        f"Unable to spawn ego actor at {len(candidate_indices)} road-frame candidates{detail}"
    )


def _spawn_road_actor_with_offsets(
    world: object,
    blueprint: object,
    carla: object,
    config: CarlaOodDemoConfig,
    road_frame: RoadFrame,
    x_m: float,
    y_m: float,
    z_m: float,
    yaw_delta_deg: float,
    *,
    offsets: list[tuple[float, float]],
) -> tuple[object, dict[str, dict[str, float]], tuple[float, float, float]] | None:
    for forward_offset, lateral_offset in offsets:
        local_x = x_m + forward_offset
        local_y = y_m + lateral_offset
        payload = _road_transform(
            config,
            road_frame,
            local_x,
            local_y,
            z_m,
            yaw_delta_deg,
        )
        actor = _spawn_actor_safely(world, blueprint, _carla_transform(carla, payload))
        if actor is not None:
            return actor, payload, (local_x, local_y, yaw_delta_deg)
    return None


def _ood_spawn_offsets(config: CarlaOodDemoConfig) -> list[tuple[float, float]]:
    lane = config.road_lane_width_m
    return [
        (0.0, 0.0),
        (8.0, 0.0),
        (14.0, 0.0),
        (-8.0, 0.0),
        (8.0, lane),
        (8.0, -lane),
        (18.0, lane),
        (18.0, -lane),
    ]


def _carla_transform(carla: object, payload: dict[str, dict[str, float]]) -> object:
    location = payload.get("location", {})
    rotation = payload.get("rotation", {})
    return carla.Transform(
        carla.Location(
            x=float(location.get("x", 0.0)),
            y=float(location.get("y", 0.0)),
            z=float(location.get("z", 0.0)),
        ),
        carla.Rotation(
            pitch=float(rotation.get("pitch", 0.0)),
            yaw=float(rotation.get("yaw", 0.0)),
            roll=float(rotation.get("roll", 0.0)),
        ),
    )


def _road_transform(
    config: CarlaOodDemoConfig,
    road_frame: RoadFrame,
    x_m: float,
    y_m: float,
    z_m: float = 0.0,
    yaw_delta_deg: float = 0.0,
) -> dict[str, dict[str, float]]:
    if config.coordinate_frame == "absolute_world":
        return _transform(x_m, y_m, z_m, yaw_delta_deg)
    return local_pose_to_payload(road_frame, x_m, y_m, z_m, yaw_delta_deg)


def _spawn_transform_for_spec(
    config: CarlaOodDemoConfig,
    road_frame: RoadFrame,
    spec: CarlaObjectSpawnSpec,
) -> dict[str, dict[str, float]]:
    if config.coordinate_frame == "absolute_world" or spec.coordinate_frame == "absolute_world":
        return spec.spawn_transform
    return transform_payload_to_road_frame(road_frame, spec.spawn_transform)


def _payload_from_actor(actor: object) -> dict[str, dict[str, float]]:
    try:
        transform = actor.get_transform()
    except Exception:
        return _transform(0.0, 0.0, 0.0, 0.0)
    return {
        "location": _vector_payload(transform.location),
        "rotation": _rotation_payload(transform.rotation),
    }


def _write_road_alignment_report(
    path: Path,
    *,
    road_frame: RoadFrame,
    alignment_transforms: dict[str, list[dict[str, dict[str, float]]]],
    config: CarlaOodDemoConfig,
) -> dict[str, Any]:
    actors = {
        actor_ref: validate_road_aligned_track(
            road_frame,
            transforms,
            actor_ref=actor_ref,
            max_lateral_offset_m=config.road_max_lateral_offset_m,
        ).to_jsonable()
        for actor_ref, transforms in sorted(alignment_transforms.items())
        if transforms
    }
    payload = {
        "coordinate_frame": config.coordinate_frame,
        "road_frame": road_frame.to_jsonable(),
        "actors": actors,
        "passes": all(report["passes"] for report in actors.values()),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _safe_set_transform(actor: object, transform: object) -> None:
    if hasattr(actor, "set_transform"):
        actor.set_transform(transform)


def _safe_apply_control_command(actor: object, command: object, carla: object) -> None:
    if not hasattr(actor, "apply_control"):
        return
    throttle = float(getattr(command, "throttle", 0.0))
    steer = float(getattr(command, "steer", 0.0))
    brake = float(getattr(command, "brake", 0.0))
    if hasattr(carla, "VehicleControl"):
        control = carla.VehicleControl(
            throttle=throttle,
            steer=steer,
            brake=brake,
        )
    else:
        control = {
            "throttle": throttle,
            "steer": steer,
            "brake": brake,
        }
    actor.apply_control(control)


def _next_image(
    images: "queue.Queue[object]",
    timeout_s: float,
    fallback: object | None,
) -> object | None:
    try:
        if fallback is not None:
            return images.get_nowait()
        return images.get(timeout=timeout_s)
    except queue.Empty:
        return fallback


def _tracks_for(
    actor_by_ref: dict[str, object],
    tick: int,
    t_s: float,
) -> list[dict[str, Any]]:
    tracks: list[dict[str, Any]] = []
    for actor_ref, actor in actor_by_ref.items():
        if actor_ref == "ego_rgb":
            continue
        transform = actor.get_transform()
        tracks.append(
            {
                "actor_ref": actor_ref,
                "actor_id": int(getattr(actor, "id")),
                "type_id": str(getattr(actor, "type_id", "")),
                "tick": tick,
                "t_s": round(float(t_s), 4),
                "location": _vector_payload(transform.location),
                "rotation": _rotation_payload(transform.rotation),
                "velocity": _vector_payload(actor.get_velocity()),
            }
        )
    return tracks


def _actor_ids(actors: list[object]) -> list[int]:
    return [int(getattr(actor, "id")) for actor in actors if hasattr(actor, "id")]


def _write_live_checkpoint(
    path: Path,
    *,
    config: CarlaOodDemoConfig,
    plan: CarlaOodDemoPlan,
    map_name: str | None,
    frame_count: int,
    tracks_path: Path,
    rgb_folder: Path,
    road_alignment_path: Path,
    spawned: list[object],
    destroyed: list[int],
    blockers: list[str],
) -> None:
    payload = {
        "status": "running",
        "host": config.host,
        "port": config.port,
        "map_name": map_name,
        "recipe_id": plan.recipe_id,
        "behavior_id": plan.behavior_id,
        "frame_count": frame_count,
        "duration_s": round(frame_count / max(config.fps, 1), 4),
        "tracks_path": str(tracks_path),
        "rgb_folder": str(rgb_folder),
        "road_alignment_path": str(road_alignment_path),
        "spawned_actor_ids": _actor_ids(spawned),
        "destroyed_actor_ids": destroyed,
        "generated_asset_ids": [spec.asset_id for spec in plan.object_spawn_specs],
        "blockers": blockers,
        "claim_boundaries": [
            "scripted_carla_ood_demo=true",
            "stock_fail2drive_score=false",
            "closed_loop_vla_control=false",
            "checkpoint_only=true",
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# CARLA OOD Demo",
        "",
        f"- status: `{payload['status']}`",
        f"- endpoint: `{payload['host']}:{payload['port']}`",
        f"- map_name: `{payload['map_name']}`",
        f"- recipe_id: `{payload['recipe_id']}`",
        f"- behavior_id: `{payload['behavior_id']}`",
        f"- frame_count: `{payload['frame_count']}`",
        f"- duration_s: `{payload['duration_s']}`",
        f"- rgb_folder: `{payload['rgb_folder']}`",
        f"- tracks_path: `{payload['tracks_path']}`",
        f"- generated_asset_ids: `{', '.join(payload['generated_asset_ids'])}`",
        f"- spawned_actor_ids: `{payload['spawned_actor_ids']}`",
        f"- destroyed_actor_ids: `{payload['destroyed_actor_ids']}`",
        f"- background_actor_ids: `{payload['background_actor_ids']}`",
        f"- fidelity_metrics: `{payload['fidelity_metrics']}`",
        "",
        "## Claim Boundaries",
        "",
    ]
    for boundary in payload["claim_boundaries"]:
        lines.append(f"- `{boundary}`")
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        for blocker in payload["blockers"]:
            lines.append(f"- {blocker}")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "CarlaOodDemoConfig",
    "CarlaOodDemoPlan",
    "CarlaOodDemoResult",
    "build_carla_ood_demo_plan",
    "load_carla_ood_demo_config",
    "run_carla_ood_demo",
    "write_carla_ood_demo",
]
