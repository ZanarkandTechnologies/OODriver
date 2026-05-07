"""Paper-style V8 final submission pack for Scenario Workbench."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir


@dataclass(frozen=True)
class FinalSubmissionPackV8Inputs:
    workbench_bundle_path: Path
    agentic_loop_path: Path
    risk_timeline_path: Path
    reasoning_overlay_path: Path
    timewarp_path: Path
    alpamayo_batch_path: Path
    final_demo_video_path: Path | None = None
    blockers_path: Path | None = None
    output_root: Path = Path("artifacts/runs")
    run_id: str = "final-submission-pack-v8"


def run_final_submission_pack_v8(inputs: FinalSubmissionPackV8Inputs) -> dict[str, Any]:
    run_dir = prepare_run_dir(inputs.output_root, inputs.run_id)
    return build_final_submission_pack_v8(run_dir, inputs)


def build_final_submission_pack_v8(run_dir: Path, inputs: FinalSubmissionPackV8Inputs) -> dict[str, Any]:
    bundle = _load_json(inputs.workbench_bundle_path)
    loop = _load_json(inputs.agentic_loop_path)
    risk = _load_json(inputs.risk_timeline_path)
    overlay = _load_json(inputs.reasoning_overlay_path)
    timewarp = _load_json(inputs.timewarp_path)
    alpamayo = _load_json(inputs.alpamayo_batch_path)
    blockers = _read_blockers(inputs.blockers_path)
    artifact_map = {
        "workbench_bundle": str(inputs.workbench_bundle_path),
        "agentic_loop": str(inputs.agentic_loop_path),
        "risk_timeline": str(inputs.risk_timeline_path),
        "reasoning_overlay": str(inputs.reasoning_overlay_path),
        "timewarp": str(inputs.timewarp_path),
        "alpamayo_batch": str(inputs.alpamayo_batch_path),
        "final_demo_video": str(inputs.final_demo_video_path) if inputs.final_demo_video_path else None,
        "blockers": str(inputs.blockers_path) if inputs.blockers_path else None,
    }
    payload = {
        "title": "0xDriver: Agentic OOD Scenario Workbench For Minimal-Shot Driving",
        "submission_version": "v8",
        "submission_status": _submission_status(loop, risk, overlay, timewarp, alpamayo),
        "thesis": (
            "0xDriver contributes a simulator data engine for minimal-shot autonomy: generate weird-but-plausible "
            "CARLA scenarios, render time-warped evidence, expose simulator-grounded risk, retrieve prior failure "
            "memory, and evaluate frozen reasoning VLAs without AV fine-tuning."
        ),
        "scorecard": _scorecard(loop, risk, overlay, timewarp, alpamayo, inputs.final_demo_video_path),
        "evidence_rows": _evidence_rows(artifact_map, bundle, loop, risk, overlay, timewarp, alpamayo),
        "video_script": _video_script(loop, risk, overlay, alpamayo),
        "two_page_writeup": _writeup(loop, risk, overlay, timewarp, alpamayo, blockers),
        "model_and_data_declarations": _declarations(alpamayo),
        "claim_boundaries": _claim_boundaries(bundle, loop, risk, overlay, timewarp, alpamayo),
        "open_blockers": blockers,
        "artifact_map": artifact_map,
    }
    return write_final_submission_pack_v8(run_dir, payload)


def write_final_submission_pack_v8(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "final_submission_pack_v8.json"
    report_path = run_dir / "final_submission_pack_v8.md"
    writeup_path = run_dir / "writeup_2page_v8.md"
    script_path = run_dir / "video_script_v8.md"
    browser_path = run_dir / "scenario_browser_v8.html"
    artifact_map_path = run_dir / "artifact_map_v8.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    artifact_map_path.write_text(json.dumps(payload["artifact_map"], indent=2), encoding="utf-8")
    report_path.write_text(_report_markdown(payload), encoding="utf-8")
    writeup_path.write_text(_writeup_markdown(payload), encoding="utf-8")
    script_path.write_text(_script_markdown(payload), encoding="utf-8")
    browser_path.write_text(_browser_html(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
        "writeup_path": str(writeup_path),
        "video_script_path": str(script_path),
        "browser_path": str(browser_path),
        "artifact_map_path": str(artifact_map_path),
    }


def _scorecard(
    loop: dict[str, Any],
    risk: dict[str, Any],
    overlay: dict[str, Any],
    timewarp: dict[str, Any],
    alpamayo: dict[str, Any],
    final_demo_video_path: Path | None,
) -> dict[str, Any]:
    final_demo_exists = final_demo_video_path.exists() if final_demo_video_path else False
    return {
        "agentic_briefs": loop.get("brief_count"),
        "agentic_candidates": loop.get("candidate_count"),
        "agentic_accepted": loop.get("accepted_count"),
        "risk_events": risk.get("event_count"),
        "max_risk_level": risk.get("max_risk_level"),
        "overlay_status": overlay.get("status"),
        "overlay_events": overlay.get("event_count"),
        "overlay_frame_count": overlay.get("frame_count"),
        "timewarp_status": timewarp.get("status"),
        "timewarp_input_duration_s": timewarp.get("input_duration_s"),
        "timewarp_output_duration_s": timewarp.get("output_duration_s"),
        "alpamayo_cases": alpamayo.get("case_count"),
        "alpamayo_reasoning_changed": alpamayo.get("reasoning_changed_count"),
        "alpamayo_mean_latency_ms": alpamayo.get("mean_latency_ms"),
        "alpamayo_max_vram_peak_mb": alpamayo.get("max_vram_peak_mb"),
        "final_demo_video_exists": final_demo_exists,
    }


def _submission_status(
    loop: dict[str, Any],
    risk: dict[str, Any],
    overlay: dict[str, Any],
    timewarp: dict[str, Any],
    alpamayo: dict[str, Any],
) -> str:
    if overlay.get("status") == "passed" and timewarp.get("status") == "passed" and alpamayo.get("passed_count", 0):
        return "submission_ready_with_claim_boundaries"
    if loop.get("accepted_count", 0) and risk.get("event_count", 0):
        return "partial_demo_ready"
    return "partial_with_blockers"


def _evidence_rows(
    artifact_map: dict[str, str | None],
    bundle: dict[str, Any],
    loop: dict[str, Any],
    risk: dict[str, Any],
    overlay: dict[str, Any],
    timewarp: dict[str, Any],
    alpamayo: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "claim": "Agentic Scenario Studio grows the OOD dataset queue.",
            "status": "proved" if loop.get("accepted_count", 0) else "partial",
            "artifact": artifact_map["agentic_loop"],
            "why_it_matters": f"{loop.get('brief_count', 0)} briefs -> {loop.get('candidate_count', 0)} candidates -> {loop.get('accepted_count', 0)} queued runtime targets.",
            "boundary": "deterministic agent loop; live LLM/Meshy provider is future polish.",
        },
        {
            "claim": "One scenario lineage links generation, CARLA evidence, Alpamayo/RAG, and curation.",
            "status": "proved" if bundle.get("product_loop") else "partial",
            "artifact": artifact_map["workbench_bundle"],
            "why_it_matters": "The workbench bundle is the product/evidence spine for the final demo.",
            "boundary": "linkage warnings are kept visible when artifacts are fallback-matched.",
        },
        {
            "claim": "CARLA ground truth produces a readable risk/perception timeline.",
            "status": "proved" if risk.get("event_count", 0) else "partial",
            "artifact": artifact_map["risk_timeline"],
            "why_it_matters": f"{risk.get('event_count', 0)} risk events, max risk {risk.get('max_risk_level')}.",
            "boundary": "simulator ground truth, not camera CV detection.",
        },
        {
            "claim": "The demo video shows risk, RAG memory, VLA reasoning, and action intent.",
            "status": "proved" if overlay.get("status") == "passed" else "partial",
            "artifact": artifact_map["reasoning_overlay"],
            "why_it_matters": f"{overlay.get('event_count', 0)} overlay events across {overlay.get('frame_count', 0)} frames.",
            "boundary": "sampled open-loop reasoning; not real-time closed-loop control.",
        },
        {
            "claim": "Time-warped offline rendering makes CARLA evidence watchable and honest.",
            "status": "proved" if timewarp.get("status") == "passed" else "partial",
            "artifact": artifact_map["timewarp"],
            "why_it_matters": f"{timewarp.get('input_duration_s')}s source -> {timewarp.get('output_duration_s')}s presentation clip.",
            "boundary": "source video retimed for presentation.",
        },
        {
            "claim": "Frozen Alpamayo 1.5 is evaluated with retrieved memory on OOD cases.",
            "status": "proved" if alpamayo.get("passed_count", 0) else "partial",
            "artifact": artifact_map["alpamayo_batch"],
            "why_it_matters": f"{alpamayo.get('passed_count', 0)} passed open-loop comparisons; {alpamayo.get('reasoning_changed_count', 0)} reasoning changes.",
            "boundary": "no AV fine-tuning and no real-time steering claim.",
        },
    ]


def _video_script(
    loop: dict[str, Any],
    risk: dict[str, Any],
    overlay: dict[str, Any],
    alpamayo: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "time": "0:00-0:10",
            "beat": "Problem",
            "visual": "Title card over Scenario Workbench motif.",
            "narration": "Minimal-shot autonomy needs a way to test weird situations before a fleet has seen them.",
        },
        {
            "time": "0:10-0:22",
            "beat": "Generate",
            "visual": "Agentic OOD queue and scenario gallery.",
            "narration": f"The generator produced {loop.get('candidate_count', 0)} candidates and queued {loop.get('accepted_count', 0)} for runtime evidence.",
        },
        {
            "time": "0:22-0:55",
            "beat": "Run and explain",
            "visual": "Reasoning overlay MP4.",
            "narration": f"The overlay shows risk, memory, sampled VLA reasoning, and action intent across {overlay.get('event_count', 0)} events.",
        },
        {
            "time": "0:55-1:08",
            "beat": "Evaluate",
            "visual": "Alpamayo/RAG scorecard.",
            "narration": f"Frozen Alpamayo was evaluated on {alpamayo.get('case_count', 0)} OOD cases; the current proof is open-loop.",
        },
        {
            "time": "1:08-1:18",
            "beat": "Flywheel",
            "visual": "Curation queue and claim boundaries.",
            "narration": f"Risk timeline events, currently {risk.get('event_count', 0)}, become reusable dataset and memory entries.",
        },
    ]


def _writeup(
    loop: dict[str, Any],
    risk: dict[str, Any],
    overlay: dict[str, Any],
    timewarp: dict[str, Any],
    alpamayo: dict[str, Any],
    blockers: list[str],
) -> dict[str, str]:
    return {
        "motivation": (
            "Autonomy that waits for data collection will always trail reality. 0xDriver focuses on the minimal-shot testing loop: "
            "make rare situations, run them, explain what the model noticed, and preserve the failure as memory."
        ),
        "architecture": (
            "Scenario Studio generates OOD briefs and candidates; CARLA renders the selected case; the risk timeline derives perception from simulator tracks; "
            "RAG supplies prior safety principles; frozen Alpamayo 1.5 supplies sampled open-loop reasoning and trajectory intent; the curation queue decides what to run next."
        ),
        "what_worked": (
            f"The V8 packet links {loop.get('candidate_count', 0)} generated candidates, {risk.get('event_count', 0)} risk events, "
            f"a {timewarp.get('output_duration_s')}s time-warped clip, and {alpamayo.get('passed_count', 0)} Alpamayo/RAG comparisons. "
            f"The reasoning overlay rendered {overlay.get('frame_count', 0)} frames."
        ),
        "what_did_not_work": (
            "The current system is not closed-loop VLA driving. The video is time-warped offline evidence, and Alpamayo is sampled as an open-loop reasoning/trajectory evaluator. "
            "A live LLM/Meshy generator and real-time VLA serving are future work, not claims in this submission."
        ),
        "where_prize_money_goes": (
            "The next prototype step is a persistent graphics/CUDA host for repeated closed-loop CARLA runs, richer generated 3D assets, and a larger OOD memory bank built from repeated failures."
        ),
        "open_blockers": "; ".join(blockers) if blockers else "No blockers prevent the V8 evidence packet; fresh source renders remain optional polish.",
    }


def _declarations(alpamayo: dict[str, Any]) -> list[str]:
    return [
        "Base VLA: nvidia/Alpamayo-1.5-10B, frozen, non-commercial research use.",
        "No AV-dataset fine-tuning was performed.",
        f"Alpamayo evidence status: {alpamayo.get('status', 'unknown')}; open-loop only.",
        "CARLA video is simulator evidence and is retimed offline for presentation.",
        "Generated videos, datasets, model weights, remote caches, and credentials are excluded from git.",
    ]


def _claim_boundaries(*payloads: dict[str, Any]) -> list[str]:
    boundaries = [
        "time_warped_offline_demo=true",
        "sampled_open_loop_reasoning=true",
        "real_time_vla_control=false",
        "simulator_ground_truth_risk=true",
        "live_meshy_asset_generation=false",
        "official_fail2drive_score=false",
    ]
    stale = {
        "fast_ffmpeg_no_reasoning_overlay=true",
    }
    for payload in payloads:
        boundaries.extend(str(item) for item in payload.get("claim_boundaries", []) if str(item) not in stale)
    return sorted(set(boundaries))


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _read_blockers(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_open = False
    blockers: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## ") and stripped[3:].strip().lower() == "open":
            in_open = True
            continue
        if in_open and stripped.startswith("## "):
            break
        if not in_open:
            continue
        if stripped.startswith("- "):
            if current:
                blockers.append(" ".join(current).strip())
            current = [stripped[2:].strip()]
        elif current and (line.startswith("  ") or line.startswith("\t")):
            current.append(stripped)
    if current:
        blockers.append(" ".join(current).strip())
    return blockers


def _report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['title']}",
        "",
        f"- Status: `{payload['submission_status']}`",
        "",
        "## Thesis",
        "",
        payload["thesis"],
        "",
        "## Scorecard",
        "",
    ]
    for key, value in payload["scorecard"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Evidence Rows", "", "| Claim | Status | Artifact | Boundary |", "| --- | --- | --- | --- |"])
    for row in payload["evidence_rows"]:
        lines.append(f"| {_cell(row['claim'])} | {_cell(row['status'])} | `{_cell(row['artifact'])}` | {_cell(row['boundary'])} |")
    lines.extend(["", "## Claim Boundaries", ""])
    lines.extend(f"- `{item}`" for item in payload["claim_boundaries"])
    return "\n".join(lines) + "\n"


def _writeup_markdown(payload: dict[str, Any]) -> str:
    lines = ["# 0xDriver V8 Two-Page Write-Up", ""]
    for key, value in payload["two_page_writeup"].items():
        lines.extend([f"## {key.replace('_', ' ').title()}", "", value, ""])
    lines.extend(["## Model And Data Declarations", ""])
    lines.extend(f"- {item}" for item in payload["model_and_data_declarations"])
    return "\n".join(lines) + "\n"


def _script_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Paper Demo Script V8", "", "| Time | Beat | Visual | Narration |", "| --- | --- | --- | --- |"]
    for beat in payload["video_script"]:
        lines.append(f"| {_cell(beat['time'])} | {_cell(beat['beat'])} | {_cell(beat['visual'])} | {_cell(beat['narration'])} |")
    return "\n".join(lines) + "\n"


def _browser_html(payload: dict[str, Any]) -> str:
    rows = "\n".join(
        f"<tr><td>{_h(row['status'])}</td><td>{_h(row['claim'])}</td><td>{_link(row['artifact'])}</td><td>{_h(row['why_it_matters'])}</td><td>{_h(row['boundary'])}</td></tr>"
        for row in payload["evidence_rows"]
    )
    score = "\n".join(f"<li><code>{_h(key)}</code>: {_h(value)}</li>" for key, value in payload["scorecard"].items())
    artifacts = "\n".join(f"<li><code>{_h(key)}</code>: {_link(value)}</li>" for key, value in payload["artifact_map"].items())
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{_h(payload['title'])}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; background: #f7faf9; color: #111827; }}
    main {{ max-width: 1180px; margin: 0 auto; }}
    h1 {{ font-size: 34px; margin-bottom: 8px; }}
    table {{ border-collapse: collapse; width: 100%; background: white; }}
    th, td {{ border: 1px solid #d9dee7; padding: 10px 12px; vertical-align: top; text-align: left; }}
    th {{ background: #eef2f7; }}
    code {{ background: #eef2f7; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body><main>
  <h1>{_h(payload['title'])}</h1>
  <p><strong>{_h(payload['submission_status'])}</strong></p>
  <p>{_h(payload['thesis'])}</p>
  <h2>Scorecard</h2><ul>{score}</ul>
  <h2>Evidence</h2>
  <table><thead><tr><th>Status</th><th>Claim</th><th>Artifact</th><th>Why it matters</th><th>Boundary</th></tr></thead><tbody>{rows}</tbody></table>
  <h2>Artifacts</h2><ul>{artifacts}</ul>
</main></body></html>
"""


def _cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def _h(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def _link(value: Any) -> str:
    if not value:
        return ""
    escaped = _h(value)
    return f'<a href="{escaped}">{escaped}</a>'


__all__ = [
    "FinalSubmissionPackV8Inputs",
    "build_final_submission_pack_v8",
    "run_final_submission_pack_v8",
    "write_final_submission_pack_v8",
]
