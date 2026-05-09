"""Read Fail2Drive toolbox metadata without launching the GUI or CARLA."""

from __future__ import annotations

import ast
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


GRAPHICAL_EDITOR_DEFAULTS = {
    "CustomObstacle",
    "CustomObstacleTwoWays",
    "RoadBlocked",
    "BadParkingObstacle",
    "PermutedConstructionObstacle",
}

SCENARIO_GROUPS = {
    "Fail2Drive Scenarios": {
        "BadParkingObstacle",
        "BadParkingObstacleTwoWays",
        "ConstructionObstacleOppositeLane",
        "ConstructionObstaclePedestrian",
        "ConstructionObstacleRightLane",
        "CustomObstacle",
        "CustomObstacleTwoWays",
        "HardBrakeNoLights",
        "ImageOnObject",
        "NormalVehicleRunningRedLight",
        "NormalVehicleTakingPriority",
        "ObscuredStopSign",
        "PedestrianCrowd",
        "PedestriansOnRoad",
        "PermutedConstructionObstacle",
        "PermutedConstructionObstacleTwoWays",
        "RoadBlocked",
    },
    "Junctions": {
        "SignalizedJunctionLeftTurn",
        "SignalizedJunctionRightTurn",
        "NonSignalizedJunctionLeftTurn",
        "NonSignalizedJunctionRightTurn",
        "OppositeVehicleRunningRedLight",
        "OppositeVehicleTakingPriority",
        "BlockedIntersection",
        "PriorityAtJunction",
    },
    "Crossing Actors": {
        "DynamicObjectCrossing",
        "ParkingCrossingPedestrian",
        "PedestrianCrossing",
        "VehicleTurningRoute",
        "VehicleTurningRoutePedestrian",
        "CrossingBicycleFlow",
    },
    "Actor Flows & Merging": {
        "EnterActorFlow",
        "EnterActorFlowV2",
        "InterurbanActorFlow",
        "InterurbanAdvancedActorFlow",
        "HighwayExit",
        "MergerIntoSlowTraffic",
        "MergerIntoSlowTrafficV2",
        "HighwayCutIn",
        "ParkingCutIn",
        "StaticCutIn",
    },
    "Route Obstacles": {
        "ConstructionObstacle",
        "ConstructionObstacleTwoWays",
        "Accident",
        "AccidentTwoWays",
        "ParkedObstacle",
        "ParkedObstacleTwoWays",
        "VehicleOpensDoorTwoWays",
        "HazardAtSideLane",
        "HazardAtSideLaneTwoWays",
        "InvadingTurn",
    },
    "Other": {
        "ControlLoss",
        "HardBreakRoute",
        "ParkingExit",
        "YieldToEmergencyVehicle",
        "BackgroundActivityParametrizer",
    },
}


@dataclass(frozen=True)
class Fail2DriveScenarioParam:
    name: str
    kind: str
    default: Any = None
    tooltip: str | None = None
    placement_hint: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "default": self.default,
            "tooltip": self.tooltip,
            "placement_hint": self.placement_hint,
        }


@dataclass(frozen=True)
class Fail2DriveScenarioType:
    name: str
    group: str
    tooltip: str
    params: tuple[Fail2DriveScenarioParam, ...]
    graphical_editor: bool
    implementation_path: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "group": self.group,
            "tooltip": self.tooltip,
            "params": [param.to_jsonable() for param in self.params],
            "graphical_editor": self.graphical_editor,
            "implementation_path": self.implementation_path,
        }


@dataclass(frozen=True)
class Fail2DriveCatalog:
    fail2drive_root: Path
    upstream_commit: str | None
    scenario_types: tuple[Fail2DriveScenarioType, ...]
    towns_with_toolbox_data: tuple[str, ...]
    source_paths: tuple[str, ...]

    def by_name(self) -> dict[str, Fail2DriveScenarioType]:
        return {scenario.name: scenario for scenario in self.scenario_types}

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": "oodrive.fail2drive_catalog.v1",
            "fail2drive_root": str(self.fail2drive_root),
            "upstream_commit": self.upstream_commit,
            "scenario_count": len(self.scenario_types),
            "scenario_types": [scenario.to_jsonable() for scenario in self.scenario_types],
            "towns_with_toolbox_data": list(self.towns_with_toolbox_data),
            "source_paths": list(self.source_paths),
            "claim_boundaries": [
                "fail2drive_is_upstream_engine=true",
                "oodrive_is_agent_cli_layer=true",
                "closed_loop_vla_control=false_unless_live_trace_score_passes",
            ],
        }


def load_fail2drive_catalog(root: Path) -> Fail2DriveCatalog:
    fail2drive_root = root.expanduser().resolve()
    config_path = fail2drive_root / "toolbox" / "scripts" / "config.py"
    if not config_path.exists():
        raise FileNotFoundError(f"Fail2Drive toolbox config not found: {config_path}")
    constants = _read_constants(config_path)
    scenario_defs = _mapping(constants.get("SCENARIO_TYPES"))
    tooltips = _mapping(constants.get("SCENARIO_TOOLTIPS"))
    default_param_tooltips = _mapping(constants.get("PARAM_TOOLTIPS_DEFAULT"))
    scenario_param_tooltips = _mapping(constants.get("SCENARIO_PARAM_TOOLTIPS"))
    placement_hints = _mapping(constants.get("SCENARIO_PARAM_PLACEMENT_HINTS"))
    graphical = set(_sequence(constants.get("GRAPHICAL_EDITOR_SCENARIO_TYPES"))) or GRAPHICAL_EDITOR_DEFAULTS
    scenarios = []
    for name in sorted(scenario_defs):
        raw_params = _sequence(scenario_defs.get(name))
        params = []
        for raw_param in raw_params:
            values = list(_sequence(raw_param))
            if len(values) < 2:
                continue
            param_name = str(values[0])
            kind = str(values[1])
            default = values[2] if len(values) > 2 else None
            params.append(
                Fail2DriveScenarioParam(
                    name=param_name,
                    kind=kind,
                    default=default,
                    tooltip=str(_mapping(scenario_param_tooltips.get(name)).get(param_name) or default_param_tooltips.get(param_name) or "Scenario parameter."),
                    placement_hint=str(_mapping(placement_hints.get(name)).get(param_name) or _mapping(scenario_param_tooltips.get(name)).get(param_name) or default_param_tooltips.get(param_name) or "Scenario parameter."),
                )
            )
        scenarios.append(
            Fail2DriveScenarioType(
                name=name,
                group=_scenario_group(name),
                tooltip=str(tooltips.get(name) or "No description available."),
                params=tuple(params),
                graphical_editor=name in graphical,
                implementation_path=_implementation_path(fail2drive_root, name),
            )
        )
    return Fail2DriveCatalog(
        fail2drive_root=fail2drive_root,
        upstream_commit=_git_commit(fail2drive_root),
        scenario_types=tuple(scenarios),
        towns_with_toolbox_data=_towns_with_toolbox_data(fail2drive_root),
        source_paths=(
            str(config_path),
            str(fail2drive_root / "toolbox" / "README.md"),
            str(fail2drive_root / "scenario_runner" / "srunner" / "scenarios"),
        ),
    )


def write_fail2drive_catalog_report(run_dir: Path, catalog: Fail2DriveCatalog, *, fmt: str = "both") -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = catalog.to_jsonable()
    result: dict[str, Any] = {**payload}
    if fmt in ("json", "both"):
        json_path = run_dir / "fail2drive_catalog.json"
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        result["json_path"] = str(json_path)
    if fmt in ("md", "markdown", "both"):
        report_path = run_dir / "fail2drive_catalog.md"
        report_path.write_text(_markdown(catalog), encoding="utf-8")
        result["report_path"] = str(report_path)
    return result


def _read_constants(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        values[target.id] = ast.literal_eval(node.value)
                    except Exception:
                        pass
    return values


def _scenario_group(name: str) -> str:
    for group, names in SCENARIO_GROUPS.items():
        if name in names:
            return group
    return "Unclassified"


def _implementation_path(root: Path, scenario_name: str) -> str | None:
    scenarios_dir = root / "scenario_runner" / "srunner" / "scenarios"
    if not scenarios_dir.exists():
        return None
    needle = scenario_name.lower()
    for path in sorted(scenarios_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if needle in text:
            return str(path)
    return None


def _towns_with_toolbox_data(root: Path) -> tuple[str, ...]:
    map_dir = root / "toolbox" / "carla_map_data"
    if not map_dir.exists():
        return ()
    return tuple(sorted({path.stem for path in map_dir.glob("*.pkl")}))


def _git_commit(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError:
        return None
    commit = completed.stdout.strip()
    return commit or None


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, (list, tuple, set)):
        return tuple(value)
    return ()


def _markdown(catalog: Fail2DriveCatalog) -> str:
    lines = [
        "# Fail2Drive Scenario Catalog",
        "",
        f"- root: `{catalog.fail2drive_root}`",
        f"- upstream commit: `{catalog.upstream_commit or 'unknown'}`",
        f"- scenarios: {len(catalog.scenario_types)}",
        f"- toolbox towns: {len(catalog.towns_with_toolbox_data)}",
        "",
    ]
    by_group: dict[str, list[Fail2DriveScenarioType]] = {}
    for scenario in catalog.scenario_types:
        by_group.setdefault(scenario.group, []).append(scenario)
    for group in sorted(by_group):
        lines.extend([f"## {group}", ""])
        for scenario in by_group[group]:
            params = ", ".join(param.name for param in scenario.params) or "no params"
            marker = " layout-editor" if scenario.graphical_editor else ""
            lines.append(f"- `{scenario.name}`{marker}: {params}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "Fail2DriveCatalog",
    "Fail2DriveScenarioParam",
    "Fail2DriveScenarioType",
    "load_fail2drive_catalog",
    "write_fail2drive_catalog_report",
]
