"""Promotion gate for paused closed-loop hero videos."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.evaluation.closed_loop_control_score import load_closed_loop_trace


@dataclass(frozen=True)
class ClosedLoopVideoScoreReport:
    status: str
    closed_loop_video_score: float
    threshold: float
    components: dict[str, float]
    blockers: list[str]
    warnings: list[str]
    trace_path: str
    manifest_path: str | None
    video_path: str | None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "closed_loop_video_score": self.closed_loop_video_score,
            "threshold": self.threshold,
            "components": dict(self.components),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "trace_path": self.trace_path,
            "manifest_path": self.manifest_path,
            "video_path": self.video_path,
        }


def score_closed_loop_video(
    *,
    trace_path: Path,
    manifest_path: Path | None = None,
    video_path: Path | None = None,
    threshold: float = 76.0,
) -> ClosedLoopVideoScoreReport:
    trace = load_closed_loop_trace(trace_path)
    manifest = _load_manifest(manifest_path)
    resolved_video = video_path or _manifest_path(manifest, "output_video")
    components, blockers, warnings = _components(trace, manifest, resolved_video)
    score = round(sum(components.values()), 4)
    if score < threshold:
        blockers.append(f"closed_loop_video_score {score:.4f} below {threshold:.4f}")
    status = "passed" if not blockers and score >= threshold else "blocked"
    return ClosedLoopVideoScoreReport(
        status=status,
        closed_loop_video_score=score,
        threshold=threshold,
        components=components,
        blockers=_dedupe(blockers),
        warnings=warnings,
        trace_path=str(trace_path),
        manifest_path=str(manifest_path) if manifest_path is not None else None,
        video_path=str(resolved_video) if resolved_video is not None else None,
    )


def write_closed_loop_video_score(run_dir: Path, report: ClosedLoopVideoScoreReport) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_jsonable()
    json_path = run_dir / "closed_loop_video_score.json"
    report_path = run_dir / "closed_loop_video_score.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _components(
    trace: dict[str, Any],
    manifest: dict[str, Any],
    video_path: Path | None,
) -> tuple[dict[str, float], list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    steps = [step for step in trace.get("steps", []) if isinstance(step, dict)]
    live = trace.get("backend") == "carla-live" and bool(manifest.get("live_carla_provenance"))
    model_driven = trace.get("policy") == "alpamayo-remote" and _has_non_fake_inference(steps)
    recurrence = len(steps) >= 2 and bool(manifest.get("recurrence_visible", len(steps) >= 2))
    video_exists = video_path is not None and video_path.exists()
    if not live:
        blockers.append("live CARLA provenance is required for hero promotion")
    if not model_driven:
        blockers.append("hero promotion requires Alpamayo remote inference or exact remote cache hits, not fake trajectory policy")
    if not recurrence:
        blockers.append("video must show at least two observe/infer/act/observe recurrences")
    if not video_exists:
        blockers.append(f"video does not exist: {video_path}")
    frame_count = int(manifest.get("frame_count") or 0)
    duration_s = float(manifest.get("duration_s") or 0.0)
    source_frame_count = int(manifest.get("source_frame_count") or trace.get("source_frame_count") or 0)
    action_frame_count = int(manifest.get("action_rgb_frame_count") or trace.get("action_rgb_frame_count") or 0)
    ego_vehicle_visible = bool(manifest.get("ego_vehicle_visible") or trace.get("ego_vehicle_visible"))
    visual_camera_role = str(manifest.get("visual_camera_role") or trace.get("visual_camera_role") or "")
    seconds_per_source_frame = duration_s / max(source_frame_count, 1)
    if video_exists:
        probed = _probe_video(video_path)
        frame_count = max(frame_count, int(probed.get("frame_count") or 0))
        duration_s = max(duration_s, float(probed.get("duration_s") or 0.0))
        seconds_per_source_frame = duration_s / max(source_frame_count, 1)
        if probed.get("warning"):
            warnings.append(str(probed["warning"]))
    min_source_frames = max(8, len(steps) * 4)
    if source_frame_count < min_source_frames:
        blockers.append(f"video source is too sparse: source_frame_count={source_frame_count}, required>={min_source_frames}")
    if not ego_vehicle_visible:
        blockers.append("hero video must use a third-person or spectator view where the ego vehicle is visible")
    if seconds_per_source_frame > 0.75:
        blockers.append(f"video is over-stretched: seconds_per_source_frame={seconds_per_source_frame:.3f} exceeds 0.750")
    components = {
        "live_carla_provenance": 10.0 if live else 0.0,
        "model_driven_policy": 8.0 if model_driven else 0.0,
        "recurrence_visibility": 10.0 if recurrence else 0.0,
        "duration": _duration_quality(duration_s) * 5.0,
        "frame_count": min(frame_count / 120.0, 1.0) * 5.0,
        "source_frame_density": _source_density(source_frame_count, min_source_frames, seconds_per_source_frame) * 12.0,
        "ego_vehicle_visible": (1.0 if ego_vehicle_visible and visual_camera_role in {"third_person_chase", "spectator_chase"} else 0.6 if ego_vehicle_visible else 0.0) * 14.0,
        "road_alignment": _step_fraction(steps, "planned_vs_actual_error_m", max_value=3.0) * 8.0,
        "smoothness": _smoothness(frame_count, duration_s) * 6.0,
        "visible_ood_object": _visible_ood_score(trace, steps) * 6.0,
        "action_tick_visibility": min(action_frame_count / max(len(steps) * 2, 1), 1.0) * 4.0,
        "overlay_legibility": _overlay_score(manifest) * 6.0,
        "claim_honesty": _claim_honesty(trace, manifest) * 6.0,
    }
    return {key: round(value, 4) for key, value in components.items()}, blockers, warnings


def _step_fraction(steps: list[dict[str, Any]], key: str, *, max_value: float) -> float:
    if not steps:
        return 0.0
    ok = 0
    for step in steps:
        value = step.get(key)
        if isinstance(value, int | float) and float(value) <= max_value:
            ok += 1
    return ok / len(steps)


def _smoothness(frame_count: int, duration_s: float) -> float:
    if frame_count <= 0 or duration_s <= 0:
        return 0.0
    fps = frame_count / duration_s
    return min(fps / 12.0, 1.0)


def _duration_quality(duration_s: float) -> float:
    if duration_s <= 0:
        return 0.0
    if 3.0 <= duration_s <= 20.0:
        return 1.0
    if duration_s < 3.0:
        return duration_s / 3.0
    return max(0.0, 1.0 - min((duration_s - 20.0) / 40.0, 1.0))


def _source_density(source_frame_count: int, min_source_frames: int, seconds_per_source_frame: float) -> float:
    if source_frame_count <= 0:
        return 0.0
    count_score = min(source_frame_count / max(min_source_frames, 1), 1.0)
    pacing_score = 1.0 if seconds_per_source_frame <= 0.5 else max(0.0, 1.0 - min((seconds_per_source_frame - 0.5) / 0.5, 1.0))
    return min(count_score, pacing_score)


def _visible_ood_score(trace: dict[str, Any], steps: list[dict[str, Any]]) -> float:
    if trace.get("visible_ood_object") is True or trace.get("entity_tracks_path"):
        return 1.0
    for step in steps:
        if step.get("post_rgb_frame_paths") or step.get("pre_rgb_frame_paths"):
            return 0.7
    return 0.0


def _has_non_fake_inference(steps: list[dict[str, Any]]) -> bool:
    if not steps:
        return False
    ok = 0
    for step in steps:
        path = step.get("inference_result_path")
        if not path or not Path(str(path)).exists():
            continue
        try:
            payload = json.loads(Path(str(path)).read_text(encoding="utf-8"))
        except Exception:
            continue
        mode = str(payload.get("mode", ""))
        status = str(payload.get("status", ""))
        if mode == "remote-kasm" and status in {"passed", "cached"}:
            ok += 1
    return ok >= len(steps)


def _overlay_score(manifest: dict[str, Any]) -> float:
    if manifest.get("sample_frame_paths"):
        return 1.0
    if manifest.get("status") == "passed":
        return 0.7
    return 0.0


def _claim_honesty(trace: dict[str, Any], manifest: dict[str, Any]) -> float:
    claims = {str(item) for item in list(trace.get("claim_boundaries", []))}
    claims.update(str(item) for item in list(manifest.get("claim_boundaries", [])))
    score = 0.0
    if "real_time_vla_control=false" in claims:
        score += 0.35
    if "time_warped_offline_demo=true" in claims:
        score += 0.25
    if "closed_loop_vla_control=paused_receding_horizon" in claims:
        score += 0.25
    if "live_carla_provenance=true" in claims or manifest.get("live_carla_provenance"):
        score += 0.15
    return min(score, 1.0)


def _probe_video(video_path: Path) -> dict[str, Any]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=nb_frames,duration",
        "-of",
        "json",
        str(video_path),
    ]
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=10.0)
    except Exception as exc:
        return {"warning": f"ffprobe unavailable: {exc}"}
    if completed.returncode != 0:
        return {"warning": "ffprobe failed: " + completed.stderr[-400:]}
    payload = json.loads(completed.stdout or "{}")
    streams = payload.get("streams") if isinstance(payload, dict) else None
    stream = streams[0] if isinstance(streams, list) and streams else {}
    return {
        "frame_count": _int_or_zero(stream.get("nb_frames")),
        "duration_s": _float_or_zero(stream.get("duration")),
    }


def _load_manifest(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _manifest_path(manifest: dict[str, Any], key: str) -> Path | None:
    value = manifest.get(key)
    return Path(str(value)) if value else None


def _int_or_zero(value: object) -> int:
    try:
        return int(str(value))
    except Exception:
        return 0


def _float_or_zero(value: object) -> float:
    try:
        return float(str(value))
    except Exception:
        return 0.0


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Closed-Loop Video Score",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Score: `{payload.get('closed_loop_video_score')}`",
        f"- Threshold: `{payload.get('threshold')}`",
        "",
        "## Components",
        "",
    ]
    for key, value in dict(payload.get("components", {})).items():
        lines.append(f"- `{key}`: `{value}`")
    blockers = list(payload.get("blockers", []))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in blockers)
    lines.append("")
    return "\n".join(lines)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


__all__ = [
    "ClosedLoopVideoScoreReport",
    "score_closed_loop_video",
    "write_closed_loop_video_score",
]
