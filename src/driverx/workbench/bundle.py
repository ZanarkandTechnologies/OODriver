"""Build linked Scenario Workbench evidence bundles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.workbench.types import EvidenceRef, JsonDict, ScenarioRunBundle, VideoEvidence, path_to_str


@dataclass(frozen=True)
class ScenarioRunBundleInputs:
    """Artifact inputs used to link one generated scenario run."""

    studio_batch_path: Path | None = None
    video_evidence_path: Path | None = None
    alpamayo_batch_path: Path | None = None
    final_pack_path: Path | None = None
    risk_timeline_path: Path | None = None
    memory_events_path: Path | None = None
    reasoning_events_path: Path | None = None
    scenario_id: str | None = None
    behavior_id: str | None = None


def build_scenario_run_bundle(inputs: ScenarioRunBundleInputs) -> ScenarioRunBundle:
    studio = _load_json(inputs.studio_batch_path)
    video = _load_json(inputs.video_evidence_path)
    alpamayo = _load_json(inputs.alpamayo_batch_path)
    final_pack = _load_json(inputs.final_pack_path)
    risk = _load_json(inputs.risk_timeline_path)
    memory = _load_json(inputs.memory_events_path)
    reasoning = _load_json(inputs.reasoning_events_path)

    scenario_id = inputs.scenario_id or video.get("scenario_id") or _first_record_value(alpamayo, "scenario_id")
    behavior_id = inputs.behavior_id or video.get("behavior_id") or _infer_behavior_id(studio, scenario_id)
    candidate = _match_studio_candidate(studio, scenario_id, behavior_id)
    brief = _candidate_brief(studio, candidate)
    curation = _match_curation_record(studio, candidate)
    alpamayo_record = _match_alpamayo_record(alpamayo, scenario_id)
    warnings = _linkage_warnings(
        requested_scenario_id=scenario_id,
        video=video,
        candidate=candidate,
        alpamayo_record=alpamayo_record,
        risk=risk,
    )
    carla_video = _video_evidence(video)
    claim_boundaries = _dedupe_strings(
        [
            "minimal_shot_scenario_generation=true",
            "time_warped_offline_demo=true",
            "sampled_open_loop_reasoning=true",
            "real_time_vla_control=false",
            *carla_video.claim_boundaries,
            *alpamayo.get("claim_boundaries", []),
            *final_pack.get("claim_boundaries", []),
        ]
    )
    product_loop = _product_loop(
        studio=studio,
        candidate=candidate,
        carla_video=carla_video,
        risk=risk,
        memory=memory,
        reasoning=reasoning,
        alpamayo_record=alpamayo_record,
        curation=curation,
    )
    return ScenarioRunBundle(
        bundle_id=_bundle_id(scenario_id, behavior_id),
        scenario_id=scenario_id,
        behavior_id=behavior_id,
        scenario_brief=brief,
        studio_candidate=candidate,
        curation_record=curation,
        carla_video=carla_video,
        alpamayo_record=alpamayo_record,
        risk_timeline_ref=_ref("risk_timeline", inputs.risk_timeline_path, risk),
        memory_ref=_ref("memory_events", inputs.memory_events_path, memory),
        reasoning_ref=_ref("reasoning_events", inputs.reasoning_events_path, reasoning),
        final_pack_ref=_ref("final_pack", inputs.final_pack_path, final_pack),
        product_loop=product_loop,
        claim_boundaries=claim_boundaries,
        linkage_warnings=warnings,
        source_paths={
            "studio_batch_path": path_to_str(inputs.studio_batch_path),
            "video_evidence_path": path_to_str(inputs.video_evidence_path),
            "alpamayo_batch_path": path_to_str(inputs.alpamayo_batch_path),
            "final_pack_path": path_to_str(inputs.final_pack_path),
            "risk_timeline_path": path_to_str(inputs.risk_timeline_path),
            "memory_events_path": path_to_str(inputs.memory_events_path),
            "reasoning_events_path": path_to_str(inputs.reasoning_events_path),
        },
    )


def _load_json(path: Path | None) -> JsonDict:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _first_record_value(payload: JsonDict, key: str) -> Any:
    records = payload.get("records")
    if isinstance(records, list):
        for record in records:
            if isinstance(record, dict) and record.get(key):
                return record[key]
    return None


def _infer_behavior_id(studio: JsonDict, scenario_id: str | None) -> str | None:
    candidate = _match_studio_candidate(studio, scenario_id, None)
    if candidate:
        return candidate.get("behavior_template_id") or candidate.get("behavior_id")
    return None


def _match_studio_candidate(studio: JsonDict, scenario_id: str | None, behavior_id: str | None) -> JsonDict | None:
    candidates = studio.get("candidates")
    if not isinstance(candidates, list):
        return None
    if scenario_id:
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            haystack = " ".join(str(candidate.get(key, "")) for key in ("candidate_id", "parent_plan_id", "scenario_id"))
            if scenario_id in haystack:
                return candidate
    if behavior_id:
        for candidate in candidates:
            if isinstance(candidate, dict) and behavior_id in str(candidate):
                return candidate
    return candidates[0] if candidates and isinstance(candidates[0], dict) else None


def _candidate_brief(studio: JsonDict, candidate: JsonDict | None) -> JsonDict | None:
    if candidate is None:
        return None
    parent_plan_id = candidate.get("parent_plan_id") or candidate.get("plan_id")
    plans = studio.get("plans")
    if isinstance(plans, list):
        for plan in plans:
            if isinstance(plan, dict) and plan.get("plan_id") == parent_plan_id:
                brief = plan.get("brief")
                return brief if isinstance(brief, dict) else None
    brief = candidate.get("brief")
    return brief if isinstance(brief, dict) else None


def _match_curation_record(studio: JsonDict, candidate: JsonDict | None) -> JsonDict | None:
    if candidate is None:
        return None
    candidate_id = candidate.get("candidate_id")
    rows = studio.get("curation")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict) and row.get("candidate_id") == candidate_id:
                return row
    return None


def _match_alpamayo_record(alpamayo: JsonDict, scenario_id: str | None) -> JsonDict | None:
    records = alpamayo.get("records")
    if not isinstance(records, list):
        return None
    if scenario_id:
        for record in records:
            if isinstance(record, dict) and scenario_id in {record.get("scenario_id"), record.get("case_id")}:
                return record
    return records[0] if records and isinstance(records[0], dict) else None


def _video_evidence(video: JsonDict) -> VideoEvidence:
    path = video.get("local_video_path") or video.get("public_video_url") or video.get("video_path")
    return VideoEvidence(
        path=path,
        export_status=video.get("video_export_status") or video.get("export_status") or ("missing" if not path else "linked"),
        duration_s=_as_float(video.get("duration_s")),
        fps=_as_float(video.get("fps")),
        frame_count=_as_int(video.get("frame_count")),
        width=_as_int(video.get("width")),
        height=_as_int(video.get("height")),
        tracks_path=video.get("tracks_path"),
        claim_boundaries=[str(item) for item in video.get("claim_boundaries", [])],
    )


def _ref(label: str, path: Path | None, payload: JsonDict) -> EvidenceRef:
    if path is None:
        return EvidenceRef(label=label, path=None, status="not_provided", summary="No artifact path supplied.")
    if not path.exists():
        return EvidenceRef(label=label, path=str(path), status="missing", summary="Path was supplied but does not exist.")
    return EvidenceRef(label=label, path=str(path), status="linked", summary=_payload_summary(payload))


def _payload_summary(payload: JsonDict) -> str:
    if not payload:
        return "Artifact loaded but did not contain JSON fields."
    for key in ("status", "summary", "title", "batch_id", "timeline_id", "bundle_id"):
        if payload.get(key):
            return f"{key}={payload[key]}"
    return f"{len(payload)} top-level fields"


def _product_loop(
    *,
    studio: JsonDict,
    candidate: JsonDict | None,
    carla_video: VideoEvidence,
    risk: JsonDict,
    memory: JsonDict,
    reasoning: JsonDict,
    alpamayo_record: JsonDict | None,
    curation: JsonDict | None,
) -> list[JsonDict]:
    return [
        {
            "stage": "generate",
            "status": "proved" if candidate else "partial",
            "evidence": f"{studio.get('prompt_count', 0)} prompts -> {studio.get('candidate_count', 0)} candidates",
            "why_visible": "Scenario Studio turns human OOD briefs into deterministic simulator-ready cases.",
        },
        {
            "stage": "simulate",
            "status": "proved" if carla_video.path else "partial",
            "evidence": f"{carla_video.duration_s or 'unknown'}s video, export_status={carla_video.export_status}",
            "why_visible": "The generated case is rendered as CARLA evidence rather than staying a text prompt.",
        },
        {
            "stage": "detect_risk",
            "status": "proved" if risk.get("event_count") or risk.get("events") else "pending",
            "evidence": _risk_summary(risk),
            "why_visible": "Simulator ground truth creates a timeline of what the autonomy stack should notice.",
        },
        {
            "stage": "retrieve_memory",
            "status": "proved" if _has_memory(memory, alpamayo_record) else "partial",
            "evidence": _memory_summary(memory, alpamayo_record),
            "why_visible": "Minimal-shot behavior is scaffolded by retrieved prior failure principles, not fine-tuning.",
        },
        {
            "stage": "reason",
            "status": "proved" if _has_reasoning(reasoning, alpamayo_record) else "partial",
            "evidence": _reasoning_summary(reasoning, alpamayo_record),
            "why_visible": "The demo can show what the VLA/RAG layer is saying at key risk moments.",
        },
        {
            "stage": "curate",
            "status": "proved" if curation else "partial",
            "evidence": _curation_summary(curation),
            "why_visible": "Accepted failures and scenario variants feed the next dataset/replay queue.",
        },
    ]


def _linkage_warnings(
    *,
    requested_scenario_id: str | None,
    video: JsonDict,
    candidate: JsonDict | None,
    alpamayo_record: JsonDict | None,
    risk: JsonDict,
) -> list[str]:
    warnings: list[str] = []
    video_id = video.get("scenario_id")
    if requested_scenario_id and video_id and requested_scenario_id != video_id:
        warnings.append(f"Requested scenario_id {requested_scenario_id} does not match video scenario_id {video_id}.")
    if requested_scenario_id and candidate:
        candidate_text = str(candidate.get("candidate_id", "")) + " " + str(candidate.get("parent_plan_id", ""))
        if requested_scenario_id not in candidate_text:
            warnings.append("Studio candidate is a best-effort fallback; exact scenario_id match was not found.")
    if requested_scenario_id and alpamayo_record and requested_scenario_id not in {
        alpamayo_record.get("scenario_id"),
        alpamayo_record.get("case_id"),
    }:
        warnings.append("Alpamayo record is a fallback; exact scenario_id match was not found.")
    if requested_scenario_id and risk.get("scenario_id") and risk.get("scenario_id") != requested_scenario_id:
        warnings.append("Risk timeline scenario_id does not match bundle scenario_id.")
    return warnings


def _risk_summary(risk: JsonDict) -> str:
    if not risk:
        return "No risk timeline linked yet."
    event_count = risk.get("event_count") or len(risk.get("events", []))
    max_risk = risk.get("max_risk_level") or risk.get("summary", {}).get("max_risk_level")
    return f"{event_count} events, max_risk={max_risk or 'unknown'}"


def _has_memory(memory: JsonDict, alpamayo_record: JsonDict | None) -> bool:
    return bool(memory.get("events") or memory.get("memory_ids") or (alpamayo_record or {}).get("memory_ids"))


def _memory_summary(memory: JsonDict, alpamayo_record: JsonDict | None) -> str:
    ids = memory.get("memory_ids") or (alpamayo_record or {}).get("memory_ids") or []
    if ids:
        return f"{len(ids)} memory ids: {', '.join(str(item) for item in ids[:3])}"
    return "No retrieved memory ids linked yet."


def _has_reasoning(reasoning: JsonDict, alpamayo_record: JsonDict | None) -> bool:
    return bool(reasoning.get("events") or reasoning.get("reasoning_events") or alpamayo_record)


def _reasoning_summary(reasoning: JsonDict, alpamayo_record: JsonDict | None) -> str:
    if reasoning.get("events"):
        return f"{len(reasoning['events'])} reasoning events"
    if alpamayo_record:
        changed = alpamayo_record.get("reasoning_changed")
        latency = alpamayo_record.get("latency_ms")
        return f"Alpamayo record linked; reasoning_changed={changed}, latency_ms={latency}"
    return "No reasoning artifact linked yet."


def _curation_summary(curation: JsonDict | None) -> str:
    if not curation:
        return "No curation row linked."
    status = curation.get("status") or curation.get("decision") or "linked"
    score = curation.get("score") or curation.get("curation_score")
    return f"status={status}, score={score if score is not None else 'unknown'}"


def _bundle_id(scenario_id: str | None, behavior_id: str | None) -> str:
    left = scenario_id or "unknown-scenario"
    right = behavior_id or "unknown-behavior"
    return f"{left}__{right}"


def _dedupe_strings(items: list[Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item is None:
            continue
        value = str(item)
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
