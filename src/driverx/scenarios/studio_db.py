"""JSON-backed OODriver scenario studio database."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCENARIO_STUDIO_DB_FILENAME = "scenario_studio_db.json"
SCENARIO_STUDIO_DB_REPORT_FILENAME = "scenario_studio_db.md"
SCENARIO_STUDIO_DB_SCHEMA_VERSION = "oodriver.studio-db.v1"
OODRIVER_PRODUCT_NAME = "OODriver"


@dataclass(frozen=True)
class ScenarioStudioDb:
    """Durable artifact index for one OODriver scenario generation run."""

    run_id: str
    product_name: str = OODRIVER_PRODUCT_NAME
    schema_version: str = SCENARIO_STUDIO_DB_SCHEMA_VERSION
    briefs: list[dict[str, Any]] = field(default_factory=list)
    plans: list[dict[str, Any]] = field(default_factory=list)
    candidates: list[dict[str, Any]] = field(default_factory=list)
    curation: list[dict[str, Any]] = field(default_factory=list)
    queue: list[dict[str, Any]] = field(default_factory=list)
    runs: list[dict[str, Any]] = field(default_factory=list)
    evaluations: list[dict[str, Any]] = field(default_factory=list)
    bundles: list[dict[str, Any]] = field(default_factory=list)
    exports: list[dict[str, Any]] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    command_log: list[dict[str, Any]] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "product_name": self.product_name,
            "run_id": self.run_id,
            "briefs": list(self.briefs),
            "plans": list(self.plans),
            "candidates": list(self.candidates),
            "curation": list(self.curation),
            "queue": list(self.queue),
            "runs": list(self.runs),
            "evaluations": list(self.evaluations),
            "bundles": list(self.bundles),
            "exports": list(self.exports),
            "artifacts": dict(self.artifacts),
            "command_log": list(self.command_log),
            "claim_boundaries": _dedupe(
                [
                    "product_name=OODriver",
                    "cli_is_database_control_plane=true",
                    "codex_is_ai_operator=true",
                    *self.claim_boundaries,
                ]
            ),
        }

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "ScenarioStudioDb":
        return cls(
            run_id=str(payload.get("run_id", "oodriver")),
            product_name=str(payload.get("product_name", OODRIVER_PRODUCT_NAME)),
            schema_version=str(payload.get("schema_version", SCENARIO_STUDIO_DB_SCHEMA_VERSION)),
            briefs=_list_of_dicts(payload.get("briefs")),
            plans=_list_of_dicts(payload.get("plans")),
            candidates=_list_of_dicts(payload.get("candidates")),
            curation=_list_of_dicts(payload.get("curation")),
            queue=_list_of_dicts(payload.get("queue")),
            runs=_list_of_dicts(payload.get("runs")),
            evaluations=_list_of_dicts(payload.get("evaluations")),
            bundles=_list_of_dicts(payload.get("bundles")),
            exports=_list_of_dicts(payload.get("exports")),
            artifacts=_string_dict(payload.get("artifacts")),
            command_log=_list_of_dicts(payload.get("command_log")),
            claim_boundaries=[str(item) for item in list(payload.get("claim_boundaries", []))],
        )


def studio_db_path(output_root: Path, run_id: str) -> Path:
    return output_root / run_id / SCENARIO_STUDIO_DB_FILENAME


def new_studio_db(run_id: str) -> ScenarioStudioDb:
    return ScenarioStudioDb(
        run_id=run_id,
        claim_boundaries=[
            "scenario_generation_ai_provider=false_until_codex_or_provider_records_briefs",
            "closed_loop_carla_execution=false_until_run_manifest_proves_it",
            "real_time_vla_control=false_until_run_manifest_proves_it",
        ],
    )


def load_studio_db(path: Path) -> ScenarioStudioDb:
    if not path.exists():
        raise FileNotFoundError(f"OODriver studio DB not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"OODriver studio DB must be a JSON object: {path}")
    db = ScenarioStudioDb.from_jsonable(payload)
    if db.schema_version != SCENARIO_STUDIO_DB_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported OODriver studio DB schema {db.schema_version}; "
            f"expected {SCENARIO_STUDIO_DB_SCHEMA_VERSION}."
        )
    return db


def write_studio_db(path: Path, db: ScenarioStudioDb) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = db.to_jsonable()
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path = path.with_name(SCENARIO_STUDIO_DB_REPORT_FILENAME)
    report_path.write_text(render_studio_db_markdown(payload), encoding="utf-8")
    return {**payload, "db_path": str(path), "report_path": str(report_path)}


def replace_db(
    db: ScenarioStudioDb,
    *,
    briefs: list[dict[str, Any]] | None = None,
    plans: list[dict[str, Any]] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    curation: list[dict[str, Any]] | None = None,
    queue: list[dict[str, Any]] | None = None,
    runs: list[dict[str, Any]] | None = None,
    evaluations: list[dict[str, Any]] | None = None,
    bundles: list[dict[str, Any]] | None = None,
    exports: list[dict[str, Any]] | None = None,
    artifacts: dict[str, str] | None = None,
    command_log: list[dict[str, Any]] | None = None,
    claim_boundaries: list[str] | None = None,
) -> ScenarioStudioDb:
    return ScenarioStudioDb(
        run_id=db.run_id,
        product_name=db.product_name,
        schema_version=db.schema_version,
        briefs=briefs if briefs is not None else list(db.briefs),
        plans=plans if plans is not None else list(db.plans),
        candidates=candidates if candidates is not None else list(db.candidates),
        curation=curation if curation is not None else list(db.curation),
        queue=queue if queue is not None else list(db.queue),
        runs=runs if runs is not None else list(db.runs),
        evaluations=evaluations if evaluations is not None else list(db.evaluations),
        bundles=bundles if bundles is not None else list(db.bundles),
        exports=exports if exports is not None else list(db.exports),
        artifacts=artifacts if artifacts is not None else dict(db.artifacts),
        command_log=command_log if command_log is not None else list(db.command_log),
        claim_boundaries=claim_boundaries if claim_boundaries is not None else list(db.claim_boundaries),
    )


def append_command(
    db: ScenarioStudioDb,
    *,
    command: str,
    status: str,
    artifacts: dict[str, str] | None = None,
    summary: Any | None = None,
) -> ScenarioStudioDb:
    entry = {
        "command": command,
        "status": status,
        "artifacts": dict(artifacts or {}),
    }
    if summary:
        entry["summary"] = summary
    return replace_db(db, command_log=[*db.command_log, entry])


def append_brief(db: ScenarioStudioDb, brief: dict[str, Any]) -> ScenarioStudioDb:
    existing_ids = {str(item.get("brief_id")) for item in db.briefs}
    if str(brief.get("brief_id")) in existing_ids:
        raise ValueError(f"Brief already exists in OODriver DB: {brief.get('brief_id')}")
    return replace_db(db, briefs=[*db.briefs, brief])


def append_run(db: ScenarioStudioDb, manifest: dict[str, Any]) -> ScenarioStudioDb:
    return replace_db(db, runs=[*db.runs, manifest])


def append_evaluation(db: ScenarioStudioDb, record: dict[str, Any]) -> ScenarioStudioDb:
    return replace_db(db, evaluations=[*db.evaluations, record])


def append_bundle(db: ScenarioStudioDb, bundle: dict[str, Any]) -> ScenarioStudioDb:
    return replace_db(db, bundles=[*db.bundles, bundle])


def append_export(db: ScenarioStudioDb, export: dict[str, Any]) -> ScenarioStudioDb:
    return replace_db(db, exports=[*db.exports, export])


def render_studio_db_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload.get('product_name', OODRIVER_PRODUCT_NAME)} Studio DB",
        "",
        f"- Run: `{payload.get('run_id')}`",
        f"- Schema: `{payload.get('schema_version')}`",
        f"- Briefs: `{len(payload.get('briefs', []))}`",
        f"- Candidates: `{len(payload.get('candidates', []))}`",
        f"- Queue records: `{len(payload.get('queue', []))}`",
        f"- Runs: `{len(payload.get('runs', []))}`",
        f"- Evaluations: `{len(payload.get('evaluations', []))}`",
        f"- Bundles: `{len(payload.get('bundles', []))}`",
        "",
        "## Queue",
        "",
        "| scenario | status | priority | policies |",
        "| --- | --- | --- | --- |",
    ]
    for record in payload.get("queue", []):
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(record.get("scenario_id")),
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
    lines.extend(["", "## Command Log", ""])
    for entry in payload.get("command_log", []):
        lines.append(f"- `{entry.get('command')}` -> `{entry.get('status')}`")
    lines.append("")
    return "\n".join(lines)


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _string_dict(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items()}


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _cell(value: Any) -> str:
    return "" if value is None else str(value).replace("|", "\\|")


__all__ = [
    "OODRIVER_PRODUCT_NAME",
    "SCENARIO_STUDIO_DB_FILENAME",
    "SCENARIO_STUDIO_DB_SCHEMA_VERSION",
    "ScenarioStudioDb",
    "append_brief",
    "append_bundle",
    "append_command",
    "append_evaluation",
    "append_export",
    "append_run",
    "load_studio_db",
    "new_studio_db",
    "replace_db",
    "render_studio_db_markdown",
    "studio_db_path",
    "write_studio_db",
]
