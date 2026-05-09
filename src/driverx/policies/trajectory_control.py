"""Convert cached trajectory intent into conservative control commands."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Sequence

from driverx.core.types import TrajectoryCandidate


@dataclass(frozen=True)
class EgoPose:
    x: float = 0.0
    y: float = 0.0
    yaw_deg: float = 0.0
    speed_mps: float = 0.0


@dataclass(frozen=True)
class TrajectoryControlConfig:
    controller: Literal["simlingo_pid", "geometric"] = "simlingo_pid"
    trajectory_frame: str = "ego"
    max_speed_mps: float = 6.0
    max_steer: float = 0.35
    max_brake: float = 0.5
    max_throttle: float = 0.45
    min_throttle_when_moving: float = 0.18
    lookahead_points: int = 3
    dt_s: float = 0.25
    stop_distance_m: float = 0.4
    current_speed_mps: float | None = None
    brake_speed_mps: float = 0.4
    brake_ratio: float = 1.1
    clip_delta_mps: float = 1.0
    turn_kp: float = 1.25
    turn_ki: float = 0.75
    turn_kd: float = 0.3
    turn_window: int = 20
    speed_kp: float = 1.75
    speed_ki: float = 1.0
    speed_kd: float = 2.0
    speed_window: int = 20
    aim_distance_fast_m: float = 3.0
    aim_distance_slow_m: float = 2.25
    aim_distance_threshold_mps: float = 5.5
    rotation_heading_weight: float = 0.2


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
    if cfg.controller not in {"simlingo_pid", "geometric"}:
        raise ValueError("controller must be either 'simlingo_pid' or 'geometric'.")
    if cfg.controller == "simlingo_pid":
        return _trajectory_to_control_trace_simlingo_pid(
            trajectory,
            source_policy_id=source_policy_id,
            ego_pose=pose,
            config=cfg,
        )
    return _trajectory_to_control_trace_geometric(
        trajectory,
        source_policy_id=source_policy_id,
        ego_pose=pose,
        config=cfg,
    )


def _trajectory_to_control_trace_geometric(
    trajectory: TrajectoryCandidate,
    *,
    source_policy_id: str,
    ego_pose: EgoPose,
    config: TrajectoryControlConfig,
) -> ControlTrace:
    cfg = config
    commands: list[ControlCommand] = []
    clamps: list[str] = []
    previous = (0.0, 0.0)
    yaw = math.radians(ego_pose.yaw_deg)
    for tick, point in enumerate(trajectory.points_xy):
        if cfg.trajectory_frame == "world":
            local_x, local_y = _world_to_ego_relative_point(point, ego_pose, yaw)
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


def _trajectory_to_control_trace_simlingo_pid(
    trajectory: TrajectoryCandidate,
    *,
    source_policy_id: str,
    ego_pose: EgoPose,
    config: TrajectoryControlConfig,
) -> ControlTrace:
    cfg = config
    local_points = [_trajectory_point_to_ego(point, ego_pose, cfg) for point in trajectory.points_xy]
    turn_controller = _PidWindow(cfg.turn_kp, cfg.turn_ki, cfg.turn_kd, cfg.turn_window)
    speed_controller = _PidWindow(cfg.speed_kp, cfg.speed_ki, cfg.speed_kd, cfg.speed_window)
    current_speed = max(0.0, float(cfg.current_speed_mps if cfg.current_speed_mps is not None else ego_pose.speed_mps))
    target_yaw = _target_yaw_rad(trajectory)
    commands: list[ControlCommand] = []
    clamps: list[str] = ["controller=simlingo_pid"]
    if target_yaw:
        clamps.append("pred_rot_yaw_hint=enabled")
    for tick, point in enumerate(local_points):
        remaining = local_points[tick:] or [point]
        desired_speed = min(_simlingo_desired_speed(remaining, cfg.dt_s), cfg.max_speed_mps)
        target_is_behind = point[0] < 0.0
        brake = target_is_behind or desired_speed < cfg.brake_speed_mps
        if desired_speed > 1e-5 and current_speed / desired_speed > cfg.brake_ratio:
            brake = True
        if target_is_behind:
            clamps.append(f"tick {tick}: target behind ego, braking instead of steering")
        delta = min(max(desired_speed - current_speed, 0.0), cfg.clip_delta_mps)
        throttle = min(max(speed_controller.step(delta), 0.0), cfg.max_throttle)
        if desired_speed > 0.05 and throttle > 0.0:
            throttle = max(throttle, min(cfg.min_throttle_when_moving, cfg.max_throttle))
        if brake:
            throttle = 0.0
        aim = _simlingo_aim_point(remaining, desired_speed, cfg)
        angle = math.degrees(math.atan2(aim[1], max(aim[0], 1e-6))) / 90.0
        if target_yaw and tick < len(target_yaw):
            yaw_angle = _clamp(target_yaw[tick] / (math.pi / 2.0), -1.0, 1.0)
            weight = _clamp(cfg.rotation_heading_weight, 0.0, 1.0)
            angle = (1.0 - weight) * angle + weight * yaw_angle
        if current_speed < 0.01 or brake:
            angle = 0.0
        raw_steer = turn_controller.step(angle)
        steer = _clamp(raw_steer, -cfg.max_steer, cfg.max_steer)
        if steer != raw_steer:
            clamps.append(f"tick {tick}: steer clamped from {raw_steer:.3f}")
        command_brake = cfg.max_brake if brake else 0.0
        commands.append(
            ControlCommand(
                tick=tick,
                target_x=round(point[0], 4),
                target_y=round(point[1], 4),
                target_speed_mps=round(desired_speed, 4),
                steer=round(steer, 4),
                throttle=round(throttle, 4),
                brake=round(command_brake, 4),
            )
        )
    return ControlTrace(
        source_policy_id=source_policy_id,
        closed_loop_control="cached_replay",
        trajectory_frame=cfg.trajectory_frame,
        commands=tuple(commands),
        safety_clamps=tuple(_dedupe(clamps)),
    )


def _trajectory_point_to_ego(
    point: tuple[float, float],
    pose: EgoPose,
    config: TrajectoryControlConfig,
) -> tuple[float, float]:
    if config.trajectory_frame == "world":
        return _world_to_ego_relative_point(point, pose, math.radians(pose.yaw_deg))
    return (float(point[0]), float(point[1]))


def _simlingo_desired_speed(points: list[tuple[float, float]], dt_s: float) -> float:
    one_second = max(2, int(round(1.0 / dt_s)))
    half_second = max(1, one_second // 2)
    first = points[min(half_second - 1, len(points) - 1)]
    second = points[min(one_second - 1, len(points) - 1)]
    return math.dist(first, second) * 2.0


def _simlingo_aim_point(
    points: list[tuple[float, float]],
    desired_speed_mps: float,
    config: TrajectoryControlConfig,
) -> tuple[float, float]:
    aim_distance = (
        config.aim_distance_slow_m
        if desired_speed_mps < config.aim_distance_threshold_mps
        else config.aim_distance_fast_m
    )
    for point in points:
        if math.hypot(point[0], point[1]) >= aim_distance:
            return point
    return points[-1]


class _PidWindow:
    def __init__(self, k_p: float, k_i: float, k_d: float, window_size: int) -> None:
        self.k_p = k_p
        self.k_i = k_i
        self.k_d = k_d
        self.window_size = max(1, int(window_size))
        self._window: list[float] = [0.0 for _ in range(self.window_size)]

    def step(self, error: float) -> float:
        self._window.append(error)
        self._window = self._window[-self.window_size :]
        integral = sum(self._window) / len(self._window)
        derivative = self._window[-1] - self._window[-2] if len(self._window) >= 2 else 0.0
        return self.k_p * error + self.k_i * integral + self.k_d * derivative


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


def _target_yaw_rad(trajectory: TrajectoryCandidate) -> list[float]:
    values = trajectory.metadata.get("target_yaw_rad")
    if not isinstance(values, list):
        return []
    result: list[float] = []
    for value in values:
        if isinstance(value, (int, float)):
            result.append(float(value))
    return result


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


__all__ = [
    "ControlCommand",
    "ControlTrace",
    "EgoPose",
    "TrajectoryControlConfig",
    "load_policy_decision_trajectory",
    "trajectory_to_control_trace",
]
