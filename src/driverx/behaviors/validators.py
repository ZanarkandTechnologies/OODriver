"""Behavior solvability and conflict validators."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.behaviors.library import simulate_behavior
from driverx.behaviors.types import BehaviorPlan, BehaviorTrace


@dataclass(frozen=True)
class BehaviorConstraints:
    ego_speed_mps: float = 4.0
    max_abs_lateral_m: float = 6.0
    max_speed_mps: float = 22.0
    max_acceleration_mps2: float = 8.0
    max_deceleration_mps2: float = 9.0
    conflict_distance_m: float = 1.5
    min_conflict_time_s: float = 0.5


@dataclass(frozen=True)
class BehaviorValidationReport:
    behavior_id: str
    passes: bool
    metrics: dict[str, float]
    blockers: list[str]
    warnings: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "behavior_id": self.behavior_id,
            "passes": self.passes,
            "metrics": self.metrics,
            "blockers": self.blockers,
            "warnings": self.warnings,
        }


def validate_behavior_plan(
    plan: BehaviorPlan,
    constraints: BehaviorConstraints | None = None,
) -> BehaviorValidationReport:
    return validate_behavior_trace(simulate_behavior(plan), constraints or BehaviorConstraints())


def validate_behavior_trace(
    trace: BehaviorTrace,
    constraints: BehaviorConstraints,
) -> BehaviorValidationReport:
    samples = trace.samples
    blockers: list[str] = []
    warnings: list[str] = []
    if not samples:
        blockers.append("Behavior trace has no samples.")
        return BehaviorValidationReport(trace.plan.behavior_id, False, {}, blockers, warnings)

    max_abs_lateral = max(abs(sample.y_m) for sample in samples)
    max_speed = max(sample.speed_mps for sample in samples)
    max_accel = 0.0
    max_decel = 0.0
    min_distance = math.inf
    time_to_conflict: float | None = None
    for left, right in zip(samples, samples[1:]):
        dt = max(right.t_s - left.t_s, 1e-6)
        acceleration = (right.speed_mps - left.speed_mps) / dt
        max_accel = max(max_accel, acceleration)
        max_decel = max(max_decel, -acceleration)
    for sample in samples:
        ego_x = constraints.ego_speed_mps * sample.t_s
        distance = math.dist((ego_x, 0.0), (sample.x_m, sample.y_m))
        min_distance = min(min_distance, distance)
        if distance <= constraints.conflict_distance_m and time_to_conflict is None:
            time_to_conflict = sample.t_s

    if max_abs_lateral > constraints.max_abs_lateral_m:
        blockers.append(
            f"max_abs_lateral_m {max_abs_lateral:.2f} exceeds {constraints.max_abs_lateral_m:.2f}"
        )
    if max_speed > constraints.max_speed_mps:
        blockers.append(f"max_speed_mps {max_speed:.2f} exceeds {constraints.max_speed_mps:.2f}")
    if max_accel > constraints.max_acceleration_mps2:
        blockers.append(
            f"max_acceleration_mps2 {max_accel:.2f} exceeds {constraints.max_acceleration_mps2:.2f}"
        )
    if max_decel > constraints.max_deceleration_mps2:
        blockers.append(
            f"max_deceleration_mps2 {max_decel:.2f} exceeds {constraints.max_deceleration_mps2:.2f}"
        )
    if time_to_conflict is None:
        warnings.append("No ego/OOD conflict within configured distance.")
    elif time_to_conflict < constraints.min_conflict_time_s:
        blockers.append(
            f"time_to_conflict_s {time_to_conflict:.2f} is too early for a solvable setup"
        )

    metrics = {
        **trace.metrics,
        "max_abs_lateral_m": round(max_abs_lateral, 4),
        "max_speed_mps": round(max_speed, 4),
        "max_acceleration_mps2": round(max_accel, 4),
        "max_deceleration_mps2": round(max_decel, 4),
        "min_ego_distance_m": round(min_distance, 4) if min_distance != math.inf else -1.0,
        "time_to_conflict_s": round(time_to_conflict, 4) if time_to_conflict is not None else -1.0,
    }
    return BehaviorValidationReport(
        behavior_id=trace.plan.behavior_id,
        passes=not blockers,
        metrics=metrics,
        blockers=blockers,
        warnings=warnings,
    )


def write_behavior_validation_report(
    output_dir: Path,
    reports: list[BehaviorValidationReport],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "behavior_validation.json"
    report_path = output_dir / "behavior_validation.md"
    payload = {
        "report_count": len(reports),
        "passing_count": sum(1 for report in reports if report.passes),
        "blocked_count": sum(1 for report in reports if not report.passes),
        "reports": [report.to_jsonable() for report in reports],
        "json_path": str(json_path),
        "report_path": str(report_path),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return payload


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Behavior Validation",
        "",
        f"- reports: `{payload.get('report_count')}`",
        f"- passing: `{payload.get('passing_count')}`",
        f"- blocked: `{payload.get('blocked_count')}`",
        "",
        "| behavior | passes | min distance | time to conflict | blockers |",
        "|---|---|---|---|---|",
    ]
    for report in list(payload.get("reports", [])):
        metrics = dict(report.get("metrics", {}))
        lines.append(
            "| "
            + " | ".join(
                [
                    str(report.get("behavior_id", "")),
                    str(report.get("passes", "")),
                    str(metrics.get("min_ego_distance_m", "")),
                    str(metrics.get("time_to_conflict_s", "")),
                    "; ".join(str(item) for item in list(report.get("blockers", []))),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "BehaviorConstraints",
    "BehaviorValidationReport",
    "validate_behavior_plan",
    "validate_behavior_trace",
    "write_behavior_validation_report",
]
