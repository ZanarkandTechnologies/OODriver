"""Generate four Fail2Drive route XMLs from the currently loaded CARLA map."""

from __future__ import annotations

import json
from pathlib import Path

import carla

from driverx.fail2drive.catalog import load_fail2drive_catalog
from driverx.fail2drive.route_authoring import write_fail2drive_route_xml
from driverx.fail2drive.route_validation import (
    validate_fail2drive_route,
    write_fail2drive_route_validation,
)


def main() -> None:
    repo = Path("/workspace/0xDriver")
    root = Path("/workspace/fail2drive")
    out = repo / "artifacts" / "runs" / "vault-f2d-scenarios"
    spec_dir = out / "specs"
    route_dir = out / "routes"
    validation_dir = out / "validation"
    for directory in (spec_dir, route_dir, validation_dir):
        directory.mkdir(parents=True, exist_ok=True)

    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(45)
    world = client.get_world()
    carla_map = world.get_map()
    town = carla_map.name.split("/")[-1]
    chosen = _choose_route(carla_map)
    waypoints = [_xyz(chosen[i]) for i in (0, 10, 20, 30, 42)]
    weather = {
        "route_percentage": 0,
        "cloudiness": 75,
        "precipitation": 35,
        "precipitation_deposits": 45,
        "wetness": 65,
        "wind_intensity": 20,
        "sun_altitude_angle": 20,
        "fog_density": 5,
    }
    cases = _cases(chosen)
    catalog = load_fail2drive_catalog(root)
    manifest = {"schema_version": "oodrive.vault_f2d_scenarios.v1", "town": town, "cases": []}
    for case in cases:
        spec = {
            "route_id": case["id"],
            "town": town,
            "weather": weather,
            "waypoints": waypoints,
            "scenarios": [case["scenario"]],
            "claim_boundaries": {
                "fail2drive_route_xml_generated": True,
                "carla_runtime_executed": False,
                "closed_loop_vla_control": False,
            },
        }
        spec_path = spec_dir / f"{case['id']}.json"
        route_path = route_dir / f"{case['id']}.xml"
        spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        write_fail2drive_route_xml(spec, route_path, catalog=catalog, validate=True, spec_path=spec_path)
        validation = validate_fail2drive_route(route_path, catalog)
        validation_summary = write_fail2drive_route_validation(validation_dir / case["id"], validation)
        manifest["cases"].append(
            {
                "id": case["id"],
                "title": case["title"],
                "spec_path": str(spec_path),
                "route_path": str(route_path),
                "validation_ok": validation.ok,
                "validation_path": validation_summary["json_path"],
                "scenario_type": case["scenario"]["type"],
            }
        )
    manifest_path = out / "vault_f2d_scenarios_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def _choose_route(carla_map: carla.Map) -> list[carla.Waypoint]:
    for spawn in carla_map.get_spawn_points():
        waypoint = carla_map.get_waypoint(
            spawn.location,
            project_to_road=True,
            lane_type=carla.LaneType.Driving,
        )
        if waypoint is None:
            continue
        route = [waypoint]
        current = waypoint
        ok = True
        for _ in range(42):
            next_waypoints = current.next(5.0)
            if not next_waypoints:
                ok = False
                break
            current = sorted(
                next_waypoints,
                key=lambda candidate: abs(candidate.transform.rotation.yaw - current.transform.rotation.yaw),
            )[0]
            route.append(current)
        if ok and route[0].transform.location.distance(route[-1].transform.location) > 100:
            return route
    raise RuntimeError(f"no long route found on {carla_map.name}")


def _xyz(waypoint: carla.Waypoint) -> dict[str, float]:
    loc = waypoint.transform.location
    return {"x": round(loc.x, 2), "y": round(loc.y, 2), "z": round(loc.z, 2)}


def _transform(waypoint: carla.Waypoint) -> dict[str, float]:
    loc = waypoint.transform.location
    rot = waypoint.transform.rotation
    return {"x": round(loc.x, 2), "y": round(loc.y, 2), "z": round(loc.z, 2), "yaw": round(rot.yaw, 2)}


def _cases(route: list[carla.Waypoint]) -> list[dict[str, object]]:
    return [
        {
            "id": "vault_static_roadblock",
            "title": "Static roadblock: stopped truck/barrels block the lane",
            "scenario": {
                "name": "RoadBlocked_0",
                "type": "RoadBlocked",
                "trigger_point": _transform(route[12]),
                "params": {"distance": 45, "wait": 12},
            },
        },
        {
            "id": "vault_occluded_moving_crossing",
            "title": "Moving object: occluded pedestrian crosses from behind roadside object",
            "scenario": {
                "name": "DynamicObjectCrossing_0",
                "type": "DynamicObjectCrossing",
                "trigger_point": _transform(route[14]),
                "params": {
                    "distance": 12,
                    "direction": "right",
                    "blocker_model": "static.prop.vendingmachine",
                    "crossing_angle": 0,
                    "walker": "walker.pedestrian.*",
                },
            },
        },
        {
            "id": "vault_accident_debris_swerve",
            "title": "Accident/debris: lane obstruction forces early slowing and evasive path",
            "scenario": {
                "name": "Accident_0",
                "type": "Accident",
                "trigger_point": _transform(route[16]),
                "params": {"distance": 65, "direction": "right", "speed": 35},
            },
        },
        {
            "id": "vault_compound_custom_block",
            "title": "Compound obstacle: mixed debris/cones create a constrained passable gap",
            "scenario": {
                "name": "CustomObstacle_0",
                "type": "CustomObstacle",
                "trigger_point": _transform(route[18]),
                "params": {
                    "distance": 50,
                    "objects": {
                        "static.prop.dirtdebris01": "0,0,0",
                        "static.prop.constructioncone": "2,0,0",
                        "static.prop.barrel": "-2,0,0",
                    },
                },
            },
        },
    ]


if __name__ == "__main__":
    main()
