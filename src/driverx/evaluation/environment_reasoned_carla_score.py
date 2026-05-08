"""Score the generated-environment to reasoned-CARLA proof chain."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EnvironmentReasonedCarlaScoreReport:
    status: str
    environment_to_reasoned_carla_score: float
    threshold: float
    components: dict[str, float]
    blockers: list[str]
    recommendations: list[str]
    claim_boundaries: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "environment_to_reasoned_carla_score": self.environment_to_reasoned_carla_score,
            "threshold": self.threshold,
            "components": self.components,
            "blockers": self.blockers,
            "recommendations": self.recommendations,
            "claim_boundaries": self.claim_boundaries,
        }


def score_environment_reasoned_carla(
    *,
    environment_summary_path: Path,
    visual_proof_path: Path,
    keyframe_analysis_path: Path,
    overlay_report_path: Path | None = None,
    video_path: Path | None = None,
    threshold: float = 90.0,
) -> EnvironmentReasonedCarlaScoreReport:
    env = _load_json(environment_summary_path)
    visual = _load_json(visual_proof_path)
    keyframes = _load_json(keyframe_analysis_path)
    overlay = _load_json(overlay_report_path) if overlay_report_path and overlay_report_path.exists() else {}
    components = {
        "cli_generation": _cli_generation_score(env),
        "same_run_carla_visual": _visual_score(visual),
        "keyframe_reasoning": _keyframe_score(keyframes),
        "video_readiness": _video_score(overlay, video_path),
        "reproducibility": _reproducibility_score(visual, keyframes, overlay),
    }
    score = round(sum(components.values()), 4)
    blockers = _blockers(visual, keyframes, overlay, video_path, score, threshold)
    return EnvironmentReasonedCarlaScoreReport(
        status="passed" if score >= threshold and not blockers else "blocked",
        environment_to_reasoned_carla_score=score,
        threshold=threshold,
        components=components,
        blockers=blockers,
        recommendations=_recommendations(blockers),
        claim_boundaries=_dedupe(
            [
                *list(visual.get("claim_boundaries", [])),
                *list(keyframes.get("claim_boundaries", [])),
                *list(overlay.get("claim_boundaries", [])),
                "closed_loop_vla_control=false",
                "real_time_vla_control=false",
                "sampled_open_loop_reasoning=true",
                "time_warped_offline_demo=true",
            ]
        ),
    )


def write_environment_reasoned_carla_score(run_dir: Path, report: EnvironmentReasonedCarlaScoreReport) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_jsonable()
    json_path = run_dir / "environment_reasoned_carla_score.json"
    report_path = run_dir / "environment_reasoned_carla_score.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _cli_generation_score(env: dict[str, Any]) -> float:
    score = 0.0
    if len(list(env.get("families", []))) >= 4:
        score += 5.0
    if len(list(env.get("recipes", []))) >= 6:
        score += 5.0
    if len(list(env.get("asset_requests", []))) >= 6:
        score += 5.0
    if env.get("summary_path") or env.get("recipes_path"):
        score += 5.0
    return min(score, 20.0)


def _visual_score(visual: dict[str, Any]) -> float:
    score = 0.0
    if visual.get("same_lineage") is True:
        score += 7.0
    if _path_exists(visual.get("preview_image_path")):
        score += 7.0
    if _path_exists(visual.get("run_manifest_path")):
        score += 4.0
    if _path_exists(visual.get("placement_plan_path")):
        score += 3.0
    if visual.get("status") == "passed":
        score += 4.0
    return min(score, 25.0)


def _keyframe_score(keyframes: dict[str, Any]) -> float:
    analyses = [item for item in list(keyframes.get("analyses", [])) if isinstance(item, dict)]
    reasoned = [
        item
        for item in analyses
        if item.get("image_path")
        and (item.get("vla_reasoning") or item.get("blockers"))
        and item.get("source_time_s") is not None
    ]
    real_reasoned = [
        item
        for item in reasoned
        if item.get("backend") not in {"fake", "blocked"} and item.get("status") == "passed"
    ]
    score = min(len(reasoned), 5) * 3.0
    if keyframes.get("same_lineage") is True:
        score += 4.0
    if len(real_reasoned) >= 3:
        score += 4.0
    elif len(reasoned) >= 5:
        score += 2.0
    if "sampled_open_loop_reasoning=true" in list(keyframes.get("claim_boundaries", [])):
        score += 2.0
    return min(score, 25.0)


def _video_score(overlay: dict[str, Any], video_path: Path | None) -> float:
    score = 0.0
    if (video_path and video_path.exists()) or _path_exists(overlay.get("video_path")):
        score += 6.0
    if overlay:
        score += 4.0
    duration = _float(overlay.get("duration_s"))
    if 60.0 <= duration <= 300.0:
        score += 4.0
    kinds = {str(item.get("kind")) for item in list(overlay.get("timeline_segments", [])) if isinstance(item, dict)}
    if {"cli_generation", "carla_preview", "keyframe_reasoning", "claim_boundary"}.issubset(kinds):
        score += 4.0
    if "time_warped_offline_demo=true" in list(overlay.get("claim_boundaries", [])):
        score += 2.0
    return min(score, 20.0)


def _reproducibility_score(visual: dict[str, Any], keyframes: dict[str, Any], overlay: dict[str, Any]) -> float:
    score = 0.0
    for payload in (visual, keyframes, overlay):
        if _path_exists(payload.get("commands_path")):
            score += 2.0
    if _path_exists(visual.get("db_path")):
        score += 2.0
    if _path_exists(keyframes.get("report_path")):
        score += 2.0
    return min(score, 10.0)


def _blockers(
    visual: dict[str, Any],
    keyframes: dict[str, Any],
    overlay: dict[str, Any],
    video_path: Path | None,
    score: float,
    threshold: float,
) -> list[str]:
    blockers: list[str] = []
    if score < threshold:
        blockers.append(f"environment_to_reasoned_carla_score {score:.4f} below {threshold:.4f}")
    if not _path_exists(visual.get("preview_image_path")):
        blockers.append("missing CARLA preview image")
    if int(keyframes.get("reasoned_keyframe_count") or 0) < 5:
        blockers.append("fewer than 5 reasoned keyframes")
    if not ((video_path and video_path.exists()) or _path_exists(overlay.get("video_path"))):
        blockers.append("missing environment-to-reasoned-CARLA MP4")
    return blockers


def _recommendations(blockers: list[str]) -> list[str]:
    if not blockers:
        return ["Promote this artifact into the final submission pack."]
    return [
        "Run `oodrive render-env --live` on the Kasm CARLA host to capture RGB frames.",
        "Run `oodrive analyze-keyframes --backend fake` locally or `--backend alpamayo-local` on the configured GPU lane.",
        "Render the final `oodrive env-demo-video` only after frame-linked analyses exist.",
    ]


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Environment To Reasoned CARLA Score",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Score: `{payload.get('environment_to_reasoned_carla_score')}`",
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
        for blocker in blockers:
            lines.append(f"- {blocker}")
    lines.append("")
    return "\n".join(lines)


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, dict) else {}


def _path_exists(value: object) -> bool:
    return bool(value) and Path(str(value)).exists()


def _float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _dedupe(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


__all__ = [
    "EnvironmentReasonedCarlaScoreReport",
    "score_environment_reasoned_carla",
    "write_environment_reasoned_carla_score",
]
