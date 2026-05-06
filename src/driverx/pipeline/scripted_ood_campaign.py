"""Run small scripted CARLA OOD campaigns with fake/live execution modes."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from driverx.assets import default_asset_requests, generate_assets_dry_run
from driverx.behaviors import BehaviorConstraints, BehaviorTrace, default_behavior_plans, simulate_behavior, validate_behavior_trace
from driverx.core.artifacts import prepare_run_dir
from driverx.core.config import read_config_mapping
from driverx.pipeline.ood_video_evidence import OodVideoEvidenceInputs, build_ood_video_evidence
from driverx.scenarios import MutationPolicy, ScenarioRecipe, generate_scenario_recipes, load_scenario_seeds
from driverx.scenarios import (
    ScenarioQualityThresholds,
    evaluate_scenario_quality,
    write_scenario_quality_outputs,
)
from driverx.simulators.carla_ood_demo import (
    CarlaOodDemoConfig,
    load_carla_ood_demo_config,
    run_carla_ood_demo,
    write_carla_ood_demo,
)


@dataclass(frozen=True)
class ScriptedOodCampaignConfig:
    scenario_config_path: Path = Path("configs/scenario_forge.sample.yaml")
    carla_ood_config_path: Path = Path("configs/carla_ood_demo.local.sample.yaml")
    output_root: Path = Path("artifacts/runs")
    run_id: str = "scripted-ood-campaign"
    behavior_ids: tuple[str, ...] = ("motorcycle_filtering", "sudden_brake", "unsignaled_u_turn")
    count: int = 3
    seed: int = 7
    live: bool = False
    assemble_video: bool = False
    resume: bool = True
    no_default_assets: bool = False
    quality_min_duration_s: float = 5.0
    quality_min_frame_count: int = 0
    quality_max_min_distance_m: float = 6.0
    quality_require_video: bool = True
    quality_require_road_alignment: bool = True
    quality_require_conflict: bool = True
    quality_min_visible_actor_count: float = 0.0
    quality_max_ood_step_m: float | None = None
    quality_retry_limit: int = 0

    def quality_thresholds(self) -> ScenarioQualityThresholds:
        return ScenarioQualityThresholds(
            min_duration_s=self.quality_min_duration_s,
            min_frame_count=self.quality_min_frame_count,
            max_min_distance_m=self.quality_max_min_distance_m,
            min_visible_actor_count=self.quality_min_visible_actor_count,
            max_ood_step_m=self.quality_max_ood_step_m,
            require_video=self.quality_require_video,
            require_road_alignment=self.quality_require_road_alignment,
            require_conflict=self.quality_require_conflict,
        )


@dataclass(frozen=True)
class CampaignCaseRecord:
    case_id: str
    recipe_id: str
    behavior_id: str
    status: str
    live: bool
    min_distance_m: float | None
    frame_count: int
    duration_s: float
    scenario_report_path: str | None
    road_alignment_path: str | None
    tracks_path: str | None
    rgb_folder: str | None
    video_status: str | None = None
    video_evidence_path: str | None = None
    video_evidence_report_path: str | None = None
    video_path: str | None = None
    blockers: tuple[str, ...] = field(default_factory=tuple)
    attempt_index: int = 0
    quality_status: str | None = None
    quality_blockers: tuple[str, ...] = field(default_factory=tuple)
    fidelity_metrics: dict[str, Any] = field(default_factory=dict)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "recipe_id": self.recipe_id,
            "behavior_id": self.behavior_id,
            "status": self.status,
            "live": self.live,
            "min_distance_m": self.min_distance_m,
            "frame_count": self.frame_count,
            "duration_s": self.duration_s,
            "scenario_report_path": self.scenario_report_path,
            "road_alignment_path": self.road_alignment_path,
            "tracks_path": self.tracks_path,
            "rgb_folder": self.rgb_folder,
            "video_status": self.video_status,
            "video_evidence_path": self.video_evidence_path,
            "video_evidence_report_path": self.video_evidence_report_path,
            "video_path": self.video_path,
            "blockers": list(self.blockers),
            "attempt_index": self.attempt_index,
            "quality_status": self.quality_status,
            "quality_blockers": list(self.quality_blockers),
            "fidelity_metrics": self.fidelity_metrics,
        }


def load_scripted_ood_campaign_config(path: Path) -> ScriptedOodCampaignConfig:
    raw = read_config_mapping(path)
    campaign = raw.get("scripted_ood_campaign", raw)
    if not isinstance(campaign, dict):
        raise ValueError("Config field 'scripted_ood_campaign' must be a mapping.")
    return ScriptedOodCampaignConfig(
        scenario_config_path=Path(str(campaign.get("scenario_config_path", "configs/scenario_forge.sample.yaml"))),
        carla_ood_config_path=Path(str(campaign.get("carla_ood_config_path", "configs/carla_ood_demo.local.sample.yaml"))),
        output_root=Path(str(campaign.get("output_root", "artifacts/runs"))),
        run_id=str(campaign.get("run_id", "scripted-ood-campaign")),
        behavior_ids=_csv_tuple(campaign.get("behavior_ids"), ("motorcycle_filtering", "sudden_brake", "unsignaled_u_turn")),
        count=max(1, int(campaign.get("count", 3))),
        seed=int(campaign.get("seed", 7)),
        live=bool(campaign.get("live", False)),
        assemble_video=bool(campaign.get("assemble_video", False)),
        resume=bool(campaign.get("resume", True)),
        no_default_assets=bool(campaign.get("no_default_assets", False)),
        quality_min_duration_s=float(campaign.get("quality_min_duration_s", 5.0)),
        quality_min_frame_count=int(campaign.get("quality_min_frame_count", 0)),
        quality_max_min_distance_m=float(campaign.get("quality_max_min_distance_m", 6.0)),
        quality_require_video=bool(campaign.get("quality_require_video", True)),
        quality_require_road_alignment=bool(campaign.get("quality_require_road_alignment", True)),
        quality_require_conflict=bool(campaign.get("quality_require_conflict", True)),
        quality_min_visible_actor_count=_optional_float(campaign.get("quality_min_visible_actor_count")) or 0.0,
        quality_max_ood_step_m=_optional_float(campaign.get("quality_max_ood_step_m")),
        quality_retry_limit=max(0, int(campaign.get("quality_retry_limit", 0))),
    )


def run_scripted_ood_campaign(config: ScriptedOodCampaignConfig) -> dict[str, Any]:
    run_dir = _prepare_campaign_run_dir(config)
    attempt_limit = config.quality_retry_limit + 1
    recipes = _load_recipes(config, count=config.count * attempt_limit)
    plans = {plan.behavior_id: plan for plan in default_behavior_plans()}
    carla_config = load_carla_ood_demo_config(config.carla_ood_config_path)
    records: list[CampaignCaseRecord] = []
    attempts: list[CampaignCaseRecord] = []
    recipe_cursor = 0
    for index in range(config.count):
        selected: CampaignCaseRecord | None = None
        for attempt_index in range(attempt_limit):
            recipe = recipes[recipe_cursor % len(recipes)]
            recipe_cursor += 1
            behavior_id = config.behavior_ids[(index + attempt_index) % len(config.behavior_ids)]
            if behavior_id not in plans:
                raise ValueError(f"Unknown behavior id: {behavior_id}")
            case_id = _case_id(index, attempt_index, recipe.recipe_id, behavior_id)
            case_dir = run_dir / "cases" / case_id
            case_dir.mkdir(parents=True, exist_ok=True)
            record = None
            if config.resume:
                record = _resume_case(
                    case_id=case_id,
                    case_dir=case_dir,
                    recipe=recipe,
                    behavior_id=behavior_id,
                    carla_config=carla_config,
                    config=config,
                )
            behavior = simulate_behavior(plans[behavior_id])
            if record is None:
                record = _run_case(
                    case_id=case_id,
                    case_dir=case_dir,
                    recipe=recipe,
                    behavior=behavior,
                    behavior_id=behavior_id,
                    carla_config=carla_config,
                    config=config,
                )
            record = _with_behavior_validation(record, behavior)
            annotated = _annotate_quality(record, config, attempt_index=attempt_index)
            attempts.append(annotated)
            selected = annotated
            if annotated.quality_status == "passed":
                break
        if selected is not None:
            records.append(selected)
    payload = _campaign_payload(run_dir, config, records, attempts=attempts)
    return write_scripted_ood_campaign(run_dir, payload)


def write_scripted_ood_campaign(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    json_path = run_dir / "scripted_ood_campaign_summary.json"
    report_path = run_dir / "scripted_ood_campaign_summary.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _run_case(
    *,
    case_id: str,
    case_dir: Path,
    recipe: ScenarioRecipe,
    behavior: BehaviorTrace,
    behavior_id: str,
    carla_config: CarlaOodDemoConfig,
    config: ScriptedOodCampaignConfig,
) -> CampaignCaseRecord:
    if not config.live:
        return _fake_case(case_id, case_dir, recipe, behavior, behavior_id, carla_config)
    result = run_carla_ood_demo(
        CarlaOodDemoConfig(**{**carla_config.__dict__, "behavior_id": behavior_id}),
        case_dir / "carla",
        recipe=recipe,
        behavior=behavior,
        asset_manifests=[] if config.no_default_assets else generate_assets_dry_run(default_asset_requests()),
    )
    summary = write_carla_ood_demo(case_dir / "carla", result)
    video_summary: dict[str, Any] | None = None
    if config.assemble_video and result.rgb_folder:
        video_summary = build_ood_video_evidence(
            case_dir / "video",
            OodVideoEvidenceInputs(
                rgb_folder=Path(result.rgb_folder),
                tracks_path=Path(result.tracks_path) if result.tracks_path else None,
                scenario_id=recipe.recipe_id,
                behavior_id=behavior_id,
                source_kind="live_carla_campaign",
                claim_label="scripted_carla_ood_campaign",
                fps=carla_config.fps,
            ),
        )
    video_summary = _best_video_summary(case_dir, video_summary)
    min_distance = _min_distance(Path(result.tracks_path)) if result.tracks_path else None
    return CampaignCaseRecord(
        case_id=case_id,
        recipe_id=recipe.recipe_id,
        behavior_id=behavior_id,
        status=result.status,
        live=True,
        min_distance_m=min_distance,
        frame_count=result.frame_count,
        duration_s=result.duration_s,
        scenario_report_path=str(summary.get("json_path")),
        road_alignment_path=result.road_alignment_path,
        tracks_path=result.tracks_path,
        rgb_folder=result.rgb_folder,
        video_status=str(video_summary.get("status")) if video_summary else None,
        video_evidence_path=str(video_summary.get("json_path")) if video_summary else None,
        video_evidence_report_path=str(video_summary.get("report_path")) if video_summary else None,
        video_path=str(video_summary.get("video_path")) if video_summary and video_summary.get("video_path") else None,
        blockers=tuple(result.blockers),
        fidelity_metrics=result.fidelity_metrics,
    )


def _fake_case(
    case_id: str,
    case_dir: Path,
    recipe: ScenarioRecipe,
    behavior: BehaviorTrace,
    behavior_id: str,
    carla_config: CarlaOodDemoConfig,
) -> CampaignCaseRecord:
    tracks = _fake_tracks(behavior, ego_speed_mps=carla_config.ego_speed_mps)
    tracks_path = case_dir / "entity_tracks.json"
    tracks_path.write_text(json.dumps(tracks, indent=2), encoding="utf-8")
    min_distance = _min_distance(tracks_path)
    scenario = {
        "status": "passed",
        "connected": False,
        "scripted_campaign_fake": True,
        "recipe_id": recipe.recipe_id,
        "scenario_id": recipe.recipe_id,
        "behavior_id": behavior_id,
        "frame_count": 0,
        "duration_s": round(len(behavior.samples) / max(carla_config.fps, 1), 4),
        "tracks_path": str(tracks_path),
        "rgb_folder": None,
        "blockers": [],
        "fidelity_metrics": _fidelity_metrics_from_tracks(
            tracks,
            camera_preset="synthetic",
            fidelity_mode="fake",
            background_actor_count=0,
        ),
        "claim_boundaries": [
            "scripted_ood_campaign_fake=true",
            "live_carla=false",
            "stock_fail2drive_score=false",
        ],
    }
    scenario_path = case_dir / "carla_ood_demo.json"
    report_path = case_dir / "carla_ood_demo.md"
    scenario_path.write_text(json.dumps(scenario, indent=2), encoding="utf-8")
    report_path.write_text(
        f"# Scripted OOD Campaign Fake Case\n\n- recipe_id: `{recipe.recipe_id}`\n- behavior_id: `{behavior_id}`\n- min_distance_m: `{min_distance}`\n",
        encoding="utf-8",
    )
    return CampaignCaseRecord(
        case_id=case_id,
        recipe_id=recipe.recipe_id,
        behavior_id=behavior_id,
        status="passed",
        live=False,
        min_distance_m=min_distance,
        frame_count=0,
        duration_s=float(scenario["duration_s"]),
        scenario_report_path=str(scenario_path),
        road_alignment_path=None,
        tracks_path=str(tracks_path),
        rgb_folder=None,
        video_status=None,
        fidelity_metrics=_mapping(scenario.get("fidelity_metrics")),
    )


def _prepare_campaign_run_dir(config: ScriptedOodCampaignConfig) -> Path:
    if config.resume:
        run_dir = config.output_root / config.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir
    return prepare_run_dir(config.output_root, config.run_id)


def _resume_case(
    *,
    case_id: str,
    case_dir: Path,
    recipe: ScenarioRecipe,
    behavior_id: str,
    carla_config: CarlaOodDemoConfig,
    config: ScriptedOodCampaignConfig,
) -> CampaignCaseRecord | None:
    live_report_path = case_dir / "carla" / "carla_ood_demo.json"
    fake_report_path = case_dir / "carla_ood_demo.json"
    report_path = live_report_path if live_report_path.exists() else fake_report_path
    if not report_path.exists():
        return None
    scenario = _load_json(report_path)
    video_summary = _best_video_summary(case_dir, None)
    tracks_path = scenario.get("tracks_path")
    min_distance = _min_distance(Path(str(tracks_path))) if tracks_path else None
    return CampaignCaseRecord(
        case_id=case_id,
        recipe_id=str(scenario.get("recipe_id") or scenario.get("scenario_id") or recipe.recipe_id),
        behavior_id=str(scenario.get("behavior_id") or behavior_id),
        status=str(scenario.get("status") or "passed"),
        live=bool(scenario.get("connected")) or bool(config.live),
        min_distance_m=min_distance,
        frame_count=int(scenario.get("frame_count") or 0),
        duration_s=float(scenario.get("duration_s") or 0.0),
        scenario_report_path=str(report_path),
        road_alignment_path=str(scenario.get("road_alignment_path")) if scenario.get("road_alignment_path") else None,
        tracks_path=str(tracks_path) if tracks_path else None,
        rgb_folder=str(scenario.get("rgb_folder")) if scenario.get("rgb_folder") else None,
        video_status=str(video_summary.get("status")) if video_summary else None,
        video_evidence_path=str(video_summary.get("json_path")) if video_summary else None,
        video_evidence_report_path=str(video_summary.get("report_path")) if video_summary else None,
        video_path=str(video_summary.get("video_path")) if video_summary and video_summary.get("video_path") else None,
        blockers=tuple(str(blocker) for blocker in list(scenario.get("blockers", []))),
        fidelity_metrics=_mapping(scenario.get("fidelity_metrics")),
    )


def _best_video_summary(case_dir: Path, generated: dict[str, Any] | None) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    if generated:
        candidates.append(generated)
    for path in (
        case_dir / "video" / "ood_video_evidence.json",
        case_dir / "local-video" / "ood_video_evidence.json",
    ):
        payload = _load_json(path) if path.exists() else {}
        if payload:
            payload.setdefault("json_path", str(path))
            payload.setdefault("report_path", str(path.with_suffix(".md")))
            candidates.append(payload)
    if not candidates:
        return None
    passed = [candidate for candidate in candidates if candidate.get("status") == "passed"]
    return passed[-1] if passed else candidates[-1]


def _load_recipes(config: ScriptedOodCampaignConfig, *, count: int | None = None) -> list[ScenarioRecipe]:
    scenario = read_config_mapping(config.scenario_config_path)
    section = scenario.get("scenario", scenario)
    seeds_path = Path(str(_mapping(section).get("seeds_path", "tests/fixtures/fail2drive_like/seeds.json")))
    mutations = _csv_tuple(_mapping(section).get("mutations"), ("regional_driving_behavior",))
    return generate_scenario_recipes(
        load_scenario_seeds(seeds_path),
        MutationPolicy(mutations=mutations),
        count=count or config.count,
        random_seed=config.seed,
    )


def _campaign_payload(
    run_dir: Path,
    config: ScriptedOodCampaignConfig,
    records: list[CampaignCaseRecord],
    *,
    attempts: list[CampaignCaseRecord] | None = None,
) -> dict[str, Any]:
    json_records = [record.to_jsonable() for record in records]
    json_attempts = [record.to_jsonable() for record in (attempts or records)]
    ranked = [record for record in json_records if record.get("min_distance_m") is not None]
    ranked.sort(key=lambda item: float(item["min_distance_m"]))
    blockers = [
        f"{record['case_id']}: {blocker}"
        for record in json_records
        for blocker in list(record.get("blockers", []))
    ]
    quality_blockers = [
        f"{record['case_id']}: {blocker}"
        for record in json_records
        for blocker in list(record.get("quality_blockers", []))
    ]
    selected_quality_passed = [
        record
        for record in json_records
        if record.get("quality_status") == "passed"
    ]
    campaign_status = "passed" if len(selected_quality_passed) == len(json_records) and not blockers else "quality_blocked"
    return {
        "campaign_id": run_dir.name,
        "status": campaign_status,
        "requested_case_count": config.count,
        "case_count": len(json_records),
        "attempt_count": len(json_attempts),
        "quality_retry_limit": config.quality_retry_limit,
        "quality_retried_case_count": sum(1 for record in json_records if int(record.get("attempt_index", 0)) > 0),
        "quality_selected_passed_count": len(selected_quality_passed),
        "live_case_count": sum(1 for record in json_records if record.get("live")),
        "behavior_ids": list(config.behavior_ids),
        "best_case": ranked[-1] if ranked else None,
        "worst_case": ranked[0] if ranked else None,
        "mean_min_distance_m": _mean([float(record["min_distance_m"]) for record in ranked]),
        "fidelity": _fidelity_summary(json_records),
        "cases": json_records,
        "quality_attempts": json_attempts,
        "quality": _quality_payload(run_dir, config, json_records),
        "blockers": [*blockers, *quality_blockers],
        "claim_boundaries": [
            "scripted_ood_campaign=true",
            "stock_fail2drive_score=false",
            "real_time_vla_control=false",
        ],
    }


def _annotate_quality(
    record: CampaignCaseRecord,
    config: ScriptedOodCampaignConfig,
    *,
    attempt_index: int,
) -> CampaignCaseRecord:
    quality = evaluate_scenario_quality(record.to_jsonable(), config.quality_thresholds())
    return replace(
        record,
        attempt_index=attempt_index,
        quality_status=quality.status,
        quality_blockers=tuple(quality.blockers),
    )


def _with_behavior_validation(record: CampaignCaseRecord, behavior: BehaviorTrace) -> CampaignCaseRecord:
    validation = validate_behavior_trace(behavior, BehaviorConstraints())
    if validation.passes:
        return record
    blockers = [
        *record.blockers,
        *[f"behavior_validation:{blocker}" for blocker in validation.blockers],
    ]
    return replace(record, blockers=tuple(blockers), status="blocked")


def _case_id(index: int, attempt_index: int, recipe_id: str, behavior_id: str) -> str:
    suffix = f"{_slug(recipe_id)}-{behavior_id}"
    if attempt_index <= 0:
        return f"{index:03d}-{suffix}"
    return f"{index:03d}-retry{attempt_index:02d}-{suffix}"


def _quality_payload(
    run_dir: Path,
    config: ScriptedOodCampaignConfig,
    json_records: list[dict[str, Any]],
) -> dict[str, Any]:
    thresholds = config.quality_thresholds()
    reports = [evaluate_scenario_quality(record, thresholds) for record in json_records]
    return write_scenario_quality_outputs(reports, run_dir / "quality", thresholds=thresholds)


def _fake_tracks(behavior: BehaviorTrace, *, ego_speed_mps: float) -> list[dict[str, Any]]:
    tracks: list[dict[str, Any]] = []
    for tick, sample in enumerate(behavior.samples):
        ego_x = ego_speed_mps * sample.t_s
        tracks.extend(
            [
                _track("ego", tick, sample.t_s, ego_x, 0.0, ego_speed_mps),
                _track("ood_actor_0", tick, sample.t_s, sample.x_m, sample.y_m, sample.speed_mps),
            ]
        )
    return tracks


def _fidelity_metrics_from_tracks(
    tracks: list[dict[str, Any]],
    *,
    camera_preset: str,
    fidelity_mode: str,
    background_actor_count: int,
) -> dict[str, Any]:
    visible_counts: dict[int, set[str]] = {}
    ood_tracks = []
    ego_tracks = []
    for track in tracks:
        actor_ref = str(track.get("actor_ref"))
        visible_counts.setdefault(int(track.get("tick", 0)), set()).add(actor_ref)
        if actor_ref == "ood_actor_0":
            ood_tracks.append(track)
        if actor_ref == "ego":
            ego_tracks.append(track)
    return {
        "fidelity_mode": fidelity_mode,
        "background_actor_count": background_actor_count,
        "camera_preset": camera_preset,
        "mean_ood_step_m": _mean(_step_distances(ood_tracks)),
        "max_ood_step_m": max(_step_distances(ood_tracks), default=0.0),
        "ego_route_progress_m": _route_progress(ego_tracks),
        "visible_actor_count_mean": (
            round(sum(len(refs) for refs in visible_counts.values()) / len(visible_counts), 4)
            if visible_counts
            else None
        ),
    }


def _fidelity_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = [_mapping(record.get("fidelity_metrics")) for record in records]
    return {
        "mean_visible_actor_count": _mean(
            [
                float(metric["visible_actor_count_mean"])
                for metric in metrics
                if metric.get("visible_actor_count_mean") is not None
            ]
        ),
        "mean_ego_route_progress_m": _mean(
            [
                float(metric["ego_route_progress_m"])
                for metric in metrics
                if metric.get("ego_route_progress_m") is not None
            ]
        ),
        "max_ood_step_m": max(
            [
                float(metric["max_ood_step_m"])
                for metric in metrics
                if metric.get("max_ood_step_m") is not None
            ],
            default=None,
        ),
        "background_actor_count": sum(
            int(float(metric.get("background_actor_count", 0) or 0))
            for metric in metrics
        ),
        "camera_presets": sorted(
            {
                str(metric["camera_preset"])
                for metric in metrics
                if metric.get("camera_preset")
            }
        ),
    }


def _step_distances(tracks: list[dict[str, Any]]) -> list[float]:
    distances: list[float] = []
    for previous, current in zip(tracks, tracks[1:]):
        prev_location = _mapping(previous.get("location"))
        curr_location = _mapping(current.get("location"))
        dx = float(curr_location.get("x", 0.0)) - float(prev_location.get("x", 0.0))
        dy = float(curr_location.get("y", 0.0)) - float(prev_location.get("y", 0.0))
        distances.append(round((dx * dx + dy * dy) ** 0.5, 4))
    return distances


def _route_progress(tracks: list[dict[str, Any]]) -> float:
    if len(tracks) < 2:
        return 0.0
    start = _mapping(tracks[0].get("location"))
    end = _mapping(tracks[-1].get("location"))
    dx = float(end.get("x", 0.0)) - float(start.get("x", 0.0))
    dy = float(end.get("y", 0.0)) - float(start.get("y", 0.0))
    return round((dx * dx + dy * dy) ** 0.5, 4)


def _track(actor_ref: str, tick: int, t_s: float, x: float, y: float, speed: float) -> dict[str, Any]:
    return {
        "actor_ref": actor_ref,
        "actor_id": 0 if actor_ref == "ego" else 1,
        "type_id": f"driverx.synthetic.{actor_ref}",
        "tick": tick,
        "t_s": round(t_s, 4),
        "location": {"x": round(x, 4), "y": round(y, 4), "z": 0.0},
        "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
        "velocity": {"x": round(speed, 4), "y": 0.0, "z": 0.0},
    }


def _min_distance(path: Path) -> float | None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_tick: dict[int, dict[str, dict[str, float]]] = {}
    for item in payload if isinstance(payload, list) else []:
        if not isinstance(item, dict):
            continue
        actor = str(item.get("actor_ref"))
        location = _mapping(item.get("location"))
        tick = int(item.get("tick", 0))
        by_tick.setdefault(tick, {})[actor] = {"x": float(location.get("x", 0.0)), "y": float(location.get("y", 0.0))}
    distances = []
    for actors in by_tick.values():
        ego = actors.get("ego")
        for actor_ref, location in actors.items():
            if actor_ref == "ego" or ego is None:
                continue
            distances.append(math.dist((ego["x"], ego["y"]), (location["x"], location["y"])))
    if not distances:
        return None
    return round(min(distances), 4)


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _csv_tuple(value: object, default: tuple[str, ...]) -> tuple[str, ...]:
    if value in (None, ""):
        return default
    if isinstance(value, (list, tuple)):
        items = tuple(str(item).strip() for item in value if str(item).strip())
    else:
        items = tuple(item.strip() for item in str(value).split(",") if item.strip())
    return items or default


def _optional_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "-" for char in value.lower()).strip("-")


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Scripted OOD Campaign",
        "",
        f"- status: `{payload.get('status')}`",
        f"- requested_case_count: `{payload.get('requested_case_count')}`",
        f"- case_count: `{payload.get('case_count')}`",
        f"- attempt_count: `{payload.get('attempt_count')}`",
        f"- quality_retry_limit: `{payload.get('quality_retry_limit')}`",
        f"- quality_retried_case_count: `{payload.get('quality_retried_case_count')}`",
        f"- quality_selected_passed_count: `{payload.get('quality_selected_passed_count')}`",
        f"- live_case_count: `{payload.get('live_case_count')}`",
        f"- mean_min_distance_m: `{payload.get('mean_min_distance_m')}`",
        f"- fidelity: `{payload.get('fidelity')}`",
        f"- worst_case: `{_mapping(payload.get('worst_case')).get('case_id')}`",
        f"- quality_passed_count: `{_mapping(payload.get('quality')).get('passed_count')}`",
        "",
        "## Cases",
        "",
    ]
    for record in list(payload.get("cases", [])):
        fidelity = _mapping(record.get("fidelity_metrics"))
        lines.append(
            f"- `{record.get('case_id')}`: behavior=`{record.get('behavior_id')}`, "
            f"status=`{record.get('status')}`, min_distance_m=`{record.get('min_distance_m')}`, "
            f"visible_actors=`{fidelity.get('visible_actor_count_mean')}`, "
            f"max_ood_step_m=`{fidelity.get('max_ood_step_m')}`, "
            f"video_status=`{record.get('video_status')}`, "
            f"road_alignment=`{record.get('road_alignment_path')}`, "
            f"video=`{record.get('video_path')}`"
        )
    blockers = list(payload.get("blockers", []))
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("- none")
    return "\n".join(lines) + "\n"


__all__ = [
    "CampaignCaseRecord",
    "ScriptedOodCampaignConfig",
    "load_scripted_ood_campaign_config",
    "run_scripted_ood_campaign",
    "write_scripted_ood_campaign",
]
