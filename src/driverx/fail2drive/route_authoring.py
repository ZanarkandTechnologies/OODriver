"""Compile small agent-authored route specs into Fail2Drive route XML."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.fail2drive.catalog import Fail2DriveCatalog
from driverx.fail2drive.route_validation import validate_fail2drive_route


HONEST_CLAIMS = {
    "fail2drive_route_xml_generated": True,
    "carla_runtime_executed": False,
    "closed_loop_vla_control": False,
}


@dataclass(frozen=True)
class Fail2DriveRouteWriteResult:
    spec_path: Path | None
    output_path: Path
    validation: dict[str, Any] | None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": "oodrive.fail2drive_route_write.v1",
            "spec_path": str(self.spec_path) if self.spec_path is not None else None,
            "output_path": str(self.output_path),
            "validation": self.validation,
            "claim_boundaries": HONEST_CLAIMS,
        }


def example_fail2drive_route_spec(scenario_type: str = "RoadBlocked") -> dict[str, Any]:
    scenario_type = scenario_type or "RoadBlocked"
    params_by_type: dict[str, dict[str, Any]] = {
        "RoadBlocked": {"distance": 60, "wait": 15, "objects": {"vehicle.carlamotors.carlacola": "0,0,0", "static.prop.barrel": "1.5,0,0"}},
        "DynamicObjectCrossing": {"distance": 12, "direction": "right", "blocker_model": "static.prop.vendingmachine", "crossing_angle": 0, "walker": "walker.pedestrian.*"},
        "Accident": {"distance": 80, "direction": "right", "speed": 35},
        "CustomObstacle": {"distance": 55, "objects": {"static.prop.dirtdebris01": "0,0,0", "static.prop.constructioncone": "2,0,0"}},
    }
    return {
        "route_id": f"oodrive-{scenario_type.lower()}-001",
        "town": "Town05",
        "weather": {"cloudiness": 40, "precipitation": 15, "sun_altitude_angle": 35},
        "waypoints": [
            {"x": 0.0, "y": 0.0, "z": 0.0},
            {"x": 75.0, "y": 0.0, "z": 0.0},
        ],
        "scenarios": [
            {
                "name": f"{scenario_type}_0",
                "type": scenario_type,
                "trigger_point": {"x": 35.0, "y": 0.0, "z": 0.0, "yaw": 0.0},
                "params": params_by_type.get(scenario_type, {"distance": 50}),
            }
        ],
        "claim_boundaries": HONEST_CLAIMS,
    }


def load_fail2drive_route_spec(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Fail2Drive route spec must be a JSON object.")
    return payload


def write_fail2drive_route_xml(
    spec: dict[str, Any],
    output_path: Path,
    *,
    catalog: Fail2DriveCatalog | None = None,
    validate: bool = False,
    spec_path: Path | None = None,
) -> Fail2DriveRouteWriteResult:
    output = output_path.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("routes")
    route = ET.SubElement(root, "route")
    route.set("id", str(spec.get("route_id") or spec.get("id") or "0"))
    route.set("town", str(spec.get("town") or "Town05"))
    weather_payload = _mapping(spec.get("weather"))
    if weather_payload:
        weathers = ET.SubElement(route, "weathers")
        weather = ET.SubElement(weathers, "weather")
        for key, value in sorted(weather_payload.items()):
            weather.set(str(key), str(value))
    waypoints = ET.SubElement(route, "waypoints")
    for waypoint in _sequence(spec.get("waypoints")):
        position = ET.SubElement(waypoints, "position")
        _set_xyz(position, _mapping(waypoint))
    scenarios = ET.SubElement(route, "scenarios")
    for index, scenario_spec in enumerate(_sequence(spec.get("scenarios"))):
        scenario_data = _mapping(scenario_spec)
        scenario_type = str(scenario_data.get("type") or "RoadBlocked")
        scenario = ET.SubElement(scenarios, "scenario")
        scenario.set("name", str(scenario_data.get("name") or f"{scenario_type}_{index}"))
        scenario.set("type", scenario_type)
        params = _mapping(scenario_data.get("params"))
        for name, value in sorted(params.items()):
            _append_param(scenario, str(name), value)
        trigger = ET.SubElement(scenario, "trigger_point")
        _set_transform(trigger, _mapping(scenario_data.get("trigger_point")))
    _indent(root)
    ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)
    validation_payload = None
    if validate and catalog is not None:
        validation_payload = validate_fail2drive_route(output, catalog).to_jsonable()
    return Fail2DriveRouteWriteResult(
        spec_path=spec_path.expanduser().resolve() if spec_path is not None else None,
        output_path=output,
        validation=validation_payload,
    )


def write_fail2drive_route_write_report(run_dir: Path, result: Fail2DriveRouteWriteResult) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = result.to_jsonable()
    json_path = run_dir / "fail2drive_route_write.json"
    report_path = run_dir / "fail2drive_route_write.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _append_param(parent: ET.Element, name: str, value: Any) -> None:
    elem = ET.SubElement(parent, name)
    if isinstance(value, dict):
        if {"x", "y", "z", "yaw"}.issubset(value.keys()):
            _set_transform(elem, value)
        elif {"x", "y", "z"}.issubset(value.keys()):
            _set_xyz(elem, value)
            if "p" in value:
                elem.set("p", str(value["p"]))
        else:
            for key, attr_value in sorted(value.items()):
                elem.set(str(key), str(attr_value))
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        elem.set("from", str(value[0]))
        elem.set("to", str(value[1]))
    else:
        elem.set("value", str(value))


def _set_xyz(elem: ET.Element, data: dict[str, Any]) -> None:
    elem.set("x", str(data.get("x", 0.0)))
    elem.set("y", str(data.get("y", 0.0)))
    elem.set("z", str(data.get("z", 0.0)))


def _set_transform(elem: ET.Element, data: dict[str, Any]) -> None:
    _set_xyz(elem, data)
    elem.set("yaw", str(data.get("yaw", 0.0)))


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return ()


def _indent(elem: ET.Element, level: int = 0) -> None:
    space = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = space + "  "
        for child in elem:
            _indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = space
    elif level and (not elem.tail or not elem.tail.strip()):
        elem.tail = space


def _markdown(payload: dict[str, Any]) -> str:
    validation = payload.get("validation") if isinstance(payload.get("validation"), dict) else {}
    return "\n".join(
        [
            "# Fail2Drive Route Write",
            "",
            f"- output: `{payload.get('output_path')}`",
            f"- validation ok: {validation.get('ok') if validation else 'not run'}",
            f"- validation errors: {validation.get('error_count') if validation else 'not run'}",
            "",
        ]
    )


__all__ = [
    "Fail2DriveRouteWriteResult",
    "example_fail2drive_route_spec",
    "load_fail2drive_route_spec",
    "write_fail2drive_route_write_report",
    "write_fail2drive_route_xml",
]
