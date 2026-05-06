"""Scenario-linked Alpamayo reasoning report for generated CARLA OOD scenes."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AlpamayoOodSceneInputs:
    package_path: Path
    policy_decision_path: Path | None = None
    prediction_path: Path | None = None
    video_evidence_path: Path | None = None
    scenario_report_path: Path | None = None


def build_alpamayo_ood_scene_report(
    run_dir: Path,
    inputs: AlpamayoOodSceneInputs,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    package = _load_json(inputs.package_path)
    decision_payload = _load_json(inputs.policy_decision_path) if inputs.policy_decision_path else {}
    prediction = _load_json(inputs.prediction_path) if inputs.prediction_path else {}
    decision = _extract_decision(decision_payload)
    trajectory = _trajectory_points(decision)
    video = _load_json(inputs.video_evidence_path) if inputs.video_evidence_path else {}
    scenario = _load_json(inputs.scenario_report_path) if inputs.scenario_report_path else {}
    scenario_id = _scenario_id(package, scenario, video, decision)
    identities = _evidence_identities(package, scenario, video)
    linkage_warnings = _linkage_warnings(identities, scenario, video)
    payload = {
        "open_loop_policy_evaluation": True,
        "closed_loop_control": False,
        "scenario_id": scenario_id,
        "package_scenario_id": identities["package_scenario_id"],
        "scenario_report_id": identities["scenario_report_id"],
        "video_scenario_id": identities["video_scenario_id"],
        "frame_name": package.get("frame_name"),
        "map_name": package.get("map_name"),
        "package_path": str(inputs.package_path),
        "policy_decision_path": str(inputs.policy_decision_path) if inputs.policy_decision_path else None,
        "prediction_path": str(inputs.prediction_path) if inputs.prediction_path else None,
        "video_evidence_path": str(inputs.video_evidence_path) if inputs.video_evidence_path else None,
        "scenario_report_path": str(inputs.scenario_report_path) if inputs.scenario_report_path else None,
        "model_id": _model_id(decision_payload, prediction),
        "latency_ms": _number(decision.get("latency_ms"))
        or _number(_mapping(decision_payload.get("prediction_summary")).get("latency_ms"))
        or _number(prediction.get("latency_ms")),
        "vram_peak_mb": _number(_mapping(_mapping(decision.get("action")).get("control")).get("vram_peak_mb"))
        or _number(_mapping(decision_payload.get("prediction_summary")).get("vram_peak_mb"))
        or _number(prediction.get("vram_peak_mb")),
        "cot_snippet": _cot_snippet(decision, decision_payload, prediction),
        "trajectory_summary": _trajectory_summary(trajectory),
        "trajectory_points_xy": trajectory,
        "video": _compact_video(video),
        "claim_boundaries": [
            "alpamayo_open_loop_policy_evaluation=true",
            "closed_loop_carla_control=false",
            "model_weights_frozen=true",
        ],
        "linkage_warnings": linkage_warnings,
        "setup_blocker": _setup_blocker(inputs, decision),
    }
    return write_alpamayo_ood_scene_report(run_dir, payload)


def write_alpamayo_ood_scene_report(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    json_path = run_dir / "alpamayo_ood_scene.json"
    report_path = run_dir / "alpamayo_ood_scene.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {"value": payload}


def _extract_decision(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("policy_decision"), dict):
        return dict(payload["policy_decision"])
    if isinstance(payload.get("decision"), dict):
        return dict(payload["decision"])
    if payload.get("policy_id") is not None:
        return payload
    return {}


def _trajectory_points(decision: dict[str, Any]) -> list[list[float]] | None:
    points = _mapping(_mapping(decision.get("action")).get("trajectory")).get("points_xy")
    if not isinstance(points, list):
        return None
    parsed: list[list[float]] = []
    for point in points:
        if isinstance(point, (list, tuple)) and len(point) >= 2:
            parsed.append([float(point[0]), float(point[1])])
    return parsed or None


def _trajectory_summary(points: list[list[float]] | None) -> dict[str, Any] | None:
    if not points:
        return None
    distances = [
        math.dist((points[index - 1][0], points[index - 1][1]), (points[index][0], points[index][1]))
        for index in range(1, len(points))
    ]
    return {
        "point_count": len(points),
        "start_xy": points[0],
        "end_xy": points[-1],
        "path_length_m": round(sum(distances), 4),
    }


def _cot_snippet(
    decision: dict[str, Any],
    decision_payload: dict[str, Any],
    prediction: dict[str, Any],
) -> str | None:
    for value in (
        decision.get("reason_summary"),
        _mapping(decision_payload.get("prediction_summary")).get("cot_summary"),
        prediction.get("cot_summary"),
        prediction.get("cot"),
        _mapping(prediction.get("extra")).get("cot"),
    ):
        text = _first_text(value)
        if text:
            return text[:700]
    return None


def _first_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (list, tuple)):
        current = value
        while isinstance(current, (list, tuple)) and current:
            current = current[0]
        return str(current).strip() or None
    return str(value).strip() or None


def _model_id(decision_payload: dict[str, Any], prediction: dict[str, Any]) -> str:
    summary = _mapping(decision_payload.get("prediction_summary"))
    return str(
        summary.get("model_id")
        or prediction.get("model_id")
        or "nvidia/Alpamayo-1.5-10B"
    )


def _scenario_id(
    package: dict[str, Any],
    scenario: dict[str, Any],
    video: dict[str, Any],
    decision: dict[str, Any],
) -> str:
    for value in (
        package.get("scenario_id"),
        video.get("scenario_id"),
        scenario.get("scenario_id"),
        scenario.get("recipe_id"),
        package.get("frame_name"),
        _mapping(decision.get("intent")).get("scene_type"),
    ):
        if value:
            return str(value)
    return "alpamayo-ood-scene"


def _evidence_identities(
    package: dict[str, Any],
    scenario: dict[str, Any],
    video: dict[str, Any],
) -> dict[str, str | None]:
    return {
        "package_scenario_id": _first_str(package.get("scenario_id"), package.get("frame_name")),
        "scenario_report_id": _first_str(scenario.get("scenario_id"), scenario.get("recipe_id")),
        "video_scenario_id": _first_str(video.get("scenario_id")),
    }


def _linkage_warnings(
    identities: dict[str, str | None],
    scenario: dict[str, Any],
    video: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    scenario_status = scenario.get("status")
    if scenario_status not in {None, "passed", "partial"}:
        warnings.append(
            f"Scenario report status is {scenario_status!r}; this is setup evidence, not a successful generated-scene capture."
        )
    if video.get("source_kind") == "fixture":
        warnings.append(
            "Attached video evidence is source_kind='fixture'; it proves the overlay pipeline, not live CARLA capture."
        )
    ids = {
        key: value
        for key, value in identities.items()
        if value
    }
    unique = {str(value) for value in ids.values()}
    if len(unique) > 1:
        warnings.append(
            "Package, scenario report, and video ids do not all match; treat this as linked evidence rather than same-capture proof."
        )
    return warnings


def _compact_video(video: dict[str, Any]) -> dict[str, Any] | None:
    if not video:
        return None
    return {
        "status": video.get("status"),
        "scenario_id": video.get("scenario_id"),
        "source_kind": video.get("source_kind"),
        "claim_label": video.get("claim_label"),
        "video_path": video.get("video_path"),
        "duration_s": video.get("duration_s"),
        "worst_risk": video.get("worst_risk"),
    }


def _setup_blocker(inputs: AlpamayoOodSceneInputs, decision: dict[str, Any]) -> str | None:
    if inputs.policy_decision_path is None:
        return "Alpamayo policy decision was not supplied; run remote inference or pass --policy-decision."
    if not decision:
        return "Policy decision payload did not contain a DriverX policy_decision or policy_id."
    return None


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _first_str(*values: Any) -> str | None:
    for value in values:
        if value not in (None, ""):
            return str(value)
    return None


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Alpamayo OOD Scene",
        "",
        f"- scenario_id: `{payload.get('scenario_id')}`",
        f"- package_scenario_id: `{payload.get('package_scenario_id')}`",
        f"- scenario_report_id: `{payload.get('scenario_report_id')}`",
        f"- video_scenario_id: `{payload.get('video_scenario_id')}`",
        f"- open_loop_policy_evaluation: `{payload.get('open_loop_policy_evaluation')}`",
        f"- closed_loop_control: `{payload.get('closed_loop_control')}`",
        f"- model_id: `{payload.get('model_id')}`",
        f"- latency_ms: `{payload.get('latency_ms')}`",
        f"- vram_peak_mb: `{payload.get('vram_peak_mb')}`",
        f"- video_evidence_path: `{payload.get('video_evidence_path')}`",
        "",
    ]
    if payload.get("cot_snippet"):
        lines.extend(["## CoC Snippet", "", f"> {payload['cot_snippet']}", ""])
    if payload.get("trajectory_summary"):
        lines.extend(["## Trajectory Summary", ""])
        for key, value in dict(payload["trajectory_summary"]).items():
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
    lines.extend(["## Claim Boundaries", ""])
    for boundary in payload["claim_boundaries"]:
        lines.append(f"- `{boundary}`")
    if payload.get("linkage_warnings"):
        lines.extend(["", "## Linkage Warnings", ""])
        for warning in list(payload["linkage_warnings"]):
            lines.append(f"- {warning}")
    if payload.get("setup_blocker"):
        lines.extend(["", "## Blocker", "", f"- {payload['setup_blocker']}"])
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "AlpamayoOodSceneInputs",
    "build_alpamayo_ood_scene_report",
    "write_alpamayo_ood_scene_report",
]
