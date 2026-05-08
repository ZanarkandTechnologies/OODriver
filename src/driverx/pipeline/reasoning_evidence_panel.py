"""Build a decongested judge-facing reasoning evidence panel."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CLAIM_BOUNDARIES = [
    "sampled_open_loop_reasoning=true",
    "time_warped_offline_demo=true",
    "closed_loop_vla_control=false",
    "real_time_vla_control=false",
    "source_citations=true",
    "hud_layout=compact_chaptered",
]


def build_reasoning_evidence_panel(
    *,
    overlay_report_path: Path,
    reasoning_diff_path: Path,
    retrieval_ledger_paths: tuple[Path, ...] = (),
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-reasoning-evidence-panel",
) -> dict[str, Any]:
    overlay = _load_json(overlay_report_path)
    diff = _load_json(reasoning_diff_path)
    ledgers = [_load_json(path) for path in retrieval_ledger_paths if path.exists()]
    chapters = _chapters(overlay, diff, ledgers)
    report = {
        "report_id": run_id,
        "overlay_report_path": str(overlay_report_path),
        "reasoning_diff_path": str(reasoning_diff_path),
        "retrieval_ledger_paths": [str(path) for path in retrieval_ledger_paths],
        "chapters": chapters,
        "max_hud_rows": 3,
        "recommended_video_layout": {
            "left": "CARLA footage with only frame/time/risk chips",
            "right": "chaptered sidecar: risk, retrieved memory, Alpamayo reasoning delta",
            "footer": "claim boundaries and latency/compute label",
        },
        "citation_count": _citation_count(overlay, diff, ledgers),
        "claim_boundaries": CLAIM_BOUNDARIES,
    }
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "reasoning_presentation_report.json"
    md_path = run_dir / "reasoning_presentation_report.md"
    html_path = run_dir / "reasoning_presentation_report.html"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown = _markdown(report)
    md_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(_html(report), encoding="utf-8")
    return {**report, "json_path": str(json_path), "report_path": str(md_path), "html_path": str(html_path)}


def _chapters(overlay: dict[str, Any], diff: dict[str, Any], ledgers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = _list(diff.get("cases"))
    ledger = ledgers[0] if ledgers else {}
    selected = _list(ledger.get("selected_memory_ids"))
    return [
        {
            "chapter_id": "scenario",
            "title": "Generated OOD Scenario",
            "evidence": [
                f"overlay events={overlay.get('event_count', len(_list(overlay.get('events'))))}",
                f"frames={overlay.get('frame_count', 'unknown')}",
            ],
            "display_rows": ["Frame/time", "OOD risk", "Action intent"],
        },
        {
            "chapter_id": "retrieval",
            "title": "Retrieved Memory",
            "evidence": [f"backend={ledger.get('retrieval_backend', 'lexical_tag_overlap')}"] + [
                f"selected_memory={memory_id}" for memory_id in selected[:5]
            ],
            "display_rows": ["Memory id", "Matched tags", "Principle"],
        },
        {
            "chapter_id": "reasoning",
            "title": "Alpamayo Reasoning Delta",
            "evidence": [
                f"{case.get('scenario_id')}: {case.get('reasoning_delta_summary')}" for case in cases[:3]
            ],
            "display_rows": ["Before", "After", "Delta"],
        },
        {
            "chapter_id": "claims",
            "title": "Claim Boundaries",
            "evidence": CLAIM_BOUNDARIES,
            "display_rows": ["Open-loop", "Offline/time-warped", "Not real-time control"],
        },
    ]


def _citation_count(overlay: dict[str, Any], diff: dict[str, Any], ledgers: list[dict[str, Any]]) -> int:
    count = 0
    for key in ("overlay_report_path", "input_video", "output_video"):
        if overlay.get(key):
            count += 1
    count += len(_list(diff.get("cases")))
    for ledger in ledgers:
        count += len(_list(ledger.get("selected_memory_ids")))
    return count


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Reasoning Evidence Panel",
        "",
        f"- Max HUD rows: `{report['max_hud_rows']}`",
        f"- Citations: `{report['citation_count']}`",
        "",
    ]
    for chapter in report["chapters"]:
        lines.extend([f"## {chapter['title']}", ""])
        for evidence in chapter.get("evidence", []):
            lines.append(f"- {evidence}")
        lines.append("")
    return "\n".join(lines)


def _html(report: dict[str, Any]) -> str:
    chapters = "\n".join(
        "<section><h2>{}</h2><ul>{}</ul></section>".format(
            chapter["title"],
            "".join(f"<li>{item}</li>" for item in chapter.get("evidence", [])),
        )
        for chapter in report["chapters"]
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>OODrive Reasoning Evidence</title>"
        "<style>body{font-family:Arial,sans-serif;max-width:960px;margin:32px auto;line-height:1.4}"
        "section{border-top:1px solid #ddd;padding:16px 0}code{background:#eee;padding:2px 4px}</style>"
        "</head><body><h1>OODrive Reasoning Evidence</h1>"
        f"<p>Max HUD rows: <code>{report['max_hud_rows']}</code>; citations: "
        f"<code>{report['citation_count']}</code></p>{chapters}</body></html>"
    )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


__all__ = ["build_reasoning_evidence_panel"]
