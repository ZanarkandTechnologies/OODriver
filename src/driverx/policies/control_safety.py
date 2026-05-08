"""Deterministic safety envelope for model-derived closed-loop controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from driverx.policies.trajectory_control import ControlCommand, ControlTrace


@dataclass(frozen=True)
class ClosedLoopSafetyConfig:
    max_abs_y_m: float = 1.65
    max_speed_mps: float = 6.0
    max_throttle: float = 0.45
    max_brake: float = 0.6
    min_blocker_distance_m: float = 1.0


@dataclass(frozen=True)
class SafetyContext:
    nearest_object_distance_m: float | None = None
    corridor_half_width_m: float | None = None


@dataclass(frozen=True)
class SafeControlChunk:
    control_trace: ControlTrace
    interventions: tuple[str, ...]
    lane_departure_proxy: bool
    max_abs_y_m: float
    speed_cap_applied: bool
    emergency_stop_applied: bool
    unsafe_control_conflict: bool
    planned_vs_actual_error_m: float | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "interventions": list(self.interventions),
            "lane_departure_proxy": self.lane_departure_proxy,
            "max_abs_y_m": self.max_abs_y_m,
            "speed_cap_applied": self.speed_cap_applied,
            "emergency_stop_applied": self.emergency_stop_applied,
            "unsafe_control_conflict": self.unsafe_control_conflict,
            "planned_vs_actual_error_m": self.planned_vs_actual_error_m,
        }


def validate_control_chunk(
    trace: ControlTrace,
    context: SafetyContext | None = None,
    config: ClosedLoopSafetyConfig | None = None,
) -> SafeControlChunk:
    cfg = config or ClosedLoopSafetyConfig()
    ctx = context or SafetyContext()
    corridor = ctx.corridor_half_width_m or cfg.max_abs_y_m
    interventions: list[str] = []
    commands: list[ControlCommand] = []
    max_abs_y = 0.0
    speed_cap = False
    emergency = bool(ctx.nearest_object_distance_m is not None and ctx.nearest_object_distance_m <= cfg.min_blocker_distance_m)
    conflict = False
    for command in trace.commands:
        target_y = max(-corridor, min(corridor, command.target_y))
        if target_y != command.target_y:
            interventions.append(f"tick {command.tick}: corridor clamp")
        max_abs_y = max(max_abs_y, abs(target_y))
        speed = min(command.target_speed_mps, cfg.max_speed_mps)
        if speed != command.target_speed_mps:
            speed_cap = True
            interventions.append(f"tick {command.tick}: speed cap")
        throttle = min(max(command.throttle, 0.0), cfg.max_throttle)
        brake = min(max(command.brake, 0.0), cfg.max_brake)
        if emergency:
            throttle = 0.0
            brake = cfg.max_brake
        if throttle > 0.0 and brake > 0.0:
            conflict = True
            interventions.append(f"tick {command.tick}: brake/throttle conflict resolved")
            throttle = 0.0
        commands.append(
            ControlCommand(
                tick=command.tick,
                target_x=command.target_x,
                target_y=round(target_y, 4),
                target_speed_mps=round(speed, 4),
                steer=command.steer,
                throttle=round(throttle, 4),
                brake=round(brake, 4),
            )
        )
    if emergency:
        interventions.append("emergency_stop")
    safe_trace = ControlTrace(
        source_policy_id=trace.source_policy_id,
        closed_loop_control=trace.closed_loop_control,
        trajectory_frame=trace.trajectory_frame,
        commands=tuple(commands),
        safety_clamps=tuple([*trace.safety_clamps, *_dedupe(interventions)]),
    )
    return SafeControlChunk(
        control_trace=safe_trace,
        interventions=tuple(_dedupe(interventions)),
        lane_departure_proxy=max_abs_y > corridor,
        max_abs_y_m=round(max_abs_y, 4),
        speed_cap_applied=speed_cap,
        emergency_stop_applied=emergency,
        unsafe_control_conflict=conflict,
    )


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


__all__ = [
    "ClosedLoopSafetyConfig",
    "SafeControlChunk",
    "SafetyContext",
    "validate_control_chunk",
]
