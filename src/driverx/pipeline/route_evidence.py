"""Normalize route video, telemetry, and result artifacts into one evidence bundle."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from driverx.simulators.simlingo_results import parse_simlingo_result


@dataclass(frozen=True)
class RouteEvidenceInputs:
    plan_path: Path | None = None
    result_path: Path | None = None
    entity_tracks_path: Path | None = None
    video_path: Path | None = None
    screenshot_paths: tuple[Path, ...] = field(default_factory=tuple)
    log_paths: tuple[Path, ...] = field(default_factory=tuple)
    video_duration_s: float | None = None


def build_route_evidence(run_dir: Path, inputs: RouteEvidenceInputs) -> dict[str, Any]:
    plan = _load_optional_mapping(inputs.plan_path)
    expected = _mapping(plan.get("expected_outputs")) if plan else {}
    result_path = _coalesce_path(inputs.result_path, expected.get("result"))
    tracks_path = _coalesce_path(inputs.entity_tracks_path, expected.get("entity_tracks") or expected.get("tracks"))
    video_path = _coalesce_path(inputs.video_path, expected.get("video"))
    screenshots = tuple(path.expanduser() for path in inputs.screenshot_paths)
    logs = tuple(path.expanduser() for path in inputs.log_paths)
    result = _result_evidence(result_path)
    tracks = _tracks_evidence(tracks_path)
    video = _video_evidence(video_path, inputs.video_duration_s)
    screenshot_assets = [_file_asset(path, "screenshot") for path in screenshots]
    log_assets = [_log_asset(path) for path in logs]
    blockers = _blockers(
        plan=plan,
        result=result,
        tracks=tracks,
        video=video,
        screenshots=screenshot_assets,
        logs=log_assets,
    )
    payload = {
        "status": _status(blockers, result, tracks, video),
        "plan": _plan_summary(inputs.plan_path, plan),
        "result": result,
        "entity_tracks": tracks,
        "video": video,
        "screenshots": screenshot_assets,
        "logs": log_assets,
        "blockers": blockers,
        "metrics": _metrics(result, tracks, video),
    }
    return write_route_evidence(run_dir, payload)


def write_route_evidence(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "run_evidence.json"
    report_path = run_dir / "run_evidence.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _load_optional_mapping(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    expanded = path.expanduser()
    if not expanded.exists():
        return {
            "path": str(expanded),
            "live_blockers": [f"Plan not found: {expanded}"],
        }
    payload = json.loads(expanded.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {expanded}")
    return payload


def _coalesce_path(explicit_path: Path | None, planned_value: Any) -> Path | None:
    if explicit_path is not None:
        return explicit_path.expanduser()
    if planned_value in (None, ""):
        return None
    return Path(str(planned_value)).expanduser()


def _result_evidence(path: Path | None) -> dict[str, Any]:
    asset = _file_asset(path, "route_result")
    if path is None or not path.exists() or not path.is_file():
        return {**asset, "summary": None}
    try:
        record = parse_simlingo_result(path)
        summary = {
            "status": record.status,
            "success": record.success,
            "driving_score": record.driving_score,
            "route_completion": record.route_completion,
            "infraction_penalty": record.infraction_penalty,
            "duration_game_s": record.duration_game_s,
            "duration_system_s": record.duration_system_s,
            "route_count": record.route_count,
            "primary_route": record.primary_route.to_jsonable() if record.primary_route else None,
            "infraction_counts": _infraction_counts(record.infractions),
        }
    except Exception as exc:
        summary = {"parse_error": str(exc)}
    return {**asset, "summary": summary}


def _tracks_evidence(path: Path | None) -> dict[str, Any]:
    asset = _file_asset(path, "entity_tracks")
    if path is None or not path.exists() or not path.is_file():
        return {**asset, "summary": None}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {**asset, "summary": {"parse_error": str(exc)}}
    tracks = _extract_track_list(payload)
    actor_refs = sorted(
        {
            value
            for track in tracks
            for value in [_track_actor_ref(track)]
            if value is not None
        }
    )
    return {
        **asset,
        "summary": {
            "track_count": len(tracks),
            "actor_refs": actor_refs,
            "sample_count": _track_sample_count(tracks),
            "cleanup_destroyed_ids": _cleanup_destroyed_ids(payload),
        },
    }


def _video_evidence(path: Path | None, duration_s: float | None) -> dict[str, Any]:
    return {
        **_file_asset(path, "video"),
        "duration_s": duration_s,
    }


def _file_asset(path: Path | None, label: str) -> dict[str, Any]:
    if path is None:
        return {
            "label": label,
            "path": None,
            "exists": False,
            "size_bytes": None,
        }
    expanded = path.expanduser()
    return {
        "label": label,
        "path": str(expanded),
        "exists": expanded.exists(),
        "size_bytes": expanded.stat().st_size if expanded.exists() and expanded.is_file() else None,
    }


def _log_asset(path: Path) -> dict[str, Any]:
    asset = _file_asset(path, "log")
    if not path.exists() or not path.is_file():
        return {**asset, "tail": []}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return {**asset, "tail": lines[-20:]}


def _blockers(
    *,
    plan: dict[str, Any],
    result: dict[str, Any],
    tracks: dict[str, Any],
    video: dict[str, Any],
    screenshots: list[dict[str, Any]],
    logs: list[dict[str, Any]],
) -> list[str]:
    blockers = _plan_blockers(plan, result, video)
    blockers.extend(_missing_blocker(result, "route result"))
    blockers.extend(_missing_blocker(tracks, "entity tracks"))
    blockers.extend(_missing_blocker(video, "route video"))
    for screenshot in screenshots:
        blockers.extend(_missing_blocker(screenshot, "screenshot"))
    for log in logs:
        blockers.extend(_missing_blocker(log, "log"))
    for label, component in [
        ("route result", result),
        ("entity tracks", tracks),
    ]:
        parse_error = _mapping(component.get("summary")).get("parse_error")
        if parse_error:
            blockers.append(f"{label.title()} parse error: {parse_error}")
    return blockers


def _plan_blockers(
    plan: dict[str, Any],
    result: dict[str, Any],
    video: dict[str, Any],
) -> list[str]:
    expected = _mapping(plan.get("expected_outputs"))
    rgb_folder = Path(str(expected.get("rgb_folder"))).expanduser() if expected.get("rgb_folder") else None
    return [
        f"Plan blocker: {blocker}"
        for blocker in list(plan.get("live_blockers", []))
        if not _is_stale_plan_blocker(str(blocker), rgb_folder=rgb_folder, result=result, video=video)
    ]


def _is_stale_plan_blocker(
    blocker: str,
    *,
    rgb_folder: Path | None,
    result: dict[str, Any],
    video: dict[str, Any],
) -> bool:
    text = blocker.lower()
    if "rgb folder does not exist yet" in text:
        return bool(video.get("exists")) or _has_frame_files(rgb_folder)
    if "video tool not found" in text:
        return bool(video.get("exists"))
    if "route result" in text and bool(result.get("exists")):
        return True
    return False


def _has_frame_files(folder: Path | None) -> bool:
    if folder is None or not folder.exists() or not folder.is_dir():
        return False
    suffixes = {".jpg", ".jpeg", ".png"}
    return any(path.is_file() and path.suffix.lower() in suffixes for path in folder.iterdir())


def _missing_blocker(asset: dict[str, Any], label: str) -> list[str]:
    if asset.get("path") and not asset.get("exists"):
        return [f"Missing {label}: {asset['path']}"]
    return []


def _status(
    blockers: list[str],
    result: dict[str, Any],
    tracks: dict[str, Any],
    video: dict[str, Any],
) -> str:
    if not blockers and result.get("exists") and tracks.get("exists") and video.get("exists"):
        return "ready"
    if any(component.get("exists") for component in [result, tracks, video]):
        return "partial"
    return "blocked" if blockers else "empty"


def _plan_summary(path: Path | None, plan: dict[str, Any]) -> dict[str, Any] | None:
    if not path and not plan:
        return None
    return {
        "path": str(path.expanduser()) if path else plan.get("path"),
        "run_command": plan.get("run_command"),
        "video_command": plan.get("video_command"),
        "expected_outputs": plan.get("expected_outputs", {}),
        "live_blockers": list(plan.get("live_blockers", [])),
    }


def _metrics(
    result: dict[str, Any],
    tracks: dict[str, Any],
    video: dict[str, Any],
) -> dict[str, Any]:
    result_summary = _mapping(result.get("summary"))
    track_summary = _mapping(tracks.get("summary"))
    return {
        "driving_score": result_summary.get("driving_score"),
        "route_completion": result_summary.get("route_completion"),
        "infraction_penalty": result_summary.get("infraction_penalty"),
        "duration_game_s": result_summary.get("duration_game_s"),
        "duration_system_s": result_summary.get("duration_system_s"),
        "track_count": track_summary.get("track_count"),
        "actor_refs": track_summary.get("actor_refs", []),
        "video_duration_s": video.get("duration_s"),
        "video_size_bytes": video.get("size_bytes"),
    }


def _extract_track_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("tracks", "entity_tracks", "actor_tracks"):
            value = payload.get(key)
            if isinstance(value, list):
                return [dict(item) for item in value if isinstance(item, dict)]
    return []


def _track_actor_ref(track: dict[str, Any]) -> str | None:
    for key in ("actor_ref", "label", "role", "actor_id"):
        value = track.get(key)
        if value is not None:
            return str(value)
    return None


def _track_sample_count(tracks: list[dict[str, Any]]) -> int:
    total = 0
    for track in tracks:
        samples = track.get("samples")
        if isinstance(samples, list):
            total += len(samples)
        elif "t_s" in track:
            total += 1
    return total


def _cleanup_destroyed_ids(payload: Any) -> list[Any]:
    if isinstance(payload, dict):
        destroyed = payload.get("destroyed_actor_ids")
        if isinstance(destroyed, list):
            return destroyed
    return []


def _infraction_counts(infractions: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key, value in infractions.items():
        counts[str(key)] = len(value) if isinstance(value, list) else int(bool(value))
    return counts


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _markdown(payload: dict[str, Any]) -> str:
    metrics = _mapping(payload.get("metrics"))
    video = _mapping(payload.get("video"))
    lines = [
        "# Route Evidence",
        "",
        f"- status: `{payload.get('status')}`",
        f"- blockers: `{len(list(payload.get('blockers', [])))}`",
        f"- driving_score: `{metrics.get('driving_score')}`",
        f"- route_completion: `{metrics.get('route_completion')}`",
        f"- track_count: `{metrics.get('track_count')}`",
        f"- video_path: `{video.get('path')}`",
        f"- video_duration_s: `{video.get('duration_s')}`",
        "",
        "## Artifacts",
        "",
    ]
    for label in ["result", "entity_tracks", "video"]:
        artifact = _mapping(payload.get(label))
        lines.append(
            f"- {label}: exists=`{artifact.get('exists')}` path=`{artifact.get('path')}`"
        )
    lines.extend(["", "## Blockers", ""])
    blockers = [str(blocker) for blocker in list(payload.get("blockers", []))]
    if blockers:
        lines.extend(f"- {blocker}" for blocker in blockers)
    else:
        lines.append("- None.")
    lines.extend(["", "## Logs", ""])
    logs = list(payload.get("logs", []))
    if logs:
        for log in logs:
            log_map = _mapping(log)
            lines.append(f"- `{log_map.get('path')}` exists=`{log_map.get('exists')}`")
    else:
        lines.append("- None attached.")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "RouteEvidenceInputs",
    "build_route_evidence",
    "write_route_evidence",
]
