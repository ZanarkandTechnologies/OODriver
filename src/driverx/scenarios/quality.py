"""Quality gates for generated OOD scenario evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScenarioQualityThresholds:
    min_duration_s: float = 5.0
    min_frame_count: int = 0
    max_min_distance_m: float = 6.0
    min_visible_actor_count: float = 0.0
    max_ood_step_m: float | None = None
    require_video: bool = True
    require_road_alignment: bool = True
    require_conflict: bool = True

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "min_duration_s": self.min_duration_s,
            "min_frame_count": self.min_frame_count,
            "max_min_distance_m": self.max_min_distance_m,
            "min_visible_actor_count": self.min_visible_actor_count,
            "max_ood_step_m": self.max_ood_step_m,
            "require_video": self.require_video,
            "require_road_alignment": self.require_road_alignment,
            "require_conflict": self.require_conflict,
        }


@dataclass(frozen=True)
class ScenarioQualityReport:
    scenario_id: str
    case_id: str
    passes: bool
    status: str
    metrics: dict[str, float | bool | str | None]
    blockers: list[str]
    warnings: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "case_id": self.case_id,
            "passes": self.passes,
            "status": self.status,
            "metrics": self.metrics,
            "blockers": self.blockers,
            "warnings": self.warnings,
        }


def evaluate_scenario_quality(
    case: dict[str, Any],
    thresholds: ScenarioQualityThresholds | None = None,
) -> ScenarioQualityReport:
    limits = thresholds or ScenarioQualityThresholds()
    case_id = str(case.get("case_id") or case.get("scenario_id") or "unknown-case")
    scenario_id = str(case.get("recipe_id") or case.get("scenario_id") or case_id)
    blockers: list[str] = []
    warnings: list[str] = []
    duration_s = _float(case.get("duration_s"), 0.0)
    frame_count = int(_float(case.get("frame_count"), 0.0))
    min_distance = _optional_float(case.get("min_distance_m"))
    has_video = bool(case.get("video_path")) or str(case.get("video_status")) == "passed"
    road_alignment_path = _optional_str(case.get("road_alignment_path"))
    road_aligned = _road_aligned(road_alignment_path)
    fidelity_metrics = _mapping(case.get("fidelity_metrics"))
    visible_actor_count = _optional_float(fidelity_metrics.get("visible_actor_count_mean"))
    max_ood_step = _optional_float(fidelity_metrics.get("max_ood_step_m"))

    if duration_s < limits.min_duration_s:
        blockers.append(f"duration_s {duration_s:.2f} below {limits.min_duration_s:.2f}")
    if frame_count < limits.min_frame_count:
        blockers.append(f"frame_count {frame_count} below {limits.min_frame_count}")
    if limits.require_video and not has_video:
        blockers.append("video evidence is required but missing")
    elif not has_video:
        warnings.append("video evidence is missing")
    if limits.require_road_alignment and road_aligned is not True:
        blockers.append("road alignment is required but missing or failed")
    elif road_aligned is not True:
        warnings.append("road alignment is unknown or failed")
    if limits.require_conflict:
        if min_distance is None:
            blockers.append("min_distance_m is required for conflict validation")
        elif min_distance > limits.max_min_distance_m:
            blockers.append(
                f"min_distance_m {min_distance:.2f} exceeds {limits.max_min_distance_m:.2f}"
            )
    if limits.min_visible_actor_count > 0:
        if visible_actor_count is None:
            blockers.append("visible_actor_count_mean is required for density validation")
        elif visible_actor_count < limits.min_visible_actor_count:
            blockers.append(
                f"visible_actor_count_mean {visible_actor_count:.2f} below {limits.min_visible_actor_count:.2f}"
            )
    if limits.max_ood_step_m is not None:
        if max_ood_step is None:
            blockers.append("max_ood_step_m is required for smoothness validation")
        elif max_ood_step > limits.max_ood_step_m:
            blockers.append(f"max_ood_step_m {max_ood_step:.2f} exceeds {limits.max_ood_step_m:.2f}")

    status = "passed" if not blockers else "blocked"
    return ScenarioQualityReport(
        scenario_id=scenario_id,
        case_id=case_id,
        passes=not blockers,
        status=status,
        metrics={
            "duration_s": duration_s,
            "frame_count": frame_count,
            "min_distance_m": min_distance,
            "has_video": has_video,
            "road_aligned": road_aligned,
            "visible_actor_count_mean": visible_actor_count,
            "max_ood_step_m": max_ood_step,
        },
        blockers=blockers,
        warnings=warnings,
    )


def select_quality_passed_cases(
    reports: list[ScenarioQualityReport],
    limit: int | None = None,
) -> list[str]:
    passed = [report.case_id for report in reports if report.passes]
    return passed[:limit] if limit is not None else passed


def write_scenario_quality_outputs(
    reports: list[ScenarioQualityReport],
    output_dir: Path,
    *,
    thresholds: ScenarioQualityThresholds | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "scenario_quality_summary.json"
    report_path = output_dir / "scenario_quality_summary.md"
    payload = {
        "thresholds": (thresholds or ScenarioQualityThresholds()).to_jsonable(),
        "report_count": len(reports),
        "passed_count": sum(1 for report in reports if report.passes),
        "blocked_count": sum(1 for report in reports if not report.passes),
        "passed_case_ids": select_quality_passed_cases(reports),
        "reports": [report.to_jsonable() for report in reports],
        "json_path": str(json_path),
        "report_path": str(report_path),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_quality_markdown(payload), encoding="utf-8")
    return payload


def _road_aligned(path: str | None) -> bool | None:
    if not path:
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict) and "passes" in payload:
        return bool(payload["passes"])
    return None


def _quality_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Scenario Quality Gates",
        "",
        f"- reports: `{payload.get('report_count')}`",
        f"- passed: `{payload.get('passed_count')}`",
        f"- blocked: `{payload.get('blocked_count')}`",
        "",
        "| case | passes | duration | frames | min distance | visible actors | max OOD step | blockers |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for report in list(payload.get("reports", [])):
        metrics = dict(report.get("metrics", {}))
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(report.get("case_id")),
                    _cell(report.get("passes")),
                    _cell(metrics.get("duration_s")),
                    _cell(metrics.get("frame_count")),
                    _cell(metrics.get("min_distance_m")),
                    _cell(metrics.get("visible_actor_count_mean")),
                    _cell(metrics.get("max_ood_step_m")),
                    _cell("; ".join(str(item) for item in list(report.get("blockers", [])))),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _cell(value: object) -> str:
    return "" if value is None else str(value).replace("|", "\\|")


def _float(value: object, default: float) -> float:
    parsed = _optional_float(value)
    return default if parsed is None else parsed


def _optional_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


__all__ = [
    "ScenarioQualityReport",
    "ScenarioQualityThresholds",
    "evaluate_scenario_quality",
    "select_quality_passed_cases",
    "write_scenario_quality_outputs",
]
