"""Render Fail2Drive animal walker assets on a live CARLA server."""

from __future__ import annotations

import json
import math
import queue
import subprocess
from pathlib import Path
from typing import Any

import carla


ANIMAL_PATTERNS = ("*elephant*", "*cow*", "*deer*", "walker.animal.*")


def main() -> None:
    repo = Path("/workspace/0xDriver") if Path("/workspace/0xDriver").exists() else Path.cwd()
    output_root = repo / "artifacts" / "runs" / "task188-animal-showcase-live"
    output_root.mkdir(parents=True, exist_ok=True)
    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(45)
    world = client.get_world()
    animals = _animal_blueprints(world)
    if not animals:
        raise RuntimeError("no animal walker blueprints are registered on the running CARLA server")
    manifest = _render_animal_crossing(world, animals, output_root)
    manifest_path = output_root / "animal_showcase_manifest.json"
    manifest["manifest_path"] = str(manifest_path)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def _animal_blueprints(world: carla.World) -> list[carla.ActorBlueprint]:
    library = world.get_blueprint_library()
    blueprints: dict[str, carla.ActorBlueprint] = {}
    for pattern in ANIMAL_PATTERNS:
        for blueprint in library.filter(pattern):
            if blueprint.id.startswith("walker.animal") or any(token in blueprint.id.lower() for token in ("elephant", "cow", "deer")):
                blueprints[blueprint.id] = blueprint
    return [blueprints[key] for key in sorted(blueprints)]


def _render_animal_crossing(world: carla.World, animals: list[carla.ActorBlueprint], output_root: Path) -> dict[str, Any]:
    case_id = "animal_assets_crossing_gallery_v2"
    case_dir = output_root / case_id
    frames_dir = case_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    prompt = (
        "Generate a weird animal road hazard with the available Fail2Drive animal assets "
        "placed directly in front of the ego vehicle, then drive forward so the animals "
        "stay visible in-frame."
    )
    (case_dir / "prompt.md").write_text(f"# Animal assets crossing gallery\n\n{prompt}\n", encoding="utf-8")
    route = _choose_route(world.get_map(), min_distance=80)
    original = world.get_settings()
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 0.05
    world.apply_settings(settings)
    world.set_weather(_clear_weather())
    cleanup: list[carla.Actor] = []
    image_queue: queue.Queue[carla.Image] = queue.Queue()
    spawned: list[dict[str, Any]] = []
    telemetry: list[dict[str, Any]] = []
    try:
        ego_bp = world.get_blueprint_library().filter("vehicle.lincoln.mkz_2020")[0]
        ego = world.try_spawn_actor(ego_bp, _route_transform(route[0], z_offset=0.25))
        if ego is None:
            raise RuntimeError("could not spawn ego vehicle")
        cleanup.append(ego)
        selected = animals
        for index, blueprint in enumerate(selected):
            if blueprint.has_attribute("role_name"):
                blueprint.set_attribute("role_name", "oodrive_animal_showcase")
            row = index // 6
            col = index % 6
            s = 13.0 + row * 9.0
            lateral = -8.5 + col * 3.4
            transform = _relative_transform(route[min(len(route) - 1, int(s / 3.0))], lateral, yaw_offset=80 - index * 12)
            actor = world.try_spawn_actor(blueprint, transform)
            spawned.append(
                {
                    "requested_blueprint": blueprint.id,
                    "spawned": actor is not None,
                    "spawned_actor_id": actor.id if actor is not None else None,
                    "s": s,
                    "lateral": lateral,
                }
            )
            if actor is not None:
                cleanup.append(actor)
                if isinstance(actor, carla.Walker):
                    actor.apply_control(carla.WalkerControl(direction=carla.Vector3D(0.0, 1.0, 0.0), speed=0.45))
        camera_bp = world.get_blueprint_library().find("sensor.camera.rgb")
        camera_bp.set_attribute("image_size_x", "1280")
        camera_bp.set_attribute("image_size_y", "720")
        camera_bp.set_attribute("fov", "82")
        camera = world.spawn_actor(camera_bp, _gallery_camera_transform(route))
        cleanup.append(camera)
        camera.listen(image_queue.put)
        start = ego.get_location()
        for tick in range(260):
            target = _target_location(route, ego.get_location(), lookahead_m=8.0)
            control = _control_to_target(ego, target, start)
            ego.apply_control(control)
            world.tick()
            image = _latest_image(image_queue, timeout=5)
            image.save_to_disk(str(frames_dir / f"{tick:05d}.jpg"))
            loc = ego.get_location()
            telemetry.append(
                {
                    "frame": tick,
                    "distance_from_start_m": round(loc.distance(start), 3),
                    "throttle": round(control.throttle, 3),
                    "steer": round(control.steer, 3),
                    "brake": round(control.brake, 3),
                }
            )
        video_path = case_dir / f"{case_id}.mp4"
        _assemble_video(frames_dir, video_path)
        telemetry_path = case_dir / "telemetry.json"
        scene_spec_path = case_dir / "scene_spec.json"
        telemetry_path.write_text(json.dumps(telemetry, indent=2), encoding="utf-8")
        scene_spec = {
            "prompt": prompt,
            "available_animal_blueprints": [bp.id for bp in animals],
            "requested_animals": [bp.id for bp in selected],
            "spawned_assets": spawned,
            "route_start": _location_json(route[0].transform.location),
            "route_end": _location_json(route[-1].transform.location),
        }
        scene_spec_path.write_text(json.dumps(scene_spec, indent=2), encoding="utf-8")
        return {
            "schema_version": "oodrive.animal_showcase_carla.v1",
            "map": world.get_map().name,
            "case_id": case_id,
            "prompt": prompt,
            "video_path": str(video_path),
            "first_frame": str(frames_dir / "00000.jpg"),
            "last_frame": str(frames_dir / f"{telemetry[-1]['frame']:05d}.jpg"),
            "scene_spec_path": str(scene_spec_path),
            "telemetry_path": str(telemetry_path),
            "frames": len(telemetry),
            "distance_from_start_m": telemetry[-1]["distance_from_start_m"],
            "available_animal_blueprints": [bp.id for bp in animals],
            "spawned_assets": spawned,
            "spawned_asset_count": sum(1 for asset in spawned if asset["spawned"]),
            "claim_boundaries": [
                "fail2drive_animal_assets_required=true",
                "generated_custom_meshes=false",
                "duck_assets_available=false",
                "closed_loop_vla_control=false",
            ],
        }
    finally:
        for actor in reversed(cleanup):
            try:
                actor.destroy()
            except RuntimeError:
                pass
        world.apply_settings(original)


def _choose_route(carla_map: carla.Map, *, min_distance: float) -> list[carla.Waypoint]:
    for spawn in carla_map.get_spawn_points():
        waypoint = carla_map.get_waypoint(spawn.location, project_to_road=True, lane_type=carla.LaneType.Driving)
        if waypoint is None:
            continue
        route = [waypoint]
        current = waypoint
        for _ in range(int(min_distance / 3.0) + 10):
            options = current.next(3.0)
            if not options:
                break
            current = min(options, key=lambda candidate: abs(_yaw_delta(candidate.transform.rotation.yaw, current.transform.rotation.yaw)))
            route.append(current)
        if route[0].transform.location.distance(route[-1].transform.location) >= min_distance:
            return route
    raise RuntimeError(f"no route over {min_distance}m found on {carla_map.name}")


def _control_to_target(ego: carla.Vehicle, target: carla.Location, start: carla.Location) -> carla.VehicleControl:
    loc = ego.get_location()
    yaw = math.radians(ego.get_transform().rotation.yaw)
    desired = math.atan2(target.y - loc.y, target.x - loc.x)
    angle = math.atan2(math.sin(desired - yaw), math.cos(desired - yaw))
    driven = loc.distance(start)
    control = carla.VehicleControl()
    control.steer = max(-0.45, min(0.45, angle * 0.8))
    if driven > 55:
        control.brake = 0.45
    else:
        control.throttle = 0.32
    return control


def _target_location(route: list[carla.Waypoint], current: carla.Location, *, lookahead_m: float) -> carla.Location:
    closest_index = min(range(len(route)), key=lambda idx: route[idx].transform.location.distance(current))
    return route[min(len(route) - 1, closest_index + max(2, int(lookahead_m / 3.0)))].transform.location


def _relative_transform(waypoint: carla.Waypoint, lateral: float, yaw_offset: float) -> carla.Transform:
    transform = waypoint.transform
    yaw = math.radians(transform.rotation.yaw)
    loc = carla.Location(
        x=transform.location.x - math.sin(yaw) * lateral,
        y=transform.location.y + math.cos(yaw) * lateral,
        z=transform.location.z + 0.35,
    )
    return carla.Transform(loc, carla.Rotation(yaw=transform.rotation.yaw + yaw_offset))


def _gallery_camera_transform(route: list[carla.Waypoint]) -> carla.Transform:
    anchor = route[6].transform
    yaw = math.radians(anchor.rotation.yaw)
    loc = carla.Location(
        x=anchor.location.x - math.cos(yaw) * 18.0,
        y=anchor.location.y - math.sin(yaw) * 18.0,
        z=anchor.location.z + 9.0,
    )
    return carla.Transform(loc, carla.Rotation(pitch=-24.0, yaw=anchor.rotation.yaw))


def _route_transform(waypoint: carla.Waypoint, *, z_offset: float = 0.0) -> carla.Transform:
    transform = waypoint.transform
    transform.location.z += z_offset
    return transform


def _clear_weather() -> carla.WeatherParameters:
    weather = carla.WeatherParameters()
    weather.cloudiness = 25.0
    weather.precipitation = 0.0
    weather.wetness = 10.0
    weather.fog_density = 0.0
    weather.sun_altitude_angle = 35.0
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
            "22",
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


def _location_json(loc: carla.Location) -> dict[str, float]:
    return {"x": round(loc.x, 3), "y": round(loc.y, 3), "z": round(loc.z, 3)}


def _yaw_delta(a: float, b: float) -> float:
    return math.degrees(math.atan2(math.sin(math.radians(a - b)), math.cos(math.radians(a - b))))


if __name__ == "__main__":
    main()
