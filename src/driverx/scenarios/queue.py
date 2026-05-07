"""OODrive scenario queue artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.scenarios.studio_db import ScenarioStudioDb


@dataclass(frozen=True)
class QueueBuildOptions:
    accept: str = "top:3"
    policy_targets: tuple[str, ...] = ("mock", "carla-autopilot", "alpamayo-trajectory")


@dataclass(frozen=True)
class ScenarioDatasetQueue:
    queue_id: str
    source_db_path: str
    records: tuple[dict[str, Any], ...]
    claim_boundaries: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "queue_id": self.queue_id,
            "source_db_path": self.source_db_path,
            "records": [dict(record) for record in self.records],
            "claim_boundaries": list(self.claim_boundaries),
        }


def build_scenario_dataset_queue(
    db: ScenarioStudioDb,
    *,
    db_path: Path,
    options: QueueBuildOptions | None = None,
) -> ScenarioDatasetQueue:
    opts = options or QueueBuildOptions()
    selected_ids = _selected_candidate_ids(db, opts.accept)
    curation_by_id = {str(row.get("candidate_id")): row for row in db.curation}
    records: list[dict[str, Any]] = []
    for index, candidate in enumerate(db.candidates):
        candidate_id = str(candidate.get("candidate_id", ""))
        curation = curation_by_id.get(candidate_id, {})
        selected = candidate_id in selected_ids
        run_status = "needs_runtime" if selected else _non_selected_status(curation)
        records.append(
            {
                "scenario_id": candidate_id,
                "candidate_id": candidate_id,
                "plan_id": candidate.get("plan_id"),
                "curation_status": curation.get("curation_status", "unknown"),
                "run_status": run_status,
                "priority": index + 1 if selected else 9999,
                "score": curation.get("score"),
                "policy_targets": list(opts.policy_targets) if selected else [],
                "memory_query": _candidate_memory_query(candidate),
                "next_command": _next_command(db_path, candidate_id, opts.policy_targets[0])
                if selected and opts.policy_targets
                else "",
            }
        )
    return ScenarioDatasetQueue(
        queue_id=f"{db.run_id}-queue",
        source_db_path=str(db_path),
        records=tuple(records),
        claim_boundaries=(
            "scenario_queue_database_view=true",
            "queue_selection_is_heuristic=true",
            "closed_loop_carla_execution=false_until_run_manifest_proves_it",
        ),
    )


def write_scenario_dataset_queue(run_dir: Path, queue: ScenarioDatasetQueue) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = queue.to_jsonable()
    json_path = run_dir / "scenario_dataset_queue.json"
    markdown_path = run_dir / "scenario_dataset_queue.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(_render_queue_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(markdown_path)}


def _selected_candidate_ids(db: ScenarioStudioDb, accept: str) -> set[str]:
    curation = [
        row
        for row in db.curation
        if str(row.get("curation_status")) in {"accept", "accept_partial", "needs_rerun"}
    ]
    if accept == "all-accepted":
        return {str(row.get("candidate_id")) for row in curation}
    if accept.startswith("top:"):
        try:
            count = max(0, int(accept.split(":", 1)[1]))
        except ValueError as exc:
            raise ValueError(f"Invalid queue selector: {accept}") from exc
        ranked = sorted(curation, key=lambda row: float(row.get("score") or 0.0), reverse=True)
        return {str(row.get("candidate_id")) for row in ranked[:count]}
    explicit = {item.strip() for item in accept.split(",") if item.strip()}
    candidate_ids = {str(candidate.get("candidate_id")) for candidate in db.candidates}
    missing = sorted(explicit - candidate_ids)
    if missing:
        raise ValueError(f"Queue selector referenced unknown candidate ids: {', '.join(missing)}")
    return explicit


def _non_selected_status(curation: dict[str, Any]) -> str:
    status = str(curation.get("curation_status", "unknown"))
    if status.startswith("reject"):
        return "blocked"
    return "ready"


def _candidate_memory_query(candidate: dict[str, Any]) -> list[str]:
    recipe = candidate.get("compiled_recipe")
    if isinstance(recipe, dict):
        return [str(item) for item in list(recipe.get("memory_query", []))]
    return []


def _next_command(db_path: Path, scenario_id: str, policy: str) -> str:
    return (
        "PYTHONPATH=src python3 -m driverx oodrive run "
        f"--db {db_path} --scenario-id {scenario_id} --policy {policy}"
    )


def _render_queue_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OODrive Scenario Dataset Queue",
        "",
        f"- Queue: `{payload.get('queue_id')}`",
        f"- Source DB: `{payload.get('source_db_path')}`",
        "",
        "| scenario | curation | run status | priority | policies |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in payload.get("records", []):
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(record.get("scenario_id")),
                    _cell(record.get("curation_status")),
                    _cell(record.get("run_status")),
                    _cell(record.get("priority")),
                    _cell(", ".join(list(record.get("policy_targets", [])))),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Claim Boundaries", ""])
    for boundary in payload.get("claim_boundaries", []):
        lines.append(f"- `{boundary}`")
    lines.append("")
    return "\n".join(lines)


def _cell(value: Any) -> str:
    return "" if value is None else str(value).replace("|", "\\|")


__all__ = [
    "QueueBuildOptions",
    "ScenarioDatasetQueue",
    "build_scenario_dataset_queue",
    "write_scenario_dataset_queue",
]
