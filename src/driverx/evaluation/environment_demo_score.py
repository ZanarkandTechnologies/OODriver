"""Environment Studio demo readiness scoring."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REQUIRED_CLAIM_BOUNDARIES = [
    "closed_loop_vla_control=false",
    "real_time_vla_control=false",
    "sampled_open_loop_reasoning=true",
    "time_warped_offline_demo=true",
]


@dataclass(frozen=True)
class EnvironmentDemoThresholds:
    pass_score: float = 90.0
    min_family_count: int = 6
    min_asset_request_count: int = 10
    min_recipe_count: int = 6

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "pass_score": self.pass_score,
            "min_family_count": self.min_family_count,
            "min_asset_request_count": self.min_asset_request_count,
            "min_recipe_count": self.min_recipe_count,
        }


@dataclass(frozen=True)
class EnvironmentDemoReadinessInputs:
    environment_summary_path: str | None = None
    demo_manifest_path: str | None = None
    family_count: int = 0
    recipe_count: int = 0
    asset_request_count: int = 0
    weather_ready_count: int = 0
    traffic_ready_count: int = 0
    road_local_asset_count: int = 0
    expected_policy_pressure_count: int = 0
    command_names: list[str] = field(default_factory=list)
    html_path: str | None = None
    commands_path: str | None = None
    storyboard_path: str | None = None
    hero_video_status: str = "missing"
    submission_pack_status: str = "missing"
    card_count: int = 0
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "environment_summary_path": self.environment_summary_path,
            "demo_manifest_path": self.demo_manifest_path,
            "family_count": self.family_count,
            "recipe_count": self.recipe_count,
            "asset_request_count": self.asset_request_count,
            "weather_ready_count": self.weather_ready_count,
            "traffic_ready_count": self.traffic_ready_count,
            "road_local_asset_count": self.road_local_asset_count,
            "expected_policy_pressure_count": self.expected_policy_pressure_count,
            "command_names": list(self.command_names),
            "html_path": self.html_path,
            "commands_path": self.commands_path,
            "storyboard_path": self.storyboard_path,
            "hero_video_status": self.hero_video_status,
            "submission_pack_status": self.submission_pack_status,
            "card_count": self.card_count,
            "claim_boundaries": list(self.claim_boundaries),
        }


@dataclass(frozen=True)
class EnvironmentDemoReadinessReport:
    status: str
    environment_demo_readiness_score: float
    threshold: float
    components: dict[str, float]
    metrics: dict[str, Any]
    blockers: list[str]
    recommendations: list[str]
    claim_boundaries: list[str]
    inputs: EnvironmentDemoReadinessInputs

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "environment_demo_readiness_score": self.environment_demo_readiness_score,
            "threshold": self.threshold,
            "components": self.components,
            "metrics": self.metrics,
            "blockers": self.blockers,
            "recommendations": self.recommendations,
            "claim_boundaries": self.claim_boundaries,
            "inputs": self.inputs.to_jsonable(),
        }


def load_environment_demo_readiness_inputs(
    *,
    environment_summary_path: Path | None = None,
    demo_manifest_path: Path | None = None,
    score_input_path: Path | None = None,
) -> EnvironmentDemoReadinessInputs:
    """Load environment demo inputs from real artifacts or a fixture."""

    if score_input_path is not None:
        return _inputs_from_fixture(_load_json(score_input_path), score_input_path)
    summary = _load_optional_json(environment_summary_path)
    manifest = _load_optional_json(demo_manifest_path)
    recipes = _list_of_mappings(summary.get("recipes"))
    assets = _list_of_mappings(summary.get("asset_requests"))
    artifacts = _mapping(manifest.get("artifacts"))
    return EnvironmentDemoReadinessInputs(
        environment_summary_path=str(environment_summary_path) if environment_summary_path else None,
        demo_manifest_path=str(demo_manifest_path) if demo_manifest_path else None,
        family_count=len({str(item) for item in list(summary.get("families", []))}),
        recipe_count=len(recipes),
        asset_request_count=len(assets),
        weather_ready_count=sum(1 for recipe in recipes if bool(_mapping(recipe.get("weather")))),
        traffic_ready_count=sum(1 for recipe in recipes if bool(_mapping(recipe.get("traffic")))),
        road_local_asset_count=sum(
            1
            for asset in assets
            if _mapping(asset.get("intended_placement")).get("coordinate_frame") == "road_local"
        ),
        expected_policy_pressure_count=sum(1 for recipe in recipes if str(recipe.get("expected_policy_pressure", "")).strip()),
        command_names=[str(item) for item in list(manifest.get("command_transcript", []))],
        html_path=_optional_str(artifacts.get("environment_demo_index_path")),
        commands_path=_optional_str(artifacts.get("environment_demo_commands_path")),
        storyboard_path=_optional_str(artifacts.get("environment_demo_storyboard_path")),
        hero_video_status=str(_mapping(manifest.get("hero_video")).get("status", "missing")),
        submission_pack_status=str(_mapping(manifest.get("submission_pack")).get("status", "missing")),
        card_count=len(_list_of_mappings(manifest.get("cards"))),
        claim_boundaries=[str(item) for item in list(manifest.get("claim_boundaries", []))],
    )


def score_environment_demo_readiness(
    inputs: EnvironmentDemoReadinessInputs,
    thresholds: EnvironmentDemoThresholds | None = None,
) -> EnvironmentDemoReadinessReport:
    limits = thresholds or EnvironmentDemoThresholds()
    components = _score_components(inputs, limits)
    score = round(_clamp(sum(components.values()), 0.0, 100.0), 4)
    blockers = _blockers(inputs, limits, score)
    status = "passed" if not blockers and score >= limits.pass_score else "blocked"
    return EnvironmentDemoReadinessReport(
        status=status,
        environment_demo_readiness_score=score,
        threshold=limits.pass_score,
        components=components,
        metrics=inputs.to_jsonable(),
        blockers=blockers,
        recommendations=_recommendations(inputs, blockers),
        claim_boundaries=_dedupe([*inputs.claim_boundaries, *REQUIRED_CLAIM_BOUNDARIES]),
        inputs=inputs,
    )


def write_environment_demo_score(run_dir: Path, report: EnvironmentDemoReadinessReport) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_jsonable()
    json_path = run_dir / "environment_demo_score.json"
    report_path = run_dir / "environment_demo_score.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_score_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _score_components(inputs: EnvironmentDemoReadinessInputs, limits: EnvironmentDemoThresholds) -> dict[str, float]:
    command_text = "\n".join(inputs.command_names)
    files = {
        "html": _path_exists(inputs.html_path),
        "commands": _path_exists(inputs.commands_path),
        "storyboard": _path_exists(inputs.storyboard_path),
    }
    components = {
        "generation_substance": (
            8.0 * _clamp(inputs.family_count / limits.min_family_count, 0.0, 1.0)
            + 4.0 * _clamp(inputs.recipe_count / limits.min_recipe_count, 0.0, 1.0)
            + 5.0 * _clamp(inputs.asset_request_count / limits.min_asset_request_count, 0.0, 1.0)
            + 4.0 * _clamp(inputs.weather_ready_count / max(inputs.recipe_count, 1), 0.0, 1.0)
            + 3.0 * _clamp(inputs.traffic_ready_count / max(inputs.recipe_count, 1), 0.0, 1.0)
            + 4.0 * _clamp(inputs.road_local_asset_count / max(inputs.asset_request_count, 1), 0.0, 1.0)
            + 2.0 * _clamp(inputs.expected_policy_pressure_count / max(inputs.recipe_count, 1), 0.0, 1.0)
        ),
        "product_surface": (
            5.0 * ("oodrive generate-envs" in command_text)
            + 5.0 * ("oodrive export-env-demo" in command_text)
            + 5.0 * ("oodrive score-env-demo" in command_text)
            + 5.0 * _bool_score(bool(inputs.demo_manifest_path))
        ),
        "judge_app_legibility": (
            6.0 * _bool_score(files["html"])
            + 6.0 * _clamp(inputs.card_count / limits.min_family_count, 0.0, 1.0)
            + 4.0 * _bool_score(_required_claim_ratio(inputs.claim_boundaries) == 1.0)
            + 4.0 * _bool_score(inputs.hero_video_status == "local_file")
            + 3.0 * _bool_score(inputs.submission_pack_status == "local_file")
            + 2.0 * _bool_score(inputs.asset_request_count >= limits.min_asset_request_count)
        ),
        "video_readiness": (
            5.0 * _bool_score(files["storyboard"])
            + 4.0 * _bool_score(inputs.hero_video_status == "local_file")
            + 3.0 * _bool_score(files["commands"])
            + 3.0 * _bool_score(any("1-5" in _read_text(inputs.storyboard_path) for _ in [0]))
        ),
        "reproducibility": (
            3.0 * _bool_score(bool(inputs.environment_summary_path))
            + 3.0 * _bool_score(bool(inputs.demo_manifest_path))
            + 2.0 * _bool_score(files["commands"])
            + 2.0 * _bool_score("oodrive score-env-demo" in command_text)
        ),
    }
    return {key: round(value, 4) for key, value in components.items()}


def _blockers(inputs: EnvironmentDemoReadinessInputs, limits: EnvironmentDemoThresholds, score: float) -> list[str]:
    blockers: list[str] = []
    if score < limits.pass_score:
        blockers.append(f"environment_demo_readiness_score {score:.2f} below {limits.pass_score:.2f}")
    if inputs.family_count < limits.min_family_count:
        blockers.append(f"family_count {inputs.family_count} below {limits.min_family_count}")
    if inputs.asset_request_count < limits.min_asset_request_count:
        blockers.append(f"asset_request_count {inputs.asset_request_count} below {limits.min_asset_request_count}")
    missing_claims = [claim for claim in REQUIRED_CLAIM_BOUNDARIES if claim not in inputs.claim_boundaries]
    if missing_claims:
        blockers.append(f"missing claim boundaries: {', '.join(missing_claims)}")
    if not _path_exists(inputs.html_path):
        blockers.append("Environment Studio index.html is missing")
    if not _path_exists(inputs.storyboard_path):
        blockers.append("video_storyboard.md is missing")
    return blockers


def _recommendations(inputs: EnvironmentDemoReadinessInputs, blockers: list[str]) -> list[str]:
    recommendations: list[str] = []
    text = " | ".join(blockers)
    if "index.html" in text:
        recommendations.append("Run `oodrive export-env-demo` to build the recordable Environment Studio page.")
    if "score" in text:
        recommendations.append("Expose the generated environment pack through OODrive commands and proof links.")
    if inputs.hero_video_status != "local_file":
        recommendations.append("Link the existing local hero CARLA video so judges can connect generated environments to navigation evidence.")
    return _dedupe(recommendations)


def _inputs_from_fixture(payload: dict[str, Any], path: Path) -> EnvironmentDemoReadinessInputs:
    return EnvironmentDemoReadinessInputs(
        environment_summary_path=_optional_str(payload.get("environment_summary_path")),
        demo_manifest_path=_optional_str(payload.get("demo_manifest_path")),
        family_count=int(_first_float(payload.get("family_count"))),
        recipe_count=int(_first_float(payload.get("recipe_count"))),
        asset_request_count=int(_first_float(payload.get("asset_request_count"))),
        weather_ready_count=int(_first_float(payload.get("weather_ready_count"))),
        traffic_ready_count=int(_first_float(payload.get("traffic_ready_count"))),
        road_local_asset_count=int(_first_float(payload.get("road_local_asset_count"))),
        expected_policy_pressure_count=int(_first_float(payload.get("expected_policy_pressure_count"))),
        command_names=[str(item) for item in list(payload.get("command_names", []))],
        html_path=_optional_str(payload.get("html_path")),
        commands_path=_optional_str(payload.get("commands_path")),
        storyboard_path=_optional_str(payload.get("storyboard_path")),
        hero_video_status=str(payload.get("hero_video_status", "missing")),
        submission_pack_status=str(payload.get("submission_pack_status", "missing")),
        card_count=int(_first_float(payload.get("card_count"))),
        claim_boundaries=[str(item) for item in list(payload.get("claim_boundaries", []))],
    )


def _score_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Environment Demo Readiness Score",
        "",
        f"- Status: `{payload['status']}`",
        f"- Score: `{payload['environment_demo_readiness_score']}` / 100",
        f"- Threshold: `{payload['threshold']}`",
        "",
        "## Components",
        "",
        "| component | points |",
        "| --- | --- |",
    ]
    for key, value in dict(payload.get("components", {})).items():
        lines.append(f"| `{key}` | `{value}` |")
    if payload.get("blockers"):
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in list(payload.get("blockers", [])))
    if payload.get("recommendations"):
        lines.extend(["", "## Recommendations", ""])
        lines.extend(f"- {item}" for item in list(payload.get("recommendations", [])))
    return "\n".join(lines) + "\n"


def _path_exists(value: str | None) -> bool:
    return bool(value and Path(value).exists())


def _read_text(value: str | None) -> str:
    if not value:
        return ""
    path = Path(value)
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _required_claim_ratio(claim_boundaries: list[str]) -> float:
    return _clamp(sum(1 for claim in REQUIRED_CLAIM_BOUNDARIES if claim in claim_boundaries) / len(REQUIRED_CLAIM_BOUNDARIES), 0.0, 1.0)


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


def _optional_str(value: object) -> str | None:
    return str(value) if isinstance(value, str) and value else None


def _first_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _bool_score(value: bool) -> float:
    return 1.0 if value else 0.0


def _clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out


__all__ = [
    "EnvironmentDemoReadinessInputs",
    "EnvironmentDemoReadinessReport",
    "EnvironmentDemoThresholds",
    "load_environment_demo_readiness_inputs",
    "score_environment_demo_readiness",
    "write_environment_demo_score",
]
