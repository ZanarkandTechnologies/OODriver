"""Score OODrive scenario choreography manifests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScenarioChoreographyScoreInputs:
    choreography_manifest_path: Path
    choreography_manifest: dict[str, Any]


@dataclass(frozen=True)
class ScenarioChoreographyScoreReport:
    status: str
    scenario_choreography_score: float
    threshold: float
    components: dict[str, float]
    blockers: list[str]
    recommendations: list[str]
    claim_boundaries: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "scenario_choreography_score": self.scenario_choreography_score,
            "threshold": self.threshold,
            "components": self.components,
            "blockers": self.blockers,
            "recommendations": self.recommendations,
            "claim_boundaries": self.claim_boundaries,
        }


def load_scenario_choreography_score_inputs(path: Path) -> ScenarioChoreographyScoreInputs:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Choreography manifest must be a JSON object: {path}")
    return ScenarioChoreographyScoreInputs(choreography_manifest_path=path, choreography_manifest=dict(payload))


def score_scenario_choreography(
    inputs: ScenarioChoreographyScoreInputs,
    *,
    threshold: float = 90.0,
) -> ScenarioChoreographyScoreReport:
    manifest = inputs.choreography_manifest
    components = {
        "case_breadth": _case_breadth_score(manifest),
        "actor_object_diversity": _actor_object_score(manifest),
        "timing_and_response": _timing_response_score(manifest),
        "track_proof": _track_proof_score(manifest, inputs.choreography_manifest_path),
        "claim_honesty": _claim_score(manifest),
    }
    score = round(min(sum(components.values()), 100.0), 4)
    blockers = _blockers(manifest, score, threshold)
    return ScenarioChoreographyScoreReport(
        status="passed" if score >= threshold and not blockers else "blocked",
        scenario_choreography_score=score,
        threshold=threshold,
        components=components,
        blockers=blockers,
        recommendations=_recommendations(blockers),
        claim_boundaries=[str(item) for item in list(manifest.get("claim_boundaries", []))],
    )


def write_scenario_choreography_score(run_dir: Path, report: ScenarioChoreographyScoreReport) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_jsonable()
    json_path = run_dir / "scenario_choreography_score.json"
    report_path = run_dir / "scenario_choreography_score.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _case_breadth_score(manifest: dict[str, Any]) -> float:
    cases = [_mapping(case) for case in list(manifest.get("cases", []))]
    score = min(len(cases), 4) * 4.0
    if any(case.get("static_hazard") is True for case in cases):
        score += 2.0
    if any(case.get("moving_hazard") is True for case in cases):
        score += 2.0
    return min(score, 20.0)


def _actor_object_score(manifest: dict[str, Any]) -> float:
    actors = [_mapping(actor) for actor in list(manifest.get("actors", []))]
    objects = [_mapping(obj) for obj in list(manifest.get("objects", []))]
    behaviors = {str(actor.get("behavior_id")) for actor in actors if actor.get("behavior_id")}
    actor_kinds = {str(actor.get("kind")) for actor in actors if actor.get("kind")}
    object_kinds = {str(obj.get("kind")) for obj in objects if obj.get("kind")}
    motions = {str(obj.get("motion")) for obj in objects if obj.get("motion")}
    score = min(len(behaviors), 4) * 3.0
    score += min(len(actor_kinds), 3) * 2.0
    score += min(len(object_kinds), 4) * 2.0
    if {"static", "moving"}.issubset(motions):
        score += 4.0
    return min(score, 30.0)


def _timing_response_score(manifest: dict[str, Any]) -> float:
    triggers = [_mapping(trigger) for trigger in list(manifest.get("triggers", []))]
    responses = {str(item) for item in list(manifest.get("expected_responses", []))}
    required = {"stop", "slow", "yield", "replan"}
    score = min(len(triggers), 8) * 1.0
    score += len(required & responses) * 3.0
    if any(float(trigger.get("at_s", 0.0)) > 0.0 for trigger in triggers):
        score += 5.0
    return min(score, 25.0)


def _track_proof_score(manifest: dict[str, Any], manifest_path: Path) -> float:
    proof = _mapping(manifest.get("proof"))
    score = 0.0
    if manifest_path.exists():
        score += 2.0
    if proof.get("backend") == "fake-carla" and proof.get("status") == "passed":
        score += 3.0
    if _path_exists(proof.get("tracks_path")):
        score += 4.0
    if int(proof.get("entity_track_count") or 0) >= 50:
        score += 4.0
    spawned = {int(item) for item in list(proof.get("spawned_actor_ids", [])) if _intish(item)}
    destroyed = {int(item) for item in list(proof.get("destroyed_actor_ids", [])) if _intish(item)}
    if spawned and spawned.issubset(destroyed):
        score += 2.0
    return min(score, 15.0)


def _claim_score(manifest: dict[str, Any]) -> float:
    claims = {str(item) for item in list(manifest.get("claim_boundaries", []))}
    required = {
        "scenario_choreography=true",
        "live_carla_execution=false",
        "closed_loop_vla_control=false",
        "custom_unreal_map_import=false",
    }
    return min(len(required & claims) * 2.5, 10.0)


def _blockers(manifest: dict[str, Any], score: float, threshold: float) -> list[str]:
    blockers: list[str] = []
    if score < threshold:
        blockers.append(f"scenario_choreography_score {score:.4f} below {threshold:.4f}")
    if int(manifest.get("case_count") or 0) < 4:
        blockers.append("fewer than four choreography cases")
    if "live_carla_execution=true" in {str(item) for item in list(manifest.get("claim_boundaries", []))}:
        blockers.append("local choreography proof must not claim live CARLA execution")
    return blockers


def _recommendations(blockers: list[str]) -> list[str]:
    if not blockers:
        return ["Use this manifest as input to TASK-172 live CARLA choreography videos."]
    return ["Add cases, timed triggers, entity tracks, and honest claim boundaries before live promotion."]


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Scenario Choreography Score",
        "",
        f"- status: `{payload.get('status')}`",
        f"- score: `{payload.get('scenario_choreography_score')}`",
        f"- threshold: `{payload.get('threshold')}`",
        "",
        "## Components",
    ]
    for key, value in _mapping(payload.get("components")).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Blockers"])
    lines.extend([f"- {item}" for item in list(payload.get("blockers", []))] or ["- none"])
    return "\n".join(lines) + "\n"


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _path_exists(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and Path(value).exists()


def _intish(value: Any) -> bool:
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False


__all__ = [
    "ScenarioChoreographyScoreInputs",
    "ScenarioChoreographyScoreReport",
    "load_scenario_choreography_score_inputs",
    "score_scenario_choreography",
    "write_scenario_choreography_score",
]
