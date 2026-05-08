"""Score production usefulness of prompt-to-CARLA scenario generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def score_research_scenario_generator(
    *,
    scenario_pack_path: Path | None = None,
    asset_manifest_paths: tuple[Path, ...] = (),
    asset_registry_path: Path | None = None,
    scenario_graph_path: Path | None = None,
    run_manifest_paths: tuple[Path, ...] = (),
    workbench_summary_path: Path | None = None,
    library_path: Path | None = None,
    video_path: Path | None = None,
    image_qa_report_path: Path | None = None,
) -> dict[str, Any]:
    components = {
        "scenario_contract": 0.0,
        "asset_generation": 0.0,
        "carla_asset_import": 0.0,
        "live_carla_execution": 0.0,
        "behavior_realism": 0.0,
        "evidence_quality": 0.0,
        "prompt_image_match": 0.0,
        "researcher_usability": 0.0,
        "export_reproducibility": 0.0,
        "claim_honesty": 10.0,
    }
    blockers: list[str] = []
    recommendations: list[str] = []
    pack = _load_optional(scenario_pack_path)
    if pack:
        validation = dict(pack.get("validation", {}))
        components["scenario_contract"] = 12.0 if validation.get("passes") is True else 6.0
        if pack.get("behavior_timelines"):
            components["behavior_realism"] += 5.0
        if pack.get("asset_requests"):
            components["asset_generation"] += 3.0
        claim_boundaries = [str(item) for item in list(pack.get("claim_boundaries", []))]
        if any("custom_asset_imported_in_carla=false" in item for item in claim_boundaries):
            components["claim_honesty"] += 5.0
    else:
        blockers.append("missing production scenario pack")
    for path in asset_manifest_paths:
        payload = _load_optional(path)
        if not payload:
            continue
        manifests = [dict(item) for item in list(payload.get("asset_manifests", [])) if isinstance(item, dict)]
        generated = [item for item in manifests if item.get("status") == "generated" and item.get("local_path")]
        if generated:
            components["asset_generation"] = max(components["asset_generation"], 15.0)
        if payload.get("status") == "passed":
            components["evidence_quality"] += 3.0
    registry = _load_optional(asset_registry_path)
    if registry:
        installed = float(registry.get("installed_blueprint_count", 0) or 0)
        fallback = float(registry.get("stock_proxy_fallback_count", 0) or 0)
        components["carla_asset_import"] = 15.0 if installed > 0 else (5.0 if fallback > 0 else 0.0)
        if installed <= 0 and fallback > 0:
            recommendations.append("Install/probe generated CARLA blueprints to move beyond stock proxy fallback.")
    else:
        recommendations.append("Add CARLA asset registry/probe evidence.")
    graph = _load_optional(scenario_graph_path)
    if graph:
        if graph.get("validation", {}).get("passes") is True:
            components["scenario_contract"] = max(components["scenario_contract"], 15.0)
        if graph.get("actions"):
            components["behavior_realism"] = max(components["behavior_realism"], 10.0)
    for path in run_manifest_paths:
        run = _load_optional(path)
        if not run:
            continue
        result = dict(run.get("result", {}))
        backend = result.get("backend")
        if backend == "carla-live" and result.get("status") in {"passed", "partial"}:
            components["live_carla_execution"] = max(components["live_carla_execution"], 20.0)
        elif backend == "fake-carla" and result.get("status") == "passed":
            components["live_carla_execution"] = max(components["live_carla_execution"], 8.0)
        if int(result.get("spawned_static_count", 0) or 0) > 0:
            components["evidence_quality"] += 5.0
        if result.get("tracks_path") and _artifact_path_exists(str(result["tracks_path"]), path):
            components["evidence_quality"] += 5.0
        if result.get("rgb_folder") and _artifact_path_exists(str(result["rgb_folder"]), path):
            components["evidence_quality"] += 7.0
    if video_path and video_path.exists() and video_path.stat().st_size > 1000:
        components["evidence_quality"] += 5.0
    if workbench_summary_path and workbench_summary_path.exists():
        components["researcher_usability"] = 8.0
    if library_path and library_path.exists():
        components["export_reproducibility"] = 8.0
    score_cap = 100.0
    image_qa = _load_optional(image_qa_report_path)
    if image_qa:
        verdict = str(image_qa.get("verdict", "")).strip().lower()
        real_carla_verdict = str(dict(image_qa.get("real_carla_evidence", {})).get("verdict", "")).lower()
        if verdict in {"pass", "passed", "exact"}:
            components["prompt_image_match"] = 10.0
        elif verdict == "partial":
            components["prompt_image_match"] = 4.0
            score_cap = min(score_cap, 92.0)
            recommendations.append("Improve CARLA visual prompt fidelity before flagship promotion.")
        else:
            score_cap = min(score_cap, 72.0)
            blockers.append("prompt image QA did not pass")
            recommendations.append("Regenerate or reposition the scenario until prompt image QA passes.")
        if real_carla_verdict not in {"real_carla", "likely_real_carla", "passed", "pass"}:
            blockers.append("prompt image QA does not prove live CARLA evidence")
    else:
        recommendations.append("Add prompt-to-CARLA image QA before treating the score as flagship evidence.")
    components["evidence_quality"] = min(components["evidence_quality"], 15.0)
    score = round(min(score_cap, sum(components.values())), 4)
    status = "passed" if score >= 85.0 and not blockers and score_cap >= 95.0 else ("partial" if score >= 55.0 else "blocked")
    return {
        "metric_name": "research_scenario_generator_score",
        "research_scenario_generator_score": score,
        "score": score,
        "threshold": 85.0,
        "status": status,
        "components": components,
        "blockers": blockers,
        "recommendations": recommendations,
        "claim_boundaries": [
            "metric_rewards_live_carla=true",
            "stock_proxy_fallback_not_custom_asset=true",
            "prompt_image_qa_caps_flagship_score=true",
            "closed_loop_vla_control_not_scored_here=true",
        ],
    }


def write_research_scenario_generator_score(run_dir: Path, report: dict[str, Any]) -> dict[str, str]:
    path = run_dir / "research_scenario_generator_score.json"
    report_path = run_dir / "research_scenario_generator_score.md"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report_path.write_text(_score_markdown(report), encoding="utf-8")
    return {"json_path": str(path), "report_path": str(report_path)}


def _load_optional(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _artifact_path_exists(value: str, context_path: Path) -> bool:
    path = Path(value)
    if path.exists():
        return True
    for parent in context_path.resolve().parents:
        candidate = parent / value
        if candidate.exists():
            return True
    return False


def _score_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Research Scenario Generator Score",
        "",
        f"- score: {report.get('score')}",
        f"- status: {report.get('status')}",
        "",
        "## Components",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in dict(report.get("components", {})).items())
    return "\n".join(lines) + "\n"


__all__ = ["score_research_scenario_generator", "write_research_scenario_generator_score"]
