"""Policy evaluation campaign over cataloged generated scenarios."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios import ScenarioCatalog, ScenarioCatalogRecord, load_scenario_catalog


@dataclass(frozen=True)
class PolicyEvaluationCampaignConfig:
    catalog_path: Path
    output_root: Path = Path("artifacts/runs")
    run_id: str = "policy-evaluation-campaign"
    selection_path: Path | None = None
    policy_modes: tuple[str, ...] = (
        "deterministic-baseline",
        "memory-guided",
        "alpamayo-open-loop",
    )
    limit: int | None = None


@dataclass(frozen=True)
class ScenarioPolicyEvaluation:
    scenario_id: str
    policy_mode: str
    status: str
    open_loop_policy_evaluation: bool
    artifacts: dict[str, str | None]
    metrics: dict[str, float | bool | str | None] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "policy_mode": self.policy_mode,
            "status": self.status,
            "open_loop_policy_evaluation": self.open_loop_policy_evaluation,
            "artifacts": self.artifacts,
            "metrics": self.metrics,
            "blockers": self.blockers,
        }


def run_policy_evaluation_campaign(
    config: PolicyEvaluationCampaignConfig,
) -> dict[str, Any]:
    run_dir = prepare_run_dir(config.output_root, config.run_id)
    records = _load_records(config)
    if config.limit is not None:
        records = records[: config.limit]
    evaluations = [
        evaluation
        for record in records
        for evaluation in evaluate_policy_on_scenario(record, list(config.policy_modes), output_dir=run_dir / "evaluations")
    ]
    summary = _summary(run_dir, config, records, evaluations)
    return write_policy_evaluation_report(summary, run_dir)


def evaluate_policy_on_scenario(
    record: ScenarioCatalogRecord,
    policy_modes: list[str],
    *,
    output_dir: Path | None = None,
) -> list[ScenarioPolicyEvaluation]:
    return [_evaluate_one(record, mode, output_dir=output_dir) for mode in policy_modes]


def write_policy_evaluation_report(
    summary: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "policy_evaluation_campaign.json"
    report_path = output_dir / "policy_evaluation_campaign.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(summary), encoding="utf-8")
    return {**summary, "json_path": str(json_path), "report_path": str(report_path)}


def _load_records(config: PolicyEvaluationCampaignConfig) -> list[ScenarioCatalogRecord]:
    if config.selection_path is not None:
        payload = json.loads(config.selection_path.read_text(encoding="utf-8"))
        return [
            ScenarioCatalogRecord.from_jsonable(dict(record))
            for record in list(payload.get("records", []))
        ]
    catalog: ScenarioCatalog = load_scenario_catalog(config.catalog_path)
    return catalog.records


def _evaluate_one(
    record: ScenarioCatalogRecord,
    mode: str,
    *,
    output_dir: Path | None,
) -> ScenarioPolicyEvaluation:
    blockers: list[str] = []
    track_metrics, track_blocker = _track_metrics(record.artifacts.tracks)
    metrics = {
        "has_video": record.quality.has_video,
        "has_model_reasoning": record.quality.has_model_reasoning,
        "road_aligned": record.quality.road_aligned,
        "scenario_quality_status": record.quality.status,
        **track_metrics,
    }
    artifacts = {
        "video": record.artifacts.video,
        "tracks": record.artifacts.tracks,
        "reasoning": record.artifacts.reasoning,
        "package": record.artifacts.package,
        "comparison": record.artifacts.comparison,
        "quality_report": record.artifacts.quality_report,
        "policy_decision": None,
    }
    if mode == "deterministic-baseline":
        if record.quality.status != "passed":
            blockers.append(f"scenario quality is not passed: {record.quality.status}")
        if track_blocker:
            blockers.append(track_blocker)
        decision_path = _write_policy_decision(record, mode, metrics, output_dir) if not blockers else None
        artifacts["policy_decision"] = decision_path
        return ScenarioPolicyEvaluation(
            scenario_id=record.scenario_id,
            policy_mode=mode,
            status="passed" if not blockers else "blocked",
            open_loop_policy_evaluation=False,
            artifacts=artifacts,
            metrics=metrics,
            blockers=blockers,
        )
    if mode == "memory-guided":
        if record.quality.status != "passed":
            blockers.append(f"scenario quality is not passed: {record.quality.status}")
        if track_blocker:
            blockers.append(track_blocker)
        decision_path = _write_policy_decision(record, mode, metrics, output_dir) if not blockers else None
        artifacts["policy_decision"] = decision_path
        return ScenarioPolicyEvaluation(
            scenario_id=record.scenario_id,
            policy_mode=mode,
            status="passed" if not blockers else "blocked",
            open_loop_policy_evaluation=True,
            artifacts=artifacts,
            metrics={**metrics, **_comparison_metrics(record.artifacts.comparison)},
            blockers=blockers,
        )
    if mode == "alpamayo-open-loop":
        if record.quality.status != "passed":
            blockers.append(f"scenario quality is not passed: {record.quality.status}")
        if not record.artifacts.package:
            blockers.append("Alpamayo package artifact missing")
        if not record.artifacts.reasoning:
            blockers.append("Alpamayo reasoning artifact missing")
        return ScenarioPolicyEvaluation(
            scenario_id=record.scenario_id,
            policy_mode=mode,
            status="passed" if not blockers else "planned",
            open_loop_policy_evaluation=True,
            artifacts=artifacts,
            metrics={**metrics, **_comparison_metrics(record.artifacts.comparison)},
            blockers=blockers,
        )
    if mode == "live-alpamayo":
        if record.quality.status != "passed":
            blockers.append(f"scenario quality is not passed: {record.quality.status}")
        if not record.artifacts.package:
            blockers.append("Alpamayo package artifact missing for live remote inference")
        return ScenarioPolicyEvaluation(
            scenario_id=record.scenario_id,
            policy_mode=mode,
            status="planned" if not blockers else "blocked",
            open_loop_policy_evaluation=True,
            artifacts=artifacts,
            metrics=metrics,
            blockers=blockers,
        )
    return ScenarioPolicyEvaluation(
        scenario_id=record.scenario_id,
        policy_mode=mode,
        status="blocked",
        open_loop_policy_evaluation=True,
        artifacts=artifacts,
        metrics=metrics,
        blockers=[f"unknown policy mode: {mode}"],
    )


def _comparison_metrics(path: str | None) -> dict[str, float | bool | str | None]:
    if not path:
        return {}
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    metrics: dict[str, float | bool | str | None] = {}
    for key in ("trajectory_final_l2_m", "reasoning_changed"):
        if key in payload:
            metrics[key] = payload[key]
    if isinstance(payload.get("latency_ms"), (int, float)):
        metrics["latency_ms"] = float(payload["latency_ms"])
    return metrics


def _write_policy_decision(
    record: ScenarioCatalogRecord,
    mode: str,
    metrics: dict[str, float | bool | str | None],
    output_dir: Path | None,
) -> str | None:
    if output_dir is None:
        return None
    scenario_dir = output_dir / _slug(record.scenario_id)
    scenario_dir.mkdir(parents=True, exist_ok=True)
    path = scenario_dir / f"{_slug(mode)}.json"
    min_distance = _optional_float(metrics.get("track_min_distance_m"))
    speed_hint = "creep" if min_distance is not None and min_distance <= 3.0 else "maintain_gap"
    if mode == "memory-guided" and record.environment_tags:
        speed_hint = "slow_and_query_memory"
    payload = {
        "scenario_id": record.scenario_id,
        "policy_mode": mode,
        "decision_kind": "local_policy_rollout",
        "open_loop_policy_evaluation": mode != "deterministic-baseline",
        "recommended_behavior": speed_hint,
        "used_tags": [*record.environment_tags, *record.ood_tags],
        "metrics": metrics,
        "claim_boundaries": [
            "local_policy_decision=true",
            "closed_loop_carla_control=false",
            "model_weights_frozen=true",
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)


def _track_metrics(path: str | None) -> tuple[dict[str, float | bool | str | None], str | None]:
    if not path:
        return {}, "tracks artifact missing for policy evaluation"
    track_path = Path(path)
    if not track_path.exists():
        return {}, f"tracks artifact does not exist: {path}"
    try:
        payload = json.loads(track_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"tracks artifact unreadable: {exc}"
    by_tick: dict[int, dict[str, tuple[float, float]]] = {}
    for item in payload if isinstance(payload, list) else []:
        if not isinstance(item, dict):
            continue
        actor_ref = str(item.get("actor_ref") or item.get("id") or "")
        tick = int(float(item.get("tick", 0) or 0))
        location = dict(item.get("location", {})) if isinstance(item.get("location"), dict) else {}
        if not actor_ref or "x" not in location or "y" not in location:
            continue
        by_tick.setdefault(tick, {})[actor_ref] = (float(location["x"]), float(location["y"]))
    distances: list[float] = []
    for actors in by_tick.values():
        ego = actors.get("ego")
        if ego is None:
            continue
        for actor_ref, location in actors.items():
            if actor_ref != "ego":
                distances.append(_distance(ego, location))
    if not by_tick:
        return {}, "tracks artifact contains no usable samples"
    metrics: dict[str, float | bool | str | None] = {
        "track_tick_count": float(len(by_tick)),
        "track_min_distance_m": round(min(distances), 4) if distances else None,
        "track_has_conflict": bool(distances and min(distances) <= 6.0),
    }
    return metrics, None


def _distance(left: tuple[float, float], right: tuple[float, float]) -> float:
    return ((left[0] - right[0]) ** 2 + (left[1] - right[1]) ** 2) ** 0.5


def _optional_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "-" for char in value.lower()).strip("-")


def _summary(
    run_dir: Path,
    config: PolicyEvaluationCampaignConfig,
    records: list[ScenarioCatalogRecord],
    evaluations: list[ScenarioPolicyEvaluation],
) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    for evaluation in evaluations:
        by_status[evaluation.status] = by_status.get(evaluation.status, 0) + 1
    decision_artifact_count = sum(
        1
        for evaluation in evaluations
        if evaluation.artifacts.get("policy_decision")
    )
    return {
        "campaign_id": run_dir.name,
        "scenario_count": len(records),
        "evaluation_count": len(evaluations),
        "passed_evaluation_count": by_status.get("passed", 0),
        "planned_evaluation_count": by_status.get("planned", 0),
        "blocked_evaluation_count": by_status.get("blocked", 0),
        "decision_artifact_count": decision_artifact_count,
        "policy_modes": list(config.policy_modes),
        "status_counts": dict(sorted(by_status.items())),
        "evaluations": [evaluation.to_jsonable() for evaluation in evaluations],
        "blockers": [
            f"{evaluation.scenario_id}/{evaluation.policy_mode}: {blocker}"
            for evaluation in evaluations
            for blocker in evaluation.blockers
        ],
        "claim_boundaries": [
            "policy_evaluation_campaign=true",
            "open_loop_policy_evaluation_may_be_true",
            "closed_loop_vla_control=false",
            "model_weights_frozen=true",
        ],
    }


def _markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Policy Evaluation Campaign",
        "",
        f"- scenarios: `{summary.get('scenario_count')}`",
        f"- evaluations by status: passed `{summary.get('passed_evaluation_count', 0)}`, planned `{summary.get('planned_evaluation_count', 0)}`, blocked `{summary.get('blocked_evaluation_count', 0)}`",
        f"- total evaluation rows: `{summary.get('evaluation_count')}`",
        f"- local decision artifacts: `{summary.get('decision_artifact_count', 0)}`",
        f"- status_counts: `{summary.get('status_counts')}`",
        "",
        "| scenario | policy | status | video | reasoning | blockers |",
        "|---|---|---|---|---|---|",
    ]
    for evaluation in list(summary.get("evaluations", [])):
        artifacts = dict(evaluation.get("artifacts", {}))
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(evaluation.get("scenario_id")),
                    _cell(evaluation.get("policy_mode")),
                    _cell(evaluation.get("status")),
                    "yes" if artifacts.get("video") else "no",
                    "yes" if artifacts.get("reasoning") else "no",
                    _cell("; ".join(str(item) for item in list(evaluation.get("blockers", [])))),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _cell(value: object) -> str:
    return "" if value is None else str(value).replace("|", "\\|")


__all__ = [
    "PolicyEvaluationCampaignConfig",
    "ScenarioPolicyEvaluation",
    "evaluate_policy_on_scenario",
    "run_policy_evaluation_campaign",
    "write_policy_evaluation_report",
]
