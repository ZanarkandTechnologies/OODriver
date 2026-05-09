"""Fast structural validation for agent-authored Fail2Drive route XML."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.fail2drive.catalog import Fail2DriveCatalog


@dataclass(frozen=True)
class RouteIssue:
    severity: str
    code: str
    xml_path: str
    message: str
    suggestion: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "xml_path": self.xml_path,
            "message": self.message,
            "suggestion": self.suggestion,
        }


@dataclass(frozen=True)
class Fail2DriveRouteValidation:
    route_path: Path
    ok: bool
    route_count: int
    town_names: tuple[str, ...]
    scenario_counts: dict[str, int]
    issues: tuple[RouteIssue, ...]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": "oodrive.fail2drive_route_validation.v1",
            "route_path": str(self.route_path),
            "ok": self.ok,
            "route_count": self.route_count,
            "town_names": list(self.town_names),
            "scenario_counts": self.scenario_counts,
            "error_count": sum(1 for issue in self.issues if issue.severity == "error"),
            "warning_count": sum(1 for issue in self.issues if issue.severity == "warning"),
            "issues": [issue.to_jsonable() for issue in self.issues],
            "claim_boundaries": [
                "structural_xml_validation=true",
                "route_geometry_runtime_validation=false",
                "fail2drive_evaluator_run=false",
            ],
        }


def validate_fail2drive_route(route_path: Path, catalog: Fail2DriveCatalog, *, strict: bool = False) -> Fail2DriveRouteValidation:
    route_file = route_path.expanduser().resolve()
    issues: list[RouteIssue] = []
    if not route_file.exists():
        return Fail2DriveRouteValidation(
            route_path=route_file,
            ok=False,
            route_count=0,
            town_names=(),
            scenario_counts={},
            issues=(RouteIssue("error", "missing_route_file", "$", f"Route XML not found: {route_file}", "Create the route file or pass the correct --route path."),),
        )
    try:
        root = ET.parse(route_file).getroot()
    except ET.ParseError as exc:
        return Fail2DriveRouteValidation(
            route_path=route_file,
            ok=False,
            route_count=0,
            town_names=(),
            scenario_counts={},
            issues=(RouteIssue("error", "xml_parse_error", "$", str(exc), "Fix XML syntax before route validation."),),
        )
    if root.tag != "routes":
        issues.append(RouteIssue("error", "invalid_root", "$", f"Expected <routes>, got <{root.tag}>.", "Wrap Fail2Drive routes in a <routes> root element."))
    scenario_by_name = catalog.by_name()
    route_elements = list(root.findall("route"))
    town_names: list[str] = []
    scenario_counts: dict[str, int] = {}
    for route_index, route in enumerate(route_elements):
        route_path_expr = f"/routes/route[{route_index}]"
        route_id = route.get("id")
        town = route.get("town")
        if not route_id:
            issues.append(RouteIssue("error", "missing_route_id", route_path_expr, "Route is missing id.", "Set route id to a stable string or integer."))
        if not town:
            issues.append(RouteIssue("error", "missing_town", route_path_expr, "Route is missing town.", "Set town to a Fail2Drive/CARLA town such as Town05 or Town10HD."))
        else:
            town_names.append(town)
        waypoints = route.find("waypoints")
        if waypoints is None or not list(waypoints.findall("position")):
            issues.append(RouteIssue("error", "missing_waypoints", route_path_expr, "Route has no waypoint positions.", "Add <waypoints><position x='...' y='...' z='...'/></waypoints>."))
        elif len(list(waypoints.findall("position"))) < 2:
            issues.append(RouteIssue("warning", "short_route", f"{route_path_expr}/waypoints", "Route has fewer than two waypoints.", "Use at least start and end waypoints for a meaningful route."))
        for waypoint_index, position in enumerate(waypoints.findall("position") if waypoints is not None else []):
            _validate_xyz(position, f"{route_path_expr}/waypoints/position[{waypoint_index}]", issues)
        scenarios = route.find("scenarios")
        if scenarios is None:
            continue
        for scenario_index, scenario in enumerate(scenarios.findall("scenario")):
            scenario_path = f"{route_path_expr}/scenarios/scenario[{scenario_index}]"
            scenario_type = scenario.get("type")
            if not scenario_type:
                issues.append(RouteIssue("error", "missing_scenario_type", scenario_path, "Scenario is missing type.", "Set type to a catalog scenario name."))
                continue
            scenario_counts[scenario_type] = scenario_counts.get(scenario_type, 0) + 1
            scenario_meta = scenario_by_name.get(scenario_type)
            if scenario_meta is None:
                issues.append(RouteIssue("error", "unknown_scenario_type", scenario_path, f"Unknown Fail2Drive scenario type: {scenario_type}", _nearest_scenario_hint(scenario_type, scenario_by_name)))
                continue
            trigger = scenario.find("trigger_point")
            if trigger is None:
                issues.append(RouteIssue("error", "missing_trigger_point", scenario_path, f"{scenario_type} is missing trigger_point.", "Add <trigger_point x='...' y='...' z='...' yaw='...'/>."))
            else:
                _validate_transform(trigger, f"{scenario_path}/trigger_point", issues)
            expected = {param.name: param for param in scenario_meta.params}
            for param in scenario_meta.params:
                elem = scenario.find(param.name)
                if elem is None and param.default is None:
                    issues.append(RouteIssue("warning", "missing_param", scenario_path, f"{scenario_type} is missing optional/unspecified param {param.name}.", f"Add <{param.name}> if this scenario requires it at runtime."))
                elif elem is not None:
                    _validate_param(elem, param.kind, f"{scenario_path}/{param.name}", issues)
            for child in list(scenario):
                if child.tag == "trigger_point":
                    continue
                if child.tag not in expected:
                    issues.append(RouteIssue("error" if strict else "warning", "unknown_param", f"{scenario_path}/{child.tag}", f"{scenario_type} has unknown param {child.tag}.", "Check `oodrive f2d-catalog` for expected params."))
    if not route_elements:
        issues.append(RouteIssue("error", "missing_routes", "$", "No <route> elements found.", "Add at least one <route id='...' town='...'>."))
    ok = not any(issue.severity == "error" for issue in issues)
    return Fail2DriveRouteValidation(
        route_path=route_file,
        ok=ok,
        route_count=len(route_elements),
        town_names=tuple(sorted(set(town_names))),
        scenario_counts=dict(sorted(scenario_counts.items())),
        issues=tuple(issues),
    )


def write_fail2drive_route_validation(run_dir: Path, validation: Fail2DriveRouteValidation) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = validation.to_jsonable()
    json_path = run_dir / "fail2drive_route_validation.json"
    report_path = run_dir / "fail2drive_route_validation.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _validate_xyz(elem: ET.Element, xml_path: str, issues: list[RouteIssue]) -> None:
    for attr in ("x", "y", "z"):
        _require_float(elem, attr, xml_path, issues)


def _validate_transform(elem: ET.Element, xml_path: str, issues: list[RouteIssue]) -> None:
    for attr in ("x", "y", "z", "yaw"):
        _require_float(elem, attr, xml_path, issues)


def _validate_param(elem: ET.Element, kind: str, xml_path: str, issues: list[RouteIssue]) -> None:
    if kind in ("value", "choice", "bool"):
        if "value" not in elem.attrib:
            issues.append(RouteIssue("error", "missing_value_attr", xml_path, f"{elem.tag} must have a value attribute.", f"Use <{elem.tag} value='...'/>."))
    elif kind == "interval":
        for attr in ("from", "to"):
            _require_float(elem, attr, xml_path, issues)
    elif kind == "transform":
        _validate_transform(elem, xml_path, issues)
    elif "location" in kind:
        _validate_xyz(elem, xml_path, issues)
        if "probability" in kind:
            _require_float(elem, "p", xml_path, issues)
    elif kind == "objects":
        if not elem.attrib:
            issues.append(RouteIssue("warning", "empty_objects", xml_path, f"{elem.tag} has no object attributes.", "Add object layout attributes if the scenario should block the road."))
    else:
        issues.append(RouteIssue("warning", "unknown_param_kind", xml_path, f"Unknown parameter kind {kind}.", "Validator preserved this as a warning to avoid over-rejecting upstream scenarios."))


def _require_float(elem: ET.Element, attr: str, xml_path: str, issues: list[RouteIssue]) -> None:
    value = elem.get(attr)
    if value is None:
        issues.append(RouteIssue("error", "missing_numeric_attr", xml_path, f"{elem.tag} is missing numeric attribute {attr}.", f"Add {attr}='0.0'."))
        return
    try:
        float(value)
    except ValueError:
        issues.append(RouteIssue("error", "invalid_numeric_attr", xml_path, f"{elem.tag}.{attr} must be numeric, got {value!r}.", "Use a number."))


def _nearest_scenario_hint(name: str, scenario_by_name: dict[str, Any]) -> str | None:
    lower = name.lower()
    for candidate in scenario_by_name:
        if lower in candidate.lower() or candidate.lower() in lower:
            return f"Did you mean {candidate}?"
    return "Run `oodrive f2d-catalog` to list valid scenario types."


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Fail2Drive Route Validation",
        "",
        f"- route: `{payload.get('route_path')}`",
        f"- ok: {payload.get('ok')}",
        f"- routes: {payload.get('route_count')}",
        f"- errors: {payload.get('error_count')}",
        f"- warnings: {payload.get('warning_count')}",
        "",
    ]
    for issue in payload.get("issues", []):
        if isinstance(issue, dict):
            lines.append(f"- [{issue.get('severity')}] `{issue.get('code')}` {issue.get('xml_path')}: {issue.get('message')}")
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["Fail2DriveRouteValidation", "RouteIssue", "validate_fail2drive_route", "write_fail2drive_route_validation"]
