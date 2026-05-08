"""Assemble Environment Studio, CARLA proof, and keyframe analysis into a story pack."""

from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios.studio_product_helpers import oodrive_command


CLAIM_BOUNDARIES = [
    "time_warped_offline_demo=true",
    "sampled_open_loop_reasoning=true",
    "closed_loop_vla_control=false",
    "real_time_vla_control=false",
]


def build_environment_reasoned_carla_video(
    *,
    environment_summary_path: Path,
    visual_proof_path: Path,
    keyframe_analysis_path: Path,
    output_root: Path,
    run_id: str,
    target_duration_s: float = 120.0,
) -> dict[str, Any]:
    """Build a judge-video story pack from generated env, CARLA visual proof, and keyframe analysis."""

    target_duration_s = max(12.0, target_duration_s)
    run_dir = prepare_run_dir(output_root, run_id)
    environment_summary = _load_json(environment_summary_path)
    visual = _load_json(visual_proof_path)
    keyframes = _load_json(keyframe_analysis_path)
    analyses = _analyses_with_images(keyframes)
    blockers: list[str] = []
    if not visual.get("preview_image_path"):
        blockers.append("No CARLA preview image is available; run `oodrive render-env --live` on Kasm/CARLA first.")
    if not analyses:
        blockers.append("No frame-linked keyframe analyses are available for video assembly.")
    timeline_segments = _timeline_segments(
        environment_summary=environment_summary,
        visual=visual,
        analyses=analyses,
        target_duration_s=target_duration_s,
    )
    video_render: dict[str, Any] = {
        "status": "not_started",
        "video_path": None,
        "sample_frame_path": None,
        "frame_dir_path": None,
        "command": [],
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "blockers": [],
    }
    if not blockers:
        video_render = _render_video_from_keyframes(
            run_dir=run_dir,
            visual=visual,
            analyses=analyses,
            timeline_segments=timeline_segments,
            target_duration_s=target_duration_s,
        )
        blockers.extend(str(item) for item in list(video_render.get("blockers", [])))
    video_path = video_render.get("video_path") if video_render.get("status") == "passed" else None
    payload = {
        "status": "blocked" if blockers else "passed" if video_path else "planned",
        "video_path": video_path,
        "overlay_report_path": str(run_dir / "environment_reasoned_carla_demo.json"),
        "report_path": str(run_dir / "environment_reasoned_carla_demo.md"),
        "commands_path": str(run_dir / "commands.sh"),
        "duration_s": target_duration_s if video_path else 0.0 if blockers else target_duration_s,
        "target_duration_s": target_duration_s,
        "video_render": video_render,
        "source_lineage": {
            "environment_summary_path": str(environment_summary_path),
            "visual_proof_path": str(visual_proof_path),
            "keyframe_analysis_path": str(keyframe_analysis_path),
            "same_lineage": bool(visual.get("same_lineage")) and bool(keyframes.get("same_lineage")),
        },
        "environment_recipe_id": visual.get("environment_recipe_id"),
        "scenario_id": visual.get("scenario_id"),
        "timeline_segments": timeline_segments,
        "claim_boundaries": list(CLAIM_BOUNDARIES),
        "blockers": blockers,
        "next_commands": [
            oodrive_command(
                f"score-env-proof --environment-summary {environment_summary_path} "
                f"--visual-proof {visual_proof_path} --keyframe-analysis {keyframe_analysis_path} "
                f"--overlay-report {run_dir / 'environment_reasoned_carla_demo.json'} --metric-only"
            )
        ],
    }
    return write_environment_reasoned_carla_video(run_dir, payload)


def write_environment_reasoned_carla_video(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Write story-pack JSON/Markdown/commands."""

    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "environment_reasoned_carla_demo.json"
    report_path = run_dir / "environment_reasoned_carla_demo.md"
    commands_path = run_dir / "commands.sh"
    payload = {
        **payload,
        "overlay_report_path": str(json_path),
        "report_path": str(report_path),
        "commands_path": str(commands_path),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    commands_path.write_text(_commands(payload), encoding="utf-8")
    return payload


def _timeline_segments(
    *,
    environment_summary: dict[str, Any],
    visual: dict[str, Any],
    analyses: list[dict[str, Any]],
    target_duration_s: float,
) -> list[dict[str, Any]]:
    target_duration_s = max(12.0, target_duration_s)
    claim_duration_s = min(6.0, max(3.0, target_duration_s * 0.08))
    claim_start_s = max(0.0, target_duration_s - claim_duration_s)
    intro_end_s = min(8.0, max(2.0, claim_start_s * 0.3))
    segments: list[dict[str, Any]] = [
        {
            "start_s": 0.0,
            "end_s": intro_end_s,
            "kind": "cli_generation",
            "frame_index": None,
            "source_time_s": None,
            "text": (
                f"OODrive generated {len(list(environment_summary.get('recipes', [])))} environment recipes "
                f"across {len(list(environment_summary.get('families', [])))} families."
            ),
        }
    ]
    preview = visual.get("preview_image_path")
    cursor = intro_end_s
    if preview:
        preview_end_s = min(claim_start_s, cursor + min(10.0, max(3.0, claim_start_s * 0.2)))
        segments.append(
            {
                "start_s": cursor,
                "end_s": preview_end_s,
                "kind": "carla_preview",
                "frame_index": None,
                "source_time_s": None,
                "text": f"CARLA preview for generated environment `{visual.get('environment_recipe_id')}`: {preview}",
            }
        )
        cursor = preview_end_s
    selected_analyses = analyses[:8]
    slot_s = max(2.0, (claim_start_s - cursor) / max(len(selected_analyses), 1))
    for analysis in selected_analyses:
        if cursor >= claim_start_s:
            break
        segments.append(
            {
                "start_s": cursor,
                "end_s": min(claim_start_s, cursor + slot_s),
                "kind": "keyframe_reasoning",
                "frame_index": analysis.get("frame_index"),
                "source_time_s": analysis.get("source_time_s"),
                "text": analysis.get("vla_reasoning") or "; ".join(str(item) for item in list(analysis.get("blockers", []))),
            }
        )
        cursor += slot_s
    segments.append(
        {
            "start_s": claim_start_s,
            "end_s": target_duration_s,
            "kind": "claim_boundary",
            "frame_index": None,
            "source_time_s": None,
            "text": "Sampled open-loop reasoning; not real-time closed-loop VLA control.",
        }
    )
    return segments


def _analyses_with_images(payload: dict[str, Any]) -> list[dict[str, Any]]:
    analyses: list[dict[str, Any]] = []
    for item in list(payload.get("analyses", [])):
        if not isinstance(item, dict):
            continue
        image = item.get("image_path")
        if image and Path(str(image)).exists():
            analyses.append(dict(item))
    return analyses


def _render_video_from_keyframes(
    *,
    run_dir: Path,
    visual: dict[str, Any],
    analyses: list[dict[str, Any]],
    timeline_segments: list[dict[str, Any]],
    target_duration_s: float,
    fps: int = 4,
) -> dict[str, Any]:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        return _video_render_blocked("ffmpeg was not found on PATH")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        return _video_render_blocked(f"Pillow unavailable: {exc}")
    preview_path = Path(str(visual.get("preview_image_path")))
    if not preview_path.exists():
        return _video_render_blocked(f"CARLA preview image does not exist: {preview_path}")
    frame_dir = run_dir / "environment_reasoned_carla_frames"
    shutil.rmtree(frame_dir, ignore_errors=True)
    frame_dir.mkdir(parents=True, exist_ok=True)
    frames = max(1, int(round(target_duration_s * fps)))
    font = ImageFont.load_default()
    image_by_frame = {
        int(item.get("frame_index")): Path(str(item.get("image_path")))
        for item in analyses
        if item.get("frame_index") is not None and item.get("image_path")
    }
    for frame_number in range(frames):
        render_time_s = frame_number / fps
        segment = _segment_for_time(timeline_segments, render_time_s)
        image_path = _image_for_segment(segment, preview_path, image_by_frame)
        frame = _render_story_frame(
            image_path=image_path,
            segment=segment,
            visual=visual,
            font=font,
            image_module=Image,
            draw_module=ImageDraw,
            render_time_s=render_time_s,
            frame_number=frame_number,
        )
        frame.save(frame_dir / f"frame_{frame_number + 1:06d}.png")
    video_path = run_dir / "environment_reasoned_carla_demo.mp4"
    command = [
        ffmpeg_path,
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frame_dir / "frame_%06d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(fps),
        str(video_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    status = "passed" if completed.returncode == 0 and video_path.exists() else "failed"
    blockers = [] if status == "passed" else ["ffmpeg failed to assemble environment reasoned CARLA video"]
    return {
        "status": status,
        "video_path": str(video_path) if status == "passed" else None,
        "sample_frame_path": str(frame_dir / "frame_000001.png") if frames else None,
        "frame_dir_path": str(frame_dir),
        "fps": fps,
        "frame_count": frames,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "blockers": blockers,
    }


def _video_render_blocked(blocker: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "video_path": None,
        "sample_frame_path": None,
        "frame_dir_path": None,
        "fps": 0,
        "frame_count": 0,
        "command": [],
        "returncode": None,
        "stdout": "",
        "stderr": blocker,
        "blockers": [blocker],
    }


def _segment_for_time(segments: list[dict[str, Any]], render_time_s: float) -> dict[str, Any]:
    for segment in segments:
        if _float(segment.get("start_s")) <= render_time_s < _float(segment.get("end_s")):
            return segment
    return segments[-1] if segments else {"kind": "claim_boundary", "text": "OODrive proof segment"}


def _image_for_segment(segment: dict[str, Any], preview_path: Path, image_by_frame: dict[int, Path]) -> Path:
    frame_index = segment.get("frame_index")
    if frame_index is not None:
        path = image_by_frame.get(int(frame_index))
        if path is not None and path.exists():
            return path
    return preview_path


def _render_story_frame(
    *,
    image_path: Path,
    segment: dict[str, Any],
    visual: dict[str, Any],
    font: Any,
    image_module: Any,
    draw_module: Any,
    render_time_s: float,
    frame_number: int,
) -> Any:
    canvas = image_module.new("RGB", (1280, 720), (14, 18, 22))
    with image_module.open(image_path) as source:
        source = source.convert("RGB")
        fitted = _fit_image(source, (1280, 720), image_module=image_module)
        canvas.paste(fitted, ((1280 - fitted.size[0]) // 2, (720 - fitted.size[1]) // 2))
    draw = draw_module.Draw(canvas, "RGBA")
    draw.rectangle((0, 0, 1280, 96), fill=(0, 0, 0, 182))
    draw.rectangle((0, 482, 1280, 720), fill=(0, 0, 0, 198))
    draw.text((32, 22), "OODrive generated environment -> CARLA -> sampled Alpamayo reasoning", fill=(255, 255, 255), font=font)
    draw.text(
        (32, 52),
        f"recipe={visual.get('environment_recipe_id')} scenario={visual.get('scenario_id')} same_lineage={visual.get('same_lineage')}",
        fill=(218, 238, 255),
        font=font,
    )
    frame_label = f"demo_frame={frame_number} demo_t={render_time_s:.1f}s"
    source_time = segment.get("source_time_s")
    if source_time is not None:
        frame_label += f" source_t={float(source_time):.2f}s source_frame={segment.get('frame_index')}"
    draw.text((980, 22), frame_label, fill=(255, 230, 180), font=font)
    kind = str(segment.get("kind") or "proof")
    draw.text((32, 506), kind.replace("_", " ").upper(), fill=(255, 230, 180), font=font)
    text = str(segment.get("text") or "")
    y = 532
    for line in _wrap(text, width=112, max_lines=5):
        draw.text((32, y), line, fill=(255, 255, 255), font=font)
        y += 22
    claims = " | ".join(CLAIM_BOUNDARIES)
    draw.text((32, 682), claims, fill=(188, 220, 255), font=font)
    return canvas


def _fit_image(image: Any, target_size: tuple[int, int], *, image_module: Any) -> Any:
    width, height = image.size
    target_width, target_height = target_size
    scale = min(target_width / max(width, 1), target_height / max(height, 1))
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    resampling = getattr(getattr(image_module, "Resampling", image_module), "LANCZOS", 1)
    return image.resize(new_size, resampling)


def _wrap(text: str, *, width: int, max_lines: int) -> list[str]:
    lines = textwrap.wrap(text, width=width)
    if len(lines) > max_lines:
        return [*lines[: max_lines - 1], lines[max_lines - 1][: max(0, width - 3)] + "..."]
    return lines or [""]


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OODrive Environment To Reasoned CARLA Demo",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Video: `{payload.get('video_path')}`",
        f"- Same lineage: `{payload.get('source_lineage', {}).get('same_lineage')}`",
        f"- Segments: `{len(list(payload.get('timeline_segments', [])))}`",
        "",
        "## Segments",
        "",
    ]
    for segment in list(payload.get("timeline_segments", [])):
        lines.append(
            f"- `{segment.get('kind')}` {segment.get('start_s')}s-{segment.get('end_s')}s: {segment.get('text')}"
        )
    blockers = list(payload.get("blockers", []))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        for blocker in blockers:
            lines.append(f"- {blocker}")
    lines.extend(["", "## Claim Boundaries", ""])
    for claim in list(payload.get("claim_boundaries", [])):
        lines.append(f"- `{claim}`")
    lines.append("")
    return "\n".join(lines)


def _commands(payload: dict[str, Any]) -> str:
    lines = ["#!/usr/bin/env bash", "set -euo pipefail", ""]
    lines.extend(str(command) for command in list(payload.get("next_commands", [])))
    return "\n".join(lines) + "\n"


def _float(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


__all__ = [
    "CLAIM_BOUNDARIES",
    "build_environment_reasoned_carla_video",
    "write_environment_reasoned_carla_video",
]
