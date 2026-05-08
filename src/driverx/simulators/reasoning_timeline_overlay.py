"""Render risk, RAG, and Alpamayo reasoning panels onto CARLA videos."""

from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReasoningOverlayEvent:
    start_s: float
    end_s: float
    source_time_s: float
    risk: str
    memory_id: str | None
    memory_principle: str | None
    vla_reasoning: str | None
    action_intent: str
    claim: str = "sampled_open_loop_reasoning"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "start_s": round(self.start_s, 3),
            "end_s": round(self.end_s, 3),
            "source_time_s": round(self.source_time_s, 3),
            "risk": self.risk,
            "memory_id": self.memory_id,
            "memory_principle": self.memory_principle,
            "vla_reasoning": self.vla_reasoning,
            "action_intent": self.action_intent,
            "claim": self.claim,
        }


@dataclass(frozen=True)
class ReasoningOverlayConfig:
    input_video: Path
    output_video: Path
    output_frame_dir: Path
    events: list[ReasoningOverlayEvent]
    fps: int = 15
    ffmpeg_path: str | None = None
    title: str = "0xDriver Scenario Workbench"
    subtitle: str = "time-warped CARLA + sampled open-loop VLA reasoning"
    speed_factor: float = 3.0
    show_frame_time: bool = True
    show_reasoning: bool = True
    show_rag: bool = True
    layout: str = "dense"


@dataclass(frozen=True)
class ReasoningOverlayResult:
    status: str
    input_video: str
    output_video: str
    output_frame_dir: str
    sample_frame_path: str | None
    fps: int
    speed_factor: float
    event_count: int
    frame_count: int
    command: list[str]
    returncode: int | None
    stdout: str
    stderr: str
    blockers: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)
    frame_time_overlay_coverage: float = 0.0

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "input_video": self.input_video,
            "output_video": self.output_video,
            "output_frame_dir": self.output_frame_dir,
            "sample_frame_path": self.sample_frame_path,
            "fps": self.fps,
            "speed_factor": self.speed_factor,
            "event_count": self.event_count,
            "frame_count": self.frame_count,
            "command": self.command,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "blockers": self.blockers,
            "claim_boundaries": self.claim_boundaries,
            "frame_time_overlay_coverage": self.frame_time_overlay_coverage,
        }


def build_reasoning_overlay_events(
    *,
    bundle: dict[str, Any],
    risk_timeline: dict[str, Any],
    alpamayo_batch: dict[str, Any],
    speed_factor: float,
    limit: int = 10,
) -> list[ReasoningOverlayEvent]:
    scenario_id = bundle.get("scenario_id") or risk_timeline.get("scenario_id")
    alpamayo_record = _match_alpamayo_record(alpamayo_batch, scenario_id)
    memory_id = _first((alpamayo_record or {}).get("memory_ids"))
    reasoning = _reasoning_snippet(alpamayo_record)
    memory_principle = _memory_principle(memory_id)
    risk_events = sorted(
        risk_timeline.get("events", []),
        key=lambda event: (_risk_rank(str(event.get("risk_level", ""))), float(event.get("distance_m", 9999))),
    )
    selected = risk_events[:limit] if risk_events else _fallback_events(risk_timeline)
    events: list[ReasoningOverlayEvent] = []
    for index, event in enumerate(selected):
        source_time = float(event.get("time_s", index * 3.0))
        start = max(0.0, source_time / max(speed_factor, 0.1))
        risk = (
            f"{event.get('risk_label', 'risk')} | {event.get('zone', 'unknown zone')} | "
            f"{event.get('distance_m', '?')}m from {event.get('actor_ref', 'actor')}"
        )
        action = str(event.get("recommended_behavior") or "slow, monitor, and preserve a safe escape path")
        events.append(
            ReasoningOverlayEvent(
                start_s=start,
                end_s=start + 4.0,
                source_time_s=source_time,
                risk=risk,
                memory_id=memory_id,
                memory_principle=memory_principle,
                vla_reasoning=reasoning,
                action_intent=action,
            )
        )
    if not events:
        events.append(
            ReasoningOverlayEvent(
                start_s=0.0,
                end_s=6.0,
                source_time_s=0.0,
                risk="No risk timeline linked yet",
                memory_id=memory_id,
                memory_principle=memory_principle,
                vla_reasoning=reasoning,
                action_intent="show generated scenario and claim boundary",
            )
        )
    return events


def render_reasoning_timeline_overlay(config: ReasoningOverlayConfig) -> ReasoningOverlayResult:
    ffmpeg_path = config.ffmpeg_path or shutil.which("ffmpeg")
    blockers = _blockers(config, ffmpeg_path)
    claim_boundaries = [
        "time_warped_offline_demo=true",
        "sampled_open_loop_reasoning=true",
        "real_time_vla_control=false",
        "overlay_uses_simulator_ground_truth_risk=true",
    ]
    if blockers:
        return ReasoningOverlayResult(
            status="blocked",
            input_video=str(config.input_video),
            output_video=str(config.output_video),
            output_frame_dir=str(config.output_frame_dir),
            sample_frame_path=None,
            fps=config.fps,
            speed_factor=config.speed_factor,
            event_count=len(config.events),
            frame_count=0,
            command=[],
            returncode=None,
            stdout="",
            stderr="\n".join(blockers),
            blockers=blockers,
            claim_boundaries=claim_boundaries,
            frame_time_overlay_coverage=0.0,
        )
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        return ReasoningOverlayResult(
            status="blocked",
            input_video=str(config.input_video),
            output_video=str(config.output_video),
            output_frame_dir=str(config.output_frame_dir),
            sample_frame_path=None,
            fps=config.fps,
            speed_factor=config.speed_factor,
            event_count=len(config.events),
            frame_count=0,
            command=[],
            returncode=None,
            stdout="",
            stderr=str(exc),
            blockers=[f"Pillow unavailable: {exc}"],
            claim_boundaries=claim_boundaries,
            frame_time_overlay_coverage=0.0,
        )

    config.output_frame_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir = config.output_frame_dir / "_extracted"
    rendered_dir = config.output_frame_dir / "frames"
    shutil.rmtree(extracted_dir, ignore_errors=True)
    shutil.rmtree(rendered_dir, ignore_errors=True)
    extracted_dir.mkdir(parents=True, exist_ok=True)
    rendered_dir.mkdir(parents=True, exist_ok=True)
    extract_command = [
        ffmpeg_path or "ffmpeg",
        "-y",
        "-i",
        str(config.input_video),
        "-vf",
        f"fps={config.fps}",
        str(extracted_dir / "frame_%06d.png"),
    ]
    extract_proc = subprocess.run(extract_command, capture_output=True, text=True, check=False)
    if extract_proc.returncode != 0:
        return ReasoningOverlayResult(
            status="failed",
            input_video=str(config.input_video),
            output_video=str(config.output_video),
            output_frame_dir=str(config.output_frame_dir),
            sample_frame_path=None,
            fps=config.fps,
            speed_factor=config.speed_factor,
            event_count=len(config.events),
            frame_count=0,
            command=extract_command,
            returncode=extract_proc.returncode,
            stdout=extract_proc.stdout,
            stderr=extract_proc.stderr,
            blockers=[],
            claim_boundaries=claim_boundaries,
            frame_time_overlay_coverage=0.0,
        )
    frames = sorted(extracted_dir.glob("frame_*.png"))
    font = ImageFont.load_default()
    for index, frame in enumerate(frames):
        event = _event_for_time(config.events, index / config.fps)
        target = rendered_dir / frame.name
        with Image.open(frame) as image:
            image = image.convert("RGB")
            draw = ImageDraw.Draw(image, "RGBA")
            render_reasoning_overlay_frame(
                draw,
                image.size,
                event,
                config.title,
                config.subtitle,
                font,
                frame_index=index,
                render_time_s=index / config.fps,
                show_frame_time=config.show_frame_time,
                show_reasoning=config.show_reasoning,
                show_rag=config.show_rag,
                layout=config.layout,
            )
            image.save(target)
    config.output_video.parent.mkdir(parents=True, exist_ok=True)
    assemble_command = [
        ffmpeg_path or "ffmpeg",
        "-y",
        "-framerate",
        str(config.fps),
        "-i",
        str(rendered_dir / "frame_%06d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        str(config.output_video),
    ]
    assemble_proc = subprocess.run(assemble_command, capture_output=True, text=True, check=False)
    sample_frame = rendered_dir / "frame_000001.png"
    return ReasoningOverlayResult(
        status="passed" if assemble_proc.returncode == 0 and config.output_video.exists() else "failed",
        input_video=str(config.input_video),
        output_video=str(config.output_video),
        output_frame_dir=str(rendered_dir),
        sample_frame_path=str(sample_frame) if sample_frame.exists() else None,
        fps=config.fps,
        speed_factor=config.speed_factor,
        event_count=len(config.events),
        frame_count=len(frames),
        command=assemble_command,
        returncode=assemble_proc.returncode,
        stdout=assemble_proc.stdout,
        stderr=assemble_proc.stderr,
        blockers=[],
        claim_boundaries=claim_boundaries,
        frame_time_overlay_coverage=1.0 if config.show_frame_time and frames else 0.0,
    )


def render_reasoning_overlay_frame(
    draw: Any,
    image_size: tuple[int, int],
    event: ReasoningOverlayEvent | None,
    title: str,
    subtitle: str,
    font: Any,
    *,
    frame_index: int | None = None,
    render_time_s: float | None = None,
    show_frame_time: bool = True,
    show_reasoning: bool = True,
    show_rag: bool = True,
    layout: str = "dense",
) -> None:
    if layout == "compact":
        _render_compact_reasoning_overlay_frame(
            draw,
            image_size,
            event,
            title,
            subtitle,
            font,
            frame_index=frame_index,
            render_time_s=render_time_s,
            show_frame_time=show_frame_time,
            show_reasoning=show_reasoning,
            show_rag=show_rag,
        )
        return
    width, height = image_size
    panel_w = min(520, max(360, width // 2))
    x0 = width - panel_w - 24
    y0 = 24
    x1 = width - 24
    y1 = min(height - 24, y0 + 330)
    draw.rounded_rectangle((x0, y0, x1, y1), radius=6, fill=(5, 10, 20, 205))
    draw.text((x0 + 18, y0 + 14), title, fill=(255, 255, 255, 245), font=font)
    draw.text((x0 + 18, y0 + 32), subtitle, fill=(194, 211, 255, 235), font=font)
    y = y0 + 62
    if show_frame_time:
        frame_text = _frame_time_text(event, frame_index, render_time_s)
        draw.rounded_rectangle((x0 + 16, y, x1 - 16, y + 34), radius=4, fill=(24, 38, 56, 220))
        draw.text((x0 + 28, y + 10), frame_text, fill=(255, 255, 255, 245), font=font)
        y += 44
    rows = _panel_rows(event, show_reasoning=show_reasoning, show_rag=show_rag)
    for label, value, color in rows:
        draw.rounded_rectangle((x0 + 16, y, x1 - 16, y + 56), radius=4, fill=color)
        draw.text((x0 + 28, y + 8), label, fill=(255, 255, 255, 245), font=font)
        for line_index, line in enumerate(_wrap(value, 58)[:2]):
            draw.text((x0 + 28, y + 24 + line_index * 14), line, fill=(255, 255, 255, 235), font=font)
        y += 64
    claim = (event.claim if event else "sampled_open_loop_reasoning") + " | real_time_vla_control=false"
    draw.text((x0 + 18, y1 - 24), claim, fill=(245, 245, 245, 210), font=font)


def _render_compact_reasoning_overlay_frame(
    draw: Any,
    image_size: tuple[int, int],
    event: ReasoningOverlayEvent | None,
    title: str,
    subtitle: str,
    font: Any,
    *,
    frame_index: int | None = None,
    render_time_s: float | None = None,
    show_frame_time: bool = True,
    show_reasoning: bool = True,
    show_rag: bool = True,
) -> None:
    width, height = image_size
    x0 = 18
    y0 = height - 128
    x1 = width - 18
    y1 = height - 18
    draw.rounded_rectangle((x0, y0, x1, y1), radius=6, fill=(4, 8, 14, 210))
    header = title if not show_frame_time else f"{title} | {_frame_time_text(event, frame_index, render_time_s)}"
    draw.text((x0 + 14, y0 + 10), header, fill=(255, 255, 255, 245), font=font)
    draw.text((x0 + 14, y0 + 26), subtitle, fill=(194, 211, 255, 225), font=font)
    rows = _panel_rows(event, show_reasoning=show_reasoning, show_rag=show_rag)[:3]
    chip_width = max(160, (x1 - x0 - 42) // max(1, len(rows)))
    y = y0 + 50
    for index, (label, value, color) in enumerate(rows):
        chip_x0 = x0 + 14 + index * (chip_width + 8)
        chip_x1 = min(x1 - 14, chip_x0 + chip_width)
        draw.rounded_rectangle((chip_x0, y, chip_x1, y + 42), radius=4, fill=color)
        draw.text((chip_x0 + 8, y + 6), label, fill=(255, 255, 255, 245), font=font)
        draw.text((chip_x0 + 8, y + 22), (_wrap(value, 34) or [""])[0], fill=(255, 255, 255, 235), font=font)
    claim = (event.claim if event else "sampled_open_loop_reasoning") + " | real_time_vla_control=false"
    draw.text((x0 + 14, y1 - 14), claim, fill=(245, 245, 245, 210), font=font)


def _blockers(config: ReasoningOverlayConfig, ffmpeg_path: str | None) -> list[str]:
    blockers: list[str] = []
    if not config.input_video.exists():
        blockers.append(f"Input video does not exist: {config.input_video}")
    if config.fps <= 0:
        blockers.append("fps must be > 0")
    if not ffmpeg_path:
        blockers.append("ffmpeg was not found on PATH")
    return blockers


def _event_for_time(events: list[ReasoningOverlayEvent], time_s: float) -> ReasoningOverlayEvent | None:
    active = [event for event in events if event.start_s <= time_s <= event.end_s]
    if active:
        return active[-1]
    previous = [event for event in events if event.start_s <= time_s]
    return previous[-1] if previous else (events[0] if events else None)


def _frame_time_text(
    event: ReasoningOverlayEvent | None,
    frame_index: int | None,
    render_time_s: float | None,
) -> str:
    frame = "?" if frame_index is None else str(frame_index)
    rendered = "?" if render_time_s is None else f"{render_time_s:.2f}s"
    source = "?" if event is None else f"{event.source_time_s:.2f}s"
    return f"frame {frame} | render t={rendered} | source t={source}"


def _panel_rows(
    event: ReasoningOverlayEvent | None,
    *,
    show_reasoning: bool,
    show_rag: bool,
) -> list[tuple[str, str, tuple[int, int, int, int]]]:
    if event is None:
        rows = [
            ("RISK", "Waiting for scenario evidence", (30, 48, 72, 210)),
            ("ACTION INTENT", "Continue monitoring", (58, 75, 57, 205)),
        ]
        if show_rag:
            rows.insert(1, ("RAG MEMORY", "No memory event yet", (32, 62, 72, 205)))
        if show_reasoning:
            rows.insert(2 if show_rag else 1, ("VLA REASONING", "No sampled reasoning yet", (55, 48, 87, 205)))
        return rows
    rows = [
        ("RISK", event.risk, (118, 41, 41, 215)),
        ("ACTION INTENT", event.action_intent, (63, 98, 57, 210)),
    ]
    if show_rag:
        rows.insert(
            1,
            (
                "RAG MEMORY",
                f"{event.memory_id or 'none'}: {event.memory_principle or 'no retrieved principle'}",
                (20, 83, 91, 210),
            ),
        )
    if show_reasoning:
        rows.insert(2 if show_rag else 1, ("VLA REASONING", event.vla_reasoning or "No CoC snippet linked", (66, 54, 113, 210)))
    return rows


def _wrap(value: str, width: int) -> list[str]:
    return textwrap.wrap(value, width=width) or [""]


def _match_alpamayo_record(alpamayo_batch: dict[str, Any], scenario_id: str | None) -> dict[str, Any] | None:
    records = alpamayo_batch.get("records")
    if not isinstance(records, list):
        return None
    if scenario_id:
        for record in records:
            if isinstance(record, dict) and scenario_id in {record.get("scenario_id"), record.get("case_id")}:
                return record
    return records[0] if records and isinstance(records[0], dict) else None


def _reasoning_snippet(record: dict[str, Any] | None) -> str | None:
    if not record:
        return None
    comparison_path = record.get("comparison_path")
    if isinstance(comparison_path, str) and Path(comparison_path).exists():
        try:
            comparison = json.loads(Path(comparison_path).read_text(encoding="utf-8"))
            records = comparison.get("records", [])
            snippets = [str(item.get("cot_snippet")) for item in records if isinstance(item, dict) and item.get("cot_snippet")]
            if snippets:
                return snippets[-1]
        except (OSError, json.JSONDecodeError):
            pass
    for key in ("cot_snippet", "cot_summary", "vla_reasoning"):
        if record.get(key):
            return str(record.get(key))
    if record.get("reasoning_changed") is not None:
        return f"Alpamayo sampled reasoning linked; reasoning_changed={record.get('reasoning_changed')}"
    return None


def _memory_principle(memory_id: str | None) -> str | None:
    if memory_id is None:
        return None
    if "motorcycle" in memory_id:
        return "leave lateral clearance; do not assume two-wheelers keep lane discipline"
    if "pedestrian" in memory_id:
        return "yield under occlusion before the pedestrian is fully visible"
    if "obstacle" in memory_id:
        return "slow first, classify second, and preserve an escape path"
    return "retrieve prior failure principle and bias toward conservative control"


def _fallback_events(risk_timeline: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for summary in risk_timeline.get("tick_summaries", [])[:8]:
        event = summary.get("nearest_actor")
        if isinstance(event, dict):
            out.append(event)
    return out


def _first(value: Any) -> str | None:
    if isinstance(value, list) and value:
        return str(value[0])
    if value:
        return str(value)
    return None


def _risk_rank(level: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(level, 4)
