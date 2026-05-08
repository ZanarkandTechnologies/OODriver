"""Run OODrive scenario graphs in fake or live CARLA-backed modes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from driverx.scenarios.generated_runtime import load_generated_scenario_runtime, run_generated_scenario_runtime

ScenarioRunnerBackend = Literal["fake-carla", "carla-live"]


@dataclass(frozen=True)
class CarlaScenarioRunResult:
    status: str
    backend: ScenarioRunnerBackend
    spawned_static_count: int
    spawned_dynamic_count: int
    custom_asset_spawn_count: int
    stock_proxy_spawn_count: int
    rgb_folder: str | None = None
    tracks_path: str | None = None
    action_trace_path: str | None = None
    video_path: str | None = None
    spawned_actor_ids: list[int] = field(default_factory=list)
    destroyed_actor_ids: list[int] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "backend": self.backend,
            "spawned_static_count": self.spawned_static_count,
            "spawned_dynamic_count": self.spawned_dynamic_count,
            "custom_asset_spawn_count": self.custom_asset_spawn_count,
            "stock_proxy_spawn_count": self.stock_proxy_spawn_count,
            "rgb_folder": self.rgb_folder,
            "tracks_path": self.tracks_path,
            "action_trace_path": self.action_trace_path,
            "video_path": self.video_path,
            "spawned_actor_ids": self.spawned_actor_ids,
            "destroyed_actor_ids": self.destroyed_actor_ids,
            "claim_boundaries": self.claim_boundaries,
            "blockers": self.blockers,
        }


def run_carla_scenario_graph(
    graph: dict[str, Any],
    *,
    pack: dict[str, Any],
    run_dir: Path,
    backend: ScenarioRunnerBackend,
    config_path: Path,
) -> CarlaScenarioRunResult:
    """Execute a scenario graph or precise blocked/live compatibility path."""

    run_dir.mkdir(parents=True, exist_ok=True)
    if backend == "fake-carla":
        return _run_fake(graph, run_dir)
    runtime_spec_path = pack.get("generated_runtime_spec_path")
    if runtime_spec_path and Path(str(runtime_spec_path)).exists():
        spec = json.loads(Path(str(runtime_spec_path)).read_text(encoding="utf-8"))
        manifest = run_generated_scenario_runtime(
            spec,
            backend="carla-live",
            config_path=config_path,
            output_root=run_dir,
            run_id="live-generated-runtime",
        )
        proof = dict(manifest.get("runtime_proof", {}))
        claim_boundaries = sorted(
            set(
                [
                    *[str(item) for item in list(manifest.get("claim_boundaries", []))],
                    "scenario_graph_runner=true",
                    "custom_asset_imported_in_carla=false_unless_registry_installed",
                ]
            )
        )
        return CarlaScenarioRunResult(
            status=str(manifest.get("status", "blocked")),
            backend="carla-live",
            spawned_static_count=int(proof.get("static_object_spawn_count", 0) or 0),
            spawned_dynamic_count=int(proof.get("dynamic_actor_spawn_count", 0) or 0),
            custom_asset_spawn_count=0,
            stock_proxy_spawn_count=int(proof.get("static_object_spawn_count", 0) or 0),
            rgb_folder=proof.get("rgb_folder") if isinstance(proof.get("rgb_folder"), str) else None,
            tracks_path=_tracks_path(proof),
            action_trace_path=proof.get("json_path") if isinstance(proof.get("json_path"), str) else None,
            spawned_actor_ids=[int(item) for item in list(proof.get("spawned_actor_ids", []))],
            destroyed_actor_ids=[int(item) for item in list(proof.get("destroyed_actor_ids", []))],
            claim_boundaries=claim_boundaries,
            blockers=[str(item) for item in list(manifest.get("blockers", []))],
        )
    return CarlaScenarioRunResult(
        status="blocked",
        backend="carla-live",
        spawned_static_count=0,
        spawned_dynamic_count=0,
        custom_asset_spawn_count=0,
        stock_proxy_spawn_count=0,
        claim_boundaries=[
            "scenario_graph_runner=true",
            "objects_spawned_in_carla=false",
            "custom_asset_imported_in_carla=false",
        ],
        blockers=["Scenario pack does not reference an existing generated runtime spec for live CARLA compatibility."],
    )


def write_carla_scenario_run(
    run_dir: Path,
    *,
    graph: dict[str, Any],
    pack: dict[str, Any],
    result: CarlaScenarioRunResult,
) -> dict[str, str]:
    payload = {
        "schema_version": "oodrive.carla_scenario_run.v1",
        "scenario_id": graph.get("scenario_id"),
        "source_prompt": pack.get("source_prompt"),
        "result": result.to_jsonable(),
        "claim_boundaries": result.claim_boundaries,
        "blockers": result.blockers,
    }
    path = run_dir / "scenario_run_manifest.json"
    report_path = run_dir / "scenario_run_manifest.md"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_run_markdown(payload), encoding="utf-8")
    return {"json_path": str(path), "report_path": str(report_path)}


def _run_fake(graph: dict[str, Any], run_dir: Path) -> CarlaScenarioRunResult:
    tracks: list[dict[str, Any]] = []
    action_trace: list[dict[str, Any]] = []
    actor_id = 1
    spawned: list[int] = []
    for index, obj in enumerate([dict(item) for item in list(graph.get("static_objects", [])) if isinstance(item, dict)]):
        spawned.append(actor_id)
        tracks.append(
            {
                "tick": 0,
                "t_s": 0.0,
                "actor_id": actor_id,
                "actor_ref": obj.get("actor_ref"),
                "type_id": obj.get("fallback_blueprint") or obj.get("blueprint_ref"),
                "transform": {"location": obj.get("placement", {})},
            }
        )
        actor_id += 1
    for index, actor in enumerate([dict(item) for item in list(graph.get("actors", [])) if isinstance(item, dict)]):
        spawned.append(actor_id)
        for tick in range(6):
            tracks.append(
                {
                    "tick": tick,
                    "t_s": tick * 0.2,
                    "actor_id": actor_id,
                    "actor_ref": actor.get("actor_ref"),
                    "type_id": actor.get("blueprint_ref"),
                    "transform": {"location": {"x": tick * 1.0, "y": -1.0 + index, "z": 0.2}},
                }
            )
        action_trace.append({"actor_ref": actor.get("actor_ref"), "action": "follow_generated_timeline"})
        actor_id += 1
    tracks_path = run_dir / "entity_tracks.json"
    action_path = run_dir / "action_trace.json"
    tracks_path.write_text(json.dumps(tracks, indent=2), encoding="utf-8")
    action_path.write_text(json.dumps(action_trace, indent=2), encoding="utf-8")
    static_objects = [dict(item) for item in list(graph.get("static_objects", [])) if isinstance(item, dict)]
    return CarlaScenarioRunResult(
        status="passed",
        backend="fake-carla",
        spawned_static_count=len(static_objects),
        spawned_dynamic_count=len(list(graph.get("actors", []))),
        custom_asset_spawn_count=sum(1 for item in static_objects if item.get("custom_asset_installed") is True),
        stock_proxy_spawn_count=sum(1 for item in static_objects if item.get("custom_asset_installed") is not True),
        tracks_path=str(tracks_path),
        action_trace_path=str(action_path),
        spawned_actor_ids=spawned,
        destroyed_actor_ids=spawned,
        claim_boundaries=[
            "scenario_graph_runner=true",
            "objects_spawned_in_fake_carla=true",
            "objects_spawned_in_carla=false_fake_backend",
            "custom_asset_imported_in_carla=false_fake_backend",
            "closed_loop_vla_control=false",
            "real_time_vla_control=false",
        ],
    )


def _tracks_path(proof: dict[str, Any]) -> str | None:
    if isinstance(proof.get("tracks_path"), str):
        return str(proof["tracks_path"])
    for case in list(proof.get("case_results", [])):
        if isinstance(case, dict) and isinstance(case.get("tracks_path"), str):
            return str(case["tracks_path"])
    return None


def _run_markdown(payload: dict[str, Any]) -> str:
    result = dict(payload.get("result", {}))
    return "\n".join(
        [
            "# OODrive Scenario Run",
            "",
            f"- scenario: `{payload.get('scenario_id')}`",
            f"- status: {result.get('status')}",
            f"- backend: {result.get('backend')}",
            f"- static objects: {result.get('spawned_static_count')}",
            f"- dynamic actors: {result.get('spawned_dynamic_count')}",
            f"- tracks: `{result.get('tracks_path')}`",
            f"- rgb: `{result.get('rgb_folder')}`",
            "",
        ]
    )


__all__ = ["CarlaScenarioRunResult", "run_carla_scenario_graph", "write_carla_scenario_run"]
