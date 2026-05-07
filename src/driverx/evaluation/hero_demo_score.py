"""Mechanical quality scoring for OODrive hero demo videos."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.perception.risk_timeline import (
    RiskTimelineConfig,
    build_risk_timeline,
    load_entity_tracks,
)


REQUIRED_CLAIM_BOUNDARIES = [
    "time_warped_offline_demo=true",
    "sampled_open_loop_reasoning=true",
    "real_time_vla_control=false",
]


@dataclass(frozen=True)
class HeroDemoThresholds:
    pass_score: float = 72.0
    min_output_duration_s: float = 30.0
    min_source_duration_s: float = 60.0
    min_mean_ego_speed_mps: float = 3.0
    min_visible_generated_object_count: int = 3
    min_risk_event_count: int = 5
    min_reasoning_event_count: int = 3
    min_rag_event_count: int = 3
    min_alpamayo_prediction_count: int = 1
    min_frame_time_overlay_coverage: float = 0.95

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "pass_score": self.pass_score,
            "min_output_duration_s": self.min_output_duration_s,
            "min_source_duration_s": self.min_source_duration_s,
            "min_mean_ego_speed_mps": self.min_mean_ego_speed_mps,
            "min_visible_generated_object_count": self.min_visible_generated_object_count,
            "min_risk_event_count": self.min_risk_event_count,
            "min_reasoning_event_count": self.min_reasoning_event_count,
            "min_rag_event_count": self.min_rag_event_count,
            "min_alpamayo_prediction_count": self.min_alpamayo_prediction_count,
            "min_frame_time_overlay_coverage": self.min_frame_time_overlay_coverage,
        }


@dataclass(frozen=True)
class HeroDemoScoreInputs:
    candidate_id: str
    video_path: str | None = None
    source_duration_s: float = 0.0
    output_duration_s: float = 0.0
    frame_count: int = 0
    fps: int = 0
    has_mp4: bool = False
    road_alignment_pass: bool = False
    frame_time_overlay_coverage: float = 0.0
    mean_ego_speed_mps: float | None = None
    visible_generated_object_count: int = 0
    risk_event_count: int = 0
    reasoning_event_count: int = 0
    rag_event_count: int = 0
    alpamayo_prediction_count: int = 0
    min_distance_m: float | None = None
    offroad_actor_count: int = 0
    claim_boundaries: list[str] = field(default_factory=list)
    source_paths: dict[str, str] = field(default_factory=dict)
    fixture_mode: bool = False

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "video_path": self.video_path,
            "source_duration_s": self.source_duration_s,
            "output_duration_s": self.output_duration_s,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "has_mp4": self.has_mp4,
            "road_alignment_pass": self.road_alignment_pass,
            "frame_time_overlay_coverage": self.frame_time_overlay_coverage,
            "mean_ego_speed_mps": self.mean_ego_speed_mps,
            "visible_generated_object_count": self.visible_generated_object_count,
            "risk_event_count": self.risk_event_count,
            "reasoning_event_count": self.reasoning_event_count,
            "rag_event_count": self.rag_event_count,
            "alpamayo_prediction_count": self.alpamayo_prediction_count,
            "min_distance_m": self.min_distance_m,
            "offroad_actor_count": self.offroad_actor_count,
            "claim_boundaries": list(self.claim_boundaries),
            "source_paths": dict(self.source_paths),
            "fixture_mode": self.fixture_mode,
        }


@dataclass(frozen=True)
class HeroDemoScoreReport:
    status: str
    hero_demo_score: float
    threshold: float
    metrics: dict[str, Any]
    components: dict[str, float]
    blockers: list[str]
    warnings: list[str]
    claim_boundaries: list[str]
    inputs: HeroDemoScoreInputs

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "hero_demo_score": self.hero_demo_score,
            "threshold": self.threshold,
            "metrics": self.metrics,
            "components": self.components,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "claim_boundaries": self.claim_boundaries,
            "inputs": self.inputs.to_jsonable(),
        }


def load_demo_score_inputs(
    *,
    db_path: Path | None = None,
    run_manifest_path: Path | None = None,
    evaluation_path: Path | None = None,
    video_path: Path | None = None,
    overlay_report_path: Path | None = None,
    score_input_path: Path | None = None,
) -> HeroDemoScoreInputs:
    """Load score inputs from either a direct fixture or product artifacts."""

    if score_input_path is not None:
        payload = _load_json(score_input_path)
        return HeroDemoScoreInputs(
            candidate_id=str(payload.get("candidate_id", score_input_path.stem)),
            video_path=_optional_str(payload.get("video_path")),
            source_duration_s=_float(payload.get("source_duration_s")),
            output_duration_s=_float(payload.get("output_duration_s")),
            frame_count=int(_float(payload.get("frame_count"))),
            fps=int(_float(payload.get("fps"))),
            has_mp4=bool(payload.get("has_mp4")),
            road_alignment_pass=bool(payload.get("road_alignment_pass")),
            frame_time_overlay_coverage=_clamp(_float(payload.get("frame_time_overlay_coverage")), 0.0, 1.0),
            mean_ego_speed_mps=_optional_float(payload.get("mean_ego_speed_mps")),
            visible_generated_object_count=int(_float(payload.get("visible_generated_object_count"))),
            risk_event_count=int(_float(payload.get("risk_event_count"))),
            reasoning_event_count=int(_float(payload.get("reasoning_event_count"))),
            rag_event_count=int(_float(payload.get("rag_event_count"))),
            alpamayo_prediction_count=int(_float(payload.get("alpamayo_prediction_count"))),
            min_distance_m=_optional_float(payload.get("min_distance_m")),
            offroad_actor_count=int(_float(payload.get("offroad_actor_count"))),
            claim_boundaries=_string_list(payload.get("claim_boundaries")),
            source_paths={"score_input_path": str(score_input_path)},
            fixture_mode=True,
        )

    db_payload = _load_json(db_path) if db_path is not None and db_path.exists() else {}
    run_payload = _load_json(run_manifest_path) if run_manifest_path is not None and run_manifest_path.exists() else {}
    eval_payload = _load_json(evaluation_path) if evaluation_path is not None and evaluation_path.exists() else {}
    overlay_payload = _load_json(overlay_report_path) if overlay_report_path is not None and overlay_report_path.exists() else {}
    artifacts = _mapping(run_payload.get("artifacts"))
    demo_payload = _load_optional_json(_path_from_artifacts(artifacts, "carla_ood_demo_json"))

    resolved_video = video_path or _path_from_artifacts(artifacts, "video_path")
    video_duration = _probe_duration(resolved_video)
    output_duration = (
        video_duration
        or _optional_float(overlay_payload.get("output_duration_s"))
        or _optional_float(overlay_payload.get("duration_s"))
        or 0.0
    )
    tracks_path = _path_from_artifacts(artifacts, "tracks_path") or _optional_path(demo_payload.get("tracks_path"))
    risk_payload = _risk_from_tracks(tracks_path, run_payload, demo_payload)
    road_alignment = _road_alignment_pass(
        _path_from_artifacts(artifacts, "road_alignment_path") or _optional_path(demo_payload.get("road_alignment_path"))
    )
    mean_speed = _mean_ego_speed_from_tracks(tracks_path) or _mean_speed_from_actions(run_payload.get("actions"))
    frame_count = int(
        _optional_float(overlay_payload.get("frame_count"))
        or _optional_float(demo_payload.get("frame_count"))
        or (output_duration * _float(overlay_payload.get("fps"), 15.0) if output_duration else 0)
    )
    fps = int(_optional_float(overlay_payload.get("fps")) or (round(frame_count / output_duration) if output_duration else 0))
    claim_boundaries = _dedupe(
        [
            *_string_list(db_payload.get("claim_boundaries")),
            *_string_list(run_payload.get("claim_boundaries")),
            *_string_list(eval_payload.get("claim_boundaries")),
            *_string_list(overlay_payload.get("claim_boundaries")),
            *_string_list(demo_payload.get("claim_boundaries")),
        ]
    )
    reasoning_events = _reasoning_event_count(eval_payload, overlay_payload)
    rag_events = _rag_event_count(eval_payload, overlay_payload)
    generated_objects = _generated_object_count(db_payload, run_payload, demo_payload)
    return HeroDemoScoreInputs(
        candidate_id=str(run_payload.get("candidate_id") or run_payload.get("scenario_id") or db_payload.get("run_id") or "demo"),
        video_path=str(resolved_video) if resolved_video else None,
        source_duration_s=_optional_float(demo_payload.get("duration_s")) or _source_duration_from_actions(run_payload.get("actions")) or output_duration,
        output_duration_s=output_duration,
        frame_count=frame_count,
        fps=fps,
        has_mp4=bool(resolved_video and resolved_video.exists() and resolved_video.suffix.lower() == ".mp4"),
        road_alignment_pass=road_alignment,
        frame_time_overlay_coverage=_clamp(_float(overlay_payload.get("frame_time_overlay_coverage")), 0.0, 1.0),
        mean_ego_speed_mps=mean_speed,
        visible_generated_object_count=generated_objects,
        risk_event_count=int(_float(risk_payload.get("event_count"))),
        reasoning_event_count=reasoning_events,
        rag_event_count=rag_events,
        alpamayo_prediction_count=1 if _has_alpamayo_prediction(eval_payload, overlay_payload) else 0,
        min_distance_m=_min_distance(risk_payload, overlay_payload),
        offroad_actor_count=int(_float(overlay_payload.get("offroad_actor_count"))),
        claim_boundaries=claim_boundaries,
        source_paths={
            "db_path": str(db_path) if db_path else "",
            "run_manifest_path": str(run_manifest_path) if run_manifest_path else "",
            "evaluation_path": str(evaluation_path) if evaluation_path else "",
            "video_path": str(resolved_video) if resolved_video else "",
            "overlay_report_path": str(overlay_report_path) if overlay_report_path else "",
            "tracks_path": str(tracks_path) if tracks_path else "",
        },
    )


def score_hero_demo(
    inputs: HeroDemoScoreInputs,
    thresholds: HeroDemoThresholds | None = None,
) -> HeroDemoScoreReport:
    limits = thresholds or HeroDemoThresholds()
    components = _score_components(inputs)
    score = components["hero_demo_score"]
    blockers = _blockers(inputs, limits, score)
    warnings: list[str] = []
    if inputs.fixture_mode:
        warnings.append("fixture_mode=true; do not promote this score as live simulator evidence.")
    missing_claims = [claim for claim in REQUIRED_CLAIM_BOUNDARIES if claim not in inputs.claim_boundaries]
    if missing_claims:
        blockers.append(f"missing claim boundaries: {', '.join(missing_claims)}")
    status = "passed" if not blockers and score >= limits.pass_score else "blocked"
    metrics = inputs.to_jsonable()
    metrics["score_pass_threshold"] = limits.pass_score
    return HeroDemoScoreReport(
        status=status,
        hero_demo_score=score,
        threshold=limits.pass_score,
        metrics=metrics,
        components=components,
        blockers=blockers,
        warnings=warnings,
        claim_boundaries=_dedupe([*inputs.claim_boundaries, *REQUIRED_CLAIM_BOUNDARIES]),
        inputs=inputs,
    )


def write_hero_demo_score(run_dir: Path, report: HeroDemoScoreReport) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_jsonable()
    json_path = run_dir / "hero_demo_score.json"
    report_path = run_dir / "hero_demo_score.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_score_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _score_components(inputs: HeroDemoScoreInputs) -> dict[str, float]:
    output_duration = inputs.output_duration_s
    source_duration = inputs.source_duration_s
    mean_speed = inputs.mean_ego_speed_mps or 0.0
    min_distance = inputs.min_distance_m or 0.0
    duration_points = 12.0 * _clamp(output_duration / 45.0, 0.0, 1.0)
    duration_points += 8.0 * _clamp(source_duration / 90.0, 0.0, 1.0)
    motion_points = 14.0 * _clamp(mean_speed / 4.5, 0.0, 1.0)
    visible_ood_points = 12.0 * _clamp(inputs.visible_generated_object_count / 4.0, 0.0, 1.0)
    risk_points = 12.0 * _clamp(inputs.risk_event_count / 5.0, 0.0, 1.0)
    reasoning_points = 14.0 * _clamp(inputs.reasoning_event_count / 3.0, 0.0, 1.0)
    rag_points = 10.0 * _clamp(inputs.rag_event_count / 3.0, 0.0, 1.0)
    alpamayo_points = 8.0 * _clamp(inputs.alpamayo_prediction_count / 3.0, 0.0, 1.0)
    evidence_points = 10.0 * _clamp(inputs.frame_time_overlay_coverage, 0.0, 1.0)
    evidence_points += 5.0 if inputs.has_mp4 else 0.0
    evidence_points += 5.0 if inputs.road_alignment_pass else 0.0
    penalty_points = 0.0
    if mean_speed < 3.0:
        penalty_points += (3.0 - mean_speed) * 6.0
    if output_duration < 30.0:
        penalty_points += (30.0 - output_duration) * 0.6
    if min_distance > 6.0:
        penalty_points += min((min_distance - 6.0) * 2.0, 16.0)
    penalty_points += inputs.offroad_actor_count * 25.0
    penalty_points += (1.0 - _clamp(inputs.frame_time_overlay_coverage, 0.0, 1.0)) * 12.0
    if not inputs.has_mp4:
        penalty_points += 25.0
    if not inputs.road_alignment_pass:
        penalty_points += 30.0
    score = (
        duration_points
        + motion_points
        + visible_ood_points
        + risk_points
        + reasoning_points
        + rag_points
        + alpamayo_points
        + evidence_points
        - penalty_points
    )
    if not math.isfinite(score):
        score = 0.0
    return {
        "hero_demo_score": round(_clamp(score, 0.0, 100.0), 4),
        "duration_points": round(duration_points, 4),
        "motion_points": round(motion_points, 4),
        "visible_ood_points": round(visible_ood_points, 4),
        "risk_points": round(risk_points, 4),
        "reasoning_points": round(reasoning_points, 4),
        "rag_points": round(rag_points, 4),
        "alpamayo_points": round(alpamayo_points, 4),
        "evidence_points": round(evidence_points, 4),
        "penalty_points": round(penalty_points, 4),
    }


def _blockers(inputs: HeroDemoScoreInputs, limits: HeroDemoThresholds, score: float) -> list[str]:
    blockers: list[str] = []
    if score < limits.pass_score:
        blockers.append(f"hero_demo_score {score:.2f} below {limits.pass_score:.2f}")
    if inputs.output_duration_s < limits.min_output_duration_s:
        blockers.append(f"output_duration_s {inputs.output_duration_s:.2f} below {limits.min_output_duration_s:.2f}")
    if inputs.source_duration_s < limits.min_source_duration_s:
        blockers.append(f"source_duration_s {inputs.source_duration_s:.2f} below {limits.min_source_duration_s:.2f}")
    if (inputs.mean_ego_speed_mps or 0.0) < limits.min_mean_ego_speed_mps:
        blockers.append(
            f"mean_ego_speed_mps {(inputs.mean_ego_speed_mps or 0.0):.2f} below {limits.min_mean_ego_speed_mps:.2f}"
        )
    if inputs.visible_generated_object_count < limits.min_visible_generated_object_count:
        blockers.append(
            f"visible_generated_object_count {inputs.visible_generated_object_count} below {limits.min_visible_generated_object_count}"
        )
    if inputs.risk_event_count < limits.min_risk_event_count:
        blockers.append(f"risk_event_count {inputs.risk_event_count} below {limits.min_risk_event_count}")
    if inputs.reasoning_event_count < limits.min_reasoning_event_count:
        blockers.append(f"reasoning_event_count {inputs.reasoning_event_count} below {limits.min_reasoning_event_count}")
    if inputs.rag_event_count < limits.min_rag_event_count:
        blockers.append(f"rag_event_count {inputs.rag_event_count} below {limits.min_rag_event_count}")
    if inputs.alpamayo_prediction_count < limits.min_alpamayo_prediction_count:
        blockers.append(
            f"alpamayo_prediction_count {inputs.alpamayo_prediction_count} below {limits.min_alpamayo_prediction_count}"
        )
    if inputs.frame_time_overlay_coverage < limits.min_frame_time_overlay_coverage:
        blockers.append(
            f"frame_time_overlay_coverage {inputs.frame_time_overlay_coverage:.2f} below {limits.min_frame_time_overlay_coverage:.2f}"
        )
    if not inputs.has_mp4:
        blockers.append("mp4 video evidence is missing")
    if not inputs.road_alignment_pass:
        blockers.append("road alignment did not pass")
    if inputs.offroad_actor_count > 0:
        blockers.append(f"offroad_actor_count {inputs.offroad_actor_count} above 0")
    return blockers


def _score_markdown(payload: dict[str, Any]) -> str:
    metrics = dict(payload.get("metrics", {}))
    lines = [
        "# Hero Demo Score",
        "",
        f"- Status: `{payload['status']}`",
        f"- Score: `{payload['hero_demo_score']}` / 100",
        f"- Threshold: `{payload['threshold']}`",
        f"- Candidate: `{metrics.get('candidate_id')}`",
        f"- Video: `{metrics.get('video_path')}`",
        "",
        "## Metrics",
        "",
        "| metric | value |",
        "| --- | --- |",
    ]
    for key in (
        "source_duration_s",
        "output_duration_s",
        "frame_count",
        "mean_ego_speed_mps",
        "visible_generated_object_count",
        "risk_event_count",
        "reasoning_event_count",
        "rag_event_count",
        "alpamayo_prediction_count",
        "frame_time_overlay_coverage",
        "min_distance_m",
    ):
        lines.append(f"| `{key}` | `{metrics.get(key)}` |")
    lines.extend(["", "## Components", "", "| component | points |", "| --- | --- |"])
    for key, value in dict(payload.get("components", {})).items():
        lines.append(f"| `{key}` | `{value}` |")
    blockers = list(payload.get("blockers", []))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend([f"- {item}" for item in blockers])
    warnings = list(payload.get("warnings", []))
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend([f"- {item}" for item in warnings])
    lines.extend(["", "## Claim Boundaries", ""])
    for claim in payload.get("claim_boundaries", []):
        lines.append(f"- `{claim}`")
    return "\n".join(lines) + "\n"


def _risk_from_tracks(
    tracks_path: Path | None,
    run_payload: dict[str, Any],
    demo_payload: dict[str, Any],
) -> dict[str, Any]:
    if tracks_path is None or not tracks_path.exists():
        return {}
    try:
        timeline = build_risk_timeline(
            load_entity_tracks(tracks_path),
            RiskTimelineConfig(
                scenario_id=str(run_payload.get("scenario_id") or demo_payload.get("recipe_id") or ""),
                behavior_id=str(demo_payload.get("behavior_id") or ""),
            ),
        )
        return timeline.to_jsonable()
    except (OSError, ValueError):
        return {}


def _mean_ego_speed_from_tracks(tracks_path: Path | None) -> float | None:
    if tracks_path is None or not tracks_path.exists():
        return None
    try:
        tracks = load_entity_tracks(tracks_path)
    except (OSError, ValueError):
        return None
    speeds: list[float] = []
    for track in tracks:
        if track.actor_ref != "ego":
            continue
        vx = track.velocity.get("x", 0.0)
        vy = track.velocity.get("y", 0.0)
        vz = track.velocity.get("z", 0.0)
        speeds.append(math.sqrt(vx * vx + vy * vy + vz * vz))
    return round(sum(speeds) / len(speeds), 4) if speeds else None


def _mean_speed_from_actions(actions: Any) -> float | None:
    if not isinstance(actions, list):
        return None
    speeds = [_optional_float(item.get("speed_mps")) for item in actions if isinstance(item, dict)]
    valid = [speed for speed in speeds if speed is not None]
    return round(sum(valid) / len(valid), 4) if valid else None


def _source_duration_from_actions(actions: Any) -> float | None:
    if not isinstance(actions, list):
        return None
    times = [_optional_float(item.get("t_s")) for item in actions if isinstance(item, dict)]
    valid = [time for time in times if time is not None]
    return round(max(valid), 4) if valid else None


def _generated_object_count(
    db_payload: dict[str, Any],
    run_payload: dict[str, Any],
    demo_payload: dict[str, Any],
) -> int:
    generated = demo_payload.get("generated_asset_ids")
    if isinstance(generated, list) and generated:
        return len(generated)
    artifacts = _mapping(run_payload.get("artifacts"))
    trace_payload = _load_optional_json(_optional_path(artifacts.get("placement_trace_path")))
    specs = trace_payload.get("object_spawn_specs")
    if isinstance(specs, list) and specs:
        return len(specs)
    candidates = db_payload.get("candidates")
    if isinstance(candidates, list) and candidates:
        recipe = _mapping(_mapping(candidates[0]).get("compiled_recipe"))
        return len(_list_of_mappings(recipe.get("actors")))
    return 0


def _road_alignment_pass(path: Path | None) -> bool:
    if path is None or not path.exists():
        return False
    payload = _load_optional_json(path)
    return bool(payload.get("passes"))


def _reasoning_event_count(eval_payload: dict[str, Any], overlay_payload: dict[str, Any]) -> int:
    events = overlay_payload.get("events")
    if isinstance(events, list):
        count = sum(1 for event in events if isinstance(event, dict) and event.get("vla_reasoning"))
        if count:
            return count
    return 1 if eval_payload.get("cot_summary") else 0


def _rag_event_count(eval_payload: dict[str, Any], overlay_payload: dict[str, Any]) -> int:
    events = overlay_payload.get("events")
    if isinstance(events, list):
        count = sum(1 for event in events if isinstance(event, dict) and event.get("memory_id"))
        if count:
            return count
    memory_ids = eval_payload.get("memory_ids")
    return len(memory_ids) if isinstance(memory_ids, list) else 0


def _has_alpamayo_prediction(eval_payload: dict[str, Any], overlay_payload: dict[str, Any]) -> bool:
    if eval_payload.get("cot_summary") or eval_payload.get("trajectory_summary"):
        return True
    return any(
        isinstance(event, dict) and event.get("vla_reasoning")
        for event in list(overlay_payload.get("events", []))
    )


def _min_distance(risk_payload: dict[str, Any], overlay_payload: dict[str, Any]) -> float | None:
    nearest = risk_payload.get("nearest_event")
    if isinstance(nearest, dict):
        value = _optional_float(nearest.get("distance_m"))
        if value is not None:
            return value
    worst = overlay_payload.get("worst_risk")
    if isinstance(worst, dict):
        return _optional_float(worst.get("distance_m"))
    return None


def _probe_duration(video_path: Path | None) -> float | None:
    if video_path is None or not video_path.exists():
        return None
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        return None
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return _optional_float(proc.stdout.strip())


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, dict) else {}


def _load_optional_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        return _load_json(path)
    except (OSError, json.JSONDecodeError):
        return {}


def _path_from_artifacts(artifacts: dict[str, Any], key: str) -> Path | None:
    return _optional_path(artifacts.get(key))


def _optional_path(value: object) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    return Path(value)


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in value] if isinstance(value, list) and all(isinstance(item, dict) for item in value) else []


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _float(value: object, default: float = 0.0) -> float:
    parsed = _optional_float(value)
    return default if parsed is None else parsed


def _optional_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value and value not in out:
            out.append(value)
    return out


__all__ = [
    "HeroDemoScoreInputs",
    "HeroDemoScoreReport",
    "HeroDemoThresholds",
    "REQUIRED_CLAIM_BOUNDARIES",
    "load_demo_score_inputs",
    "score_hero_demo",
    "write_hero_demo_score",
]
