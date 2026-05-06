"""Final-sprint scenario selection matrix for SoTA submission evidence."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios import ScenarioCatalogRecord, load_scenario_catalog

EvalRole = Literal["hero", "support", "failure", "backup"]


@dataclass(frozen=True)
class SubmissionEvalMatrixConfig:
    catalog_paths: tuple[Path, ...]
    evidence_paths: tuple[Path, ...] = ()
    output_root: Path = Path("artifacts/runs")
    run_id: str = "submission-eval-matrix"
    limit: int = 10


def build_submission_eval_matrix(
    catalog_paths: list[Path] | tuple[Path, ...],
    evidence_paths: list[Path] | tuple[Path, ...],
    output_dir: Path,
    *,
    limit: int = 10,
) -> dict[str, Any]:
    records = _load_records(tuple(catalog_paths))
    evidence = _load_evidence(tuple(evidence_paths))
    selected = _select_records(records, max(1, limit))
    cases = [
        _case_from_record(record, index, selected, evidence)
        for index, record in enumerate(selected)
    ]
    payload = {
        "matrix_id": output_dir.name,
        "case_count": len(cases),
        "hero_count": sum(1 for case in cases if case["role"] == "hero"),
        "role_counts": _count_by(cases, "role"),
        "scenario_families": sorted({str(case["scenario_family"]) for case in cases}),
        "needed_next_counts": _needed_next_counts(cases),
        "cases": cases,
        "claim_boundaries": [
            "submission_eval_matrix_is_selection_planning=true",
            "closed_loop_carla_execution=false",
            "alpamayo_inference_executed_by_this_ticket=false",
        ],
    }
    return write_submission_eval_matrix(output_dir, payload)


def run_submission_eval_matrix(config: SubmissionEvalMatrixConfig) -> dict[str, Any]:
    run_dir = prepare_run_dir(config.output_root, config.run_id)
    return build_submission_eval_matrix(
        config.catalog_paths,
        config.evidence_paths,
        run_dir,
        limit=config.limit,
    )


def write_submission_eval_matrix(output_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "submission_eval_matrix.json"
    report_path = output_dir / "submission_eval_matrix.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _load_records(catalog_paths: tuple[Path, ...]) -> list[ScenarioCatalogRecord]:
    records: dict[str, ScenarioCatalogRecord] = {}
    for path in catalog_paths:
        catalog = load_scenario_catalog(path)
        for record in catalog.records:
            current = records.get(record.scenario_id)
            if current is None or _record_score(record) > _record_score(current):
                records[record.scenario_id] = record
            elif current is not None:
                records[record.scenario_id] = _combine_record(current, record)
    return sorted(records.values(), key=lambda record: (-_record_score(record), record.scenario_id))


def _combine_record(left: ScenarioCatalogRecord, right: ScenarioCatalogRecord) -> ScenarioCatalogRecord:
    from dataclasses import replace
    from driverx.scenarios import ScenarioArtifacts, ScenarioQuality

    return replace(
        left,
        behavior_id=left.behavior_id or right.behavior_id,
        environment_tags=sorted(set(left.environment_tags) | set(right.environment_tags)),
        ood_tags=sorted(set(left.ood_tags) | set(right.ood_tags)),
        quality=ScenarioQuality(
            road_aligned=left.quality.road_aligned if left.quality.road_aligned is not None else right.quality.road_aligned,
            has_conflict=left.quality.has_conflict if left.quality.has_conflict is not None else right.quality.has_conflict,
            has_video=left.quality.has_video or right.quality.has_video,
            has_model_reasoning=left.quality.has_model_reasoning or right.quality.has_model_reasoning,
            status=_best_status(left.quality.status, right.quality.status),
        ),
        artifacts=ScenarioArtifacts(
            video=left.artifacts.video or right.artifacts.video,
            tracks=left.artifacts.tracks or right.artifacts.tracks,
            reasoning=left.artifacts.reasoning or right.artifacts.reasoning,
            quality_report=left.artifacts.quality_report or right.artifacts.quality_report,
            scenario_report=left.artifacts.scenario_report or right.artifacts.scenario_report,
            rgb_folder=left.artifacts.rgb_folder or right.artifacts.rgb_folder,
            package=left.artifacts.package or right.artifacts.package,
            comparison=left.artifacts.comparison or right.artifacts.comparison,
        ),
        source_artifacts=sorted(set(left.source_artifacts) | set(right.source_artifacts)),
        blockers=sorted(set(left.blockers) | set(right.blockers)),
    )


def _best_status(left: str, right: str) -> str:
    order = {
        "passed": 6,
        "open_loop_only": 5,
        "planned": 4,
        "legacy_passed": 3,
        "blocked": 2,
        "failed": 1,
        "unknown": 0,
    }
    return left if order.get(left, 0) >= order.get(right, 0) else right


def _load_evidence(evidence_paths: tuple[Path, ...]) -> dict[str, dict[str, str]]:
    evidence: dict[str, dict[str, str]] = {}
    for path in evidence_paths:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        scenario_id = _scenario_id_from_evidence(payload, path)
        if not scenario_id:
            continue
        bucket = evidence.setdefault(scenario_id, {})
        kind = _evidence_kind(payload, path)
        bucket[kind] = str(path)
    return evidence


def _scenario_id_from_evidence(payload: dict[str, Any], path: Path) -> str | None:
    for key in ("scenario_id", "case_id", "recipe_id"):
        if payload.get(key):
            return str(payload[key])
    tensor = payload.get("tensor_manifest")
    if isinstance(tensor, dict):
        frame_name = str(tensor.get("frame_name", ""))
        if "driverx_ood_" in frame_name:
            return frame_name.split("driverx_ood_", 1)[1]
    decision = payload.get("policy_decision")
    if isinstance(decision, dict):
        scene_type = str(dict(decision.get("intent", {})).get("scene_type", ""))
        if "driverx_ood_" in scene_type:
            return scene_type.split("driverx_ood_", 1)[1]
    stem = path.stem
    match = re.search(r"(generated-[a-z0-9-]+)", stem)
    return match.group(1) if match else None


def _evidence_kind(payload: dict[str, Any], path: Path) -> str:
    name = path.name
    if name == "alpamayo_policy_decision.json" or "policy_decision" in payload:
        decision = payload.get("policy_decision")
        if isinstance(decision, dict):
            retrieved = list(decision.get("retrieved_memory_ids", []))
            hazards = " ".join(str(item) for item in list(dict(decision.get("intent", {})).get("hazards", [])))
            if retrieved or "memory" in hazards.lower():
                return "alpamayo_memory"
        return "alpamayo_baseline"
    if "alpamayo" in name:
        return "alpamayo_baseline"
    if "comparison" in name:
        return "rag_comparison"
    return "supporting_evidence"


def _select_records(records: list[ScenarioCatalogRecord], limit: int) -> list[ScenarioCatalogRecord]:
    selected: list[ScenarioCatalogRecord] = []
    seen_families: set[str] = set()
    for record in records:
        if record.quality.status == "passed" and record.quality.has_video:
            selected.append(record)
            seen_families.add(record.family)
            break
    for record in records:
        if len(selected) >= limit:
            break
        if record in selected:
            continue
        if record.family not in seen_families or len(selected) < 6:
            selected.append(record)
            seen_families.add(record.family)
    return selected[:limit]


def _case_from_record(
    record: ScenarioCatalogRecord,
    index: int,
    selected: list[ScenarioCatalogRecord],
    evidence: dict[str, dict[str, str]],
) -> dict[str, Any]:
    evidence_paths = evidence.get(record.scenario_id, {})
    role = _role_for_record(record, index)
    merged_evidence = {
        "quality_status": record.quality.status,
        "video_path": _normalize_artifact_path(record.artifacts.video),
        "tracks_path": _normalize_artifact_path(record.artifacts.tracks),
        "quality_report": _normalize_artifact_path(record.artifacts.quality_report),
        "alpamayo_baseline": _normalize_artifact_path(record.artifacts.reasoning)
        or _normalize_artifact_path(evidence_paths.get("alpamayo_baseline")),
        "alpamayo_memory": _normalize_artifact_path(evidence_paths.get("alpamayo_memory")),
        "rag_comparison": _normalize_artifact_path(record.artifacts.comparison)
        or _normalize_artifact_path(evidence_paths.get("rag_comparison")),
    }
    needed_next = _needed_next(record, merged_evidence)
    return {
        "case_id": f"case-{index + 1:02d}",
        "scenario_id": record.scenario_id,
        "role": role,
        "scenario_family": record.family,
        "behavior_id": record.behavior_id,
        "environment_tags": record.environment_tags,
        "ood_tags": record.ood_tags,
        "evidence": merged_evidence,
        "needed_next": needed_next,
        "selection_score": round(_record_score(record), 4),
        "submission_claim": _submission_claim(record, role, merged_evidence, needed_next),
        "blockers": record.blockers,
    }


def _role_for_record(record: ScenarioCatalogRecord, index: int) -> EvalRole:
    if index == 0 and record.quality.status == "passed" and record.quality.has_video:
        return "hero"
    if record.quality.status in {"blocked", "failed"} or record.blockers:
        return "failure"
    if record.quality.has_conflict or record.quality.has_model_reasoning:
        return "support"
    return "backup"


def _needed_next(record: ScenarioCatalogRecord, evidence: dict[str, Any]) -> list[str]:
    needed: list[str] = []
    if record.quality.status != "passed" or not record.quality.has_video or record.quality.road_aligned is not True:
        needed.append("TASK-102_high_fidelity_carla_video")
    if evidence.get("alpamayo_baseline") is None:
        needed.append("TASK-104_alpamayo_baseline")
    if evidence.get("alpamayo_memory") is None:
        needed.append("TASK-104_alpamayo_memory")
    if evidence.get("rag_comparison") is None:
        needed.append("TASK-104_rag_comparison")
    if not record.behavior_id:
        needed.append("TASK-103_behavior_binding")
    needed.append("TASK-105_fail2drive_reference")
    return sorted(set(needed))


def _submission_claim(
    record: ScenarioCatalogRecord,
    role: EvalRole,
    evidence: dict[str, Any],
    needed_next: list[str],
) -> str:
    if role == "hero":
        return "Primary generated OOD CARLA case with road-aligned video; use it to show the simulator and anchor Alpamayo/RAG comparison."
    if "TASK-102_high_fidelity_carla_video" in needed_next:
        return "Candidate scenario family for additional generated evidence; currently useful for breadth or failure analysis, not hero promotion."
    if evidence.get("alpamayo_baseline") or evidence.get("alpamayo_memory"):
        return "Open-loop VLA reasoning support case for minimal-shot model reaction analysis."
    return "Backup generated OOD case for breadth if stronger cases fail."


def _record_score(record: ScenarioCatalogRecord) -> float:
    score = 0.0
    score += 4.0 if record.quality.status == "passed" else 0.0
    score += 3.0 if record.promotion.status == "hero" else 0.0
    score += 2.0 if record.quality.has_video else 0.0
    score += 1.5 if record.quality.road_aligned is True else 0.0
    score += 1.0 if record.quality.has_conflict else 0.0
    score += 1.0 if record.quality.has_model_reasoning else 0.0
    score += 0.25 * len(set(record.environment_tags + record.ood_tags))
    score -= 1.0 if record.blockers else 0.0
    return score


def _normalize_artifact_path(path: str | None) -> str | None:
    if not path:
        return None
    candidate = Path(path)
    if candidate.exists():
        return path
    text = str(path)
    if text.startswith("tickets/TASK-"):
        archived = Path(text.replace("tickets/TASK-", "tickets/archive/TASK-", 1))
        if archived.exists():
            return str(archived)
    return path


def _count_by(cases: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in cases:
        value = str(case.get(key, "unknown"))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _needed_next_counts(cases: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in cases:
        for item in list(case.get("needed_next", [])):
            counts[str(item)] = counts.get(str(item), 0) + 1
    return dict(sorted(counts.items()))


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Submission Evaluation Matrix",
        "",
        f"- Matrix id: `{payload['matrix_id']}`",
        f"- Cases: `{payload['case_count']}`",
        f"- Hero cases: `{payload['hero_count']}`",
        "",
        "## Why These Cases",
        "",
        "This matrix freezes the final sprint queue around generated OOD simulation, Alpamayo/RAG reaction, and Fail2Drive-style reference framing.",
        "",
        "## Case Table",
        "",
        "| case | role | scenario | family | behavior | quality | next |",
        "|---|---|---|---|---|---|---|",
    ]
    for case in list(payload.get("cases", [])):
        evidence = dict(case.get("evidence", {}))
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(case.get("case_id")),
                    _cell(case.get("role")),
                    _cell(case.get("scenario_id")),
                    _cell(case.get("scenario_family")),
                    _cell(case.get("behavior_id")),
                    _cell(evidence.get("quality_status")),
                    _cell(", ".join(list(case.get("needed_next", [])))),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Claims", ""])
    for case in list(payload.get("cases", [])):
        lines.append(f"- `{case['case_id']}` `{case['scenario_id']}`: {case['submission_claim']}")
    lines.extend(["", "## Claim Boundaries", ""])
    for boundary in list(payload.get("claim_boundaries", [])):
        lines.append(f"- `{boundary}`")
    lines.append("")
    return "\n".join(lines)


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|")


__all__ = [
    "SubmissionEvalMatrixConfig",
    "build_submission_eval_matrix",
    "run_submission_eval_matrix",
    "write_submission_eval_matrix",
]
