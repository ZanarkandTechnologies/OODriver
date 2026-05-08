"""Score whether a CARLA/Alpamayo trace proves honest closed-loop control."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.policies.closed_loop_types import normalize_closed_loop_trace, validate_closed_loop_trace


@dataclass(frozen=True)
class ClosedLoopControlScoreReport:
    status: str
    closed_loop_score: float
    threshold: float
    mode: str
    components: dict[str, float]
    blockers: list[str]
    warnings: list[str]
    claim_boundaries: list[str]
    trace_path: str

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "closed_loop_score": self.closed_loop_score,
            "threshold": self.threshold,
            "mode": self.mode,
            "components": dict(self.components),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "claim_boundaries": list(self.claim_boundaries),
            "trace_path": self.trace_path,
        }


def load_closed_loop_trace(trace_path: Path) -> dict[str, Any]:
    payload = json.loads(trace_path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Closed-loop trace must be a JSON object: {trace_path}")
    return normalize_closed_loop_trace(payload)


def score_closed_loop_control(trace_path: Path, *, threshold: float = 72.0) -> ClosedLoopControlScoreReport:
    trace = load_closed_loop_trace(trace_path)
    validation = validate_closed_loop_trace(trace)
    components = _components(trace, validation.to_jsonable())
    score = round(sum(components.values()), 4)
    blockers = list(validation.blockers)
    if score < threshold:
        blockers.append(f"closed_loop_score {score:.4f} below {threshold:.4f}")
    status = "passed" if not blockers and score >= threshold else "blocked"
    return ClosedLoopControlScoreReport(
        status=status,
        closed_loop_score=score,
        threshold=threshold,
        mode=str(trace.get("mode", "none")),
        components=components,
        blockers=_dedupe(blockers),
        warnings=list(validation.warnings),
        claim_boundaries=[str(item) for item in list(trace.get("claim_boundaries", []))],
        trace_path=str(trace_path),
    )


def write_closed_loop_control_score(run_dir: Path, report: ClosedLoopControlScoreReport) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_jsonable()
    json_path = run_dir / "closed_loop_control_score.json"
    report_path = run_dir / "closed_loop_control_score.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _components(trace: dict[str, Any], validation: dict[str, Any]) -> dict[str, float]:
    steps = [dict(item) for item in list(trace.get("steps", [])) if isinstance(item, dict)]
    mode = str(trace.get("mode", "none"))
    recurrence = min(float(validation.get("recurrence_count", 0)) / 2.0, 1.0) * 25.0
    controls = min(float(validation.get("applied_control_count", 0)) / 8.0, 1.0) * 15.0
    observations = min(float(validation.get("observed_after_action_count", 0)) / max(len(steps), 1), 1.0) * 15.0
    artifacts = _artifact_score(steps)
    safety = _safety_score(steps)
    claims = _claim_score(trace, mode)
    mode_bonus = {"none": 0.0, "cached_replay": 5.0, "paused_receding_horizon": 10.0, "real_time": 15.0}.get(mode, 0.0)
    return {
        "recurrence": round(recurrence, 4),
        "applied_controls": round(controls, 4),
        "post_action_observations": round(observations, 4),
        "artifact_traceability": round(artifacts, 4),
        "control_safety": round(safety, 4),
        "claim_honesty": round(claims, 4),
        "mode_bonus": round(mode_bonus, 4),
    }


def _artifact_score(steps: list[dict[str, Any]]) -> float:
    if not steps:
        return 0.0
    total = 0.0
    for step in steps:
        if step.get("prediction_path") or step.get("inference_result_path"):
            total += 1.0
        if step.get("control_trace_path"):
            total += 1.0
        if step.get("checkpoint_path") or step.get("sensor_frame_ids"):
            total += 1.0
    return min(total / (len(steps) * 3.0), 1.0) * 15.0


def _safety_score(steps: list[dict[str, Any]]) -> float:
    if not steps:
        return 0.0
    ok = 0
    for step in steps:
        safety = step.get("safety_report")
        if isinstance(safety, dict) and not safety.get("lane_departure_proxy") and not safety.get("unsafe_control_conflict"):
            ok += 1
    return ok / len(steps) * 10.0


def _claim_score(trace: dict[str, Any], mode: str) -> float:
    claims = {str(item) for item in list(trace.get("claim_boundaries", []))}
    score = 0.0
    if f"closed_loop_vla_control={mode if mode != 'none' else 'false'}" in claims:
        score += 5.0
    if mode != "real_time" and "real_time_vla_control=false" in claims:
        score += 5.0
    if mode == "real_time" and "real_time_vla_control=true" in claims:
        score += 5.0
    return min(score, 10.0)


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Closed-Loop Control Score",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Score: `{payload.get('closed_loop_score')}`",
        f"- Threshold: `{payload.get('threshold')}`",
        f"- Mode: `{payload.get('mode')}`",
        "",
        "## Components",
        "",
    ]
    for key, value in dict(payload.get("components", {})).items():
        lines.append(f"- `{key}`: `{value}`")
    blockers = list(payload.get("blockers", []))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in blockers)
    lines.append("")
    return "\n".join(lines)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


__all__ = [
    "ClosedLoopControlScoreReport",
    "load_closed_loop_trace",
    "score_closed_loop_control",
    "write_closed_loop_control_score",
]
