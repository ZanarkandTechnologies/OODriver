"""Build judge-facing reasoning packs from CARLA video and Alpamayo evidence."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReasoningVideoPackInputs:
    ood_video_evidence_path: Path
    alpamayo_scene_path: Path | None = None
    alpamayo_comparison_path: Path | None = None
    source_rgb_folder: Path | None = None
    fps: int = 5


def build_reasoning_video_pack(
    run_dir: Path,
    inputs: ReasoningVideoPackInputs,
) -> dict[str, Any]:
    video = _load_json(inputs.ood_video_evidence_path)
    scene = _load_json(inputs.alpamayo_scene_path) if inputs.alpamayo_scene_path else {}
    comparison = _load_json(inputs.alpamayo_comparison_path) if inputs.alpamayo_comparison_path else {}
    records = [record for record in list(comparison.get("records", [])) if isinstance(record, dict)]
    baseline = _record(records, "alpamayo")
    memory = _record(records, "alpamayo+memory")
    payload = {
        "status": "ready" if video else "blocked",
        "scenario_id": _first_str(video.get("scenario_id"), scene.get("scenario_id"), comparison.get("scenario_id")),
        "behavior_id": video.get("behavior_id") or _mapping(comparison.get("scenario_report")).get("behavior_id"),
        "video_path": video.get("video_path"),
        "source_rgb_folder": str(inputs.source_rgb_folder) if inputs.source_rgb_folder else video.get("input_rgb_folder"),
        "duration_s": video.get("duration_s"),
        "worst_risk": video.get("worst_risk"),
        "cot_snippets": {
            "scene": scene.get("cot_snippet"),
            "baseline": baseline.get("cot_snippet"),
            "memory": memory.get("cot_snippet"),
        },
        "memory_ids": list(comparison.get("memory_ids", [])),
        "memory_context": list(comparison.get("memory_context", [])),
        "trajectory_delta": _mapping(comparison.get("trajectory_delta")),
        "reasoning_delta": _mapping(comparison.get("reasoning_delta")),
        "latency": {
            "scene_latency_ms": scene.get("latency_ms"),
            "latency_delta_ms": comparison.get("latency_delta_ms"),
            "records": [
                {
                    "mode": record.get("mode"),
                    "latency_ms": record.get("latency_ms"),
                    "vram_peak_mb": record.get("vram_peak_mb"),
                }
                for record in records
            ],
        },
        "inputs": {
            "ood_video_evidence_path": str(inputs.ood_video_evidence_path),
            "alpamayo_scene_path": str(inputs.alpamayo_scene_path) if inputs.alpamayo_scene_path else None,
            "alpamayo_comparison_path": str(inputs.alpamayo_comparison_path) if inputs.alpamayo_comparison_path else None,
        },
        "claim_boundaries": [
            "reasoning_pack_is_evidence_surface=true",
            "scripted_carla_video_may_be_live_or_cached=true",
            "alpamayo_open_loop_policy_evaluation=true",
            "real_time_vla_control=false",
        ],
    }
    return write_reasoning_video_pack(run_dir, payload)


def write_reasoning_video_pack(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "reasoning_video_pack.json"
    report_path = run_dir / "reasoning_video_pack.md"
    html_path = run_dir / "reasoning_video_pack.html"
    output = {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
        "html_path": str(html_path),
    }
    json_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(output), encoding="utf-8")
    html_path.write_text(_html(output), encoding="utf-8")
    return output


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _record(records: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    for record in records:
        if record.get("mode") == mode:
            return record
    return {}


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _first_str(*values: object) -> str:
    for value in values:
        if value:
            return str(value)
    return "unknown-scenario"


def _markdown(payload: dict[str, Any]) -> str:
    delta = _mapping(payload.get("trajectory_delta"))
    snippets = _mapping(payload.get("cot_snippets"))
    lines = [
        "# Reasoning Video Pack",
        "",
        f"- status: `{payload.get('status')}`",
        f"- scenario_id: `{payload.get('scenario_id')}`",
        f"- behavior_id: `{payload.get('behavior_id')}`",
        f"- video_path: `{payload.get('video_path')}`",
        f"- duration_s: `{payload.get('duration_s')}`",
        f"- memory_ids: `{', '.join(str(item) for item in payload.get('memory_ids', []))}`",
        "",
        "## Trajectory Delta",
        "",
    ]
    lines.extend(f"- `{key}`: `{value}`" for key, value in delta.items()) if delta else lines.append("- unavailable")
    lines.extend(["", "## CoC Snippets", ""])
    for label, text in snippets.items():
        if text:
            lines.extend([f"### {label}", "", f"> {str(text)[:700]}", ""])
    lines.extend(["## Claim Boundaries", ""])
    lines.extend(f"- `{item}`" for item in list(payload.get("claim_boundaries", [])))
    return "\n".join(lines) + "\n"


def _html(payload: dict[str, Any]) -> str:
    snippets = _mapping(payload.get("cot_snippets"))
    memories = list(payload.get("memory_context", []))
    delta = _mapping(payload.get("trajectory_delta"))
    risk = _mapping(payload.get("worst_risk"))
    cards = [
        _card("Scenario", f"{payload.get('scenario_id')}<br>{payload.get('behavior_id')}"),
        _card("Video", str(payload.get("video_path") or "not available")),
        _card("Worst Risk", "<br>".join(f"{html.escape(str(k))}: {html.escape(str(v))}" for k, v in risk.items()) or "none"),
        _card("Trajectory Delta", "<br>".join(f"{html.escape(str(k))}: {html.escape(str(v))}" for k, v in delta.items()) or "unavailable"),
    ]
    memory_html = "".join(
        f"<li><strong>{html.escape(str(memory.get('entry_id')))}</strong>: "
        f"{html.escape(str(memory.get('recommended_behavior') or memory.get('principle') or ''))}</li>"
        for memory in memories
        if isinstance(memory, dict)
    )
    snippet_html = "".join(
        f"<section><h2>{html.escape(str(label))}</h2><blockquote>{html.escape(str(text or 'unavailable'))}</blockquote></section>"
        for label, text in snippets.items()
    )
    boundaries = "".join(f"<li><code>{html.escape(str(item))}</code></li>" for item in payload.get("claim_boundaries", []))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>DriverX Reasoning Video Pack</title>
  <style>
    body {{ font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; color: #111827; background: #f8fafc; }}
    h1 {{ font-size: 32px; margin-bottom: 8px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 24px 0; }}
    .card {{ background: white; border: 1px solid #d1d5db; border-radius: 8px; padding: 14px; }}
    .card h2 {{ font-size: 14px; text-transform: uppercase; color: #4b5563; margin: 0 0 8px; }}
    blockquote {{ background: white; border-left: 4px solid #2563eb; margin: 10px 0 22px; padding: 12px 16px; }}
    code {{ background: #e5e7eb; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>DriverX Reasoning Video Pack</h1>
  <p>CARLA OOD video evidence paired with frozen Alpamayo open-loop reasoning.</p>
  <div class="grid">{''.join(cards)}</div>
  <section><h2>Retrieved Memory</h2><ul>{memory_html or '<li>none</li>'}</ul></section>
  {snippet_html}
  <section><h2>Claim Boundaries</h2><ul>{boundaries}</ul></section>
</body>
</html>
"""


def _card(title: str, body: str) -> str:
    return f"<section class=\"card\"><h2>{html.escape(title)}</h2><p>{body}</p></section>"


__all__ = [
    "ReasoningVideoPackInputs",
    "build_reasoning_video_pack",
    "write_reasoning_video_pack",
]
