"""OODriver policy evaluation records."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PolicyEvaluationRecord:
    evaluation_id: str
    scenario_id: str
    policy: str
    reasoning_mode: str
    memory_mode: str
    cot_summary: str | None = None
    trajectory_summary: dict[str, Any] = field(default_factory=dict)
    control_trace_path: str | None = None
    latency_ms: float | None = None
    memory_ids: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "scenario_id": self.scenario_id,
            "policy": self.policy,
            "reasoning_mode": self.reasoning_mode,
            "memory_mode": self.memory_mode,
            "cot_summary": self.cot_summary,
            "trajectory_summary": dict(self.trajectory_summary),
            "control_trace_path": self.control_trace_path,
            "latency_ms": self.latency_ms,
            "memory_ids": list(self.memory_ids),
            "claim_boundaries": list(self.claim_boundaries),
            "blockers": list(self.blockers),
        }


def write_policy_evaluation(run_dir: Path, record: PolicyEvaluationRecord) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = record.to_jsonable()
    json_path = run_dir / "policy_evaluation.json"
    markdown_path = run_dir / "policy_evaluation.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(markdown_path)}


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OODriver Policy Evaluation",
        "",
        f"- Evaluation: `{payload.get('evaluation_id')}`",
        f"- Scenario: `{payload.get('scenario_id')}`",
        f"- Policy: `{payload.get('policy')}`",
        f"- Reasoning mode: `{payload.get('reasoning_mode')}`",
        f"- Memory mode: `{payload.get('memory_mode')}`",
        f"- Latency: `{payload.get('latency_ms')}`",
        "",
    ]
    if payload.get("cot_summary"):
        lines.extend(["## Reasoning", "", str(payload["cot_summary"]), ""])
    lines.extend(["## Claim Boundaries", ""])
    for boundary in payload.get("claim_boundaries", []):
        lines.append(f"- `{boundary}`")
    blockers = payload.get("blockers", [])
    if blockers:
        lines.extend(["", "## Blockers", ""])
        for blocker in blockers:
            lines.append(f"- {blocker}")
    lines.append("")
    return "\n".join(lines)


__all__ = ["PolicyEvaluationRecord", "write_policy_evaluation"]
