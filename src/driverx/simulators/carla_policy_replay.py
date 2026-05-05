"""Replay cached policy trajectories as conservative CARLA control traces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.policies.trajectory_control import (
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


def replay_policy_decision(
    config: CarlaPolicyReplayConfig,
    *,
    actor: Any | None = None,
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
    if config.apply_to_actor and actor is not None:
        try:
            for command in trace.commands:
                actor.apply_control(
                    {
                        "throttle": command.throttle,
                        "steer": command.steer,
                        "brake": command.brake,
                    }
                )
                applied += 1
        except Exception as exc:
            error = f"Policy replay actor application failed: {exc}"
    return CarlaPolicyReplayResult(
        decision_path=config.decision_path,
        source_policy_id=policy_id,
        command_count=len(trace.commands),
        applied_count=applied,
        closed_loop_control=trace.closed_loop_control,
        safety_clamps=trace.safety_clamps,
        cleanup_complete=True,
        dry_run=not config.apply_to_actor,
        trace=trace.to_jsonable(),
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


__all__ = [
    "CarlaPolicyReplayConfig",
    "CarlaPolicyReplayResult",
    "replay_policy_decision",
    "write_carla_policy_replay",
]
