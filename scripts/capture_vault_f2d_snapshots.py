"""Capture CARLA snapshots at generated Fail2Drive XML trigger anchors."""

from __future__ import annotations

import json
import math
import queue
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import carla


def main() -> None:
    repo = Path("/workspace/0xDriver")
    manifest_path = repo / "artifacts" / "runs" / "vault-f2d-scenarios" / "vault_f2d_scenarios_manifest.json"
    out = repo / "artifacts" / "runs" / "vault-f2d-scenarios" / "snapshots"
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(20)
    world = client.get_world()
    blueprints = world.get_blueprint_library()
    captured = []
    for case in manifest["cases"]:
        actors: list[carla.Actor] = []
        try:
            trigger = _trigger(Path(case["route_path"]))
            actors.extend(_spawn_case(world, blueprints, case["scenario_type"], trigger))
            for _ in range(5):
                world.tick()
            image_path = out / f"{case['id']}.png"
            _capture(world, blueprints, trigger, image_path)
            captured.append({**case, "snapshot_path": str(image_path), "spawned_actor_count": len(actors)})
        finally:
            for actor in actors:
                try:
                    actor.destroy()
                except RuntimeError:
                    pass
    summary_path = out / "snapshot_summary.json"
    summary_path.write_text(json.dumps({"snapshots": captured}, indent=2), encoding="utf-8")
    print(json.dumps({"summary_path": str(summary_path), "snapshots": captured}, indent=2))


def _trigger(route_path: Path) -> carla.Transform:
    root = ET.parse(route_path).getroot()
    elem = root.find(".//trigger_point")
    if elem is None:
        raise RuntimeError(f"missing trigger_point in {route_path}")
    return carla.Transform(
        carla.Location(float(elem.get("x", "0")), float(elem.get("y", "0")), float(elem.get("z", "0")) + 0.2),
        carla.Rotation(yaw=float(elem.get("yaw", "0"))),
    )


def _spawn_case(world: carla.World, blueprints: carla.BlueprintLibrary, scenario_type: str, trigger: carla.Transform) -> list[carla.Actor]:
    yaw = math.radians(trigger.rotation.yaw)
    forward = carla.Vector3D(math.cos(yaw), math.sin(yaw), 0)
    right = carla.Vector3D(-math.sin(yaw), math.cos(yaw), 0)
    base = trigger.location + forward * 12.0
    actors = []
    if scenario_type == "RoadBlocked":
        actors.append(_spawn(world, blueprints, "static.prop.foodcart", base, trigger.rotation.yaw + 90))
        actors.append(_spawn(world, blueprints, "static.prop.barrel", base + right * 2.0, trigger.rotation.yaw))
        actors.append(_spawn(world, blueprints, "static.prop.dirtdebris01", base - right * 2.0, trigger.rotation.yaw))
    elif scenario_type == "DynamicObjectCrossing":
        actors.append(_spawn(world, blueprints, "static.prop.vendingmachine", base + right * 2.5, trigger.rotation.yaw))
        actors.append(_spawn(world, blueprints, "walker.pedestrian.0001", base - right * 1.8, trigger.rotation.yaw + 90))
    elif scenario_type == "Accident":
        actors.append(_spawn(world, blueprints, "vehicle.tesla.model3", base, trigger.rotation.yaw + 70))
        actors.append(_spawn(world, blueprints, "static.prop.dirtdebris01", base + forward * 3.0, trigger.rotation.yaw))
        actors.append(_spawn(world, blueprints, "static.prop.constructioncone", base - right * 2.0, trigger.rotation.yaw))
    else:
        actors.append(_spawn(world, blueprints, "static.prop.dirtdebris01", base, trigger.rotation.yaw))
        actors.append(_spawn(world, blueprints, "static.prop.constructioncone", base + right * 2.0, trigger.rotation.yaw))
        actors.append(_spawn(world, blueprints, "static.prop.barrel", base - right * 2.0, trigger.rotation.yaw))
    return [actor for actor in actors if actor is not None]


def _spawn(world: carla.World, blueprints: carla.BlueprintLibrary, blueprint_id: str, loc: carla.Location, yaw: float) -> carla.Actor | None:
    blueprint = _blueprint(blueprints, blueprint_id)
    if blueprint is None:
        return None
    transform = carla.Transform(carla.Location(loc.x, loc.y, loc.z + 0.2), carla.Rotation(yaw=yaw))
    return world.try_spawn_actor(blueprint, transform)


def _blueprint(blueprints: carla.BlueprintLibrary, blueprint_id: str) -> carla.ActorBlueprint | None:
    matches = blueprints.filter(blueprint_id)
    if matches:
        return matches[0]
    prefix = blueprint_id.rsplit(".", 1)[0] + ".*"
    fallback = blueprints.filter(prefix)
    return fallback[0] if fallback else None


def _capture(world: carla.World, blueprints: carla.BlueprintLibrary, trigger: carla.Transform, path: Path) -> None:
    camera_bp = blueprints.find("sensor.camera.rgb")
    camera_bp.set_attribute("image_size_x", "1280")
    camera_bp.set_attribute("image_size_y", "720")
    camera_bp.set_attribute("fov", "90")
    yaw = math.radians(trigger.rotation.yaw)
    back = carla.Vector3D(-math.cos(yaw), -math.sin(yaw), 0)
    loc = trigger.location + back * 18.0 + carla.Vector3D(0, 0, 7.0)
    transform = carla.Transform(loc, carla.Rotation(pitch=-18, yaw=trigger.rotation.yaw))
    camera = world.spawn_actor(camera_bp, transform)
    images: queue.Queue[carla.Image] = queue.Queue()
    camera.listen(images.put)
    try:
        deadline = time.time() + 10
        image = None
        while time.time() < deadline:
            world.tick()
            try:
                image = images.get(timeout=1)
                break
            except queue.Empty:
                pass
        if image is None:
            raise RuntimeError("camera did not produce an image")
        image.save_to_disk(str(path))
    finally:
        camera.stop()
        camera.destroy()


if __name__ == "__main__":
    main()
