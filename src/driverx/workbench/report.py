"""Reports for Scenario Workbench evidence bundles."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from driverx.workbench.types import ScenarioRunBundle


def write_scenario_run_bundle(run_dir: Path, bundle: ScenarioRunBundle) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = bundle.to_jsonable()
    json_path = run_dir / "scenario_run_bundle.json"
    markdown_path = run_dir / "scenario_run_bundle.md"
    html_path = run_dir / "scenario_run_bundle.html"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(render_bundle_markdown(payload), encoding="utf-8")
    html_path.write_text(render_bundle_html(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(markdown_path),
        "html_path": str(html_path),
    }


def render_bundle_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Scenario Workbench Bundle: {payload.get('bundle_id')}",
        "",
        f"- Scenario: `{payload.get('scenario_id')}`",
        f"- Behavior: `{payload.get('behavior_id')}`",
        f"- Video: `{payload.get('carla_video', {}).get('path')}`",
        f"- Export status: `{payload.get('carla_video', {}).get('export_status')}`",
        "",
        "## Product Loop",
        "",
        "| Stage | Status | Evidence | Why it matters |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload.get("product_loop", []):
        lines.append(
            "| {stage} | {status} | {evidence} | {why} |".format(
                stage=_md(row.get("stage")),
                status=_md(row.get("status")),
                evidence=_md(row.get("evidence")),
                why=_md(row.get("why_visible")),
            )
        )
    lines.extend(["", "## Claim Boundaries", ""])
    for item in payload.get("claim_boundaries", []):
        lines.append(f"- `{item}`")
    warnings = payload.get("linkage_warnings", [])
    if warnings:
        lines.extend(["", "## Linkage Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
    lines.extend(["", "## Source Artifacts", ""])
    for key, value in payload.get("source_paths", {}).items():
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines) + "\n"


def render_bundle_html(payload: dict[str, Any]) -> str:
    loop_rows = "\n".join(
        "<tr><td>{stage}</td><td>{status}</td><td>{evidence}</td><td>{why}</td></tr>".format(
            stage=_h(row.get("stage")),
            status=_h(row.get("status")),
            evidence=_h(row.get("evidence")),
            why=_h(row.get("why_visible")),
        )
        for row in payload.get("product_loop", [])
    )
    boundaries = "\n".join(f"<li><code>{_h(item)}</code></li>" for item in payload.get("claim_boundaries", []))
    warnings = "\n".join(f"<li>{_h(item)}</li>" for item in payload.get("linkage_warnings", []))
    warnings_section = f"<section><h2>Linkage Warnings</h2><ul>{warnings}</ul></section>" if warnings else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Scenario Workbench Bundle</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #16181d; background: #f8fafc; }}
    main {{ max-width: 1100px; margin: 0 auto; }}
    h1 {{ font-size: 28px; margin-bottom: 8px; }}
    .meta {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 24px; margin: 20px 0; }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ border: 1px solid #d9dee7; padding: 10px 12px; vertical-align: top; text-align: left; }}
    th {{ background: #eef2f7; }}
    code {{ background: #eef2f7; padding: 2px 4px; border-radius: 4px; }}
    section {{ margin-top: 28px; }}
  </style>
</head>
<body>
<main>
  <h1>Scenario Workbench Bundle</h1>
  <p>One linked lineage object for generated OOD scenario evidence.</p>
  <div class="meta">
    <div><strong>Bundle</strong><br><code>{_h(payload.get("bundle_id"))}</code></div>
    <div><strong>Scenario</strong><br><code>{_h(payload.get("scenario_id"))}</code></div>
    <div><strong>Behavior</strong><br><code>{_h(payload.get("behavior_id"))}</code></div>
    <div><strong>Video</strong><br><code>{_h(payload.get("carla_video", {}).get("path"))}</code></div>
  </div>
  <section>
    <h2>Product Loop</h2>
    <table>
      <thead><tr><th>Stage</th><th>Status</th><th>Evidence</th><th>Why it matters</th></tr></thead>
      <tbody>{loop_rows}</tbody>
    </table>
  </section>
  <section>
    <h2>Claim Boundaries</h2>
    <ul>{boundaries}</ul>
  </section>
  {warnings_section}
</main>
</body>
</html>
"""


def _md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def _h(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))
