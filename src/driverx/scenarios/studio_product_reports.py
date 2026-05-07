"""Report builders for OODriver replay and export commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.scenarios.studio_db import OODRIVER_PRODUCT_NAME, ScenarioStudioDb


def build_bundle_payload(
    db: ScenarioStudioDb,
    run_payload: dict[str, Any],
    eval_payload: dict[str, Any],
    candidate: dict[str, Any],
    bundle_id: str,
) -> dict[str, Any]:
    scenario_id = str(run_payload.get("scenario_id", eval_payload.get("scenario_id", "scenario")))
    rows = [
        {
            "stage": "Generate",
            "status": "done" if db.candidates else "missing",
            "artifact": db.artifacts.get("scenario_studio_batch"),
        },
        {"stage": "Queue", "status": "done" if db.queue else "missing", "artifact": db.artifacts.get("json_path")},
        {"stage": "Run", "status": str(run_payload.get("status", "missing")), "artifact": run_payload.get("json_path")},
        {
            "stage": "Evaluate",
            "status": str(eval_payload.get("reasoning_mode", "missing")),
            "artifact": eval_payload.get("json_path"),
        },
    ]
    boundaries = sorted(
        set(db.claim_boundaries + list(run_payload.get("claim_boundaries", [])) + list(eval_payload.get("claim_boundaries", [])))
    )
    return {
        "bundle_id": bundle_id,
        "product": OODRIVER_PRODUCT_NAME,
        "scenario_id": scenario_id,
        "candidate_id": run_payload.get("candidate_id"),
        "candidate": candidate,
        "run": run_payload,
        "evaluation": eval_payload,
        "product_loop": rows,
        "claim_boundaries": boundaries,
    }


def write_bundle(run_dir: Path, payload: dict[str, Any]) -> dict[str, str]:
    json_path = run_dir / "scenario_run_bundle.json"
    md_path = run_dir / "scenario_run_bundle.md"
    html_path = run_dir / "scenario_run_bundle.html"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(_bundle_markdown(payload), encoding="utf-8")
    html_path.write_text(_html_doc("OODriver Scenario Replay", _bundle_html(payload)), encoding="utf-8")
    return {"json_path": str(json_path), "report_path": str(md_path), "html_path": str(html_path)}


def build_export_payload(db: ScenarioStudioDb, db_path: Path, export_id: str) -> dict[str, Any]:
    closed_loop_count = sum(
        1 for run in db.runs if "closed_loop_carla_execution=true" in list(run.get("claim_boundaries", []))
    )
    return {
        "pack_id": export_id,
        "product": OODRIVER_PRODUCT_NAME,
        "db_path": str(db_path),
        "command_transcript": [str(item.get("command", "")) for item in db.command_log],
        "scenario_count": len(db.candidates),
        "queued_count": len(db.queue),
        "run_count": len(db.runs),
        "closed_loop_count": closed_loop_count,
        "alpamayo_eval_count": sum(1 for item in db.evaluations if "alpamayo" in str(item.get("policy", ""))),
        "evidence_rows": _export_evidence_rows(db),
        "claim_boundaries": sorted(
            set(
                db.claim_boundaries
                + [boundary for item in db.runs + db.evaluations for boundary in list(item.get("claim_boundaries", []))]
            )
        ),
        "next_work": [
            "Attach high-fidelity CARLA video/tracks to queued scenarios.",
            "Attach live Alpamayo prediction JSON for memory/no-memory comparison.",
            "Promote high-value scenarios into the final submission dossier.",
        ],
    }


def write_export_pack(run_dir: Path, payload: dict[str, Any]) -> dict[str, str]:
    json_path = run_dir / "scenario_generator_cli_pack.json"
    md_path = run_dir / "scenario_generator_cli_pack.md"
    html_path = run_dir / "scenario_generator_cli_pack.html"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(_export_markdown(payload), encoding="utf-8")
    html_path.write_text(_html_doc("OODriver CLI Evidence Pack", _export_html(payload)), encoding="utf-8")
    return {"json_path": str(json_path), "report_path": str(md_path), "html_path": str(html_path)}


def _export_evidence_rows(db: ScenarioStudioDb) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in db.queue:
        candidate_id = str(record.get("candidate_id", ""))
        run = next((item for item in db.runs if str(item.get("candidate_id", "")) == candidate_id), {})
        evaluation = next(
            (item for item in db.evaluations if str(item.get("scenario_id", "")) == str(record.get("scenario_id", ""))),
            {},
        )
        rows.append(
            {
                "scenario_id": record.get("scenario_id"),
                "candidate_id": candidate_id,
                "queue_status": record.get("run_status"),
                "run_status": run.get("status", "missing"),
                "policy": run.get("policy", "not_run"),
                "reasoning_mode": evaluation.get("reasoning_mode", "missing"),
                "bundle": next(
                    (item.get("html_path") for item in db.bundles if item.get("scenario_id") == record.get("scenario_id")),
                    None,
                ),
            }
        )
    return rows


def _bundle_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OODriver Scenario Replay",
        "",
        f"- Scenario: `{payload.get('scenario_id')}`",
        f"- Candidate: `{payload.get('candidate_id')}`",
        "",
        "## Product Loop",
        "",
        "| Stage | Status | Artifact |",
        "| --- | --- | --- |",
    ]
    for row in payload.get("product_loop", []):
        lines.append(f"| {row.get('stage')} | {row.get('status')} | {row.get('artifact') or ''} |")
    lines.extend(["", "## Claim Boundaries", ""])
    lines.extend(f"- `{boundary}`" for boundary in payload.get("claim_boundaries", []))
    return "\n".join(lines) + "\n"


def _bundle_html(payload: dict[str, Any]) -> str:
    rows = "".join(
        f"<tr><td>{_esc(row.get('stage'))}</td><td>{_esc(row.get('status'))}</td><td>{_esc(row.get('artifact') or '')}</td></tr>"
        for row in payload.get("product_loop", [])
    )
    boundaries = "".join(f"<li><code>{_esc(boundary)}</code></li>" for boundary in payload.get("claim_boundaries", []))
    return (
        f"<h1>OODriver Scenario Replay</h1><p>Scenario <code>{_esc(payload.get('scenario_id'))}</code></p>"
        f"<table><tr><th>Stage</th><th>Status</th><th>Artifact</th></tr>{rows}</table>"
        f"<h2>Claim Boundaries</h2><ul>{boundaries}</ul>"
    )


def _export_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OODriver CLI Evidence Pack",
        "",
        f"- Pack: `{payload.get('pack_id')}`",
        f"- Scenarios: `{payload.get('scenario_count')}`",
        f"- Queued: `{payload.get('queued_count')}`",
        f"- Runs: `{payload.get('run_count')}`",
        f"- Alpamayo evaluations: `{payload.get('alpamayo_eval_count')}`",
        "",
        "## Evidence Rows",
        "",
        "| Scenario | Queue | Run | Policy | Reasoning | Bundle |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload.get("evidence_rows", []):
        lines.append(
            f"| {row.get('scenario_id')} | {row.get('queue_status')} | {row.get('run_status')} | "
            f"{row.get('policy')} | {row.get('reasoning_mode')} | {row.get('bundle') or ''} |"
        )
    lines.extend(["", "## Command Transcript", ""])
    lines.extend(f"- `{command}`" for command in payload.get("command_transcript", []))
    lines.extend(["", "## Claim Boundaries", ""])
    lines.extend(f"- `{boundary}`" for boundary in payload.get("claim_boundaries", []))
    lines.extend(["", "## Next Work", ""])
    lines.extend(f"- {item}" for item in payload.get("next_work", []))
    return "\n".join(lines) + "\n"


def _export_html(payload: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{_esc(row.get('scenario_id'))}</td>"
        f"<td>{_esc(row.get('queue_status'))}</td>"
        f"<td>{_esc(row.get('run_status'))}</td>"
        f"<td>{_esc(row.get('policy'))}</td>"
        f"<td>{_esc(row.get('reasoning_mode'))}</td>"
        f"<td>{_esc(row.get('bundle') or '')}</td>"
        "</tr>"
        for row in payload.get("evidence_rows", [])
    )
    boundaries = "".join(f"<li><code>{_esc(boundary)}</code></li>" for boundary in payload.get("claim_boundaries", []))
    return (
        f"<h1>OODriver CLI Evidence Pack</h1><p>{_esc(payload.get('scenario_count'))} scenarios, "
        f"{_esc(payload.get('run_count'))} runs, {_esc(payload.get('alpamayo_eval_count'))} Alpamayo evaluations.</p>"
        f"<table><tr><th>Scenario</th><th>Queue</th><th>Run</th><th>Policy</th><th>Reasoning</th><th>Bundle</th></tr>{rows}</table>"
        f"<h2>Claim Boundaries</h2><ul>{boundaries}</ul>"
    )


def _html_doc(title: str, body: str) -> str:
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{_esc(title)}</title>"
        "<style>body{font-family:Inter,Arial,sans-serif;max-width:1100px;margin:40px auto;padding:0 24px;line-height:1.45;color:#17202a}"
        "table{border-collapse:collapse;width:100%;margin:18px 0}td,th{border:1px solid #d6dde5;padding:8px;text-align:left;vertical-align:top}th{background:#f4f7fb}code{background:#eef3f8;padding:2px 4px;border-radius:4px}</style>"
        f"</head><body>{body}</body></html>"
    )


def _esc(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


__all__ = [
    "build_bundle_payload",
    "build_export_payload",
    "write_bundle",
    "write_export_pack",
]
