"""Compact paused closed-loop hero video assembly."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ClosedLoopVideoInputs:
    trace_path: Path
    rgb_folder: Path | None = None
    source_video: Path | None = None
    scenario_pack: Path | None = None
    output_video: Path | None = None
    output_root: Path | None = None
    run_id: str = "closed-loop-video"
    fps: int = 24
    duration_s: float = 0.0


@dataclass(frozen=True)
class ClosedLoopVideoResult:
    status: str
    video_path: str | None
    manifest_path: str
    sample_frame_paths: tuple[str, ...]
    frame_count: int
    duration_s: float
    blockers: tuple[str, ...]
    claim_boundaries: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "video_path": self.video_path,
            "manifest_path": self.manifest_path,
            "sample_frame_paths": list(self.sample_frame_paths),
            "frame_count": self.frame_count,
            "duration_s": self.duration_s,
            "blockers": list(self.blockers),
            "claim_boundaries": list(self.claim_boundaries),
        }


def build_closed_loop_video(inputs: ClosedLoopVideoInputs) -> ClosedLoopVideoResult:
    run_dir = (inputs.output_root or inputs.trace_path.parent) / inputs.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "closed_loop_video_manifest.json"
    trace = _load_json(inputs.trace_path)
    blockers: list[str] = []
    source_frames = _resolve_source_frames(inputs, trace, run_dir, blockers)
    if blockers:
        result = _blocked_result(manifest_path, blockers)
        _write_manifest(manifest_path, inputs, trace, result, source_frames=[])
        return result
    rendered_dir = run_dir / "rendered_frames"
    rendered_dir.mkdir(parents=True, exist_ok=True)
    duration_s = _target_duration_s(inputs.duration_s, len(source_frames), inputs.fps)
    target_count = max(len(source_frames), int(duration_s * max(inputs.fps, 1)))
    try:
        sample_frame_paths = _render_overlay_frames(
            source_frames=source_frames,
            trace=trace,
            output_dir=rendered_dir,
            target_count=target_count,
        )
    except ModuleNotFoundError as exc:
        blockers.append(f"closed-loop video overlay requires Pillow: {exc}")
        result = _blocked_result(manifest_path, blockers, frame_count=target_count)
        _write_manifest(manifest_path, inputs, trace, result, source_frames=source_frames)
        return result
    video_path = inputs.output_video or (run_dir / "closed_loop_hero.mp4")
    ffmpeg_error = _encode_mp4(rendered_dir, video_path, inputs.fps)
    if ffmpeg_error:
        blockers.append(ffmpeg_error)
        result = _blocked_result(manifest_path, blockers, sample_frame_paths=sample_frame_paths, frame_count=target_count)
        _write_manifest(manifest_path, inputs, trace, result, source_frames=source_frames)
        return result
    result = ClosedLoopVideoResult(
        status="passed",
        video_path=str(video_path),
        manifest_path=str(manifest_path),
        sample_frame_paths=tuple(str(path) for path in sample_frame_paths),
        frame_count=target_count,
        duration_s=round(target_count / max(inputs.fps, 1), 3),
        blockers=(),
        claim_boundaries=(
            "closed_loop_vla_control=paused_receding_horizon",
            "real_time_vla_control=false",
            "time_warped_offline_demo=true",
            f"closed_loop_backend={trace.get('backend')}",
        ),
    )
    _write_manifest(manifest_path, inputs, trace, result, source_frames=source_frames)
    return result


def _resolve_source_frames(
    inputs: ClosedLoopVideoInputs,
    trace: dict[str, Any],
    run_dir: Path,
    blockers: list[str],
) -> list[Path]:
    if inputs.rgb_folder is not None:
        folder = inputs.rgb_folder
    elif trace.get("rgb_folder"):
        folder = Path(str(trace["rgb_folder"]))
    else:
        folder = None
    if folder is not None:
        frames = sorted([*folder.glob("*.png"), *folder.glob("*.jpg"), *folder.glob("*.jpeg")])
        if frames:
            return frames
        blockers.append(f"RGB folder contains no frames: {folder}")
        return []
    if inputs.source_video is not None:
        return _extract_video_frames(inputs.source_video, run_dir / "source_frames", blockers)
    step_frames = []
    for step in trace.get("steps", []):
        if isinstance(step, dict):
            for key in ("visual_rgb_frame_paths", "action_rgb_frame_paths", "pre_rgb_frame_paths", "post_rgb_frame_paths"):
                paths = [Path(str(path)) for path in step.get(key, [])]
                if paths:
                    step_frames.extend(paths)
    if step_frames:
        return step_frames
    blockers.append("No RGB frames were provided by --rgb-folder, --source-video, trace.rgb_folder, or step frame paths")
    return []


def _extract_video_frames(source_video: Path, output_dir: Path, blockers: list[str]) -> list[Path]:
    if not source_video.exists():
        blockers.append(f"Source video does not exist: {source_video}")
        return []
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_video),
        "-vf",
        "fps=6",
        str(output_dir / "source_%06d.png"),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        blockers.append("ffmpeg source extraction failed: " + completed.stderr[-600:])
        return []
    return sorted(output_dir.glob("source_*.png"))


def _render_overlay_frames(
    *,
    source_frames: list[Path],
    trace: dict[str, Any],
    output_dir: Path,
    target_count: int,
) -> list[Path]:
    from PIL import Image, ImageDraw, ImageFont

    steps = [step for step in trace.get("steps", []) if isinstance(step, dict)]
    font = ImageFont.load_default()
    sample_paths: list[Path] = []
    for frame_index in range(target_count):
        source = source_frames[min(len(source_frames) - 1, int(frame_index * len(source_frames) / max(target_count, 1)))]
        image = Image.open(source).convert("RGB")
        draw = ImageDraw.Draw(image, "RGBA")
        width, height = image.size
        step = steps[min(len(steps) - 1, int(frame_index * max(len(steps), 1) / max(target_count, 1)))] if steps else {}
        overlay_h = max(72, min(118, height // 4))
        draw.rectangle((0, height - overlay_h, width, height), fill=(0, 0, 0, 150))
        selected = _selected_action(step)
        safety = _safety_line(step)
        reasoning = _reasoning_line(step)
        draw.text((18, height - overlay_h + 10), f"checkpoint {step.get('step_index', 0)}  |  {selected}", font=font, fill=(255, 255, 255, 255))
        draw.text((18, height - overlay_h + 32), reasoning, font=font, fill=(228, 235, 255, 255))
        draw.text((18, height - overlay_h + 54), safety, font=font, fill=(255, 222, 150, 255))
        draw.text((18, height - 20), "paused closed-loop demo | real_time_vla_control=false", font=font, fill=(220, 220, 220, 255))
        out = output_dir / f"frame_{frame_index:06d}.png"
        image.save(out)
        if frame_index in {0, target_count // 2, target_count - 1}:
            sample_paths.append(out)
    return sample_paths


def _encode_mp4(frames_dir: Path, video_path: Path, fps: int) -> str | None:
    if shutil.which("ffmpeg") is None:
        return "ffmpeg is not installed"
    video_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%06d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(video_path),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        return "ffmpeg MP4 encode failed: " + completed.stderr[-800:]
    return None


def _selected_action(step: dict[str, Any]) -> str:
    summary = step.get("applied_control_summary")
    if isinstance(summary, dict):
        count = summary.get("applied_count", step.get("applied_control_count", 0))
        return f"apply {count} safe controls"
    return f"apply {step.get('applied_control_count', 0)} safe controls"


def _safety_line(step: dict[str, Any]) -> str:
    summary = step.get("safety_summary") or step.get("safety_report")
    if isinstance(summary, dict):
        interventions = summary.get("interventions") or []
        if interventions:
            return "safety: " + ", ".join(str(item) for item in interventions[:2])
        return "safety: no intervention"
    return "safety: recorded in trace"


def _reasoning_line(step: dict[str, Any]) -> str:
    path = step.get("inference_result_path")
    if path and Path(str(path)).exists():
        inference_path = Path(str(path))
        payload = _load_json(inference_path)
        value = _reasoning_value(payload)
        prediction_path = payload.get("prediction_json_path")
        prediction = _load_prediction_for_overlay(prediction_path, inference_path)
        if not value and prediction:
            value = _reasoning_value(prediction)
        if value:
            label = "cached Alpamayo" if prediction.get("cached_prior_prediction") else "VLA"
            return f"{label}: " + str(value).replace("\n", " ")[:128]
    return "VLA: trajectory selected from checkpoint observation"


def _reasoning_value(payload: dict[str, Any]) -> object | None:
    value = (
        payload.get("reasoning_snippet")
        or payload.get("cot_summary")
        or payload.get("cot")
        or payload.get("reasoning")
    )
    extra = payload.get("extra")
    if value is None and isinstance(extra, dict):
        value = extra.get("cot") or extra.get("reasoning")
    return value


def _load_prediction_for_overlay(value: object, inference_path: Path) -> dict[str, Any]:
    candidates: list[Path] = []
    if value:
        candidates.append(Path(str(value)))
    candidates.append(inference_path.with_name("alpamayo_live_prediction.json"))
    for candidate in candidates:
        if candidate.exists():
            return _load_json(candidate)
    return {}


def _blocked_result(
    manifest_path: Path,
    blockers: list[str],
    *,
    sample_frame_paths: list[Path] | None = None,
    frame_count: int = 0,
) -> ClosedLoopVideoResult:
    return ClosedLoopVideoResult(
        status="blocked",
        video_path=None,
        manifest_path=str(manifest_path),
        sample_frame_paths=tuple(str(path) for path in (sample_frame_paths or [])),
        frame_count=frame_count,
        duration_s=0.0,
        blockers=tuple(blockers),
        claim_boundaries=("real_time_vla_control=false",),
    )


def _write_manifest(
    manifest_path: Path,
    inputs: ClosedLoopVideoInputs,
    trace: dict[str, Any],
    result: ClosedLoopVideoResult,
    *,
    source_frames: list[Path],
) -> None:
    manifest = {
        "status": result.status,
        "trace_path": str(inputs.trace_path),
        "rgb_folder": str(inputs.rgb_folder) if inputs.rgb_folder is not None else trace.get("rgb_folder"),
        "source_video": str(inputs.source_video) if inputs.source_video is not None else None,
        "scenario_pack": str(inputs.scenario_pack) if inputs.scenario_pack is not None else None,
        "output_video": result.video_path,
        "sample_frame_paths": list(result.sample_frame_paths),
        "source_frame_count": len(source_frames),
        "seconds_per_source_frame": round(result.duration_s / max(len(source_frames), 1), 4),
        "frame_count": result.frame_count,
        "duration_s": result.duration_s,
        "fps": inputs.fps,
        "backend": trace.get("backend"),
        "policy": trace.get("policy"),
        "step_count": len(list(trace.get("steps", []))),
        "live_carla_provenance": trace.get("backend") == "carla-live",
        "recurrence_visible": len(list(trace.get("steps", []))) >= 2,
        "ego_vehicle_visible": bool(trace.get("ego_vehicle_visible")),
        "visual_camera_role": trace.get("visual_camera_role"),
        "action_rgb_frame_count": trace.get("action_rgb_frame_count", 0),
        "blockers": list(result.blockers),
        "claim_boundaries": list(result.claim_boundaries),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _target_duration_s(requested_duration_s: float, source_frame_count: int, fps: int) -> float:
    if requested_duration_s > 0:
        return max(requested_duration_s, 1.0)
    if source_frame_count <= 0:
        return 1.0
    # Keep paused-loop demos brisk: sparse frames should not be stretched into
    # a fake 60s movie, while richer action captures can breathe a little.
    return min(max(source_frame_count / 12.0, 3.0), 12.0)


__all__ = [
    "ClosedLoopVideoInputs",
    "ClosedLoopVideoResult",
    "build_closed_loop_video",
]
