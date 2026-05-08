"""Score CARLA capability matrices and generated suite manifests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CarlaSuiteScoreInputs:
    suite_manifest_path: Path
    suite_manifest: dict[str, Any]
    capability_matrix_path: Path | None = None
    capability_matrix: dict[str, Any] | None = None


@dataclass(frozen=True)
class CarlaSuiteScoreReport:
    status: str
    carla_capability_suite_score: float
    threshold: float
    components: dict[str, float]
    blockers: list[str]
    recommendations: list[str]
    claim_boundaries: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "carla_capability_suite_score": self.carla_capability_suite_score,
            "threshold": self.threshold,
            "components": self.components,
            "blockers": self.blockers,
            "recommendations": self.recommendations,
            "claim_boundaries": self.claim_boundaries,
        }


def load_carla_suite_score_inputs(
    suite_manifest_path: Path,
    *,
    capability_matrix_path: Path | None = None,
) -> CarlaSuiteScoreInputs:
    """Load a CARLA suite manifest plus optional explicit capability matrix."""

    suite = _load_mapping(suite_manifest_path)
    matrix_path = capability_matrix_path
    if matrix_path is None:
        raw_path = suite.get("capability_matrix_path")
        if isinstance(raw_path, str) and raw_path:
            matrix_path = Path(raw_path)
    matrix = _load_mapping(matrix_path) if matrix_path is not None and matrix_path.exists() else None
    return CarlaSuiteScoreInputs(
        suite_manifest_path=suite_manifest_path,
        suite_manifest=suite,
        capability_matrix_path=matrix_path,
        capability_matrix=matrix,
    )


def score_carla_suite(
    inputs: CarlaSuiteScoreInputs,
    *,
    threshold: float = 90.0,
) -> CarlaSuiteScoreReport:
    """Score whether the generated suite is a real CARLA capability artifact."""

    manifest = inputs.suite_manifest
    matrix = inputs.capability_matrix or _mapping(manifest.get("capability_matrix"))
    cases = [_mapping(item) for item in list(manifest.get("cases", []))]
    components = {
        "capability_matrix": _capability_matrix_score(matrix),
        "suite_count_and_artifacts": _suite_count_artifact_score(manifest, cases, inputs.suite_manifest_path),
        "diversity": _diversity_score(cases),
        "case_richness": _case_richness_score(cases),
        "claim_honesty": _claim_honesty_score(manifest, matrix),
    }
    score = round(min(sum(components.values()), 100.0), 4)
    blockers = _blockers(manifest, matrix, cases, score, threshold)
    return CarlaSuiteScoreReport(
        status="passed" if score >= threshold and not blockers else "blocked",
        carla_capability_suite_score=score,
        threshold=threshold,
        components=components,
        blockers=blockers,
        recommendations=_recommendations(blockers),
        claim_boundaries=_dedupe(
            [
                *[str(item) for item in list(manifest.get("claim_boundaries", []))],
                *([str(item) for item in list(matrix.get("claim_boundaries", []))] if matrix else []),
            ]
        ),
    )


def write_carla_suite_score(run_dir: Path, report: CarlaSuiteScoreReport) -> dict[str, Any]:
    """Write score JSON and Markdown artifacts."""

    run_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_jsonable()
    json_path = run_dir / "carla_capability_suite_score.json"
    report_path = run_dir / "carla_capability_suite_score.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _capability_matrix_score(matrix: dict[str, Any]) -> float:
    score = 0.0
    available_maps = {str(item) for item in list(matrix.get("available_maps", []))}
    weather = {str(item) for item in list(matrix.get("weather_presets", []))}
    camera_modes = {str(item) for item in list(matrix.get("camera_anchor_modes", []))}
    blueprint_families = {str(item) for item in list(matrix.get("blueprint_families", []))}
    can = {str(item) for item in list(matrix.get("can", []))}
    cannot = {str(item) for item in list(matrix.get("cannot", []))}
    labels = _mapping(matrix.get("claim_labels"))
    if len(available_maps) >= 12:
        score += 5.0
    elif len(available_maps) >= 6:
        score += 4.0
    if len(weather) >= 5:
        score += 4.0
    if len(camera_modes) >= 3:
        score += 3.0
    if len(blueprint_families) >= 4:
        score += 4.0
    if can and cannot:
        score += 2.0
    if labels.get("carla_existing_map_composition") is True and labels.get("custom_unreal_map_import") is False:
        score += 2.0
    return min(score, 20.0)


def _suite_count_artifact_score(manifest: dict[str, Any], cases: list[dict[str, Any]], suite_path: Path) -> float:
    score = 0.0
    if len(cases) == 10:
        score += 8.0
    elif len(cases) >= 8:
        score += 5.0
    if suite_path.exists():
        score += 3.0
    if _path_exists(manifest.get("capability_matrix_path")):
        score += 4.0
    if _path_exists(manifest.get("report_path")):
        score += 3.0
    if _path_exists(manifest.get("storyboard_path")):
        score += 2.0
    existing_runtime_paths = sum(
        1 for case in cases if _path_exists(case.get("runtime_manifest_path")) and _path_exists(case.get("carla_config_path"))
    )
    score += min(existing_runtime_paths, 10) * 0.5
    return min(round(score, 4), 25.0)


def _diversity_score(cases: list[dict[str, Any]]) -> float:
    maps = {str(case.get("map_name")) for case in cases if case.get("map_name")}
    weather = {str(case.get("weather_preset")) for case in cases if case.get("weather_preset")}
    behaviors = {
        str(item)
        for case in cases
        for item in list(case.get("behavior_ids", []))
        if item
    }
    objects = {
        str(item)
        for case in cases
        for item in list(case.get("object_kinds", []))
        if item
    }
    pressures = {str(case.get("expected_policy_pressure")) for case in cases if case.get("expected_policy_pressure")}
    score = 0.0
    score += min(len(maps), 4) * 3.0
    score += min(len(weather), 5) * 2.0
    score += min(len(behaviors), 4) * 2.0
    score += min(len(objects), 4) * 1.5
    score += min(len(pressures), 4) * 1.0
    return min(round(score, 4), 30.0)


def _case_richness_score(cases: list[dict[str, Any]]) -> float:
    if not cases:
        return 0.0
    rich = 0
    static_cases = 0
    moving_cases = 0
    for case in cases:
        hazards = [_mapping(item) for item in list(case.get("hazards", []))]
        if case.get("prompt") and case.get("camera_pose") and case.get("road_anchor_spawn_index") is not None:
            if case.get("behavior_ids") and case.get("object_kinds") and hazards:
                rich += 1
        kinds = {str(hazard.get("kind")) for hazard in hazards}
        if "static" in kinds:
            static_cases += 1
        if "moving" in kinds:
            moving_cases += 1
    score = min(rich, 10) * 1.0
    if static_cases >= 5:
        score += 2.5
    if moving_cases >= 5:
        score += 2.5
    return min(round(score, 4), 15.0)


def _claim_honesty_score(manifest: dict[str, Any], matrix: dict[str, Any]) -> float:
    claims = {str(item) for item in list(manifest.get("claim_boundaries", []))}
    claims.update(str(item) for item in list(matrix.get("claim_boundaries", [])))
    required = {
        "carla_existing_map_composition=true",
        "custom_unreal_map_import=false",
        "arbitrary_mesh_spawn=false",
        "true_flood_physics=false",
    }
    score = len(required & claims) * 1.5
    if manifest.get("gallery_ready") is False:
        score += 2.0
    if str(manifest.get("gallery_promotion_blocker", "")).startswith("TASK-167"):
        score += 2.0
    return min(score, 10.0)


def _blockers(
    manifest: dict[str, Any],
    matrix: dict[str, Any],
    cases: list[dict[str, Any]],
    score: float,
    threshold: float,
) -> list[str]:
    blockers: list[str] = []
    if score < threshold:
        blockers.append(f"carla_capability_suite_score {score:.4f} below {threshold:.4f}")
    if not matrix:
        blockers.append("missing capability matrix")
    if len(cases) != 10:
        blockers.append("suite must contain exactly 10 cases")
    if manifest.get("gallery_ready") is not False:
        blockers.append("TASK-166 suite must remain gallery_ready=false until TASK-167 live image scoring passes")
    for blocker in list(manifest.get("blockers", [])):
        blockers.append(str(blocker))
    return _dedupe(blockers)


def _recommendations(blockers: list[str]) -> list[str]:
    if not blockers:
        return [
            "Use TASK-167 to capture live CARLA screenshots and compute image diversity before gallery promotion."
        ]
    recommendations = []
    joined = " ".join(blockers)
    if "capability matrix" in joined:
        recommendations.append("Generate the suite with `oodrive carla-suite --probe-capabilities`.")
    if "exactly 10" in joined:
        recommendations.append("Use the default suite count or add enough capability-grounded cases.")
    if "gallery_ready" in joined:
        recommendations.append("Keep TASK-166 gallery_ready=false until live CARLA image scoring exists.")
    if not recommendations:
        recommendations.append("Inspect the suite manifest and fill missing map/weather/behavior/object diversity.")
    return recommendations


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# CARLA Capability Suite Score",
        "",
        f"- status: `{payload.get('status')}`",
        f"- score: `{payload.get('carla_capability_suite_score')}`",
        f"- threshold: `{payload.get('threshold')}`",
        "",
        "## Components",
    ]
    for key, value in _mapping(payload.get("components")).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Blockers"])
    blockers = list(payload.get("blockers", []))
    lines.extend([f"- {item}" for item in blockers] or ["- none"])
    lines.extend(["", "## Claim Boundaries"])
    lines.extend([f"- `{item}`" for item in list(payload.get("claim_boundaries", []))])
    return "\n".join(lines) + "\n"


def _load_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return dict(payload)


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _path_exists(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and Path(value).exists()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


__all__ = [
    "CarlaSuiteScoreInputs",
    "CarlaSuiteScoreReport",
    "load_carla_suite_score_inputs",
    "score_carla_suite",
    "write_carla_suite_score",
]
