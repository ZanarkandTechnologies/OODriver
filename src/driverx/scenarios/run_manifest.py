"""OODriver run manifest records."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScenarioRunManifest:
    run_id: str
    scenario_id: str
    candidate_id: str
    policy: str
    runtime: str
    status: str
    artifacts: dict[str, str | None] = field(default_factory=dict)
    timings_ms: dict[str, float] = field(default_factory=dict)
    actions: list[dict[str, Any]] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "candidate_id": self.candidate_id,
            "policy": self.policy,
            "runtime": self.runtime,
            "status": self.status,
            "artifacts": dict(self.artifacts),
            "timings_ms": dict(self.timings_ms),
            "actions": list(self.actions),
            "claim_boundaries": list(self.claim_boundaries),
            "blockers": list(self.blockers),
        }


def write_run_manifest(run_dir: Path, manifest: ScenarioRunManifest) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = manifest.to_jsonable()
    json_path = run_dir / "run_manifest.json"
    markdown_path = run_dir / "run_manifest.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(markdown_path)}


def load_run_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Run manifest must be a JSON object: {path}")
    return payload


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OODriver Run Manifest",
        "",
        f"- Run: `{payload.get('run_id')}`",
        f"- Scenario: `{payload.get('scenario_id')}`",
        f"- Policy: `{payload.get('policy')}`",
        f"- Runtime: `{payload.get('runtime')}`",
        f"- Status: `{payload.get('status')}`",
        "",
        "## Artifacts",
        "",
    ]
    for key, value in dict(payload.get("artifacts", {})).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Claim Boundaries", ""])
    for boundary in payload.get("claim_boundaries", []):
        lines.append(f"- `{boundary}`")
    blockers = payload.get("blockers", [])
    if blockers:
        lines.extend(["", "## Blockers", ""])
        for blocker in blockers:
            lines.append(f"- {blocker}")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "ScenarioRunManifest",
    "load_run_manifest",
    "write_run_manifest",
]
