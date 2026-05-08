"""Score OODrive generated behavior/object runtime usability."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GeneratorRuntimeScoreInputs:
    runtime_manifest_path: Path
    runtime_manifest: dict[str, Any]


@dataclass(frozen=True)
class GeneratorRuntimeScoreReport:
    status: str
    generator_runtime_score: float
    threshold: float
    components: dict[str, float]
    blockers: list[str]
    recommendations: list[str]
    claim_boundaries: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "generator_runtime_score": self.generator_runtime_score,
            "threshold": self.threshold,
            "components": self.components,
            "blockers": self.blockers,
            "recommendations": self.recommendations,
            "claim_boundaries": self.claim_boundaries,
        }


def load_generator_runtime_score_inputs(runtime_manifest_path: Path) -> GeneratorRuntimeScoreInputs:
    """Load score inputs from a generated runtime manifest."""

    payload = json.loads(runtime_manifest_path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Runtime manifest must be a JSON object: {runtime_manifest_path}")
    return GeneratorRuntimeScoreInputs(
        runtime_manifest_path=runtime_manifest_path,
        runtime_manifest=dict(payload),
    )


def score_generator_runtime(
    inputs: GeneratorRuntimeScoreInputs,
    *,
    threshold: float = 90.0,
) -> GeneratorRuntimeScoreReport:
    """Score whether generated behavior/object runtime proof is usable."""

    manifest = inputs.runtime_manifest
    proof = _mapping(manifest.get("runtime_proof"))
    components = {
        "scenario_generation": _scenario_generation_score(manifest),
        "behavior_breadth": _behavior_breadth_score(manifest),
        "object_spawn_readiness": _object_spawn_score(manifest),
        "carla_runtime_proof": _runtime_proof_score(proof),
        "cleanup_and_lineage": _cleanup_score(manifest, proof, inputs.runtime_manifest_path),
        "claim_honesty": _claim_score(manifest),
    }
    score = round(sum(components.values()), 4)
    blockers = _blockers(manifest, proof, score, threshold)
    return GeneratorRuntimeScoreReport(
        status="passed" if score >= threshold and not blockers else "blocked",
        generator_runtime_score=score,
        threshold=threshold,
        components=components,
        blockers=blockers,
        recommendations=_recommendations(blockers),
        claim_boundaries=_dedupe(
            [
                *list(manifest.get("claim_boundaries", [])),
                "generated_vehicle_behaviors=true",
                "closed_loop_vla_control=false",
                "real_time_vla_control=false",
            ]
        ),
    )


def write_generator_runtime_score(run_dir: Path, report: GeneratorRuntimeScoreReport) -> dict[str, Any]:
    """Write generator-runtime score JSON and Markdown artifacts."""

    run_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_jsonable()
    json_path = run_dir / "generator_runtime_score.json"
    report_path = run_dir / "generator_runtime_score.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _scenario_generation_score(manifest: dict[str, Any]) -> float:
    score = 0.0
    if manifest.get("prompt"):
        score += 4.0
    if manifest.get("scenario_id"):
        score += 3.0
    if manifest.get("environment_recipe_id") or manifest.get("template_id"):
        score += 4.0
    validation = _mapping(manifest.get("validation"))
    if validation.get("passes") is True:
        score += 4.0
    return min(score, 15.0)


def _behavior_breadth_score(manifest: dict[str, Any]) -> float:
    cases = [_mapping(item) for item in list(manifest.get("behavior_cases", []))]
    behavior_ids = {str(case.get("behavior_id")) for case in cases if case.get("behavior_id")}
    passed = [
        case
        for case in cases
        if _mapping(case.get("validation")).get("passes") is True
    ]
    score = min(len(behavior_ids), 3) * 4.0
    score += min(len(passed), 3) * 2.0
    if any(str(case.get("behavior_id")) == "motorcycle_filtering" for case in cases):
        score += 1.0
    if any(str(case.get("behavior_id")) == "no_signal_cut_in" for case in cases):
        score += 1.0
    return min(score, 20.0)


def _object_spawn_score(manifest: dict[str, Any]) -> float:
    specs = [_mapping(item) for item in list(manifest.get("object_spawn_specs", []))]
    asset_requests = [_mapping(item) for item in list(manifest.get("asset_requests", []))]
    score = min(len(specs), 4) * 3.0
    if len(specs) >= 2:
        score += 3.0
    if all(spec.get("blueprint_filter") and spec.get("spawn_transform") for spec in specs):
        score += 3.0
    if len(asset_requests) >= len(specs) and specs:
        score += 2.0
    return min(score, 20.0)


def _runtime_proof_score(proof: dict[str, Any]) -> float:
    backend = str(proof.get("backend", ""))
    status = str(proof.get("status", ""))
    score = 0.0
    if backend == "fake-carla" and status == "passed":
        score += 7.0
    elif backend == "carla-live" and status in {"passed", "partial"}:
        score += 9.0
    elif backend == "dry-run" and status == "passed":
        score += 3.0
    if int(proof.get("static_object_spawn_count") or 0) >= 2:
        score += 4.0
    if int(proof.get("dynamic_actor_spawn_count") or 0) >= 1:
        score += 4.0
    if int(proof.get("applied_behavior_tick_count") or 0) >= 10:
        score += 3.0
    if _path_exists(proof.get("tracks_path")) and int(proof.get("track_count") or 0) >= 10:
        score += 2.0
    return min(score, 20.0)


def _cleanup_score(manifest: dict[str, Any], proof: dict[str, Any], runtime_manifest_path: Path) -> float:
    spawned = {int(item) for item in list(proof.get("spawned_actor_ids", [])) if _intish(item)}
    destroyed = {int(item) for item in list(proof.get("destroyed_actor_ids", [])) if _intish(item)}
    score = 0.0
    if runtime_manifest_path.exists():
        score += 3.0
    if _path_exists(manifest.get("spec_path")):
        score += 2.0
    if spawned and spawned.issubset(destroyed):
        score += 6.0
    elif proof.get("backend") == "dry-run":
        score += 2.0
    if manifest.get("run_id") and manifest.get("scenario_id"):
        score += 2.0
    if proof.get("json_path") and _path_exists(proof.get("json_path")):
        score += 2.0
    return min(score, 15.0)


def _claim_score(manifest: dict[str, Any]) -> float:
    claims = {str(item) for item in list(manifest.get("claim_boundaries", []))}
    required = {
        "generated_vehicle_behaviors=true",
        "closed_loop_vla_control=false",
        "real_time_vla_control=false",
    }
    score = 0.0
    score += len(required & claims) * 2.0
    if any(item.startswith("objects_spawned_in_carla=") for item in claims):
        score += 2.0
    if any(item.startswith("generator_runtime_backend=") for item in claims):
        score += 2.0
    return min(score, 10.0)


def _blockers(manifest: dict[str, Any], proof: dict[str, Any], score: float, threshold: float) -> list[str]:
    blockers: list[str] = []
    if score < threshold:
        blockers.append(f"generator_runtime_score {score:.4f} below {threshold:.4f}")
    if int(manifest.get("behavior_case_count") or 0) < 1:
        blockers.append("missing generated behavior cases")
    if int(manifest.get("object_spawn_spec_count") or 0) < 2:
        blockers.append("fewer than two generated object spawn specs")
    if proof.get("backend") != "dry-run" and int(proof.get("dynamic_actor_spawn_count") or 0) < 1:
        blockers.append("no dynamic behavior actor spawned")
    if proof.get("backend") != "dry-run" and not _has_runtime_tracks(proof):
        blockers.append("missing runtime entity tracks")
    for blocker in list(manifest.get("blockers", [])):
        blockers.append(str(blocker))
    return _dedupe(blockers)


def _recommendations(blockers: list[str]) -> list[str]:
    if not blockers:
        return ["Use this generated runtime manifest as the source for TASK-139 time-warped VLA driving."]
    return [
        "Run `oodrive generate-run --backend fake-carla` with at least three behavior ids and two object kinds.",
        "Use `--backend carla-live` on the Kasm/CARLA host only after fake-CARLA proof passes.",
        "Keep claim labels visible when promoting this artifact into a final video."
    ]


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Generator Runtime Score",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Score: `{payload.get('generator_runtime_score')}`",
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


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _path_exists(value: object) -> bool:
    return bool(value) and Path(str(value)).exists()


def _has_runtime_tracks(proof: dict[str, Any]) -> bool:
    if _path_exists(proof.get("tracks_path")):
        return True
    for case in list(proof.get("case_results", [])):
        if isinstance(case, dict) and _path_exists(case.get("tracks_path")):
            return True
    return False


def _intish(value: object) -> bool:
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False


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
    "GeneratorRuntimeScoreInputs",
    "GeneratorRuntimeScoreReport",
    "load_generator_runtime_score_inputs",
    "score_generator_runtime",
    "write_generator_runtime_score",
]
