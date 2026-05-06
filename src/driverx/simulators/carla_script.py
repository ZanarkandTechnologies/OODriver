"""Compile scenario recipes and behavior traces into CARLA script plans."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.behaviors import BehaviorTrace
from driverx.scenarios import ScenarioRecipe
from driverx.simulators.carla_road_frame import RoadFrameSelector, transform_payload


@dataclass(frozen=True)
class CarlaActorScript:
    actor_ref: str
    role: str
    blueprint_filter: str
    spawn_transform: dict[str, dict[str, float]]
    behavior_id: str | None = None
    sample_count: int = 0

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "actor_ref": self.actor_ref,
            "role": self.role,
            "blueprint_filter": self.blueprint_filter,
            "spawn_transform": self.spawn_transform,
            "behavior_id": self.behavior_id,
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True)
class CarlaSensorScript:
    sensor_ref: str
    attach_to: str
    blueprint: str
    transform: dict[str, dict[str, float]]
    attributes: dict[str, str]
    output: str

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "sensor_ref": self.sensor_ref,
            "attach_to": self.attach_to,
            "blueprint": self.blueprint,
            "transform": self.transform,
            "attributes": self.attributes,
            "output": self.output,
        }


@dataclass(frozen=True)
class CarlaScriptPlan:
    script_id: str
    recipe_id: str
    behavior_id: str
    route_path: Path
    coordinate_frame: str
    road_frame_selector: RoadFrameSelector
    actors: list[CarlaActorScript]
    sensors: list[CarlaSensorScript]
    ticks: list[dict[str, Any]]
    expected_outputs: list[Path]
    cleanup_order: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "script_id": self.script_id,
            "recipe_id": self.recipe_id,
            "behavior_id": self.behavior_id,
            "route_path": str(self.route_path),
            "coordinate_frame": self.coordinate_frame,
            "road_frame_selector": self.road_frame_selector.to_jsonable(),
            "actors": [actor.to_jsonable() for actor in self.actors],
            "sensors": [sensor.to_jsonable() for sensor in self.sensors],
            "ticks": self.ticks,
            "expected_outputs": [str(path) for path in self.expected_outputs],
            "cleanup_order": self.cleanup_order,
        }


def _transform(x: float, y: float, z: float = 0.2, yaw: float = 0.0) -> dict[str, dict[str, float]]:
    return transform_payload(x, y, z, yaw)


def _blueprint_for(actor_kind: str) -> str:
    if actor_kind == "motorcycle":
        return "vehicle.kawasaki.ninja"
    if actor_kind == "pedestrian":
        return "walker.pedestrian.*"
    return "vehicle.*"


def compile_carla_script_plan(
    recipe: ScenarioRecipe,
    behavior_trace: BehaviorTrace,
    output_dir: Path,
    *,
    road_frame_selector: RoadFrameSelector | None = None,
) -> CarlaScriptPlan:
    if recipe.route_path is None:
        raise ValueError("ScenarioRecipe.route_path is required for CARLA script compilation.")
    if not behavior_trace.samples:
        raise ValueError("BehaviorTrace must contain samples.")

    script_id = f"{recipe.recipe_id}__{behavior_trace.plan.behavior_id}"
    selector = road_frame_selector or RoadFrameSelector()
    behavior_actor_ref = "ood_actor_0"
    ego_actor_ref = "ego"
    camera_ref = "ego_rgb"
    first_sample = behavior_trace.samples[0]
    actors = [
        CarlaActorScript(
            actor_ref=ego_actor_ref,
            role="ego",
            blueprint_filter="vehicle.lincoln.mkz_2020",
            spawn_transform=_transform(0.0, 0.0, 0.0, 0.0),
        ),
        CarlaActorScript(
            actor_ref=behavior_actor_ref,
            role=behavior_trace.plan.actor_kind,
            blueprint_filter=_blueprint_for(behavior_trace.plan.actor_kind),
            spawn_transform=_transform(
                first_sample.x_m,
                first_sample.y_m,
                0.0,
                first_sample.heading_deg,
            ),
            behavior_id=behavior_trace.plan.behavior_id,
            sample_count=len(behavior_trace.samples),
        ),
    ]
    sensors = [
        CarlaSensorScript(
            sensor_ref=camera_ref,
            attach_to=ego_actor_ref,
            blueprint="sensor.camera.rgb",
            transform=_transform(1.5, 0.0, 2.4, 0.0),
            attributes={"image_size_x": "640", "image_size_y": "360", "fov": "90"},
            output=str(output_dir / "ego_rgb"),
        )
    ]
    ticks = [
        {
            "t_s": sample.t_s,
            "actor_ref": behavior_actor_ref,
            "target_transform": _transform(sample.x_m, sample.y_m, 0.0, sample.heading_deg),
            "target_speed_mps": sample.speed_mps,
        }
        for sample in behavior_trace.samples
    ]
    return CarlaScriptPlan(
        script_id=script_id,
        recipe_id=recipe.recipe_id,
        behavior_id=behavior_trace.plan.behavior_id,
        route_path=recipe.route_path,
        coordinate_frame="road_local",
        road_frame_selector=selector,
        actors=actors,
        sensors=sensors,
        ticks=ticks,
        expected_outputs=[
            output_dir / "carla_script_plan.json",
            output_dir / "entity_tracks.json",
            output_dir / "ego_rgb",
        ],
        cleanup_order=[camera_ref, behavior_actor_ref, ego_actor_ref],
    )


def validate_carla_script_plan(plan: CarlaScriptPlan) -> list[str]:
    errors: list[str] = []
    if not plan.actors:
        errors.append("script plan requires actors")
    if not any(actor.role == "ego" for actor in plan.actors):
        errors.append("script plan requires an ego actor")
    if not plan.ticks:
        errors.append("script plan requires behavior ticks")
    actor_refs = {actor.actor_ref for actor in plan.actors}
    for sensor in plan.sensors:
        if sensor.attach_to not in actor_refs:
            errors.append(f"sensor {sensor.sensor_ref} attaches to unknown actor {sensor.attach_to}")
    cleanup_refs = set(plan.cleanup_order)
    expected_refs = actor_refs | {sensor.sensor_ref for sensor in plan.sensors}
    if cleanup_refs != expected_refs:
        errors.append("cleanup_order must contain every actor and sensor ref exactly once")
    return errors


def write_carla_script_plan(run_dir: Path, plan: CarlaScriptPlan) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "carla_script_plan.json"
    report_path = run_dir / "carla_script_plan.md"
    payload = plan.to_jsonable()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_script_markdown(plan), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
        "validation_errors": validate_carla_script_plan(plan),
    }


def _script_markdown(plan: CarlaScriptPlan) -> str:
    lines = [
        "# CARLA Script Plan",
        "",
        f"- script_id: `{plan.script_id}`",
        f"- recipe_id: `{plan.recipe_id}`",
        f"- behavior_id: `{plan.behavior_id}`",
        f"- route_path: `{plan.route_path}`",
        f"- coordinate_frame: `{plan.coordinate_frame}`",
        f"- road_anchor_spawn_index: `{plan.road_frame_selector.spawn_index}`",
        f"- actors: `{len(plan.actors)}`",
        f"- sensors: `{len(plan.sensors)}`",
        f"- ticks: `{len(plan.ticks)}`",
        f"- cleanup_order: `{', '.join(plan.cleanup_order)}`",
        "",
        "## Actors",
        "",
    ]
    for actor in plan.actors:
        lines.append(f"- `{actor.actor_ref}`: `{actor.blueprint_filter}` role `{actor.role}`")
    lines.extend(["", "## Sensors", ""])
    for sensor in plan.sensors:
        lines.append(f"- `{sensor.sensor_ref}` -> `{sensor.attach_to}` output `{sensor.output}`")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "CarlaActorScript",
    "CarlaScriptPlan",
    "CarlaSensorScript",
    "compile_carla_script_plan",
    "validate_carla_script_plan",
    "write_carla_script_plan",
]
