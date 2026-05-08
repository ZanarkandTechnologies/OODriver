"""Convert cached trajectory intent into conservative control commands."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from driverx.core.types import TrajectoryCandidate


@dataclass(frozen=True)
class EgoPose:
    x: float = 0.0
    y: float = 0.0
    yaw_deg: float = 0.0


@dataclass(frozen=True)
class TrajectoryControlConfig:
    trajectory_frame: str = "ego"
    max_speed_mps: float = 6.0
    max_steer: float = 0.35
    max_brake: float = 0.5
    max_throttle: float = 0.45
    min_throttle_when_moving: float = 0.18
    lookahead_points: int = 3
    dt_s: float = 0.25
    stop_distance_m: float = 0.4


@dataclass(frozen=True)
class ControlCommand:
    tick: int
    target_x: float
    target_y: float
    target_speed_mps: float
    steer: float
    throttle: float
    brake: float

    def to_jsonable(self) -> dict[str, float | int]:
        return {
            "tick": self.tick,
            "target_x": self.target_x,
            "target_y": self.target_y,
            "target_speed_mps": self.target_speed_mps,
            "steer": self.steer,
            "throttle": self.throttle,
            "brake": self.brake,
        }


@dataclass(frozen=True)
class ControlTrace:
    source_policy_id: str
    closed_loop_control: bool | str
    trajectory_frame: str
    commands: tuple[ControlCommand, ...]
    safety_clamps: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "source_policy_id": self.source_policy_id,
            "closed_loop_control": self.closed_loop_control,
            "trajectory_frame": self.trajectory_frame,
            "commands": [command.to_jsonable() for command in self.commands],
            "safety_clamps": list(self.safety_clamps),
        }


def load_policy_decision_trajectory(path: Path) -> tuple[str, TrajectoryCandidate]:
    """Load a DriverX PolicyDecision JSON and return policy id plus trajectory."""

    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "policy_decision" in payload:
        payload = payload["policy_decision"]
    if not isinstance(payload, dict):
        raise ValueError("Policy decision JSON must be a mapping.")
    action = payload.get("action")
    if not isinstance(action, dict):
        raise ValueError("Policy decision is missing action.")
    trajectory = action.get("trajectory")
    if not isinstance(trajectory, dict):
        raise ValueError("Policy decision action is missing trajectory.")
    points = trajectory.get("points_xy")
    if not isinstance(points, list):
        raise ValueError("Policy decision trajectory.points_xy must be a list.")
    candidate = TrajectoryCandidate(
        points_xy=[_point2(item) for item in points],
        source=str(trajectory.get("source", "policy_decision")),
        score=float(trajectory.get("score", 0.0) or 0.0),
        metadata=dict(trajectory.get("metadata", {}))
        if isinstance(trajectory.get("metadata"), dict)
        else {},
    )
    return str(payload.get("policy_id", "unknown-policy")), candidate


def trajectory_to_control_trace(
    trajectory: TrajectoryCandidate,
    *,
    source_policy_id: str,
    ego_pose: EgoPose | None = None,
    config: TrajectoryControlConfig | None = None,
) -> ControlTrace:
    """Convert future waypoints into bounded replay controls."""

    pose = ego_pose or EgoPose()
    cfg = config or TrajectoryControlConfig()
    if cfg.max_speed_mps <= 0 or cfg.dt_s <= 0:
        raise ValueError("max_speed_mps and dt_s must be positive.")
    if cfg.trajectory_frame not in {"ego", "world"}:
        raise ValueError("trajectory_frame must be either 'ego' or 'world'.")
    commands: list[ControlCommand] = []
    clamps: list[str] = []
    previous = (0.0, 0.0)
    yaw = math.radians(pose.yaw_deg)
    for tick, point in enumerate(trajectory.points_xy):
        if cfg.trajectory_frame == "world":
            local_x, local_y = _world_to_ego_relative_point(point, pose, yaw)
        else:
            local_x, local_y = (float(point[0]), float(point[1]))
        target_distance = math.hypot(local_x, local_y)
        step_distance = math.dist(previous, (local_x, local_y))
        raw_speed = step_distance / cfg.dt_s
        target_speed = min(raw_speed, cfg.max_speed_mps)
        if raw_speed > cfg.max_speed_mps:
            clamps.append(f"tick {tick}: speed clamped from {raw_speed:.3f}m/s")
        target_is_behind = local_x < 0.0
        if target_is_behind:
            clamps.append(f"tick {tick}: target behind ego, braking instead of steering")
            steer = 0.0
        else:
            heading = math.atan2(local_y, max(local_x, 1e-6))
            raw_steer = heading / math.radians(45.0) * cfg.max_steer
            steer = _clamp(raw_steer, -cfg.max_steer, cfg.max_steer)
            if steer != raw_steer:
                clamps.append(f"tick {tick}: steer clamped from {raw_steer:.3f}")
        if target_is_behind or target_distance <= cfg.stop_distance_m and tick >= cfg.lookahead_points:
            throttle = 0.0
            brake = cfg.max_brake
        else:
            throttle = _clamp(target_speed / cfg.max_speed_mps * cfg.max_throttle, 0.0, cfg.max_throttle)
            if target_speed > 0.05 and throttle > 0.0:
                throttle = max(throttle, min(cfg.min_throttle_when_moving, cfg.max_throttle))
            brake = 0.0
        commands.append(
            ControlCommand(
                tick=tick,
                target_x=round(local_x, 4),
                target_y=round(local_y, 4),
                target_speed_mps=round(target_speed, 4),
                steer=round(steer, 4),
                throttle=round(throttle, 4),
                brake=round(brake, 4),
            )
        )
        previous = (local_x, local_y)
    return ControlTrace(
        source_policy_id=source_policy_id,
        closed_loop_control="cached_replay",
        trajectory_frame=cfg.trajectory_frame,
        commands=tuple(commands),
        safety_clamps=tuple(clamps),
    )


def _world_to_ego_relative_point(
    point: tuple[float, float],
    pose: EgoPose,
    yaw: float,
) -> tuple[float, float]:
    dx = float(point[0]) - pose.x
    dy = float(point[1]) - pose.y
    cos_yaw = math.cos(-yaw)
    sin_yaw = math.sin(-yaw)
    return (
        dx * cos_yaw - dy * sin_yaw,
        dx * sin_yaw + dy * cos_yaw,
    )


def _point2(value: Sequence[float | int]) -> tuple[float, float]:
    if len(value) < 2:
        raise ValueError("Trajectory point must contain at least x and y.")
    return (float(value[0]), float(value[1]))


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


__all__ = [
    "ControlCommand",
    "ControlTrace",
    "EgoPose",
    "TrajectoryControlConfig",
    "load_policy_decision_trajectory",
    "trajectory_to_control_trace",
]
