"""Research scenario graph compiled from OODrive production packs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios.production_pack import load_production_scenario_pack


@dataclass(frozen=True)
class ScenarioGraphValidation:
    passes: bool
    blockers: list[str]

    def to_jsonable(self) -> dict[str, object]:
        return {"passes": self.passes, "blockers": self.blockers}


def compile_scenario_graph(
    pack: dict[str, Any],
    asset_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry_by_asset = {
        str(entry.get("asset_id")): dict(entry)
        for entry in list((asset_registry or {}).get("entries", []))
        if isinstance(entry, dict)
    }
    static_objects = []
    for index, request in enumerate(list(pack.get("asset_requests", []))):
        if not isinstance(request, dict):
            continue
        asset_id = str(request.get("asset_id", f"asset-{index}"))
        registry_entry = registry_by_asset.get(asset_id, {})
        static_objects.append(
            {
                "asset_id": asset_id,
                "actor_ref": f"static_{asset_id.replace('-', '_')}",
                "blueprint_ref": registry_entry.get("expected_blueprint_id")
                or _spawn_blueprint(pack, index)
                or "static.prop.dirtdebris01",
                "fallback_blueprint": registry_entry.get("fallback_blueprint") or _spawn_blueprint(pack, index),
                "custom_asset_installed": bool(registry_entry.get("installed")),
                "placement": request.get("intended_placement", {}),
                "semantic_tags": request.get("semantic_tags", []),
            }
        )
    actors = []
    actions = []
    for index, timeline in enumerate(list(pack.get("behavior_timelines", []))):
        if not isinstance(timeline, dict):
            continue
        actor_ref = str(timeline.get("actor_ref") or f"behavior_actor_{index}")
        actors.append(
            {
                "actor_ref": actor_ref,
                "kind": str(timeline.get("actor_kind") or "vehicle"),
                "blueprint_ref": str(timeline.get("blueprint_filter") or "vehicle.kawasaki.ninja"),
            }
        )
        actions.append(
            {
                "actor_ref": actor_ref,
                "start_s": 0.0,
                "end_s": max(3.0, float(timeline.get("sample_count", 12)) * 0.2),
                "intent": str(timeline.get("behavior_id") or "generated_behavior"),
                "trace_path": timeline.get("trace_path"),
            }
        )
    graph = {
        "schema_version": "oodrive.scenario_graph.v1",
        "scenario_id": pack.get("scenario_id"),
        "source_prompt": pack.get("source_prompt"),
        "map_constraints": pack.get("map_constraints", {}),
        "weather": pack.get("weather", {}),
        "actors": actors,
        "static_objects": static_objects,
        "actions": actions,
        "triggers": [{"at_s": 0.0, "condition": "scenario_start"}],
        "assertions": [
            {"name": "rgb_evidence_present", "metric": "rgb_frame_count", "operator": ">", "threshold": 0.0},
            {"name": "objects_spawned", "metric": "spawned_static_count", "operator": ">", "threshold": 0.0},
        ],
        "sidecar_refs": {
            "scenario_pack_path": pack.get("scenario_pack_path"),
            "asset_registry_path": (asset_registry or {}).get("json_path"),
        },
        "claim_boundaries": pack.get("claim_boundaries", []),
    }
    graph["validation"] = validate_scenario_graph(graph).to_jsonable()
    return graph


def validate_scenario_graph(graph: dict[str, Any]) -> ScenarioGraphValidation:
    blockers: list[str] = []
    if graph.get("schema_version") != "oodrive.scenario_graph.v1":
        blockers.append("Unsupported scenario graph schema_version.")
    if not list(graph.get("actors", [])):
        blockers.append("At least one dynamic actor is required.")
    if not list(graph.get("static_objects", [])):
        blockers.append("At least one static object is required.")
    if not list(graph.get("actions", [])):
        blockers.append("At least one action is required.")
    if not list(graph.get("assertions", [])):
        blockers.append("At least one assertion is required.")
    return ScenarioGraphValidation(passes=not blockers, blockers=blockers)


def write_scenario_graph_bundle(
    graph: dict[str, Any],
    *,
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-scenario-graph",
) -> dict[str, str]:
    run_dir = prepare_run_dir(output_root, run_id)
    graph_path = run_dir / "scenario_graph.json"
    report_path = run_dir / "scenario_graph.md"
    xosc_path = run_dir / "scenario.xosc"
    sidecar_path = run_dir / "scenario_sidecar.json"
    graph_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    sidecar_path.write_text(
        json.dumps(
            {
                "scenario_id": graph.get("scenario_id"),
                "source_prompt": graph.get("source_prompt"),
                "claim_boundaries": graph.get("claim_boundaries", []),
                "sidecar_only_fields": ["claim_boundaries", "asset provenance", "OODrive evidence requirements"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    xosc_path.write_text(_open_scenario_xml(graph), encoding="utf-8")
    report_path.write_text(_graph_markdown(graph, xosc_path, sidecar_path), encoding="utf-8")
    return {
        "json_path": str(graph_path),
        "report_path": str(report_path),
        "open_scenario_path": str(xosc_path),
        "sidecar_path": str(sidecar_path),
    }


def build_scenario_graph_from_pack_path(
    pack_path: Path,
    *,
    asset_registry_path: Path | None = None,
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-scenario-graph",
) -> dict[str, Any]:
    pack = load_production_scenario_pack(pack_path)
    registry = json.loads(asset_registry_path.read_text(encoding="utf-8")) if asset_registry_path else None
    graph = compile_scenario_graph(pack, registry)
    paths = write_scenario_graph_bundle(graph, output_root=output_root, run_id=run_id)
    return {**graph, **paths}


def _spawn_blueprint(pack: dict[str, Any], index: int) -> str | None:
    specs = [dict(item) for item in list(pack.get("object_spawn_specs", [])) if isinstance(item, dict)]
    if index < len(specs):
        return str(specs[index].get("blueprint_filter") or "")
    return None


def _open_scenario_xml(graph: dict[str, Any]) -> str:
    scenario_id = str(graph.get("scenario_id", "oodrive-scenario"))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<OpenSCENARIO>\n'
        f'  <FileHeader revMajor="1" revMinor="0" date="2026-05-08T00:00:00" '
        f'description="CARLA: {scenario_id}" author="OODrive"/>\n'
        "  <ParameterDeclarations/>\n"
        "  <CatalogLocations/>\n"
        "  <RoadNetwork/>\n"
        "  <Entities>\n"
        + "\n".join(
            f'    <ScenarioObject name="{actor.get("actor_ref")}"/>'
            for actor in list(graph.get("actors", []))
            if isinstance(actor, dict)
        )
        + "\n  </Entities>\n"
        "  <Storyboard><Init><Actions/></Init><Story name=\"OODriveGeneratedStory\"/></Storyboard>\n"
        "</OpenSCENARIO>\n"
    )


def _graph_markdown(graph: dict[str, Any], xosc_path: Path, sidecar_path: Path) -> str:
    return "\n".join(
        [
            "# OODrive Scenario Graph",
            "",
            f"- scenario: `{graph.get('scenario_id')}`",
            f"- actors: {len(list(graph.get('actors', [])))}",
            f"- static objects: {len(list(graph.get('static_objects', [])))}",
            f"- actions: {len(list(graph.get('actions', [])))}",
            f"- OpenSCENARIO export: `{xosc_path}`",
            f"- OODrive sidecar: `{sidecar_path}`",
            "",
        ]
    )


__all__ = [
    "ScenarioGraphValidation",
    "build_scenario_graph_from_pack_path",
    "compile_scenario_graph",
    "validate_scenario_graph",
    "write_scenario_graph_bundle",
]
