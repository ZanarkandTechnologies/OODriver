"""Commission-readiness scoring for OODrive submission evidence."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REQUIRED_HONEST_CLAIMS = [
    "closed_loop_vla_control=false",
    "real_time_vla_control=false",
    "sampled_open_loop_reasoning=true",
    "time_warped_offline_demo=true",
]

FORBIDDEN_OVERCLAIMS = [
    "closed_loop_vla_control=true",
    "real_time_vla_control=true",
]

CANONICAL_LOOP_COMMANDS = [
    "oodrive generate",
    "oodrive place",
    "oodrive reason",
    "oodrive demo-video",
    "oodrive score-demo",
]


@dataclass(frozen=True)
class SubmissionReadinessThresholds:
    pass_score: float = 90.0
    min_hero_demo_score: float = 72.0
    min_generated_candidate_count: int = 4
    min_reasoning_event_count: int = 3
    min_rag_event_count: int = 3

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "pass_score": self.pass_score,
            "min_hero_demo_score": self.min_hero_demo_score,
            "min_generated_candidate_count": self.min_generated_candidate_count,
            "min_reasoning_event_count": self.min_reasoning_event_count,
            "min_rag_event_count": self.min_rag_event_count,
        }


@dataclass(frozen=True)
class SubmissionReadinessInputs:
    product_name: str = "OODrive"
    db_path: str | None = None
    run_manifest_path: str | None = None
    evaluation_path: str | None = None
    hero_score_path: str | None = None
    overlay_report_path: str | None = None
    pack_manifest_path: str | None = None
    generated_candidate_count: int = 0
    generated_brief_count: int = 0
    command_names: list[str] = field(default_factory=list)
    claim_boundaries: list[str] = field(default_factory=list)
    artifact_paths: dict[str, str] = field(default_factory=dict)
    hero_demo_score: float | None = None
    hero_video_duration_s: float = 0.0
    visible_generated_object_count: int = 0
    risk_event_count: int = 0
    reasoning_event_count: int = 0
    rag_event_count: int = 0
    alpamayo_prediction_count: int = 0
    latency_ms: float | None = None
    live_carla_evidence: bool = False
    placement_plan_evidence: bool = False
    pack_sections: list[str] = field(default_factory=list)
    claim_matrix_rows: int = 0
    failure_case_count: int = 0
    motivation_present: bool = False
    code_quality_signals: dict[str, Any] = field(default_factory=dict)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "product_name": self.product_name,
            "db_path": self.db_path,
            "run_manifest_path": self.run_manifest_path,
            "evaluation_path": self.evaluation_path,
            "hero_score_path": self.hero_score_path,
            "overlay_report_path": self.overlay_report_path,
            "pack_manifest_path": self.pack_manifest_path,
            "generated_candidate_count": self.generated_candidate_count,
            "generated_brief_count": self.generated_brief_count,
            "command_names": list(self.command_names),
            "claim_boundaries": list(self.claim_boundaries),
            "artifact_paths": dict(self.artifact_paths),
            "hero_demo_score": self.hero_demo_score,
            "hero_video_duration_s": self.hero_video_duration_s,
            "visible_generated_object_count": self.visible_generated_object_count,
            "risk_event_count": self.risk_event_count,
            "reasoning_event_count": self.reasoning_event_count,
            "rag_event_count": self.rag_event_count,
            "alpamayo_prediction_count": self.alpamayo_prediction_count,
            "latency_ms": self.latency_ms,
            "live_carla_evidence": self.live_carla_evidence,
            "placement_plan_evidence": self.placement_plan_evidence,
            "pack_sections": list(self.pack_sections),
            "claim_matrix_rows": self.claim_matrix_rows,
            "failure_case_count": self.failure_case_count,
            "motivation_present": self.motivation_present,
            "code_quality_signals": dict(self.code_quality_signals),
        }


@dataclass(frozen=True)
class SubmissionReadinessReport:
    status: str
    submission_readiness_score: float
    threshold: float
    components: dict[str, float]
    metrics: dict[str, Any]
    blockers: list[str]
    warnings: list[str]
    recommendations: list[str]
    claim_boundaries: list[str]
    inputs: SubmissionReadinessInputs

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "submission_readiness_score": self.submission_readiness_score,
            "threshold": self.threshold,
            "components": self.components,
            "metrics": self.metrics,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "claim_boundaries": self.claim_boundaries,
            "inputs": self.inputs.to_jsonable(),
        }


def load_submission_readiness_inputs(
    *,
    db_path: Path | None = None,
    run_manifest_path: Path | None = None,
    evaluation_path: Path | None = None,
    hero_score_path: Path | None = None,
    overlay_report_path: Path | None = None,
    pack_manifest_path: Path | None = None,
    checks_report_path: Path | None = None,
    score_input_path: Path | None = None,
) -> SubmissionReadinessInputs:
    """Load commission-readiness inputs from product artifacts or a fixture."""

    if score_input_path is not None:
        payload = _load_json(score_input_path)
        return _inputs_from_fixture(payload, score_input_path)

    db_payload = _load_optional_json(db_path)
    run_payload = _load_optional_json(run_manifest_path)
    eval_payload = _load_optional_json(evaluation_path)
    hero_payload = _load_optional_json(hero_score_path)
    overlay_payload = _load_optional_json(overlay_report_path)
    pack_payload = _load_optional_json(pack_manifest_path)
    checks_payload = _load_optional_json(checks_report_path)
    artifacts = _string_dict(db_payload.get("artifacts"))
    artifacts.update(_string_dict(run_payload.get("artifacts")))
    artifacts.update(_string_dict(eval_payload.get("artifacts")))
    artifacts.update(_string_dict(hero_payload.get("artifacts")))
    artifacts.update(_string_dict(pack_payload.get("artifacts")))
    claim_boundaries = _dedupe(
        [
            *_string_list(db_payload.get("claim_boundaries")),
            *_string_list(run_payload.get("claim_boundaries")),
            *_string_list(eval_payload.get("claim_boundaries")),
            *_string_list(hero_payload.get("claim_boundaries")),
            *_string_list(overlay_payload.get("claim_boundaries")),
            *_string_list(pack_payload.get("claim_boundaries")),
        ]
    )
    hero_metrics = _mapping(hero_payload.get("metrics"))
    hero_inputs = _mapping(hero_payload.get("inputs"))
    hero_score = _optional_float(hero_payload.get("hero_demo_score"))
    command_names = _command_names(db_payload.get("command_log"))
    pack_sections = _pack_sections(pack_payload)
    return SubmissionReadinessInputs(
        product_name=str(db_payload.get("product_name", "OODrive")),
        db_path=str(db_path) if db_path else None,
        run_manifest_path=str(run_manifest_path) if run_manifest_path else None,
        evaluation_path=str(evaluation_path) if evaluation_path else None,
        hero_score_path=str(hero_score_path) if hero_score_path else None,
        overlay_report_path=str(overlay_report_path) if overlay_report_path else None,
        pack_manifest_path=str(pack_manifest_path) if pack_manifest_path else None,
        generated_candidate_count=len(_list_of_mappings(db_payload.get("candidates"))),
        generated_brief_count=len(_list_of_mappings(db_payload.get("briefs"))),
        command_names=command_names,
        claim_boundaries=claim_boundaries,
        artifact_paths=artifacts,
        hero_demo_score=hero_score,
        hero_video_duration_s=_first_float(
            overlay_payload.get("output_duration_s"),
            overlay_payload.get("duration_s"),
            hero_metrics.get("output_duration_s"),
            hero_inputs.get("output_duration_s"),
        ),
        visible_generated_object_count=int(
            _first_float(hero_metrics.get("visible_generated_object_count"), hero_inputs.get("visible_generated_object_count"))
        ),
        risk_event_count=int(_first_float(hero_metrics.get("risk_event_count"), hero_inputs.get("risk_event_count"))),
        reasoning_event_count=_reasoning_event_count(eval_payload, overlay_payload, hero_metrics, hero_inputs),
        rag_event_count=_rag_event_count(eval_payload, overlay_payload, hero_metrics, hero_inputs),
        alpamayo_prediction_count=int(
            _first_float(hero_metrics.get("alpamayo_prediction_count"), hero_inputs.get("alpamayo_prediction_count"))
        ),
        latency_ms=_first_optional_float(eval_payload.get("latency_ms"), hero_metrics.get("latency_ms"), checks_payload.get("latency_ms")),
        live_carla_evidence=_has_live_carla_evidence(db_payload, run_payload, artifacts, claim_boundaries),
        placement_plan_evidence=_has_placement_evidence(artifacts, claim_boundaries),
        pack_sections=pack_sections,
        claim_matrix_rows=_claim_matrix_rows(pack_payload),
        failure_case_count=_failure_case_count(pack_payload, eval_payload),
        motivation_present=_motivation_present(pack_payload),
        code_quality_signals=_code_quality_signals(checks_payload),
    )


def score_submission_readiness(
    inputs: SubmissionReadinessInputs,
    thresholds: SubmissionReadinessThresholds | None = None,
) -> SubmissionReadinessReport:
    limits = thresholds or SubmissionReadinessThresholds()
    components = _score_components(inputs, limits)
    score = round(_clamp(sum(components.values()), 0.0, 100.0), 4)
    blockers = _blockers(inputs, limits, score)
    warnings = _warnings(inputs)
    recommendations = _recommendations(inputs, blockers)
    status = "passed" if not blockers and score >= limits.pass_score else "blocked"
    metrics = inputs.to_jsonable()
    metrics["score_pass_threshold"] = limits.pass_score
    return SubmissionReadinessReport(
        status=status,
        submission_readiness_score=score,
        threshold=limits.pass_score,
        components=components,
        metrics=metrics,
        blockers=blockers,
        warnings=warnings,
        recommendations=recommendations,
        claim_boundaries=_dedupe([*inputs.claim_boundaries, *REQUIRED_HONEST_CLAIMS]),
        inputs=inputs,
    )


def write_submission_readiness_score(run_dir: Path, report: SubmissionReadinessReport) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_jsonable()
    json_path = run_dir / "submission_readiness_score.json"
    report_path = run_dir / "submission_readiness_score.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_score_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _score_components(inputs: SubmissionReadinessInputs, limits: SubmissionReadinessThresholds) -> dict[str, float]:
    hero_score = inputs.hero_demo_score or 0.0
    canonical_loop_seen = _canonical_loop_count(inputs.command_names)
    code_quality = inputs.code_quality_signals
    components = {
        "challenge_adherence": (
            3.0 * (inputs.product_name == "OODrive")
            + 5.0 * _required_claim_ratio(inputs.claim_boundaries)
            + 2.0 * _bool_score(inputs.motivation_present)
            + 3.0 * _bool_score(inputs.failure_case_count > 0)
            + 2.0 * _bool_score(not _has_forbidden_overclaim(inputs.claim_boundaries))
        ),
        "minimal_shot_simulation_environment": (
            4.0 * _clamp(inputs.generated_candidate_count / limits.min_generated_candidate_count, 0.0, 1.0)
            + 3.0 * _bool_score(inputs.generated_brief_count > 0)
            + 4.0 * _bool_score(inputs.placement_plan_evidence)
            + 4.0 * _bool_score(inputs.live_carla_evidence)
            + 3.0 * _clamp(inputs.visible_generated_object_count / 4.0, 0.0, 1.0)
        ),
        "navigation_and_risk_evidence": (
            4.0 * _bool_score(bool(inputs.run_manifest_path))
            + 4.0 * _clamp(hero_score / limits.min_hero_demo_score, 0.0, 1.0)
            + 3.0 * _clamp(inputs.risk_event_count / 5.0, 0.0, 1.0)
            + 3.0 * _clamp(inputs.hero_video_duration_s / 60.0, 0.0, 1.0)
        ),
        "reasoning_memory_latency": (
            3.0 * _bool_score("sampled_open_loop_reasoning=true" in inputs.claim_boundaries)
            + 3.0 * _clamp(inputs.alpamayo_prediction_count / 1.0, 0.0, 1.0)
            + 4.0 * _clamp(inputs.reasoning_event_count / limits.min_reasoning_event_count, 0.0, 1.0)
            + 3.0 * _clamp(inputs.rag_event_count / limits.min_rag_event_count, 0.0, 1.0)
            + 3.0 * _bool_score(inputs.latency_ms is not None)
        ),
        "judge_comprehension_pack": (
            4.0 * _bool_score(bool(inputs.pack_manifest_path))
            + 4.0 * _clamp(len(inputs.pack_sections) / 6.0, 0.0, 1.0)
            + 3.0 * _clamp(inputs.claim_matrix_rows / 6.0, 0.0, 1.0)
            + 3.0 * _bool_score(inputs.motivation_present)
            + 2.0 * _bool_score(inputs.failure_case_count > 0)
        ),
        "operator_reproducibility": (
            5.0 * _clamp(canonical_loop_seen / len(CANONICAL_LOOP_COMMANDS), 0.0, 1.0)
            + 3.0 * _artifact_presence_ratio(inputs.artifact_paths)
            + 2.0 * _bool_score(bool(inputs.pack_manifest_path))
            + 2.0 * _bool_score(inputs.latency_ms is not None)
        ),
        "code_quality": (
            3.0 * _bool_score(bool(code_quality.get("checks_passed", False)))
            + 2.0 * _bool_score(bool(code_quality.get("pre_push_passed", False)))
            + 2.0 * _bool_score(int(_first_float(code_quality.get("large_file_count"), 9.0)) <= 6)
            + 2.0 * _bool_score(bool(code_quality.get("review_passed", False)))
        ),
    }
    return {key: round(value, 4) for key, value in components.items()}


def _blockers(inputs: SubmissionReadinessInputs, limits: SubmissionReadinessThresholds, score: float) -> list[str]:
    blockers: list[str] = []
    if score < limits.pass_score:
        blockers.append(f"submission_readiness_score {score:.2f} below {limits.pass_score:.2f}")
    if _has_forbidden_overclaim(inputs.claim_boundaries):
        blockers.append("forbidden closed-loop or real-time VLA claim present without proof")
    missing_claims = [claim for claim in REQUIRED_HONEST_CLAIMS if claim not in inputs.claim_boundaries]
    if missing_claims:
        blockers.append(f"missing honest claim boundaries: {', '.join(missing_claims)}")
    if (inputs.hero_demo_score or 0.0) < limits.min_hero_demo_score:
        blockers.append(f"hero_demo_score {(inputs.hero_demo_score or 0.0):.2f} below {limits.min_hero_demo_score:.2f}")
    if inputs.generated_candidate_count < limits.min_generated_candidate_count:
        blockers.append(
            f"generated_candidate_count {inputs.generated_candidate_count} below {limits.min_generated_candidate_count}"
        )
    if not inputs.live_carla_evidence:
        blockers.append("live CARLA evidence is missing")
    if not inputs.pack_manifest_path:
        blockers.append("judge-facing submission pack manifest is missing")
    if inputs.claim_matrix_rows < 6:
        blockers.append(f"claim_matrix_rows {inputs.claim_matrix_rows} below 6")
    if inputs.failure_case_count < 1:
        blockers.append("failure case evidence is missing")
    if not inputs.motivation_present:
        blockers.append("motivation write-up evidence is missing")
    return blockers


def _warnings(inputs: SubmissionReadinessInputs) -> list[str]:
    warnings: list[str] = []
    if inputs.hero_video_duration_s and inputs.hero_video_duration_s < 60.0:
        warnings.append("hero video is under one minute; rely on a slide/HTML pack or lengthen final presentation.")
    if inputs.latency_ms is None:
        warnings.append("latency_ms missing; commission gives extra credit for realistic compute and latency constraints.")
    if "closed_loop_vla_control=false" in inputs.claim_boundaries:
        warnings.append("open-loop Alpamayo reasoning is honest but weaker than true closed-loop navigation proof.")
    return warnings


def _recommendations(inputs: SubmissionReadinessInputs, blockers: list[str]) -> list[str]:
    recommendations: list[str] = []
    blocker_text = " | ".join(blockers)
    if "submission pack" in blocker_text or not inputs.pack_manifest_path:
        recommendations.append("Build the TASK-133 judge pack with motivation, claim matrix, commands, and a failure case.")
    if "failure case" in blocker_text:
        recommendations.append("Include at least one understood failure mode and what it taught the final system.")
    if inputs.latency_ms is None:
        recommendations.append("Attach Alpamayo latency/VRAM evidence, even if it proves open-loop inference is slow.")
    if not inputs.live_carla_evidence:
        recommendations.append("Link the TASK-128 live CARLA run manifest or record a precise remote-intake blocker.")
    if inputs.generated_candidate_count < 4:
        recommendations.append("Show randomized scenario generation with at least four generated candidates.")
    return _dedupe(recommendations)


def _inputs_from_fixture(payload: dict[str, Any], score_input_path: Path) -> SubmissionReadinessInputs:
    return SubmissionReadinessInputs(
        product_name=str(payload.get("product_name", "OODrive")),
        db_path=_optional_str(payload.get("db_path")),
        run_manifest_path=_optional_str(payload.get("run_manifest_path")),
        evaluation_path=_optional_str(payload.get("evaluation_path")),
        hero_score_path=_optional_str(payload.get("hero_score_path")),
        overlay_report_path=_optional_str(payload.get("overlay_report_path")),
        pack_manifest_path=_optional_str(payload.get("pack_manifest_path")),
        generated_candidate_count=int(_first_float(payload.get("generated_candidate_count"))),
        generated_brief_count=int(_first_float(payload.get("generated_brief_count"))),
        command_names=_string_list(payload.get("command_names")),
        claim_boundaries=_string_list(payload.get("claim_boundaries")),
        artifact_paths=_string_dict(payload.get("artifact_paths")),
        hero_demo_score=_optional_float(payload.get("hero_demo_score")),
        hero_video_duration_s=_first_float(payload.get("hero_video_duration_s")),
        visible_generated_object_count=int(_first_float(payload.get("visible_generated_object_count"))),
        risk_event_count=int(_first_float(payload.get("risk_event_count"))),
        reasoning_event_count=int(_first_float(payload.get("reasoning_event_count"))),
        rag_event_count=int(_first_float(payload.get("rag_event_count"))),
        alpamayo_prediction_count=int(_first_float(payload.get("alpamayo_prediction_count"))),
        latency_ms=_optional_float(payload.get("latency_ms")),
        live_carla_evidence=bool(payload.get("live_carla_evidence")),
        placement_plan_evidence=bool(payload.get("placement_plan_evidence")),
        pack_sections=_string_list(payload.get("pack_sections")),
        claim_matrix_rows=int(_first_float(payload.get("claim_matrix_rows"))),
        failure_case_count=int(_first_float(payload.get("failure_case_count"))),
        motivation_present=bool(payload.get("motivation_present")),
        code_quality_signals={
            **_mapping(payload.get("code_quality_signals")),
            "score_input_path": str(score_input_path),
        },
    )


def _score_markdown(payload: dict[str, Any]) -> str:
    metrics = dict(payload.get("metrics", {}))
    lines = [
        "# Submission Readiness Score",
        "",
        f"- Status: `{payload['status']}`",
        f"- Score: `{payload['submission_readiness_score']}` / 100",
        f"- Threshold: `{payload['threshold']}`",
        f"- Product: `{metrics.get('product_name')}`",
        "",
        "## Components",
        "",
        "| component | points |",
        "| --- | --- |",
    ]
    for key, value in dict(payload.get("components", {})).items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(["", "## Challenge Metrics", "", "| metric | value |", "| --- | --- |"])
    for key in (
        "generated_candidate_count",
        "hero_demo_score",
        "hero_video_duration_s",
        "reasoning_event_count",
        "rag_event_count",
        "latency_ms",
        "live_carla_evidence",
        "claim_matrix_rows",
        "failure_case_count",
        "motivation_present",
    ):
        lines.append(f"| `{key}` | `{metrics.get(key)}` |")
    for title, values in (
        ("Blockers", payload.get("blockers", [])),
        ("Warnings", payload.get("warnings", [])),
        ("Recommendations", payload.get("recommendations", [])),
    ):
        if values:
            lines.extend(["", f"## {title}", ""])
            lines.extend([f"- {item}" for item in values])
    lines.extend(["", "## Claim Boundaries", ""])
    for claim in payload.get("claim_boundaries", []):
        lines.append(f"- `{claim}`")
    return "\n".join(lines) + "\n"


def _reasoning_event_count(
    eval_payload: dict[str, Any],
    overlay_payload: dict[str, Any],
    hero_metrics: dict[str, Any],
    hero_inputs: dict[str, Any],
) -> int:
    explicit = int(_first_float(hero_metrics.get("reasoning_event_count"), hero_inputs.get("reasoning_event_count")))
    if explicit:
        return explicit
    events = overlay_payload.get("events")
    if isinstance(events, list):
        return sum(1 for item in events if isinstance(item, dict) and item.get("vla_reasoning"))
    return 1 if eval_payload.get("cot_summary") else 0


def _rag_event_count(
    eval_payload: dict[str, Any],
    overlay_payload: dict[str, Any],
    hero_metrics: dict[str, Any],
    hero_inputs: dict[str, Any],
) -> int:
    explicit = int(_first_float(hero_metrics.get("rag_event_count"), hero_inputs.get("rag_event_count")))
    if explicit:
        return explicit
    events = overlay_payload.get("events")
    if isinstance(events, list):
        return sum(1 for item in events if isinstance(item, dict) and item.get("memory_id"))
    memory_ids = eval_payload.get("memory_ids")
    return len(memory_ids) if isinstance(memory_ids, list) else 0


def _has_live_carla_evidence(
    db_payload: dict[str, Any],
    run_payload: dict[str, Any],
    artifacts: dict[str, str],
    claim_boundaries: list[str],
) -> bool:
    if "objects_placed_in_carla=true" in claim_boundaries or "scripted_carla_ood_demo=true" in claim_boundaries:
        return True
    if run_payload.get("runtime") == "carla-scripted-ood-demo":
        return True
    if artifacts.get("carla_ood_demo_json") or artifacts.get("carla_ood_demo_report"):
        return True
    return any(
        isinstance(run, dict) and run.get("runtime") == "carla-scripted-ood-demo"
        for run in _list_of_mappings(db_payload.get("runs"))
    )


def _has_placement_evidence(artifacts: dict[str, str], claim_boundaries: list[str]) -> bool:
    return bool(
        artifacts.get("placement_plan_path")
        or artifacts.get("carla_plan_path")
        or "carla_placement_plan=true" in claim_boundaries
        or "oodrive_generate_to_carla_placement_plan=true" in claim_boundaries
    )


def _pack_sections(pack_payload: dict[str, Any]) -> list[str]:
    sections = pack_payload.get("sections")
    if isinstance(sections, list):
        return [str(item.get("id") or item.get("title") or item) for item in sections]
    return _string_list(pack_payload.get("pack_sections"))


def _claim_matrix_rows(pack_payload: dict[str, Any]) -> int:
    matrix = pack_payload.get("claim_matrix")
    if isinstance(matrix, list):
        return len(matrix)
    return int(_first_float(pack_payload.get("claim_matrix_rows")))


def _failure_case_count(pack_payload: dict[str, Any], eval_payload: dict[str, Any]) -> int:
    cases = pack_payload.get("failure_cases")
    if isinstance(cases, list):
        return len(cases)
    if eval_payload.get("failure_case") or eval_payload.get("failure_summary"):
        return 1
    return int(_first_float(pack_payload.get("failure_case_count")))


def _motivation_present(pack_payload: dict[str, Any]) -> bool:
    return bool(pack_payload.get("motivation") or pack_payload.get("motivation_present"))


def _code_quality_signals(checks_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "checks_passed": bool(checks_payload.get("checks_passed")),
        "pre_push_passed": bool(checks_payload.get("pre_push_passed")),
        "review_passed": bool(checks_payload.get("review_passed")),
        "large_file_count": int(_first_float(checks_payload.get("large_file_count"), 9.0)),
    }


def _command_names(command_log: Any) -> list[str]:
    commands = []
    for entry in _list_of_mappings(command_log):
        command = str(entry.get("command", "")).strip()
        if command:
            commands.append(command)
    return commands


def _canonical_loop_count(command_names: list[str]) -> int:
    return sum(1 for command in CANONICAL_LOOP_COMMANDS if any(item.startswith(command) for item in command_names))


def _required_claim_ratio(claim_boundaries: list[str]) -> float:
    return _clamp(sum(1 for claim in REQUIRED_HONEST_CLAIMS if claim in claim_boundaries) / len(REQUIRED_HONEST_CLAIMS), 0.0, 1.0)


def _artifact_presence_ratio(artifact_paths: dict[str, str]) -> float:
    if not artifact_paths:
        return 0.0
    keys = (
        "placement_plan_path",
        "carla_ood_demo_json",
        "evaluation_path",
        "hero_demo_video_path",
        "hero_demo_score_json_path",
        "submission_pack_manifest_path",
    )
    return _clamp(sum(1 for key in keys if artifact_paths.get(key)) / len(keys), 0.0, 1.0)


def _has_forbidden_overclaim(claim_boundaries: list[str]) -> bool:
    return any(claim in claim_boundaries for claim in FORBIDDEN_OVERCLAIMS)


def _bool_score(value: bool) -> float:
    return 1.0 if value else 0.0


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


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in value] if isinstance(value, list) and all(isinstance(item, dict) for item in value) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _string_dict(value: Any) -> dict[str, str]:
    return {str(key): str(item) for key, item in dict(value).items()} if isinstance(value, dict) else {}


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _first_float(*values: object) -> float:
    return _first_optional_float(*values) or 0.0


def _first_optional_float(*values: object) -> float | None:
    for value in values:
        parsed = _optional_float(value)
        if parsed is not None:
            return parsed
    return None


def _optional_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    except (TypeError, ValueError):
        return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out
