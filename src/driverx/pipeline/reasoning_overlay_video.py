"""Pipeline wrapper for reasoning/RAG timeline overlay videos."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.simulators.reasoning_timeline_overlay import (
    ReasoningOverlayConfig,
    build_reasoning_overlay_events,
    render_reasoning_timeline_overlay,
)


@dataclass(frozen=True)
class ReasoningOverlayInputs:
    input_video: Path
    output_video: Path
    workbench_bundle_path: Path
    risk_timeline_path: Path
    alpamayo_batch_path: Path
    output_root: Path = Path("artifacts/runs")
    run_id: str = "reasoning-overlay-video"
    frame_dir: Path | None = None
    fps: int = 15
    speed_factor: float = 3.0


def build_reasoning_overlay_video(inputs: ReasoningOverlayInputs) -> dict[str, Any]:
    run_dir = prepare_run_dir(inputs.output_root, inputs.run_id)
    bundle = _load_json(inputs.workbench_bundle_path)
    risk = _load_json(inputs.risk_timeline_path)
    alpamayo = _load_json(inputs.alpamayo_batch_path)
    events = build_reasoning_overlay_events(
        bundle=bundle,
        risk_timeline=risk,
        alpamayo_batch=alpamayo,
        speed_factor=inputs.speed_factor,
    )
    frame_dir = inputs.frame_dir or run_dir / "reasoning_overlay_frames"
    result = render_reasoning_timeline_overlay(
        ReasoningOverlayConfig(
            input_video=inputs.input_video,
            output_video=inputs.output_video,
            output_frame_dir=frame_dir,
            events=events,
            fps=inputs.fps,
            speed_factor=inputs.speed_factor,
        )
    )
    return write_reasoning_overlay_video(run_dir, result.to_jsonable(), [event.to_jsonable() for event in events])


def write_reasoning_overlay_video(
    run_dir: Path,
    result: dict[str, Any],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = {
        **result,
        "events": events,
    }
    json_path = run_dir / "reasoning_overlay_video.json"
    report_path = run_dir / "reasoning_overlay_video.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_report_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Reasoning Overlay Video",
        "",
        f"- Status: `{payload['status']}`",
        f"- Output video: `{payload['output_video']}`",
        f"- Sample frame: `{payload['sample_frame_path']}`",
        f"- Events: `{payload['event_count']}`",
        f"- Frames: `{payload['frame_count']}`",
        "",
        "## Events",
        "",
        "| Start | Risk | Memory | Action |",
        "| --- | --- | --- | --- |",
    ]
    for event in payload.get("events", [])[:12]:
        lines.append(
            f"| {event['start_s']} | {event['risk']} | `{event.get('memory_id')}` | {event['action_intent']} |"
        )
    lines.extend(["", "## Claim Boundaries", ""])
    for item in payload.get("claim_boundaries", []):
        lines.append(f"- `{item}`")
    return "\n".join(lines) + "\n"
