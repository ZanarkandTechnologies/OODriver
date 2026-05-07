"""Flagship OODrive scenario contract builder."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.core.config import read_config_mapping


@dataclass(frozen=True)
class FlagshipScenarioConfig:
    scenario_id: str = "flagship-malaysia-wet-roadwork"
    title: str = "Malaysian wet night roadwork chaos"
    prompt: str = (
        "Malaysian wet night roadwork: a lorry brakes without signal, a "
        "motorcycle filters between cars, cones/debris narrow the lane, and a "
        "roadside vendor occludes a wrong-way scooter."
    )
    map_name: str = "Town10HD_Opt"
    output_root: Path = Path("artifacts/runs")
    run_id: str = "flagship-malaysia"
    carla_config_path: Path = Path("configs/carla_ood_demo.runpod.high_fidelity.yaml")
    campaign_config_path: Path = Path("configs/scripted_ood_campaign.runpod.high_fidelity.yaml")
    behavior_sequence: tuple[str, ...] = (
        "sudden_brake",
        "motorcycle_filtering",
        "double_parked_door_swerve",
        "wrong_way_shoulder_creep",
    )
    memory_queries: tuple[str, ...] = (
        "motorcycle_filtering",
        "unsignaled_brake",
        "roadwork_lane_narrowing",
        "vendor_occlusion",
        "wrong_way_shoulder_creep",
    )
    checkpoint_count: int = 10
    target_duration_s: float = 90.0
    weather: str = "wet_night_glare"
    region: str = "malaysia_urban"
    traffic_density: str = "dense_mixed"
    road_condition: str = "temporary_roadwork_lane_narrowing"


@dataclass(frozen=True)
class FlagshipScenarioPack:
    scenario_id: str
    title: str
    prompt: str
    map_name: str
    environment: dict[str, Any]
    actors: list[dict[str, Any]]
    behavior_sequence: list[str]
    memory_queries: list[str]
    quality_targets: dict[str, Any]
    planned_checkpoints: list[dict[str, Any]]
    runtime_commands: list[dict[str, Any]]
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "prompt": self.prompt,
            "map_name": self.map_name,
            "environment": self.environment,
            "actors": self.actors,
            "behavior_sequence": self.behavior_sequence,
            "memory_queries": self.memory_queries,
            "quality_targets": self.quality_targets,
            "planned_checkpoints": self.planned_checkpoints,
            "runtime_commands": self.runtime_commands,
            "claim_boundaries": self.claim_boundaries,
        }


def load_flagship_config(path: Path) -> FlagshipScenarioConfig:
    raw = read_config_mapping(path)
    data = raw.get("flagship", raw)
    if not isinstance(data, dict):
        raise ValueError("Config field 'flagship' must be a mapping.")
    return FlagshipScenarioConfig(
        scenario_id=str(data.get("scenario_id", "flagship-malaysia-wet-roadwork")),
        title=str(data.get("title", "Malaysian wet night roadwork chaos")),
        prompt=str(data.get("prompt", FlagshipScenarioConfig.prompt)),
        map_name=str(data.get("map_name", "Town10HD_Opt")),
        output_root=Path(str(data.get("output_root", "artifacts/runs"))),
        run_id=str(data.get("run_id", "flagship-malaysia")),
        carla_config_path=Path(str(data.get("carla_config_path", "configs/carla_ood_demo.runpod.high_fidelity.yaml"))),
        campaign_config_path=Path(
            str(data.get("campaign_config_path", "configs/scripted_ood_campaign.runpod.high_fidelity.yaml"))
        ),
        behavior_sequence=tuple(
            _csv_list(
                data.get("behavior_sequence"),
                [
                    "sudden_brake",
                    "motorcycle_filtering",
                    "double_parked_door_swerve",
                    "wrong_way_shoulder_creep",
                ],
            )
        ),
        memory_queries=tuple(
            _csv_list(
                data.get("memory_queries"),
                [
                    "motorcycle_filtering",
                    "unsignaled_brake",
                    "roadwork_lane_narrowing",
                    "vendor_occlusion",
                    "wrong_way_shoulder_creep",
                ],
            )
        ),
        checkpoint_count=max(1, int(data.get("checkpoint_count", 10))),
        target_duration_s=max(1.0, float(data.get("target_duration_s", 90.0))),
        weather=str(data.get("weather", "wet_night_glare")),
        region=str(data.get("region", "malaysia_urban")),
        traffic_density=str(data.get("traffic_density", "dense_mixed")),
        road_condition=str(data.get("road_condition", "temporary_roadwork_lane_narrowing")),
    )


def build_flagship_scenario(config: FlagshipScenarioConfig) -> FlagshipScenarioPack:
    return FlagshipScenarioPack(
        scenario_id=config.scenario_id,
        title=config.title,
        prompt=config.prompt,
        map_name=config.map_name,
        environment=_environment(config),
        actors=_actors(),
        behavior_sequence=list(config.behavior_sequence),
        memory_queries=list(config.memory_queries),
        quality_targets=_quality_targets(config),
        planned_checkpoints=_planned_checkpoints(config),
        runtime_commands=_runtime_commands(config),
        claim_boundaries=[
            "flagship_case_study=true",
            "minimal_shot_scenario_generation=true",
            "scripted_carla_ood_demo_until_live_capture=true",
            "sampled_open_loop_reasoning_until_replay=true",
            "closed_loop_alpamayo_control=false_until_TASK_123",
            "real_time_vla_control=false",
        ],
    )


def write_flagship_scenario(run_dir: Path, pack: FlagshipScenarioPack) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = pack.to_jsonable()
    json_path = run_dir / "flagship_scenario.json"
    report_path = run_dir / "flagship_scenario.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _environment(config: FlagshipScenarioConfig) -> dict[str, Any]:
    return {
        "region": config.region,
        "weather": config.weather,
        "traffic_density": config.traffic_density,
        "road_condition": config.road_condition,
        "lighting": "night_market_glare_and_headlights",
        "lane_discipline": "low",
        "surface": "wet_reflective",
        "visibility_pressure": "occlusion_plus_glare",
    }


def _actors() -> list[dict[str, Any]]:
    return [
        {
            "actor_id": "lead_lorry",
            "kind": "vehicle",
            "blueprint_hint": "vehicle.carlamotors.carlacola",
            "behavior": "sudden_brake",
            "pressure": "brakes hard without signal after entering narrowed roadwork lane",
        },
        {
            "actor_id": "filtering_motorcycle",
            "kind": "motorcycle",
            "blueprint_hint": "vehicle.kawasaki.ninja",
            "behavior": "motorcycle_filtering",
            "pressure": "fast two-wheeler filters through lateral gap beside ego",
        },
        {
            "actor_id": "roadside_vendor_occluder",
            "kind": "static_proxy",
            "blueprint_hint": "static.prop.foodcart",
            "behavior": "occluder",
            "pressure": "blocks view of shoulder and informal crossing zone",
        },
        {
            "actor_id": "roadwork_debris_and_cones",
            "kind": "static_proxy_cluster",
            "blueprint_hint": "static.prop.constructioncone,static.prop.dirtdebris01",
            "behavior": "lane_narrowing",
            "pressure": "forces route to bias around temporary obstruction",
        },
        {
            "actor_id": "wrong_way_scooter",
            "kind": "vehicle_proxy",
            "blueprint_hint": "vehicle.kawasaki.ninja",
            "behavior": "wrong_way_shoulder_creep",
            "pressure": "emerges from occluded shoulder against expected traffic direction",
        },
    ]


def _quality_targets(config: FlagshipScenarioConfig) -> dict[str, Any]:
    return {
        "min_duration_s": min(60.0, config.target_duration_s),
        "target_duration_s": config.target_duration_s,
        "min_frame_count": 300,
        "min_visible_actor_count": 8,
        "max_ood_step_m": 1.15,
        "require_video": True,
        "require_road_alignment": True,
        "require_conflict": True,
        "require_planned_vs_actual_path": True,
        "require_reasoning_overlay": True,
    }


def _planned_checkpoints(config: FlagshipScenarioConfig) -> list[dict[str, Any]]:
    if config.checkpoint_count == 1:
        times = [0.0]
    else:
        step = config.target_duration_s / float(config.checkpoint_count - 1)
        times = [round(index * step, 3) for index in range(config.checkpoint_count)]
    return [
        {
            "checkpoint_id": f"{config.scenario_id}-ckpt-{index:03d}",
            "sim_time_s": time_s,
            "purpose": _checkpoint_purpose(index, config.checkpoint_count),
        }
        for index, time_s in enumerate(times)
    ]


def _checkpoint_purpose(index: int, count: int) -> str:
    if index == 0:
        return "establish route, weather, and roadwork context"
    if index == count - 1:
        return "verify recovery and route continuation after OOD interaction"
    if index < count / 3:
        return "approach occlusion and lane narrowing"
    if index < (2 * count) / 3:
        return "reason through lorry brake and motorcycle filtering conflict"
    return "handle wrong-way shoulder emergence and stabilize trajectory"


def _runtime_commands(config: FlagshipScenarioConfig) -> list[dict[str, Any]]:
    db_path = f"{config.output_root}/{config.run_id}/scenario_studio_db.json"
    return [
        {
            "command_id": "build_contract",
            "phase": "local_contract",
            "requires": [],
            "command": (
                "PYTHONPATH=src python3 -m driverx build-flagship-oodrive-scenario "
                f"--config configs/oodrive_flagship_malaysia.yaml --run-id {config.run_id}"
            ),
            "expected_outputs": ["flagship_scenario.json", "flagship_scenario.md"],
        },
        {
            "command_id": "seed_oodrive_db",
            "phase": "local_database",
            "requires": ["build_contract"],
            "command": (
                "PYTHONPATH=src python3 -m oodrive quickstart "
                f"--prompt \"{config.prompt}\" --run-id {config.run_id}-db --count 6 --severity 5 --seed 120"
            ),
            "expected_outputs": ["scenario_studio_db.json", "scenario_generator_cli_pack.html"],
        },
        {
            "command_id": "run_carla_campaign_baseline",
            "phase": "h100_kasm_carla",
            "requires": ["build_contract"],
            "command": (
                "PYTHONPATH=src python3 -m driverx run-scripted-ood-campaign "
                f"--config {config.campaign_config_path} --run-id {config.run_id}-carla-baseline "
                "--limit 1 --live --assemble-video --quality-retry-limit 2"
            ),
            "expected_outputs": ["scripted_ood_campaign_summary.json", "ood_video_evidence.json", "mp4"],
        },
        {
            "command_id": "capture_checkpoints",
            "phase": "h100_kasm_carla",
            "requires": ["run_carla_campaign_baseline"],
            "command": (
                "PYTHONPATH=src python3 -m driverx run-flagship-carla-capture "
                f"--scenario {config.output_root}/{config.run_id}/flagship_scenario.json "
                f"--config {config.carla_config_path} --run-id {config.run_id}-checkpoints"
            ),
            "expected_outputs": ["flagship_checkpoint_manifest.json", "rgb checkpoints", "actor tracks"],
        },
        {
            "command_id": "run_alpamayo_checkpoints",
            "phase": "h100_kasm_alpamayo",
            "requires": ["capture_checkpoints"],
            "command": (
                "PYTHONPATH=src python3 -m driverx run-alpamayo-checkpoint-batch "
                f"--manifest artifacts/runs/{config.run_id}-checkpoints/flagship_checkpoint_manifest.json "
                f"--run-id {config.run_id}-alpamayo-checkpoints"
            ),
            "expected_outputs": ["alpamayo_checkpoint_batch.json", "CoC reasoning", "trajectory samples"],
        },
        {
            "command_id": "replay_alpamayo_trajectory",
            "phase": "h100_kasm_carla",
            "requires": ["run_alpamayo_checkpoints"],
            "command": (
                "PYTHONPATH=src python3 -m driverx run-alpamayo-timewarped-replay "
                f"--scenario {config.output_root}/{config.run_id}/flagship_scenario.json "
                f"--predictions artifacts/runs/{config.run_id}-alpamayo-checkpoints/alpamayo_checkpoint_batch.json "
                f"--run-id {config.run_id}-trajectory-replay"
            ),
            "expected_outputs": ["planned_vs_actual_path.json", "control_trace.json", "replay_video.mp4"],
        },
        {
            "command_id": "build_final_pack",
            "phase": "local_or_h100_video",
            "requires": ["replay_alpamayo_trajectory"],
            "command": (
                "PYTHONPATH=src python3 -m driverx build-flagship-evidence-pack "
                f"--scenario {config.output_root}/{config.run_id}/flagship_scenario.json "
                f"--run-id {config.run_id}-v9-final"
            ),
            "expected_outputs": ["final demo mp4", "browser html", "two-page writeup"],
        },
    ]


def _csv_list(value: Any, default: list[str]) -> list[str]:
    if value is None:
        return list(default)
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['title']}",
        "",
        f"- Scenario: `{payload['scenario_id']}`",
        f"- Map: `{payload['map_name']}`",
        f"- Prompt: {payload['prompt']}",
        "",
        "## Environment",
        "",
    ]
    for key, value in payload["environment"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Actors", "", "| actor | behavior | pressure |", "| --- | --- | --- |"])
    for actor in payload["actors"]:
        lines.append(f"| `{actor['actor_id']}` | `{actor['behavior']}` | {actor['pressure']} |")
    lines.extend(["", "## Planned Checkpoints", "", "| checkpoint | sim time | purpose |", "| --- | ---: | --- |"])
    for checkpoint in payload["planned_checkpoints"]:
        lines.append(
            f"| `{checkpoint['checkpoint_id']}` | {checkpoint['sim_time_s']} | {checkpoint['purpose']} |"
        )
    lines.extend(["", "## Runtime Command Plan", ""])
    for command in payload["runtime_commands"]:
        lines.extend(
            [
                f"### `{command['command_id']}`",
                "",
                f"- Phase: `{command['phase']}`",
                f"- Requires: `{', '.join(command['requires']) or 'none'}`",
                "",
                "```bash",
                command["command"],
                "```",
                "",
            ]
        )
    lines.extend(["## Claim Boundaries", ""])
    for boundary in payload["claim_boundaries"]:
        lines.append(f"- `{boundary}`")
    return "\n".join(lines) + "\n"


__all__ = [
    "FlagshipScenarioConfig",
    "FlagshipScenarioPack",
    "build_flagship_scenario",
    "load_flagship_config",
    "write_flagship_scenario",
]
