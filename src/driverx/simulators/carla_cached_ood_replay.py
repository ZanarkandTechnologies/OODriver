"""Replay cached Alpamayo policy decisions inside DriverX OOD CARLA scenes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.assets import default_asset_requests, generate_assets_dry_run
from driverx.behaviors import default_behavior_plans, simulate_behavior
from driverx.core.config import read_config_mapping
from driverx.policies.trajectory_control import (
    EgoPose,
    TrajectoryControlConfig,
    load_policy_decision_trajectory,
    trajectory_to_control_trace,
)
from driverx.scenarios import MutationPolicy, generate_scenario_recipes, load_scenario_seeds
from driverx.simulators.carla_ood_demo import (
    CarlaOodDemoConfig,
    load_carla_ood_demo_config,
    run_carla_ood_demo,
    write_carla_ood_demo,
)


@dataclass(frozen=True)
class CachedOodReplayConfig:
    decision_path: Path
    carla_ood_config_path: Path = Path("configs/carla_ood_demo.local.sample.yaml")
    seeds_path: Path = Path("tests/fixtures/fail2drive_like/seeds.json")
    behavior_id: str = "motorcycle_filtering"
    tick_count: int | None = None
    fps: int | None = None
    live: bool = False
    no_default_assets: bool = False
    ego_pose: EgoPose = EgoPose()
    control_config: TrajectoryControlConfig = TrajectoryControlConfig()


@dataclass(frozen=True)
class CachedOodReplayResult:
    status: str
    decision_path: Path
    source_policy_id: str
    closed_loop_control: str
    command_count: int
    applied_count: int
    frame_count: int
    duration_s: float
    live: bool
    control_trace_path: str
    tracks_path: str | None
    rgb_folder: str | None
    carla_report_path: str | None
    safety_clamps: tuple[str, ...]
    blockers: tuple[str, ...]
    claim_boundaries: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "decision_path": str(self.decision_path),
            "source_policy_id": self.source_policy_id,
            "closed_loop_control": self.closed_loop_control,
            "command_count": self.command_count,
            "applied_count": self.applied_count,
            "frame_count": self.frame_count,
            "duration_s": self.duration_s,
            "live": self.live,
            "control_trace_path": self.control_trace_path,
            "tracks_path": self.tracks_path,
            "rgb_folder": self.rgb_folder,
            "carla_report_path": self.carla_report_path,
            "safety_clamps": list(self.safety_clamps),
            "blockers": list(self.blockers),
            "claim_boundaries": list(self.claim_boundaries),
        }


def load_cached_ood_replay_config(path: Path, *, decision_path: Path | None = None) -> CachedOodReplayConfig:
    raw = read_config_mapping(path)
    replay = raw.get("cached_ood_replay", raw)
    if not isinstance(replay, dict):
        raise ValueError("Config field 'cached_ood_replay' must be a mapping.")
    decision = decision_path or Path(str(replay.get("decision_path", "")))
    if not str(decision):
        raise ValueError("Cached OOD replay requires decision_path or --decision.")
    return CachedOodReplayConfig(
        decision_path=decision,
        carla_ood_config_path=Path(str(replay.get("carla_ood_config_path", "configs/carla_ood_demo.local.sample.yaml"))),
        seeds_path=Path(str(replay.get("seeds_path", "tests/fixtures/fail2drive_like/seeds.json"))),
        behavior_id=str(replay.get("behavior_id", "motorcycle_filtering")),
        tick_count=_optional_int(replay.get("tick_count")),
        fps=_optional_int(replay.get("fps")),
        live=bool(replay.get("live", False)),
        no_default_assets=bool(replay.get("no_default_assets", False)),
        control_config=TrajectoryControlConfig(
            trajectory_frame=str(replay.get("trajectory_frame", "ego")),
            max_speed_mps=float(replay.get("max_speed_mps", 6.0)),
            max_steer=float(replay.get("max_steer", 0.35)),
            max_brake=float(replay.get("max_brake", 0.5)),
            max_throttle=float(replay.get("max_throttle", 0.45)),
            lookahead_points=int(replay.get("lookahead_points", 3)),
            dt_s=float(replay.get("dt_s", 0.25)),
        ),
    )


def run_cached_ood_replay(
    config: CachedOodReplayConfig,
    run_dir: Path,
    *,
    carla_module: object | None = None,
) -> CachedOodReplayResult:
    run_dir.mkdir(parents=True, exist_ok=True)
    policy_id, trajectory = load_policy_decision_trajectory(config.decision_path)
    trace = trajectory_to_control_trace(
        trajectory,
        source_policy_id=policy_id,
        ego_pose=config.ego_pose,
        config=config.control_config,
    )
    trace_path = run_dir / "control_trace.json"
    trace_path.write_text(json.dumps(trace.to_jsonable(), indent=2), encoding="utf-8")

    if config.live:
        return _run_live_replay(config, run_dir, policy_id, trace_path, trace, carla_module)
    tracks_path = run_dir / "entity_tracks.json"
    tracks_path.write_text(json.dumps(_synthetic_tracks(trace.to_jsonable()), indent=2), encoding="utf-8")
    return CachedOodReplayResult(
        status="passed",
        decision_path=config.decision_path,
        source_policy_id=policy_id,
        closed_loop_control="cached_replay",
        command_count=len(trace.commands),
        applied_count=len(trace.commands),
        frame_count=0,
        duration_s=round(len(trace.commands) * config.control_config.dt_s, 4),
        live=False,
        control_trace_path=str(trace_path),
        tracks_path=str(tracks_path),
        rgb_folder=None,
        carla_report_path=None,
        safety_clamps=trace.safety_clamps,
        blockers=(),
        claim_boundaries=_claim_boundaries(live=False),
    )


def write_cached_ood_replay(run_dir: Path, result: CachedOodReplayResult) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = result.to_jsonable()
    json_path = run_dir / "cached_ood_replay.json"
    report_path = run_dir / "cached_ood_replay.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _run_live_replay(
    config: CachedOodReplayConfig,
    run_dir: Path,
    policy_id: str,
    trace_path: Path,
    trace: Any,
    carla_module: object | None,
) -> CachedOodReplayResult:
    carla_config = load_carla_ood_demo_config(config.carla_ood_config_path)
    tick_count = config.tick_count or min(len(trace.commands), carla_config.tick_count)
    carla_config = CarlaOodDemoConfig(
        **{
            **carla_config.__dict__,
            "tick_count": tick_count,
            "fps": config.fps or carla_config.fps,
            "behavior_id": config.behavior_id,
            "ego_mode": "policy_replay",
        }
    )
    recipe = generate_scenario_recipes(
        load_scenario_seeds(config.seeds_path),
        MutationPolicy(mutations=("regional_driving_behavior",)),
        count=1,
        random_seed=7,
    )[0]
    plans = {plan.behavior_id: plan for plan in default_behavior_plans()}
    behavior_plan = plans.get(config.behavior_id) or plans["motorcycle_filtering"]
    carla_result = run_carla_ood_demo(
        carla_config,
        run_dir / "carla",
        recipe=recipe,
        behavior=simulate_behavior(behavior_plan),
        asset_manifests=[] if config.no_default_assets else generate_assets_dry_run(default_asset_requests()),
        carla_module=carla_module,
        ego_control_trace=trace,
    )
    carla_summary = write_carla_ood_demo(run_dir / "carla", carla_result)
    return CachedOodReplayResult(
        status=carla_result.status,
        decision_path=config.decision_path,
        source_policy_id=policy_id,
        closed_loop_control="cached_replay",
        command_count=len(trace.commands),
        applied_count=min(len(trace.commands), carla_config.tick_count) if carla_result.connected else 0,
        frame_count=carla_result.frame_count,
        duration_s=carla_result.duration_s,
        live=True,
        control_trace_path=str(trace_path),
        tracks_path=carla_result.tracks_path,
        rgb_folder=carla_result.rgb_folder,
        carla_report_path=str(carla_summary.get("report_path")),
        safety_clamps=trace.safety_clamps,
        blockers=tuple(carla_result.blockers),
        claim_boundaries=_claim_boundaries(live=True),
    )


def _synthetic_tracks(trace_payload: dict[str, Any]) -> list[dict[str, Any]]:
    tracks: list[dict[str, Any]] = []
    for command in list(trace_payload.get("commands", [])):
        tick = int(command.get("tick", 0))
        tracks.append(
            {
                "actor_ref": "ego",
                "actor_id": 0,
                "type_id": "driverx.synthetic.cached_replay",
                "tick": tick,
                "t_s": round(tick * 0.25, 4),
                "location": {
                    "x": float(command.get("target_x", 0.0)),
                    "y": float(command.get("target_y", 0.0)),
                    "z": 0.0,
                },
                "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                "velocity": {
                    "x": float(command.get("target_speed_mps", 0.0)),
                    "y": 0.0,
                    "z": 0.0,
                },
            }
        )
    return tracks


def _claim_boundaries(*, live: bool) -> tuple[str, ...]:
    return (
        "cached_alpamayo_replay=true",
        f"live_carla_replay={str(live).lower()}",
        "real_time_vla_control=false",
        "stock_fail2drive_score=false",
        "policy_output_source=cached_policy_decision",
    )


def _optional_int(value: object) -> int | None:
    if value in (None, "", "null"):
        return None
    return int(value)


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Cached OOD Replay",
        "",
        f"- status: `{payload['status']}`",
        f"- source_policy_id: `{payload['source_policy_id']}`",
        f"- closed_loop_control: `{payload['closed_loop_control']}`",
        f"- live: `{payload['live']}`",
        f"- command_count: `{payload['command_count']}`",
        f"- applied_count: `{payload['applied_count']}`",
        f"- frame_count: `{payload['frame_count']}`",
        f"- duration_s: `{payload['duration_s']}`",
        f"- rgb_folder: `{payload['rgb_folder']}`",
        f"- tracks_path: `{payload['tracks_path']}`",
        "",
        "## Claim Boundaries",
        "",
    ]
    lines.extend(f"- `{item}`" for item in payload["claim_boundaries"])
    lines.extend(["", "## Safety Clamps", ""])
    clamps = list(payload.get("safety_clamps", []))
    lines.extend(f"- {item}" for item in clamps) if clamps else lines.append("- none")
    blockers = list(payload.get("blockers", []))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines) + "\n"


__all__ = [
    "CachedOodReplayConfig",
    "CachedOodReplayResult",
    "load_cached_ood_replay_config",
    "run_cached_ood_replay",
    "write_cached_ood_replay",
]
