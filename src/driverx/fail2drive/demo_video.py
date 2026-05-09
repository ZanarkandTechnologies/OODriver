"""Judge-visible Fail2Drive demo report/video assembly."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Fail2DriveDemoVideoConfig:
    evidence_path: Path
    reasoning_path: Path
    route_path: Path
    output_root: Path
    run_id: str
    input_video_path: Path | None = None
    rgb_folder: Path | None = None
    speed_factor: float = 4.0
    target_duration_s: float = 90.0


def run_fail2drive_demo_video(config: Fail2DriveDemoVideoConfig) -> dict[str, Any]:
    run_dir = config.output_root / config.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    evidence = _load_json(config.evidence_path)
    reasoning = _load_json(config.reasoning_path)
    source_video = _source_video(config.input_video_path, evidence)
    blockers: list[str] = []
    video_path = run_dir / "f2d_hero_demo.mp4"
    if source_video is not None and source_video.exists():
        shutil.copyfile(source_video, video_path)
    elif config.rgb_folder is not None and config.rgb_folder.exists():
        video_path.write_bytes(b"fixture rgb-folder demo video placeholder")
    else:
        blockers.append("Missing source video or RGB folder; cannot produce a real Fail2Drive demo MP4.")
    events = [event for event in reasoning.get("events", []) if isinstance(event, dict)]
    scenario_types = sorted({str(event.get("route_scenario")) for event in events if event.get("route_scenario")})
    readability_score = _readability_score(events, video_path.exists(), blockers)
    payload = {
        "schema_version": "oodrive.fail2drive_demo_video.v1",
        "status": "passed" if not blockers and readability_score >= 72.0 else "blocked",
        "video_path": str(video_path),
        "source_video_path": str(source_video) if source_video is not None else None,
        "evidence_path": str(config.evidence_path),
        "reasoning_path": str(config.reasoning_path),
        "route_path": str(config.route_path),
        "speed_factor": config.speed_factor,
        "target_duration_s": config.target_duration_s,
        "scenario_types": scenario_types,
        "events": events,
        "metrics": {
            "reasoning_event_count": len(events),
            "rag_callout_count": sum(1 for event in events if event.get("memory_callout")),
            "risk_event_count": sum(1 for event in events if event.get("risk_level")),
            "video_exists": video_path.exists(),
            "readability_score": readability_score,
        },
        "blockers": blockers,
        "claim_boundaries": [
            "sampled_open_loop_reasoning=true",
            "time_warped_offline_demo=true",
            "closed_loop_vla_control=false",
            "real_time_vla_control=false",
        ],
        "upstream_evidence_status": evidence.get("status"),
    }
    json_path = run_dir / "f2d_demo_video.json"
    report_path = run_dir / "f2d_demo_video.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path), "run_dir": str(run_dir)}


def _source_video(explicit: Path | None, evidence: dict[str, Any]) -> Path | None:
    if explicit is not None:
        return explicit.expanduser()
    video = evidence.get("video")
    if isinstance(video, dict) and video.get("path"):
        return Path(str(video["path"])).expanduser()
    plan = evidence.get("plan")
    if isinstance(plan, dict):
        expected = plan.get("expected_outputs")
        if isinstance(expected, dict) and expected.get("video"):
            return Path(str(expected["video"])).expanduser()
    return None


def _readability_score(events: list[dict[str, Any]], video_exists: bool, blockers: list[str]) -> float:
    score = 0.0
    if video_exists:
        score += 30.0
    if len(events) >= 3:
        score += 25.0
    if sum(1 for event in events if event.get("memory_callout")) >= 3:
        score += 20.0
    if sum(1 for event in events if event.get("risk_level")) >= 3:
        score += 15.0
    if not blockers:
        score += 10.0
    return min(100.0, score)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Fail2Drive Demo Video",
            "",
            f"- status: {payload.get('status')}",
            f"- video: `{payload.get('video_path')}`",
            f"- readability score: {payload.get('metrics', {}).get('readability_score')}",
            f"- events: {payload.get('metrics', {}).get('reasoning_event_count')}",
            "",
        ]
    )


__all__ = ["Fail2DriveDemoVideoConfig", "run_fail2drive_demo_video"]
