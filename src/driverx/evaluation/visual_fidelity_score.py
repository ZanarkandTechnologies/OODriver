"""Score prompt-to-CARLA media proof for agent-authored OODrive scenarios."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VisualFidelityScoreReport:
    status: str
    visual_fidelity_score: float
    threshold: float
    components: dict[str, float]
    blockers: list[str]
    recommendations: list[str]
    claim_boundaries: list[str]
    inputs: dict[str, Any]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "visual_fidelity_score": self.visual_fidelity_score,
            "threshold": self.threshold,
            "components": self.components,
            "blockers": self.blockers,
            "recommendations": self.recommendations,
            "claim_boundaries": self.claim_boundaries,
            "inputs": self.inputs,
        }


def score_visual_fidelity(media_manifest_path: Path, *, threshold: float = 90.0) -> VisualFidelityScoreReport:
    """Score whether visual proof actually matches and explains the requested CARLA scene."""

    manifest = _load_json(media_manifest_path)
    components = {
        "media_presence": _score_media_presence(manifest),
        "prompt_grounding": _score_prompt_grounding(manifest),
        "scenario_richness": _score_scenario_richness(manifest),
        "behavior_evidence": _score_behavior_evidence(manifest),
        "reasoning_readability": _score_reasoning_readability(manifest),
        "reproducibility": _score_reproducibility(manifest),
    }
    score = round(sum(components.values()), 4)
    blockers = _blockers(manifest, score, threshold)
    return VisualFidelityScoreReport(
        status="passed" if score >= threshold and not blockers else "blocked",
        visual_fidelity_score=score,
        threshold=threshold,
        components=components,
        blockers=blockers,
        recommendations=_recommendations(blockers),
        claim_boundaries=_dedupe(
            [
                *_string_list(manifest.get("claim_boundaries")),
                "prompt_to_carla_visual_fidelity_scored=true",
                "closed_loop_vla_control=false_unless_trace_score_passes",
                "arbitrary_mesh_spawn=false_until_live_spawn_proof_exists",
            ]
        ),
        inputs={"media_manifest_path": str(media_manifest_path), **manifest},
    )


def write_visual_fidelity_score(run_dir: Path, report: VisualFidelityScoreReport) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_jsonable()
    json_path = run_dir / "visual_fidelity_score.json"
    report_path = run_dir / "visual_fidelity_score.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _score_media_presence(manifest: dict[str, Any]) -> float:
    score = 0.0
    if _path_exists(manifest.get("video_path")):
        score += 6.0
    if len(_existing_paths(manifest.get("frames"))) >= 3 or _path_exists(manifest.get("preview_image_path")):
        score += 5.0
    duration = _float(manifest.get("duration_s"))
    if 15.0 <= duration <= 300.0:
        score += 2.0
    if int(_float(manifest.get("frame_count"))) >= 30 or len(_existing_paths(manifest.get("frames"))) >= 5:
        score += 2.0
    return min(score, 15.0)


def _score_prompt_grounding(manifest: dict[str, Any]) -> float:
    expected = _tokens(manifest.get("expected_visual_tags") or manifest.get("ood_tags"))
    visible = _tokens(manifest.get("visible_visual_tags") or manifest.get("visible_tags"))
    if not str(manifest.get("prompt") or "").strip():
        return 0.0
    score = 5.0
    if expected:
        score += 10.0 * (len(expected & visible) / len(expected))
    if len(visible) >= 4:
        score += 3.0
    if str(manifest.get("map") or "").strip():
        score += 2.0
    return min(score, 20.0)


def _score_scenario_richness(manifest: dict[str, Any]) -> float:
    score = 0.0
    if str(manifest.get("map") or "").strip():
        score += 2.0
    if _mapping(manifest.get("weather")):
        score += 2.0
    if int(_float(manifest.get("static_obstacle_count"))) >= 1 or "static_obstacle" in _tokens(manifest.get("visible_visual_tags")):
        score += 3.0
    if int(_float(manifest.get("moving_actor_count"))) >= 1 or "moving_hazard" in _tokens(manifest.get("visible_visual_tags")):
        score += 3.0
    if int(_float(manifest.get("background_actor_count"))) >= 2:
        score += 2.0
    if int(_float(manifest.get("environment_variation_count"))) >= 2:
        score += 3.0
    return min(score, 15.0)


def _score_behavior_evidence(manifest: dict[str, Any]) -> float:
    behaviors = _tokens(manifest.get("behavior_events"))
    score = min(len(behaviors), 4) * 2.5
    if int(_float(manifest.get("risk_event_count"))) >= 3:
        score += 3.0
    if bool(manifest.get("lane_alignment_pass")):
        score += 3.0
    if bool(manifest.get("dynamic_actor_motion_proved")):
        score += 2.0
    if bool(manifest.get("ego_action_trace_present")):
        score += 2.0
    return min(score, 20.0)


def _score_reasoning_readability(manifest: dict[str, Any]) -> float:
    score = 0.0
    if int(_float(manifest.get("reasoning_snippet_count"))) >= 3:
        score += 5.0
    if int(_float(manifest.get("rag_callout_count"))) >= 3:
        score += 4.0
    if bool(manifest.get("frame_time_overlay_present")):
        score += 3.0
    if _float(manifest.get("hud_congestion_ratio"), 0.5) <= 0.32:
        score += 3.0
    return min(score, 15.0)


def _score_reproducibility(manifest: dict[str, Any]) -> float:
    score = 0.0
    for key in ("osc2_path", "sidecar_path", "run_manifest_path", "commands_path", "score_report_path"):
        if _path_exists(manifest.get(key)):
            score += 2.0
    boundaries = _string_list(manifest.get("claim_boundaries"))
    if "agent_authored_scenario=true" in boundaries:
        score += 2.0
    if any(item.startswith("closed_loop_vla_control=") for item in boundaries):
        score += 1.5
    if any(item.startswith("arbitrary_mesh_spawn=") for item in boundaries):
        score += 1.5
    return min(score, 15.0)


def _blockers(manifest: dict[str, Any], score: float, threshold: float) -> list[str]:
    blockers: list[str] = []
    if score < threshold:
        blockers.append(f"visual_fidelity_score {score:.4f} below {threshold:.4f}")
    if not (_path_exists(manifest.get("video_path")) or _path_exists(manifest.get("preview_image_path")) or _existing_paths(manifest.get("frames"))):
        blockers.append("missing live visual media proof")
    expected = _tokens(manifest.get("expected_visual_tags") or manifest.get("ood_tags"))
    visible = _tokens(manifest.get("visible_visual_tags") or manifest.get("visible_tags"))
    if expected and len(expected & visible) / len(expected) < 0.6:
        blockers.append("visible tags cover less than 60% of requested OOD scene")
    if ("moving_hazard" in expected or int(_float(manifest.get("moving_actor_count"))) > 0) and not manifest.get("dynamic_actor_motion_proved"):
        blockers.append("moving hazard requested but no dynamic actor motion proof exists")
    if manifest.get("lane_departure_detected") is True:
        blockers.append("lane departure detected in visual/behavior proof")
    if manifest.get("duplicate_gallery_match") is True:
        blockers.append("scene is visually duplicate of an existing gallery artifact")
    if manifest.get("custom_asset_requested") is True and manifest.get("custom_asset_spawn_proved") is not True:
        blockers.append("custom asset requested but no custom CARLA spawn proof exists")
    if manifest.get("custom_map_requested") is True and manifest.get("custom_map_probe_passed") is not True:
        blockers.append("custom map requested but no CARLA map load proof exists")
    boundaries = _string_list(manifest.get("claim_boundaries"))
    if "arbitrary_mesh_spawn=true" in boundaries and manifest.get("custom_asset_spawn_proved") is not True:
        blockers.append("false custom-asset claim: arbitrary mesh spawn is not proved")
    if "custom_unreal_map_import=true" in boundaries and manifest.get("custom_map_probe_passed") is not True:
        blockers.append("false custom-map claim: custom Unreal map import is not proved")
    if _float(manifest.get("hud_congestion_ratio"), 0.0) > 0.45:
        blockers.append("HUD is too congested for judge-readable reasoning")
    return blockers


def _recommendations(blockers: list[str]) -> list[str]:
    if not blockers:
        return ["Promote this CARLA media proof into the generator gallery or submission reel."]
    recs: list[str] = []
    if any("visual media" in blocker for blocker in blockers):
        recs.append("Capture a live CARLA preview image or MP4 and point the media manifest at the local file.")
    if any("visible tags" in blocker for blocker in blockers):
        recs.append("Move the spectator camera and spawn anchors until requested hazards are visible in-frame.")
    if any("moving hazard" in blocker for blocker in blockers):
        recs.append("Add a behavior trace with actor motion samples before scoring the scene.")
    if any("lane departure" in blocker for blocker in blockers):
        recs.append("Fix route anchors/control so the ego holds lane or performs a justified lane change.")
    if any("custom asset" in blocker or "custom-asset" in blocker for blocker in blockers):
        recs.append("Run `oodrive package-asset`, `probe-asset-blueprint`, and `spawn-custom-asset` before claiming custom asset proof.")
    if any("custom map" in blocker or "custom-map" in blocker for blocker in blockers):
        recs.append("Run `oodrive prepare-map-import`, `validate-map-import`, and `carla-map-probe` before claiming custom map proof.")
    if any("duplicate" in blocker for blocker in blockers):
        recs.append("Change map, weather, anchors, camera, or actor set before promoting another gallery artifact.")
    if any("HUD" in blocker for blocker in blockers):
        recs.append("Use sparse callouts, frame/time labels, and a side panel rather than covering the driving scene.")
    return recs or ["Improve the lowest scoring components and rerun `oodrive score-visual-fidelity`."]


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Visual Fidelity Score",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Score: `{payload.get('visual_fidelity_score')}`",
        f"- Threshold: `{payload.get('threshold')}`",
        "",
        "## Components",
        "",
    ]
    for key, value in dict(payload.get("components", {})).items():
        lines.append(f"- `{key}`: `{value}`")
    blockers = list(payload.get("blockers", []))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {blocker}" for blocker in blockers)
    lines.append("")
    return "\n".join(lines)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_exists(value: object) -> bool:
    return isinstance(value, str) and bool(value) and Path(value).exists()


def _existing_paths(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if _path_exists(item)]


def _tokens(value: object) -> set[str]:
    if isinstance(value, str):
        return {value}
    if not isinstance(value, list):
        return set()
    return {str(item) for item in value if str(item).strip()}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


__all__ = ["VisualFidelityScoreReport", "score_visual_fidelity", "write_visual_fidelity_score"]
