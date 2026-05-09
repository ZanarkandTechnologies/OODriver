"""Render two paragraph-to-CARLA showcase videos on a live CARLA server."""

from __future__ import annotations

import json
import math
import queue
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import carla


@dataclass(frozen=True)
class ShowcaseCase:
    case_id: str
    title: str
    paragraph: str
    weather: dict[str, float]
    route_distance_m: float
    target_drive_m: float
    props: tuple[dict[str, Any], ...]
    vehicles: tuple[dict[str, Any], ...]
    walkers: tuple[dict[str, Any], ...] = ()


CASES = (
    ShowcaseCase(
        case_id="prompt_market_lane_squeeze",
        title="Wet night-market lane squeeze",
        paragraph=(
            "Generate a wet Malaysian night-market road where a delivery van, food cart, "
            "cones, and spilled debris squeeze the right side of the lane. The ego car "
            "must continue for at least 50 meters while the scene makes clear this is "
            "an OOD roadside-market hazard, not a normal empty road."
        ),
        weather={
            "cloudiness": 85,
            "precipitation": 45,
            "precipitation_deposits": 70,
            "wetness": 85,
            "fog_density": 8,
            "sun_altitude_angle": -8,
            "sun_azimuth_angle": 35,
        },
        route_distance_m=90,
        target_drive_m=55,
        props=(
            {"blueprint": "static.prop.foodcart", "s": 28, "lateral": 3.2, "yaw": 95},
            {"blueprint": "static.prop.constructioncone", "s": 34, "lateral": 1.4, "yaw": 0},
            {"blueprint": "static.prop.constructioncone", "s": 39, "lateral": 1.3, "yaw": 0},
            {"blueprint": "static.prop.dirtdebris01", "s": 47, "lateral": 1.1, "yaw": 25},
        ),
        vehicles=(
            {"blueprint": "vehicle.carlamotors.carlacola", "s": 31, "lateral": 3.8, "yaw": 0},
            {"blueprint": "vehicle.vespa.zx125", "s": 52, "lateral": -2.9, "yaw": 180},
        ),
    ),
    ShowcaseCase(
        case_id="prompt_crash_debris_chicane",
        title="Crash debris chicane",
        paragraph=(
            "Generate a post-accident road segment with a stranded car, a work truck, "
            "barrels, cones, and debris forming a chicane. The ego car should drive "
            "roughly 100 meters through the generated environment so a judge can see "
            "the simulator route, the hazards, and the moving vehicle in one continuous video."
        ),
        weather={
            "cloudiness": 65,
            "precipitation": 10,
            "precipitation_deposits": 35,
            "wetness": 50,
            "fog_density": 3,
            "sun_altitude_angle": 18,
            "sun_azimuth_angle": 120,
        },
        route_distance_m=130,
        target_drive_m=100,
        props=(
            {"blueprint": "static.prop.barrel", "s": 42, "lateral": 3.6, "yaw": 0},
            {"blueprint": "static.prop.barrel", "s": 48, "lateral": -3.4, "yaw": 0},
            {"blueprint": "static.prop.constructioncone", "s": 55, "lateral": 3.4, "yaw": 0},
            {"blueprint": "static.prop.dirtdebris01", "s": 64, "lateral": -3.2, "yaw": 30},
        ),
        vehicles=(
            {"blueprint": "vehicle.tesla.model3", "s": 50, "lateral": 5.0, "yaw": 18},
            {"blueprint": "vehicle.carlamotors.carlacola", "s": 70, "lateral": -5.0, "yaw": 180},
        ),
    ),
)


def main() -> None:
    repo = Path("/workspace/0xDriver") if Path("/workspace/0xDriver").exists() else Path.cwd()
    output_root = repo / "artifacts" / "runs" / "prompt-showcase-carla"
    output_root.mkdir(parents=True, exist_ok=True)
    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(45)
    world = client.get_world()
    carla_map = world.get_map()
    route = _choose_route(carla_map, min_distance=max(case.route_distance_m for case in CASES))
    manifest = {
        "schema_version": "oodrive.prompt_showcase_carla.v1",
        "map": carla_map.name,
        "cases": [],
        "claim_boundaries": [
            "paragraph_to_carla_scene=true",
            "stock_carla_assets=true",
            "generated_custom_meshes=false",
            "closed_loop_vla_control=false",
        ],
    }
    for case in CASES:
        manifest["cases"].append(_render_case(world, route, case, output_root))
    manifest_path = output_root / "prompt_showcase_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({**manifest, "manifest_path": str(manifest_path)}, indent=2))


def _render_case(world: carla.World, route: list[carla.Waypoint], case: ShowcaseCase, output_root: Path) -> dict[str, Any]:
    case_dir = output_root / case.case_id
    frames_dir = case_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "prompt.md").write_text(f"# {case.title}\n\n{case.paragraph}\n", encoding="utf-8")
    (case_dir / "scene_spec.json").write_text(json.dumps(_case_spec(route, case), indent=2), encoding="utf-8")
    cleanup: list[carla.Actor] = []
    world.set_weather(_weather(case.weather))
    original = world.get_settings()
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 0.05
    world.apply_settings(settings)
    image_queue: queue.Queue[carla.Image] = queue.Queue()
    telemetry: list[dict[str, Any]] = []
    try:
        ego_bp = _blueprint(world, "vehicle.lincoln.mkz_2020", "vehicle.*")
        ego = world.try_spawn_actor(ego_bp, _route_transform(route[0], z_offset=0.25))
        if ego is None:
            raise RuntimeError("could not spawn ego vehicle")
        cleanup.append(ego)
        for item in case.props:
            actor = _spawn_relative(world, route, item)
            if actor is not None:
                cleanup.append(actor)
        for item in case.vehicles:
            actor = _spawn_relative(world, route, item)
            if actor is not None:
                cleanup.append(actor)
        camera_bp = world.get_blueprint_library().find("sensor.camera.rgb")
        camera_bp.set_attribute("image_size_x", "1280")
        camera_bp.set_attribute("image_size_y", "720")
        camera_bp.set_attribute("fov", "92")
        camera = world.spawn_actor(
            camera_bp,
            carla.Transform(carla.Location(x=-7.5, z=3.8), carla.Rotation(pitch=-12)),
            attach_to=ego,
        )
        cleanup.append(camera)
        camera.listen(image_queue.put)
        start = ego.get_location()
        max_frames = 1100
        for tick in range(max_frames):
            target = _target_location(route, ego.get_location(), lookahead_m=8.0)
            control = _control_to_target(ego, target, tick, case.target_drive_m, start)
            ego.apply_control(control)
            world.tick()
            image = _latest_image(image_queue, timeout=5)
            image.save_to_disk(str(frames_dir / f"{tick:05d}.jpg"))
            loc = ego.get_location()
            driven = loc.distance(start)
            telemetry.append(
                {
                    "frame": tick,
                    "x": round(loc.x, 3),
                    "y": round(loc.y, 3),
                    "z": round(loc.z, 3),
                    "distance_from_start_m": round(driven, 3),
                    "throttle": round(control.throttle, 3),
                    "steer": round(control.steer, 3),
                    "brake": round(control.brake, 3),
                }
            )
            if driven >= case.target_drive_m and tick > 180:
                break
        video_path = case_dir / f"{case.case_id}.mp4"
        _assemble_video(frames_dir, video_path)
        telemetry_path = case_dir / "telemetry.json"
        telemetry_path.write_text(json.dumps(telemetry, indent=2), encoding="utf-8")
        return {
            "case_id": case.case_id,
            "title": case.title,
            "paragraph_path": str(case_dir / "prompt.md"),
            "scene_spec_path": str(case_dir / "scene_spec.json"),
            "video_path": str(video_path),
            "first_frame": str(frames_dir / "00000.jpg"),
            "last_frame": str(frames_dir / f"{telemetry[-1]['frame']:05d}.jpg"),
            "telemetry_path": str(telemetry_path),
            "frames": len(telemetry),
            "target_drive_m": case.target_drive_m,
            "distance_from_start_m": telemetry[-1]["distance_from_start_m"],
            "stock_assets": True,
        }
    finally:
        for actor in reversed(cleanup):
            try:
                actor.destroy()
            except RuntimeError:
                pass
        world.apply_settings(original)


def _choose_route(carla_map: carla.Map, *, min_distance: float) -> list[carla.Waypoint]:
    best: list[carla.Waypoint] | None = None
    best_score = float("inf")
    for spawn in carla_map.get_spawn_points():
        waypoint = carla_map.get_waypoint(spawn.location, project_to_road=True, lane_type=carla.LaneType.Driving)
        if waypoint is None:
            continue
        route = [waypoint]
        current = waypoint
        yaw_change = 0.0
        for _ in range(int(min_distance / 3.0) + 15):
            options = current.next(3.0)
            if not options:
                break
            nxt = min(options, key=lambda candidate: abs(_yaw_delta(candidate.transform.rotation.yaw, current.transform.rotation.yaw)))
            yaw_change += abs(_yaw_delta(nxt.transform.rotation.yaw, current.transform.rotation.yaw))
            route.append(nxt)
            current = nxt
        distance = route[0].transform.location.distance(route[-1].transform.location)
        if distance >= min_distance and yaw_change < best_score:
            best = route
            best_score = yaw_change
    if best is None:
        raise RuntimeError(f"no route over {min_distance}m found on {carla_map.name}")
    return best


def _spawn_relative(world: carla.World, route: list[carla.Waypoint], item: dict[str, Any]) -> carla.Actor | None:
    waypoint = route[min(len(route) - 1, max(0, int(float(item["s"]) / 3.0)))]
    transform = _relative_transform(waypoint, float(item.get("lateral", 0.0)), float(item.get("yaw", 0.0)))
    bp = _blueprint(world, str(item["blueprint"]), str(item["blueprint"]).split(".")[0] + ".*")
    if bp.has_attribute("role_name"):
        bp.set_attribute("role_name", "oodrive_showcase")
    return world.try_spawn_actor(bp, transform)


def _control_to_target(
    ego: carla.Vehicle,
    target: carla.Location,
    tick: int,
    target_drive_m: float,
    start: carla.Location,
) -> carla.VehicleControl:
    loc = ego.get_location()
    yaw = math.radians(ego.get_transform().rotation.yaw)
    dx = target.x - loc.x
    dy = target.y - loc.y
    desired = math.atan2(dy, dx)
    angle = math.atan2(math.sin(desired - yaw), math.cos(desired - yaw))
    driven = loc.distance(start)
    control = carla.VehicleControl()
    control.steer = max(-0.55, min(0.55, angle * 0.9))
    if driven >= target_drive_m:
        control.brake = 0.7
        control.throttle = 0.0
    else:
        control.throttle = 0.65 if tick < 120 else 0.5
        control.brake = 0.0
    return control


def _target_location(route: list[carla.Waypoint], current: carla.Location, *, lookahead_m: float) -> carla.Location:
    closest_index = min(range(len(route)), key=lambda idx: route[idx].transform.location.distance(current))
    target_index = min(len(route) - 1, closest_index + max(2, int(lookahead_m / 3.0)))
    return route[target_index].transform.location


def _relative_transform(waypoint: carla.Waypoint, lateral: float, yaw_offset: float) -> carla.Transform:
    transform = waypoint.transform
    yaw = math.radians(transform.rotation.yaw)
    loc = carla.Location(
        x=transform.location.x - math.sin(yaw) * lateral,
        y=transform.location.y + math.cos(yaw) * lateral,
        z=transform.location.z + 0.35,
    )
    return carla.Transform(loc, carla.Rotation(yaw=transform.rotation.yaw + yaw_offset))


def _route_transform(waypoint: carla.Waypoint, *, z_offset: float = 0.0) -> carla.Transform:
    transform = waypoint.transform
    transform.location.z += z_offset
    return transform


def _blueprint(world: carla.World, preferred: str, fallback: str) -> carla.ActorBlueprint:
    library = world.get_blueprint_library()
    matches = library.filter(preferred)
    if not matches:
        matches = library.filter(fallback)
    if not matches:
        raise RuntimeError(f"no CARLA blueprint for {preferred} or {fallback}")
    return matches[0]


def _weather(payload: dict[str, float]) -> carla.WeatherParameters:
    weather = carla.WeatherParameters()
    for key, value in payload.items():
        setattr(weather, key, float(value))
    return weather


def _latest_image(images: queue.Queue[carla.Image], *, timeout: float) -> carla.Image:
    image = images.get(timeout=timeout)
    while True:
        try:
            image = images.get_nowait()
        except queue.Empty:
            return image


def _assemble_video(frames_dir: Path, video_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            "20",
            "-pattern_type",
            "glob",
            "-i",
            str(frames_dir / "*.jpg"),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "24",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(video_path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _case_spec(route: list[carla.Waypoint], case: ShowcaseCase) -> dict[str, Any]:
    return {
        "title": case.title,
        "paragraph": case.paragraph,
        "weather": case.weather,
        "route_start": _location_json(route[0].transform.location),
        "route_end": _location_json(route[-1].transform.location),
        "target_drive_m": case.target_drive_m,
        "props": case.props,
        "vehicles": case.vehicles,
    }


def _location_json(loc: carla.Location) -> dict[str, float]:
    return {"x": round(loc.x, 3), "y": round(loc.y, 3), "z": round(loc.z, 3)}


def _yaw_delta(a: float, b: float) -> float:
    return math.degrees(math.atan2(math.sin(math.radians(a - b)), math.cos(math.radians(a - b))))


if __name__ == "__main__":
    main()
