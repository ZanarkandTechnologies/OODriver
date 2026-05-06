"""Scenario Studio catalog for generated OOD evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

PromotionStatus = Literal["candidate", "hero", "failure_case", "rejected", "blocked"]


@dataclass(frozen=True)
class ScenarioQuality:
    road_aligned: bool | None = None
    has_conflict: bool | None = None
    has_video: bool = False
    has_model_reasoning: bool = False
    status: str = "unknown"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "road_aligned": self.road_aligned,
            "has_conflict": self.has_conflict,
            "has_video": self.has_video,
            "has_model_reasoning": self.has_model_reasoning,
            "status": self.status,
        }

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "ScenarioQuality":
        return cls(
            road_aligned=_optional_bool(payload.get("road_aligned")),
            has_conflict=_optional_bool(payload.get("has_conflict")),
            has_video=bool(payload.get("has_video", False)),
            has_model_reasoning=bool(payload.get("has_model_reasoning", False)),
            status=str(payload.get("status", "unknown")),
        )


@dataclass(frozen=True)
class ScenarioArtifacts:
    video: str | None = None
    tracks: str | None = None
    reasoning: str | None = None
    quality_report: str | None = None
    scenario_report: str | None = None
    rgb_folder: str | None = None
    package: str | None = None
    comparison: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "video": self.video,
            "tracks": self.tracks,
            "reasoning": self.reasoning,
            "quality_report": self.quality_report,
            "scenario_report": self.scenario_report,
            "rgb_folder": self.rgb_folder,
            "package": self.package,
            "comparison": self.comparison,
        }

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "ScenarioArtifacts":
        return cls(
            video=_optional_str(payload.get("video")),
            tracks=_optional_str(payload.get("tracks")),
            reasoning=_optional_str(payload.get("reasoning")),
            quality_report=_optional_str(payload.get("quality_report")),
            scenario_report=_optional_str(payload.get("scenario_report")),
            rgb_folder=_optional_str(payload.get("rgb_folder")),
            package=_optional_str(payload.get("package")),
            comparison=_optional_str(payload.get("comparison")),
        )


@dataclass(frozen=True)
class PromotionDecision:
    status: PromotionStatus = "candidate"
    reason: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {"status": self.status, "reason": self.reason}

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "PromotionDecision":
        return cls(
            status=_promotion_status(str(payload.get("status", "candidate"))),
            reason=_optional_str(payload.get("reason")),
        )


@dataclass(frozen=True)
class ScenarioCatalogRecord:
    scenario_id: str
    recipe_id: str | None
    case_id: str | None
    family: str
    behavior_id: str | None
    environment_tags: list[str]
    ood_tags: list[str]
    quality: ScenarioQuality
    artifacts: ScenarioArtifacts
    promotion: PromotionDecision = field(default_factory=PromotionDecision)
    source_artifacts: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "recipe_id": self.recipe_id,
            "case_id": self.case_id,
            "family": self.family,
            "behavior_id": self.behavior_id,
            "environment_tags": self.environment_tags,
            "ood_tags": self.ood_tags,
            "quality": self.quality.to_jsonable(),
            "artifacts": self.artifacts.to_jsonable(),
            "promotion": self.promotion.to_jsonable(),
            "source_artifacts": self.source_artifacts,
            "blockers": self.blockers,
        }

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "ScenarioCatalogRecord":
        return cls(
            scenario_id=str(payload["scenario_id"]),
            recipe_id=_optional_str(payload.get("recipe_id")),
            case_id=_optional_str(payload.get("case_id")),
            family=str(payload.get("family", "unknown")),
            behavior_id=_optional_str(payload.get("behavior_id")),
            environment_tags=_string_list(payload.get("environment_tags", [])),
            ood_tags=_string_list(payload.get("ood_tags", [])),
            quality=ScenarioQuality.from_jsonable(dict(payload.get("quality", {}))),
            artifacts=ScenarioArtifacts.from_jsonable(dict(payload.get("artifacts", {}))),
            promotion=PromotionDecision.from_jsonable(dict(payload.get("promotion", {}))),
            source_artifacts=_string_list(payload.get("source_artifacts", [])),
            blockers=_string_list(payload.get("blockers", [])),
        )


@dataclass(frozen=True)
class ScenarioCatalog:
    records: list[ScenarioCatalogRecord]
    source_roots: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "record_count": len(self.records),
            "source_roots": self.source_roots,
            "records": [record.to_jsonable() for record in self.records],
            "promotion_counts": _promotion_counts(self.records),
            "quality_counts": _quality_counts(self.records),
        }

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "ScenarioCatalog":
        return cls(
            records=[
                ScenarioCatalogRecord.from_jsonable(dict(record))
                for record in list(payload.get("records", []))
            ],
            source_roots=_string_list(payload.get("source_roots", [])),
        )


@dataclass(frozen=True)
class ScenarioQuery:
    tag: str | None = None
    behavior_id: str | None = None
    promotion_status: PromotionStatus | None = None
    requires_video: bool = False
    requires_model_reasoning: bool = False
    requires_road_aligned: bool = False


def load_scenario_catalog(path: Path) -> ScenarioCatalog:
    return ScenarioCatalog.from_jsonable(json.loads(path.read_text(encoding="utf-8")))


def index_scenario_artifacts(artifact_roots: list[Path]) -> ScenarioCatalog:
    records: dict[str, ScenarioCatalogRecord] = {}
    source_roots: list[str] = []
    for root in artifact_roots:
        source_roots.append(str(root))
        if root.is_file():
            _index_artifact_file(root, records)
            continue
        for path in sorted(root.rglob("*.json")):
            if path.name in {
                "scripted_ood_campaign_summary.json",
                "alpamayo_ood_batch_summary.json",
                "carla_ood_demo.json",
                "ood_video_evidence.json",
            }:
                _index_artifact_file(path, records)
    return ScenarioCatalog(records=sorted(records.values(), key=lambda item: item.scenario_id), source_roots=source_roots)


def filter_catalog(catalog: ScenarioCatalog, query: ScenarioQuery) -> list[ScenarioCatalogRecord]:
    records = catalog.records
    if query.tag:
        tag = query.tag.lower()
        records = [
            record
            for record in records
            if tag in {item.lower() for item in [*record.environment_tags, *record.ood_tags]}
        ]
    if query.behavior_id:
        records = [record for record in records if record.behavior_id == query.behavior_id]
    if query.promotion_status:
        records = [record for record in records if record.promotion.status == query.promotion_status]
    if query.requires_video:
        records = [record for record in records if record.quality.has_video]
    if query.requires_model_reasoning:
        records = [record for record in records if record.quality.has_model_reasoning]
    if query.requires_road_aligned:
        records = [record for record in records if record.quality.road_aligned is True]
    return records


def promote_scenario(
    catalog: ScenarioCatalog,
    scenario_id: str,
    decision: PromotionDecision,
) -> ScenarioCatalog:
    found = False
    records: list[ScenarioCatalogRecord] = []
    for record in catalog.records:
        if record.scenario_id == scenario_id or record.case_id == scenario_id:
            records.append(replace(record, promotion=decision))
            found = True
        else:
            records.append(record)
    if not found:
        raise ValueError(f"Scenario not found in catalog: {scenario_id}")
    return ScenarioCatalog(records=records, source_roots=catalog.source_roots)


def write_scenario_catalog_outputs(
    catalog: ScenarioCatalog,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "scenario_catalog.json"
    report_path = output_dir / "scenario_catalog.md"
    payload = catalog.to_jsonable()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_catalog_markdown(catalog), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def write_scenario_selection(
    records: list[ScenarioCatalogRecord],
    output_dir: Path,
    *,
    selection_id: str = "scenario-selection",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{selection_id}.json"
    report_path = output_dir / f"{selection_id}.md"
    payload = {
        "selection_id": selection_id,
        "record_count": len(records),
        "records": [record.to_jsonable() for record in records],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_selection_markdown(selection_id, records), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _index_artifact_file(path: Path, records: dict[str, ScenarioCatalogRecord]) -> None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if path.name == "scripted_ood_campaign_summary.json":
        for case in list(payload.get("cases", [])):
            if isinstance(case, dict):
                _merge_record(records, _record_from_campaign_case(path, case))
    elif path.name == "alpamayo_ood_batch_summary.json":
        for record in list(payload.get("records", [])):
            if isinstance(record, dict):
                _merge_record(records, _record_from_alpamayo_record(path, record))
    elif path.name == "carla_ood_demo.json":
        _merge_record(records, _record_from_carla_demo(path, payload))
    elif path.name == "ood_video_evidence.json":
        _merge_record(records, _record_from_ood_video_evidence(path, payload))


def _record_from_campaign_case(path: Path, case: dict[str, Any]) -> ScenarioCatalogRecord:
    recipe_id = _optional_str(case.get("recipe_id"))
    scenario_id = recipe_id or str(case.get("case_id", path.parent.name))
    video = _resolved_artifact_path(path, _optional_str(case.get("video_path")))
    quality_report = _road_alignment_path_from_case(path, case)
    road_aligned = _road_aligned_from_report(quality_report)
    blockers = sorted(
        set(_string_list(case.get("blockers", [])))
        | set(_string_list(case.get("quality_blockers", [])))
    )
    has_video = bool(video) or str(case.get("video_status")) == "passed"
    min_distance = case.get("min_distance_m")
    parsed_distance = _safe_float(min_distance)
    has_conflict = bool(parsed_distance is not None and parsed_distance <= 6.0)
    status = _campaign_quality_status(case, has_video=has_video, road_aligned=road_aligned)
    return ScenarioCatalogRecord(
        scenario_id=scenario_id,
        recipe_id=recipe_id,
        case_id=_optional_str(case.get("case_id")),
        family=_family_from_recipe_id(scenario_id),
        behavior_id=_optional_str(case.get("behavior_id")),
        environment_tags=_environment_tags_from_id(scenario_id),
        ood_tags=_ood_tags_from_case(case),
        quality=ScenarioQuality(
            road_aligned=road_aligned,
            has_conflict=has_conflict,
            has_video=has_video,
            has_model_reasoning=False,
            status=status,
        ),
        artifacts=ScenarioArtifacts(
            video=video,
            tracks=_resolved_artifact_path(path, _optional_str(case.get("tracks_path"))),
            quality_report=quality_report,
            scenario_report=_resolved_artifact_path(path, _optional_str(case.get("scenario_report_path"))),
            rgb_folder=_resolved_artifact_path(path, _optional_str(case.get("rgb_folder"))),
        ),
        promotion=PromotionDecision(status=_default_promotion(status, has_video, blockers), reason=_default_reason(status, blockers)),
        source_artifacts=[str(path)],
        blockers=blockers,
    )


def _record_from_alpamayo_record(path: Path, record: dict[str, Any]) -> ScenarioCatalogRecord:
    scenario_id = str(record.get("scenario_id") or record.get("case_id") or path.parent.name)
    raw_status = str(record.get("status", "unknown"))
    status = "open_loop_only" if raw_status == "passed" else raw_status
    blockers = _string_list(record.get("blockers", []))
    return ScenarioCatalogRecord(
        scenario_id=scenario_id,
        recipe_id=_optional_str(record.get("scenario_id")),
        case_id=_optional_str(record.get("case_id")),
        family=_family_from_recipe_id(scenario_id),
        behavior_id=None,
        environment_tags=_environment_tags_from_id(scenario_id),
        ood_tags=_string_list(record.get("memory_ids", [])),
        quality=ScenarioQuality(
            road_aligned=None,
            has_conflict=None,
            has_video=False,
            has_model_reasoning=bool(record.get("baseline_decision_path") or record.get("memory_decision_path")),
            status=status,
        ),
        artifacts=ScenarioArtifacts(
            reasoning=_optional_str(record.get("memory_decision_path") or record.get("baseline_decision_path")),
            package=_optional_str(record.get("package_path")),
            comparison=_optional_str(record.get("comparison_path")),
        ),
        promotion=PromotionDecision(status=_default_promotion(status, False, blockers), reason=_default_reason(status, blockers)),
        source_artifacts=[str(path)],
        blockers=blockers,
    )


def _record_from_carla_demo(path: Path, payload: dict[str, Any]) -> ScenarioCatalogRecord:
    scenario_id = str(payload.get("scenario_id") or payload.get("recipe_id") or path.parent.name)
    quality_report = _resolved_artifact_path(path, _optional_str(payload.get("road_alignment_path")))
    road_aligned = _road_aligned_from_report(quality_report)
    blockers = _string_list(payload.get("blockers", []))
    has_video = bool(payload.get("rgb_folder")) and int(payload.get("frame_count", 0) or 0) > 0
    status = _legacy_quality_status(str(payload.get("status", "unknown")), has_video=has_video, road_aligned=road_aligned)
    return ScenarioCatalogRecord(
        scenario_id=scenario_id,
        recipe_id=_optional_str(payload.get("recipe_id")),
        case_id=None,
        family=_family_from_recipe_id(scenario_id),
        behavior_id=_optional_str(payload.get("behavior_id")),
        environment_tags=_environment_tags_from_id(scenario_id),
        ood_tags=_string_list(payload.get("generated_asset_ids", [])),
        quality=ScenarioQuality(
            road_aligned=road_aligned,
            has_conflict=None,
            has_video=has_video,
            has_model_reasoning=False,
            status=status,
        ),
        artifacts=ScenarioArtifacts(
            tracks=_resolved_artifact_path(path, _optional_str(payload.get("tracks_path"))),
            quality_report=quality_report,
            scenario_report=str(path),
            rgb_folder=_resolved_artifact_path(path, _optional_str(payload.get("rgb_folder"))),
        ),
        promotion=PromotionDecision(status=_default_promotion(status, has_video, blockers), reason=_default_reason(status, blockers)),
        source_artifacts=[str(path)],
        blockers=blockers,
    )


def _record_from_ood_video_evidence(path: Path, payload: dict[str, Any]) -> ScenarioCatalogRecord:
    scenario_id = str(payload.get("scenario_id") or path.parent.name)
    behavior_id = _optional_str(payload.get("behavior_id"))
    raw_status = str(payload.get("status", "unknown"))
    blockers = _string_list(payload.get("blockers", []))
    video = _resolved_artifact_path(path, _optional_str(payload.get("video_path")))
    min_distance = _video_worst_risk_distance(payload)
    has_conflict = bool(min_distance is not None and min_distance <= 6.0)
    has_video = bool(video) or raw_status == "passed"
    status = raw_status if raw_status != "unknown" else ("passed" if has_video else "unknown")
    return ScenarioCatalogRecord(
        scenario_id=scenario_id,
        recipe_id=scenario_id,
        case_id=None,
        family=_family_from_recipe_id(scenario_id),
        behavior_id=behavior_id,
        environment_tags=_environment_tags_from_id(scenario_id),
        ood_tags=sorted(set(_string_list(payload.get("ood_tags", [])) + ([behavior_id] if behavior_id else []) + ["video"])),
        quality=ScenarioQuality(
            road_aligned=None,
            has_conflict=has_conflict,
            has_video=has_video,
            has_model_reasoning=False,
            status=status,
        ),
        artifacts=ScenarioArtifacts(
            video=video,
            quality_report=str(path),
        ),
        promotion=PromotionDecision(status=_default_promotion(status, has_video, blockers), reason=_default_reason(status, blockers)),
        source_artifacts=[str(path)],
        blockers=blockers,
    )


def _merge_record(records: dict[str, ScenarioCatalogRecord], update: ScenarioCatalogRecord) -> None:
    existing = records.get(update.scenario_id)
    if existing is None:
        records[update.scenario_id] = update
        return
    quality = ScenarioQuality(
        road_aligned=_prefer_bool(existing.quality.road_aligned, update.quality.road_aligned),
        has_conflict=_prefer_conflict(existing.quality.has_conflict, update.quality.has_conflict),
        has_video=existing.quality.has_video or update.quality.has_video,
        has_model_reasoning=existing.quality.has_model_reasoning or update.quality.has_model_reasoning,
        status=_merge_quality_status(existing.quality.status, update.quality.status),
    )
    artifacts = ScenarioArtifacts(
        video=_preferred_video(existing, update),
        tracks=existing.artifacts.tracks or update.artifacts.tracks,
        reasoning=existing.artifacts.reasoning or update.artifacts.reasoning,
        quality_report=existing.artifacts.quality_report or update.artifacts.quality_report,
        scenario_report=existing.artifacts.scenario_report or update.artifacts.scenario_report,
        rgb_folder=existing.artifacts.rgb_folder or update.artifacts.rgb_folder,
        package=existing.artifacts.package or update.artifacts.package,
        comparison=existing.artifacts.comparison or update.artifacts.comparison,
    )
    blockers = sorted(set(existing.blockers) | set(update.blockers))
    promotion = _promotion_from_merged_quality(quality, blockers, existing.promotion, update.promotion)
    records[update.scenario_id] = replace(
        existing,
        behavior_id=existing.behavior_id or update.behavior_id,
        environment_tags=sorted(set(existing.environment_tags) | set(update.environment_tags)),
        ood_tags=sorted(set(existing.ood_tags) | set(update.ood_tags)),
        quality=quality,
        artifacts=artifacts,
        promotion=promotion,
        source_artifacts=sorted(set(existing.source_artifacts) | set(update.source_artifacts)),
        blockers=blockers,
    )


def _preferred_video(existing: ScenarioCatalogRecord, update: ScenarioCatalogRecord) -> str | None:
    if update.artifacts.video and _is_overlay_video_record(update):
        return update.artifacts.video
    return existing.artifacts.video or update.artifacts.video


def _is_overlay_video_record(record: ScenarioCatalogRecord) -> bool:
    return any(Path(source).name == "ood_video_evidence.json" for source in record.source_artifacts)


def _video_worst_risk_distance(payload: dict[str, Any]) -> float | None:
    top_level = payload.get("worst_risk")
    if isinstance(top_level, dict):
        return _safe_float(top_level.get("distance_m"))
    overlay = payload.get("overlay")
    if isinstance(overlay, dict):
        nested = overlay.get("worst_risk")
        if isinstance(nested, dict):
            return _safe_float(nested.get("distance_m"))
    return None


def _catalog_markdown(catalog: ScenarioCatalog) -> str:
    lines = [
        "# Scenario Catalog",
        "",
        f"- records: `{len(catalog.records)}`",
        f"- source_roots: `{', '.join(catalog.source_roots)}`",
        "",
        "| scenario | behavior | quality | promotion | video | reasoning |",
        "|---|---|---|---|---|---|",
    ]
    for record in catalog.records:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(record.scenario_id),
                    _cell(record.behavior_id),
                    _cell(record.quality.status),
                    _cell(record.promotion.status),
                    "yes" if record.quality.has_video else "no",
                    "yes" if record.quality.has_model_reasoning else "no",
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _selection_markdown(selection_id: str, records: list[ScenarioCatalogRecord]) -> str:
    lines = [
        f"# Scenario Selection: {selection_id}",
        "",
        f"- records: `{len(records)}`",
        "",
    ]
    for record in records:
        lines.append(f"- `{record.scenario_id}` promotion `{record.promotion.status}`")
    lines.append("")
    return "\n".join(lines)


def _road_alignment_path_from_case(path: Path, case: dict[str, Any]) -> str | None:
    explicit_path = _resolved_artifact_path(path, _optional_str(case.get("road_alignment_path")))
    if explicit_path:
        return explicit_path
    report_path = _resolved_artifact_path(path, _optional_str(case.get("scenario_report_path")))
    if not report_path:
        return None
    candidate = Path(report_path).with_name("road_alignment_report.json")
    return str(candidate) if candidate.exists() else None


def _road_aligned_from_report(path: str | None) -> bool | None:
    if not path:
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict):
        return bool(payload.get("passes")) if "passes" in payload else None
    return None


def _resolved_artifact_path(source_path: Path, raw_path: str | None) -> str | None:
    if not raw_path:
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute() or candidate.exists():
        return str(candidate)
    for parent in [source_path.parent, *source_path.parents]:
        relative_candidate = parent / candidate
        if relative_candidate.exists():
            return str(relative_candidate)
    parts = candidate.parts
    for parent in [source_path.parent, *source_path.parents]:
        if parent.name not in parts:
            continue
        index = parts.index(parent.name)
        if index + 1 >= len(parts):
            continue
        suffix_candidate = parent / Path(*parts[index + 1 :])
        if suffix_candidate.exists():
            return str(suffix_candidate)
    sibling = source_path.parent / candidate.name
    if sibling.exists():
        return str(sibling)
    return raw_path


def _family_from_recipe_id(recipe_id: str) -> str:
    parts = [part for part in recipe_id.split("-") if part]
    for marker in ("occlusion", "visual", "lane", "regional", "obstacle"):
        if marker in parts:
            return marker
    return parts[1] if len(parts) > 1 else "unknown"


def _environment_tags_from_id(recipe_id: str) -> list[str]:
    tags = []
    lowered = recipe_id.lower()
    for tag in ("animals", "customobstacles", "pedestrians", "visual-noise", "occlusion", "regional-driving-behavior"):
        if tag in lowered:
            tags.append(tag)
    return tags


def _ood_tags_from_case(case: dict[str, Any]) -> list[str]:
    tags = []
    behavior = _optional_str(case.get("behavior_id"))
    if behavior:
        tags.append(behavior)
    status = _optional_str(case.get("status"))
    if status:
        tags.append(status)
    if case.get("live") is True:
        tags.append("live_carla")
    if case.get("video_status") == "passed":
        tags.append("video")
    return tags


def _default_promotion(status: str, has_video: bool, blockers: list[str]) -> PromotionStatus:
    if blockers or status in {"blocked", "partial", "quality_blocked"} or status.startswith("legacy_"):
        return "blocked"
    if status == "passed" and has_video:
        return "candidate"
    if status == "passed":
        return "blocked"
    return "rejected"


def _campaign_quality_status(case: dict[str, Any], *, has_video: bool, road_aligned: bool | None) -> str:
    explicit_quality = _optional_str(case.get("quality_status"))
    if explicit_quality:
        return explicit_quality
    raw_status = str(case.get("status") or "unknown")
    return _legacy_quality_status(raw_status, has_video=has_video, road_aligned=road_aligned)


def _legacy_quality_status(raw_status: str, *, has_video: bool, road_aligned: bool | None) -> str:
    if raw_status == "passed" and has_video and road_aligned is True:
        return "passed"
    if raw_status == "unknown":
        return "unknown"
    return f"legacy_{raw_status}"


def _merge_quality_status(left: str, right: str) -> str:
    rank = {
        "blocked": 5,
        "quality_blocked": 5,
        "partial": 4,
        "passed": 4,
        "legacy_passed": 3,
        "legacy_blocked": 3,
        "planned": 1,
        "open_loop_only": 1,
        "unknown": 0,
    }
    return left if rank.get(left, 0) >= rank.get(right, 0) else right


def _promotion_from_merged_quality(
    quality: ScenarioQuality,
    blockers: list[str],
    left: PromotionDecision,
    right: PromotionDecision,
) -> PromotionDecision:
    if blockers or quality.status != "passed" or not quality.has_video or quality.road_aligned is not True:
        reason = "; ".join(blockers) if blockers else f"quality_status={quality.status}"
        return PromotionDecision(status="blocked", reason=reason)
    return _stronger_promotion(left, right)


def _default_reason(status: str, blockers: list[str]) -> str | None:
    if blockers:
        return "; ".join(blockers)
    if status not in {"passed", "unknown"}:
        return f"status={status}"
    return None


def _stronger_promotion(left: PromotionDecision, right: PromotionDecision) -> PromotionDecision:
    rank = {"hero": 5, "failure_case": 4, "candidate": 3, "blocked": 2, "rejected": 1}
    return left if rank.get(left.status, 0) >= rank.get(right.status, 0) else right


def _promotion_counts(records: list[ScenarioCatalogRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.promotion.status] = counts.get(record.promotion.status, 0) + 1
    return dict(sorted(counts.items()))


def _quality_counts(records: list[ScenarioCatalogRecord]) -> dict[str, int]:
    return {
        "has_video": sum(1 for record in records if record.quality.has_video),
        "has_model_reasoning": sum(1 for record in records if record.quality.has_model_reasoning),
        "road_aligned_true": sum(1 for record in records if record.quality.road_aligned is True),
        "road_aligned_unknown": sum(1 for record in records if record.quality.road_aligned is None),
    }


def _cell(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|")


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value if str(item)]
    return [str(value)] if str(value) else []


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _safe_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _prefer_bool(left: bool | None, right: bool | None) -> bool | None:
    return left if left is not None else right


def _prefer_conflict(left: bool | None, right: bool | None) -> bool | None:
    if left is True or right is True:
        return True
    return left if left is not None else right


def _promotion_status(value: str) -> PromotionStatus:
    if value in {"candidate", "hero", "failure_case", "rejected", "blocked"}:
        return value  # type: ignore[return-value]
    return "candidate"


__all__ = [
    "PromotionDecision",
    "ScenarioArtifacts",
    "ScenarioCatalog",
    "ScenarioCatalogRecord",
    "ScenarioQuality",
    "ScenarioQuery",
    "filter_catalog",
    "index_scenario_artifacts",
    "load_scenario_catalog",
    "promote_scenario",
    "write_scenario_catalog_outputs",
    "write_scenario_selection",
]
