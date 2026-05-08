"""Integration readiness score for hardened closed-loop Alpamayo/CARLA traces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.evaluation.closed_loop_control_score import score_closed_loop_control


@dataclass(frozen=True)
class ClosedLoopIntegrationScoreReport:
    status: str
    closed_loop_integration_score: float
    threshold: float
    subscores: dict[str, float]
    blockers: list[str]
    evidence_paths: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "closed_loop_integration_score": self.closed_loop_integration_score,
            "threshold": self.threshold,
            "subscores": dict(self.subscores),
            "blockers": list(self.blockers),
            "evidence_paths": list(self.evidence_paths),
        }


def score_closed_loop_integration(trace_path: Path, *, threshold: float = 85.0) -> ClosedLoopIntegrationScoreReport:
    trace = _load(trace_path)
    base = score_closed_loop_control(trace_path, threshold=72.0)
    steps = [dict(item) for item in list(trace.get("steps", [])) if isinstance(item, dict)]
    subscores = {
        "recurrence": min(base.components.get("recurrence", 0.0), 20.0),
        "sensor_sync": _sensor_sync_score(steps),
        "control_safety": _control_safety_score(steps),
        "inference_handoff": _inference_score(steps),
        "claim_honesty": min(base.components.get("claim_honesty", 0.0), 10.0),
        "artifact_completeness": _artifact_score(steps),
    }
    score = round(sum(subscores.values()), 4)
    blockers = list(base.blockers)
    if score < threshold:
        blockers.append(f"closed_loop_integration_score {score:.4f} below {threshold:.4f}")
    if subscores["sensor_sync"] < 15.0:
        blockers.append("missing synchronized sensor frame provenance")
    if subscores["control_safety"] < 15.0:
        blockers.append("missing or failing control safety reports")
    status = "passed" if not blockers and score >= threshold else "blocked"
    return ClosedLoopIntegrationScoreReport(
        status=status,
        closed_loop_integration_score=score,
        threshold=threshold,
        subscores=subscores,
        blockers=_dedupe(blockers),
        evidence_paths=_evidence_paths(trace_path, steps),
    )


def write_closed_loop_integration_score(run_dir: Path, report: ClosedLoopIntegrationScoreReport) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_jsonable()
    json_path = run_dir / "closed_loop_integration_score.json"
    report_path = run_dir / "closed_loop_integration_score.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("closed-loop trace must be a JSON object")
    return payload


def _sensor_sync_score(steps: list[dict[str, Any]]) -> float:
    if not steps:
        return 0.0
    ok = sum(1 for step in steps if len(list(step.get("sensor_frame_ids", []))) >= 3 or step.get("checkpoint_path"))
    return ok / len(steps) * 20.0


def _control_safety_score(steps: list[dict[str, Any]]) -> float:
    if not steps:
        return 0.0
    ok = 0
    for step in steps:
        safety = step.get("safety_report")
        if isinstance(safety, dict) and not safety.get("lane_departure_proxy") and not safety.get("unsafe_control_conflict"):
            ok += 1
    return ok / len(steps) * 20.0


def _inference_score(steps: list[dict[str, Any]]) -> float:
    if not steps:
        return 0.0
    ok = sum(1 for step in steps if step.get("inference_result_path") or step.get("prediction_path"))
    return ok / len(steps) * 15.0


def _artifact_score(steps: list[dict[str, Any]]) -> float:
    if not steps:
        return 0.0
    ok = sum(1 for step in steps if step.get("control_trace_path") and (step.get("prediction_path") or step.get("inference_result_path")))
    return ok / len(steps) * 15.0


def _evidence_paths(trace_path: Path, steps: list[dict[str, Any]]) -> list[str]:
    paths = [str(trace_path)]
    for step in steps:
        for key in ("checkpoint_path", "prediction_path", "inference_result_path", "control_trace_path"):
            value = step.get(key)
            if value:
                paths.append(str(value))
    return _dedupe(paths)


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Closed-Loop Integration Score",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Score: `{payload.get('closed_loop_integration_score')}`",
        f"- Threshold: `{payload.get('threshold')}`",
        "",
        "## Subscores",
        "",
    ]
    for key, value in dict(payload.get("subscores", {})).items():
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
    "ClosedLoopIntegrationScoreReport",
    "score_closed_loop_integration",
    "write_closed_loop_integration_score",
]
