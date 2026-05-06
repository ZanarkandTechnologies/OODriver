"""Replay cached policy trajectories as conservative CARLA control traces."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.policies.trajectory_control import (
    ControlTrace,
    EgoPose,
    TrajectoryControlConfig,
    load_policy_decision_trajectory,
    trajectory_to_control_trace,
)


@dataclass(frozen=True)
class CarlaPolicyReplayConfig:
    decision_path: Path
    ego_pose: EgoPose = EgoPose()
    control_config: TrajectoryControlConfig = TrajectoryControlConfig()
    apply_to_actor: bool = False


@dataclass(frozen=True)
class CarlaPolicyReplayResult:
    decision_path: Path
    source_policy_id: str
    command_count: int
    applied_count: int
    closed_loop_control: bool | str
    safety_clamps: tuple[str, ...]
    cleanup_complete: bool
    dry_run: bool
    trace: dict[str, Any]
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "decision_path": str(self.decision_path),
            "source_policy_id": self.source_policy_id,
            "command_count": self.command_count,
            "applied_count": self.applied_count,
            "closed_loop_control": self.closed_loop_control,
            "safety_clamps": list(self.safety_clamps),
            "cleanup_complete": self.cleanup_complete,
            "dry_run": self.dry_run,
            "trace": self.trace,
            "error": self.error,
        }


@dataclass(frozen=True)
class AppliedControlReplay:
    applied_count: int
    command_count: int
    tick_count: int
    controls: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return not self.errors and self.applied_count == self.command_count

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": "passed" if self.passed else "partial",
            "applied_count": self.applied_count,
            "command_count": self.command_count,
            "tick_count": self.tick_count,
            "controls": list(self.controls),
            "errors": list(self.errors),
        }


def apply_control_trace(
    actor: object,
    trace: ControlTrace,
    *,
    world: object | None = None,
    carla_module: object | None = None,
    tick_timeout_s: float = 2.0,
    limit: int | None = None,
) -> AppliedControlReplay:
    """Apply a bounded control trace to a CARLA-like actor.

    The helper accepts either a real CARLA actor or the tiny fake actor used by
    tests. Real CARLA receives ``VehicleControl`` when available; fake actors
    receive a plain mapping.
    """

    commands = trace.commands[:limit] if limit is not None else trace.commands
    applied = 0
    ticks = 0
    controls: list[dict[str, Any]] = []
    errors: list[str] = []
    for command in commands:
        payload = {
            "tick": command.tick,
            "throttle": command.throttle,
            "steer": command.steer,
            "brake": command.brake,
            "target_x": command.target_x,
            "target_y": command.target_y,
            "target_speed_mps": command.target_speed_mps,
        }
        try:
            actor.apply_control(_carla_control(carla_module, payload))
            applied += 1
            controls.append(payload)
            if world is not None:
                _tick_world(world, tick_timeout_s)
                ticks += 1
        except Exception as exc:
            errors.append(f"tick {command.tick}: {exc}")
            break
    return AppliedControlReplay(
        applied_count=applied,
        command_count=len(commands),
        tick_count=ticks,
        controls=tuple(controls),
        errors=tuple(errors),
    )


def replay_policy_decision(
    config: CarlaPolicyReplayConfig,
    *,
    actor: Any | None = None,
    world: object | None = None,
    carla_module: object | None = None,
) -> CarlaPolicyReplayResult:
    """Build and optionally apply cached replay controls to an actor-like object."""

    policy_id, trajectory = load_policy_decision_trajectory(config.decision_path)
    trace = trajectory_to_control_trace(
        trajectory,
        source_policy_id=policy_id,
        ego_pose=config.ego_pose,
        config=config.control_config,
    )
    applied = 0
    error: str | None = None
    applied_payload: dict[str, Any] | None = None
    if config.apply_to_actor and actor is not None:
        application = apply_control_trace(
            actor,
            trace,
            world=world,
            carla_module=carla_module,
        )
        applied = application.applied_count
        applied_payload = application.to_jsonable()
        if application.errors:
            error = "Policy replay actor application failed: " + "; ".join(application.errors)
    return CarlaPolicyReplayResult(
        decision_path=config.decision_path,
        source_policy_id=policy_id,
        command_count=len(trace.commands),
        applied_count=applied,
        closed_loop_control=trace.closed_loop_control,
        safety_clamps=trace.safety_clamps,
        cleanup_complete=True,
        dry_run=not config.apply_to_actor,
        trace={
            **trace.to_jsonable(),
            "application": applied_payload,
        },
        error=error,
    )


def write_carla_policy_replay(
    run_dir: Path,
    result: CarlaPolicyReplayResult,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = result.to_jsonable()
    json_path = run_dir / "carla_policy_replay.json"
    report_path = run_dir / "carla_policy_replay.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# CARLA Policy Replay",
        "",
        f"- source_policy_id: `{payload['source_policy_id']}`",
        f"- decision_path: `{payload['decision_path']}`",
        f"- command_count: `{payload['command_count']}`",
        f"- applied_count: `{payload['applied_count']}`",
        f"- closed_loop_control: `{payload['closed_loop_control']}`",
        f"- trajectory_frame: `{payload['trace'].get('trajectory_frame', 'unknown')}`",
        f"- dry_run: `{payload['dry_run']}`",
        f"- cleanup_complete: `{payload['cleanup_complete']}`",
    ]
    if payload.get("error"):
        lines.append(f"- error: `{payload['error']}`")
    clamps = list(payload.get("safety_clamps", []))
    lines.extend(["", "## Safety Clamps", ""])
    lines.extend(f"- {clamp}" for clamp in clamps) if clamps else lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _carla_control(carla_module: object | None, payload: dict[str, Any]) -> object:
    if carla_module is not None and hasattr(carla_module, "VehicleControl"):
        return carla_module.VehicleControl(
            throttle=float(payload["throttle"]),
            steer=float(payload["steer"]),
            brake=float(payload["brake"]),
        )
    return {
        "throttle": float(payload["throttle"]),
        "steer": float(payload["steer"]),
        "brake": float(payload["brake"]),
    }


def _tick_world(world: object, timeout_s: float) -> None:
    if hasattr(world, "tick"):
        world.tick()
        return
    if hasattr(world, "wait_for_tick"):
        try:
            world.wait_for_tick(timeout_s)
        except TypeError:
            world.wait_for_tick()


__all__ = [
    "AppliedControlReplay",
    "apply_control_trace",
    "CarlaPolicyReplayConfig",
    "CarlaPolicyReplayResult",
    "replay_policy_decision",
    "write_carla_policy_replay",
]
