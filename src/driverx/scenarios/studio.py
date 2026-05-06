"""Scenario Studio prompt compiler and OOD dataset curation loop."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from driverx.behaviors import BehaviorPlan, generate_behavior_variants
from driverx.core.artifacts import prepare_run_dir
from driverx.core.config import read_config_mapping
from driverx.environments import (
    EnvironmentRecipe,
    attach_environment_to_recipe,
    environment_to_asset_requests,
    generate_environment_recipe,
)
from driverx.scenarios.catalog import ScenarioCatalogRecord, load_scenario_catalog
from driverx.scenarios.loader import load_scenario_seeds
from driverx.scenarios.types import ScenarioRecipe, ScenarioSeed

BriefAuthor = Literal["human", "agent", "fixture"]
StudioProvider = Literal["deterministic", "llm"]
CurationStatus = Literal[
    "accept",
    "accept_partial",
    "needs_rerun",
    "reject_duplicate",
    "reject_invalid",
    "blocked_runtime",
]


@dataclass(frozen=True)
class ScenarioBrief:
    brief_id: str
    prompt: str
    author: BriefAuthor = "human"
    region: str | None = None
    requested_tags: list[str] = field(default_factory=list)
    target_policy_pressure: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "brief_id": self.brief_id,
            "prompt": self.prompt,
            "author": self.author,
            "region": self.region,
            "requested_tags": self.requested_tags,
            "target_policy_pressure": self.target_policy_pressure,
        }


@dataclass(frozen=True)
class StudioValidationReport:
    passes: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {"passes": self.passes, "errors": self.errors, "warnings": self.warnings}


@dataclass(frozen=True)
class ScenarioStudioPlan:
    plan_id: str
    brief: ScenarioBrief
    environment_template_id: str
    environment_family: str
    behavior_template_id: str
    mutation: str
    asset_tags: list[str]
    ood_tags: list[str]
    memory_query: list[str]
    expected_failure_mode: str
    safe_behavior_principle: str
    quality_targets: dict[str, float | bool | str]
    provider: StudioProvider
    validation: StudioValidationReport
    logical_recipe: ScenarioRecipe

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "brief": self.brief.to_jsonable(),
            "environment_template_id": self.environment_template_id,
            "environment_family": self.environment_family,
            "behavior_template_id": self.behavior_template_id,
            "mutation": self.mutation,
            "asset_tags": self.asset_tags,
            "ood_tags": self.ood_tags,
            "memory_query": self.memory_query,
            "expected_failure_mode": self.expected_failure_mode,
            "safe_behavior_principle": self.safe_behavior_principle,
            "quality_targets": self.quality_targets,
            "provider": self.provider,
            "validation": self.validation.to_jsonable(),
            "logical_recipe": self.logical_recipe.to_jsonable(),
        }


@dataclass(frozen=True)
class ScenarioStudioCandidate:
    candidate_id: str
    plan_id: str
    variant_index: int
    random_seed: int
    compiled_recipe: ScenarioRecipe
    environment_recipe: EnvironmentRecipe
    behavior_plan: BehaviorPlan
    asset_requests: list[dict[str, Any]]
    carla_run_ready: bool
    alpamayo_package_ready: bool

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "plan_id": self.plan_id,
            "variant_index": self.variant_index,
            "random_seed": self.random_seed,
            "compiled_recipe": self.compiled_recipe.to_jsonable(),
            "environment_recipe": self.environment_recipe.to_jsonable(),
            "behavior_plan": self.behavior_plan.to_jsonable(),
            "asset_requests": self.asset_requests,
            "carla_run_ready": self.carla_run_ready,
            "alpamayo_package_ready": self.alpamayo_package_ready,
        }


@dataclass(frozen=True)
class DatasetCurationRecord:
    candidate_id: str
    curation_status: CurationStatus
    score: float
    gate_results: dict[str, bool | str | float | None]
    novelty_tags: list[str]
    evidence_paths: dict[str, str | None]
    model_eval_status: str
    why_keep: str
    next_action: str

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "curation_status": self.curation_status,
            "score": self.score,
            "gate_results": self.gate_results,
            "novelty_tags": self.novelty_tags,
            "evidence_paths": self.evidence_paths,
            "model_eval_status": self.model_eval_status,
            "why_keep": self.why_keep,
            "next_action": self.next_action,
        }


@dataclass(frozen=True)
class ScenarioStudioConfig:
    prompts: tuple[str, ...]
    seeds_path: Path = Path("tests/fixtures/fail2drive_like/seeds.json")
    catalog_path: Path | None = None
    output_root: Path = Path("artifacts/runs")
    run_id: str = "scenario-studio"
    count_per_prompt: int = 2
    severity: int = 3
    random_seed: int = 7
    provider: StudioProvider = "deterministic"


def compile_scenario_prompt(
    prompt: str,
    *,
    seed: int,
    catalog: Any | None = None,
) -> ScenarioStudioPlan:
    text = prompt.strip()
    if not text:
        raise ValueError("Scenario prompt is required.")
    lowered = text.lower()
    brief = ScenarioBrief(
        brief_id=f"brief-{seed:04d}-{_slug(text)[:48]}",
        prompt=text,
        region=_region(lowered),
        requested_tags=_requested_tags(lowered),
        target_policy_pressure=_policy_pressure(lowered),
    )
    environment_id, environment_family = _select_environment(lowered)
    behavior_id = _select_behavior(lowered)
    mutation = _select_mutation(lowered, environment_id, behavior_id)
    asset_tags = _asset_tags(lowered, environment_id)
    ood_tags = sorted(set([*_requested_tags(lowered), environment_family, behavior_id, mutation, *asset_tags]))
    memory_query = sorted(set([behavior_id, mutation, *_requested_tags(lowered), environment_family]))
    validation = validate_studio_plan_parts(
        prompt=prompt,
        environment_template_id=environment_id,
        behavior_template_id=behavior_id,
        memory_query=memory_query,
        recognized_any=bool(_matched_keywords(lowered)),
    )
    expected_failure = _expected_failure_mode(environment_id, behavior_id, lowered)
    safe_principle = _safe_behavior_principle(environment_id, behavior_id)
    logical_recipe = _logical_recipe(
        plan_id=f"studio-{seed:04d}-{_slug(text)[:48]}",
        mutation=mutation,
        environment_template_id=environment_id,
        behavior_id=behavior_id,
        asset_tags=asset_tags,
        ood_tags=ood_tags,
        memory_query=memory_query,
        expected_failure=expected_failure,
        safe_principle=safe_principle,
    )
    return ScenarioStudioPlan(
        plan_id=logical_recipe.recipe_id,
        brief=brief,
        environment_template_id=environment_id,
        environment_family=environment_family,
        behavior_template_id=behavior_id,
        mutation=mutation,
        asset_tags=asset_tags,
        ood_tags=ood_tags,
        memory_query=memory_query,
        expected_failure_mode=expected_failure,
        safe_behavior_principle=safe_principle,
        quality_targets={
            "min_duration_s": 45.0,
            "require_conflict": True,
            "require_road_alignment": True,
            "min_ood_stressor_count": 2,
        },
        provider="deterministic",
        validation=validation,
        logical_recipe=logical_recipe,
    )


def validate_studio_plan(plan: ScenarioStudioPlan) -> StudioValidationReport:
    return validate_studio_plan_parts(
        prompt=plan.brief.prompt,
        environment_template_id=plan.environment_template_id,
        behavior_template_id=plan.behavior_template_id,
        memory_query=plan.memory_query,
        recognized_any=plan.validation.passes or "unsupported_prompt" not in plan.validation.errors,
    )


def validate_studio_plan_parts(
    *,
    prompt: str,
    environment_template_id: str,
    behavior_template_id: str,
    memory_query: list[str],
    recognized_any: bool,
) -> StudioValidationReport:
    errors: list[str] = []
    warnings: list[str] = []
    if not recognized_any:
        errors.append("unsupported_prompt: no supported environment or behavior keywords detected")
    if environment_template_id not in _ENVIRONMENT_FAMILIES:
        errors.append(f"unknown_environment_template: {environment_template_id}")
    if behavior_template_id not in _BEHAVIOR_KINDS:
        errors.append(f"unknown_behavior_template: {behavior_template_id}")
    if not memory_query:
        errors.append("memory_query_empty")
    if len(prompt.split()) < 4:
        warnings.append("brief_is_short; add region, hazard, actor, or expected behavior for stronger generation")
    return StudioValidationReport(passes=not errors, errors=errors, warnings=warnings)


def expand_studio_plan(
    plan: ScenarioStudioPlan,
    *,
    count: int,
    random_seed: int,
    seeds: list[ScenarioSeed] | None = None,
    severity: int = 3,
) -> list[ScenarioStudioCandidate]:
    if count <= 0:
        raise ValueError("count must be positive.")
    seed_pool = seeds or [_default_seed(plan)]
    candidates: list[ScenarioStudioCandidate] = []
    for index in range(count):
        variant_seed = random_seed + index
        parent_seed = seed_pool[index % len(seed_pool)]
        environment = generate_environment_recipe(
            plan.environment_template_id,
            severity=severity,
            random_seed=variant_seed,
        )
        behavior = generate_behavior_variants(
            plan.behavior_template_id,
            count=1,
            random_seed=variant_seed,
            severity=severity,
        )[0]
        base_recipe = ScenarioRecipe(
            recipe_id=f"{plan.plan_id}-v{index:02d}",
            parent_seed_id=parent_seed.seed_id,
            mutation=plan.mutation,
            actors=[
                {
                    "actor_id": f"behavior_actor_{behavior.behavior_id}",
                    "kind": behavior.actor_kind,
                    "role": "dynamic_ood_actor",
                    "behavior_id": behavior.behavior_id,
                    "expected_pressure": behavior.expected_pressure,
                }
            ],
            environment={
                "studio_plan_id": plan.plan_id,
                "environment_template_id": plan.environment_template_id,
                "behavior_id": behavior.behavior_id,
                "behavior_tags": behavior.tags,
                "asset_tags": plan.asset_tags,
                "quality_targets": plan.quality_targets,
            },
            expected_failure_mode=plan.expected_failure_mode,
            memory_query=plan.memory_query,
            solvability_assumption=f"Safe behavior: {plan.safe_behavior_principle}",
            route_path=parent_seed.route_path,
        )
        compiled = attach_environment_to_recipe(base_recipe, environment)
        requests = [request.to_jsonable() for request in environment_to_asset_requests(environment)]
        candidates.append(
            ScenarioStudioCandidate(
                candidate_id=compiled.recipe_id,
                plan_id=plan.plan_id,
                variant_index=index,
                random_seed=variant_seed,
                compiled_recipe=compiled,
                environment_recipe=environment,
                behavior_plan=behavior,
                asset_requests=requests,
                carla_run_ready=plan.validation.passes,
                alpamayo_package_ready=False,
            )
        )
    return candidates


def score_studio_candidate(
    candidate: ScenarioStudioCandidate,
    existing_records: list[ScenarioCatalogRecord],
) -> DatasetCurationRecord:
    tags = sorted(
        set(
            candidate.compiled_recipe.memory_query
            + list(candidate.environment_recipe.tags)
            + list(candidate.behavior_plan.tags)
        )
    )
    compiles = candidate.carla_run_ready
    solvable = bool(candidate.compiled_recipe.solvability_assumption)
    ood_pressure = len(tags) >= 5
    duplicate = _is_duplicate(candidate, existing_records)
    evidence_ready = False
    model_value = False
    gate_results: dict[str, bool | str | float | None] = {
        "compiles": compiles,
        "solvable": solvable,
        "novel": not duplicate,
        "ood_pressure": ood_pressure,
        "evidence_complete": evidence_ready,
        "model_value": model_value,
        "stressor_count": float(len(tags)),
    }
    score = round(
        (0.20 if compiles else 0.0)
        + (0.20 if ood_pressure else 0.0)
        + (0.15 if not duplicate else 0.0)
        + (0.15 if solvable else 0.0)
        + (0.15 if evidence_ready else 0.0)
        + (0.15 if model_value else 0.0),
        4,
    )
    if not compiles:
        status: CurationStatus = "reject_invalid"
        next_action = "Revise prompt with a supported region, environment, actor behavior, or risk mechanism."
        why_keep = "Rejected because the prompt did not compile into a supported DriverX scenario."
    elif duplicate:
        status = "reject_duplicate"
        next_action = "Use a different behavior/environment combination or increase severity to create a novel case."
        why_keep = "Rejected because an equivalent behavior/environment family already exists in the catalog."
    else:
        status = "accept_partial"
        next_action = "Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory."
        why_keep = "Useful generated OOD candidate; it needs simulator/model evidence before final promotion."
    return DatasetCurationRecord(
        candidate_id=candidate.candidate_id,
        curation_status=status,
        score=score,
        gate_results=gate_results,
        novelty_tags=tags,
        evidence_paths={
            "video": None,
            "tracks": None,
            "alpamayo_baseline": None,
            "alpamayo_memory": None,
            "rag_comparison": None,
        },
        model_eval_status="not_run",
        why_keep=why_keep,
        next_action=next_action,
    )


def generate_studio_batch(config: ScenarioStudioConfig) -> dict[str, Any]:
    run_dir = prepare_run_dir(config.output_root, config.run_id)
    seeds = load_scenario_seeds(config.seeds_path)
    existing_records = _load_existing_records(config.catalog_path)
    plans = [
        compile_scenario_prompt(prompt, seed=config.random_seed + index)
        for index, prompt in enumerate(config.prompts)
    ]
    candidates: list[ScenarioStudioCandidate] = []
    curation: list[DatasetCurationRecord] = []
    for plan_index, plan in enumerate(plans):
        expanded = expand_studio_plan(
            plan,
            count=config.count_per_prompt,
            random_seed=config.random_seed + plan_index * 100,
            seeds=seeds,
            severity=config.severity,
        )
        candidates.extend(expanded)
        curation.extend(score_studio_candidate(candidate, existing_records) for candidate in expanded)
    payload = _batch_payload(run_dir, config, plans, candidates, curation)
    return write_scenario_studio_batch(run_dir, payload)


def load_scenario_studio_config(path: Path) -> ScenarioStudioConfig:
    raw = read_config_mapping(path)
    section = raw.get("scenario_studio", raw)
    if not isinstance(section, dict):
        raise ValueError("Config field 'scenario_studio' must be a mapping.")
    output = raw.get("output", {})
    output = output if isinstance(output, dict) else {}
    prompts = _prompts_from_config(section)
    if not prompts:
        raise ValueError("Scenario Studio config requires at least one prompt.")
    catalog_raw = section.get("catalog_path")
    provider = str(section.get("provider", "deterministic"))
    if provider not in {"deterministic", "llm"}:
        raise ValueError("Scenario Studio provider must be 'deterministic' or 'llm'.")
    return ScenarioStudioConfig(
        prompts=tuple(prompts),
        seeds_path=Path(str(section.get("seeds_path", "tests/fixtures/fail2drive_like/seeds.json"))),
        catalog_path=Path(str(catalog_raw)) if catalog_raw else None,
        output_root=Path(str(output.get("root", section.get("output_root", "artifacts/runs")))),
        run_id=str(output.get("run_id", section.get("run_id", "scenario-studio"))),
        count_per_prompt=max(1, int(section.get("count_per_prompt", 2))),
        severity=max(1, min(5, int(section.get("severity", 3)))),
        random_seed=int(section.get("random_seed", 7)),
        provider=provider,  # type: ignore[arg-type]
    )


def write_scenario_studio_batch(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "scenario_studio_batch.json"
    gallery_path = run_dir / "scenario_studio_gallery.md"
    recipes_path = run_dir / "scenario_studio_recipes.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    recipes_path.write_text(
        json.dumps([candidate["compiled_recipe"] for candidate in payload["candidates"]], indent=2),
        encoding="utf-8",
    )
    gallery_path.write_text(_gallery_markdown(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "gallery_path": str(gallery_path),
        "recipes_path": str(recipes_path),
    }


def _batch_payload(
    run_dir: Path,
    config: ScenarioStudioConfig,
    plans: list[ScenarioStudioPlan],
    candidates: list[ScenarioStudioCandidate],
    curation: list[DatasetCurationRecord],
) -> dict[str, Any]:
    return {
        "batch_id": run_dir.name,
        "prompt_count": len(config.prompts),
        "plan_count": len(plans),
        "candidate_count": len(candidates),
        "curation_counts": _status_counts(curation),
        "accepted_candidate_ids": [
            record.candidate_id
            for record in curation
            if record.curation_status in {"accept", "accept_partial"}
        ],
        "plans": [plan.to_jsonable() for plan in plans],
        "candidates": [candidate.to_jsonable() for candidate in candidates],
        "curation": [record.to_jsonable() for record in curation],
        "claim_boundaries": [
            "prompt_to_ood_compiler=true",
            "deterministic_reproducible_generation=true",
            "ai_scenario_authoring=false_without_provider_run",
            "closed_loop_carla_execution=false",
            "dataset_curation_heuristic=true",
        ],
    }


def _prompts_from_config(section: dict[str, Any]) -> list[str]:
    raw = section.get("prompts")
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item).strip()]
    if isinstance(raw, str) and raw.strip():
        return [item.strip() for item in raw.split("||") if item.strip()]
    prompt_path = section.get("prompt_path")
    if prompt_path:
        path = Path(str(prompt_path))
        return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    keyed = [
        str(value)
        for key, value in sorted(section.items())
        if key.startswith("prompt_") and str(value).strip()
    ]
    return keyed


def _load_existing_records(path: Path | None) -> list[ScenarioCatalogRecord]:
    if path is None or not path.exists():
        return []
    return load_scenario_catalog(path).records


def _is_duplicate(candidate: ScenarioStudioCandidate, records: list[ScenarioCatalogRecord]) -> bool:
    family = str(candidate.compiled_recipe.environment.get("environment_family", ""))
    behavior_id = candidate.behavior_plan.behavior_id
    for record in records:
        if record.behavior_id == behavior_id and family and family in record.environment_tags:
            return True
    return False


def _default_seed(plan: ScenarioStudioPlan) -> ScenarioSeed:
    return ScenarioSeed(
        seed_id=f"seed-{plan.plan_id}",
        source="generated",
        split="Generated",
        scenario_class=plan.environment_family,
        route_id="studio-route",
    )


def _logical_recipe(
    *,
    plan_id: str,
    mutation: str,
    environment_template_id: str,
    behavior_id: str,
    asset_tags: list[str],
    ood_tags: list[str],
    memory_query: list[str],
    expected_failure: str,
    safe_principle: str,
) -> ScenarioRecipe:
    return ScenarioRecipe(
        recipe_id=plan_id,
        parent_seed_id="studio-logical-seed",
        mutation=mutation,
        actors=[
            {
                "actor_id": f"logical_{behavior_id}",
                "kind": _BEHAVIOR_KINDS.get(behavior_id, "vehicle"),
                "role": "dynamic_ood_actor",
                "behavior_id": behavior_id,
            }
        ],
        environment={
            "environment_template_id": environment_template_id,
            "behavior_id": behavior_id,
            "asset_tags": asset_tags,
            "ood_tags": ood_tags,
        },
        expected_failure_mode=expected_failure,
        memory_query=memory_query,
        solvability_assumption=f"Safe behavior: {safe_principle}",
    )


def _select_environment(text: str) -> tuple[str, str]:
    if _has_any(text, ["school", "child", "children", "crossing", "school bag"]):
        return "school_zone_unstructured_crossing", "pedestrian_occlusion"
    if _has_any(text, ["market", "food cart", "vendor", "roadside", "hawker"]):
        return "roadside_market_occlusion", "regional_market"
    if _has_any(text, ["flood", "flooded", "waterlogged", "monsoon"]) or (
        "wet road" in text and "roadwork" not in text
    ):
        return "flooded_road", "weather_surface"
    if _has_any(text, ["night", "fog", "glare", "rain", "low visibility"]):
        return "night_rain_fog", "visibility"
    if _has_any(text, ["roadwork", "construction", "cone", "cones", "lane closure", "barrier"]):
        return "construction_lane_closure", "construction"
    if _has_any(text, ["visual-noise", "visual noise", "ufo", "billboard", "debris", "artifact"]):
        return "construction_lane_closure", "construction"
    if _has_any(text, ["malaysian", "motorbike", "motorcycle", "scooter", "dense traffic"]):
        return "dense_regional_traffic", "regional_traffic"
    return "dense_regional_traffic", "regional_traffic"


def _select_behavior(text: str) -> str:
    if _has_any(text, ["superman", "stunt", "low profile"]):
        return "stunt_motorcycle_proxy"
    if _has_any(text, ["u-turn", "u turn", "turn across"]):
        return "unsignaled_u_turn"
    if _has_any(text, ["door", "double parked", "double-parked", "swerve"]):
        return "double_parked_door_swerve"
    if _has_any(text, ["wrong way", "wrong-way", "opposing shoulder", "against traffic"]):
        return "wrong_way_shoulder_creep"
    if _has_any(text, ["motorbike", "motorcycle", "scooter", "filter", "lane split"]):
        return "motorcycle_filtering"
    if _has_any(text, ["sudden brake", "brakes", "hard brake", "lorry brake"]):
        return "sudden_brake"
    if _has_any(text, ["no signal", "cut in", "cuts in", "merge"]):
        return "no_signal_cut_in"
    if _has_any(text, ["right of way", "right-of-way", "pushes", "push ", "creep"]):
        return "informal_right_of_way_push"
    return "no_signal_cut_in"


def _select_mutation(text: str, environment_id: str, behavior_id: str) -> str:
    if _has_any(text, ["occlusion", "hidden", "parked van", "blocked view"]):
        return "occlusion"
    if _has_any(text, ["glare", "sign", "visual noise", "ufo", "artifact"]):
        return "visual_noise"
    if _has_any(text, ["block", "closure", "roadwork", "barrier"]):
        return "lane_blockage"
    if behavior_id in {"motorcycle_filtering", "stunt_motorcycle_proxy", "wrong_way_shoulder_creep"}:
        return "regional_driving_behavior"
    if environment_id in {"flooded_road", "school_zone_unstructured_crossing"}:
        return "obstacle_substitution"
    return "obstacle_substitution"


def _asset_tags(text: str, environment_id: str) -> list[str]:
    tags = list(_ENVIRONMENT_ASSET_TAGS.get(environment_id, ()))
    if _has_any(text, ["lorry", "truck"]):
        tags.append("lorry_proxy")
    if _has_any(text, ["ufo", "artifact"]):
        tags.append("irrelevant_visual_artifact")
    return sorted(set(tags))


def _requested_tags(text: str) -> list[str]:
    tags: list[str] = []
    keyword_tags = {
        "malaysian": "malaysian_driving",
        "wet": "wet_road",
        "rain": "rain",
        "monsoon": "monsoon",
        "roadwork": "roadwork",
        "construction": "construction",
        "motorbike": "motorcycle_filtering",
        "motorcycle": "motorcycle_filtering",
        "scooter": "motorcycle_filtering",
        "brake": "sudden_brake",
        "occlusion": "occlusion",
        "hidden": "occlusion",
        "school": "school_zone",
        "market": "roadside_market",
        "flood": "flood",
        "glare": "glare",
        "visual-noise": "visual_noise",
        "visual noise": "visual_noise",
        "ufo": "visual_noise",
        "billboard": "visual_noise",
        "debris": "debris",
        "night": "night",
        "wrong way": "wrong_way",
        "wrong-way": "wrong_way",
        "u-turn": "u_turn",
        "u turn": "u_turn",
    }
    for keyword, tag in keyword_tags.items():
        if keyword in text:
            tags.append(tag)
    return sorted(set(tags))


def _matched_keywords(text: str) -> list[str]:
    probes = [
        "malaysian",
        "roadwork",
        "construction",
        "motorbike",
        "motorcycle",
        "scooter",
        "brake",
        "occlusion",
        "school",
        "market",
        "flood",
        "night",
        "rain",
        "glare",
        "visual-noise",
        "visual noise",
        "ufo",
        "billboard",
        "debris",
        "wrong way",
        "wrong-way",
        "u-turn",
        "door",
        "double parked",
        "superman",
        "stunt",
    ]
    return [keyword for keyword in probes if keyword in text]


def _region(text: str) -> str | None:
    if "malaysian" in text or "motorbike" in text or "scooter" in text:
        return "malaysia"
    if "asian" in text:
        return "dense_asian_urban"
    return None


def _policy_pressure(text: str) -> str:
    if _has_any(text, ["motorbike", "motorcycle", "scooter"]):
        return "Predict lateral two-wheeler motion and keep clearance instead of assuming lane discipline."
    if _has_any(text, ["school", "child", "crossing"]):
        return "Creep around occlusion and yield to hidden pedestrian risk."
    if _has_any(text, ["flood", "wet", "rain"]):
        return "Slow for reduced traction and identify low-profile obstacles."
    return "Separate route-relevant hazards from harmless novelty and preserve a safe fallback."


def _expected_failure_mode(environment_id: str, behavior_id: str, text: str) -> str:
    return (
        f"Policy overfits normal lane-disciplined driving in `{environment_id}` while handling "
        f"`{behavior_id}`, causing late braking, unsafe lateral clearance, or overreaction to novelty."
    )


def _safe_behavior_principle(environment_id: str, behavior_id: str) -> str:
    if behavior_id in {"motorcycle_filtering", "stunt_motorcycle_proxy"}:
        return "slow early, keep lateral buffer, and avoid squeezing two-wheelers"
    if behavior_id == "sudden_brake":
        return "increase following gap and brake smoothly before closing distance"
    if environment_id == "school_zone_unstructured_crossing":
        return "creep around occlusion and yield before the hidden crossing point"
    if environment_id == "flooded_road":
        return "reduce speed, avoid low obstacles, and preserve a dry bypass when available"
    return "slow, yield, and choose the locally safest route around the hazard"


def _status_counts(records: list[DatasetCurationRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.curation_status] = counts.get(record.curation_status, 0) + 1
    return dict(sorted(counts.items()))


def _gallery_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Scenario Studio Gallery",
        "",
        f"- Batch: `{payload['batch_id']}`",
        f"- Prompts: `{payload['prompt_count']}`",
        f"- Candidates: `{payload['candidate_count']}`",
        f"- Curation counts: `{payload['curation_counts']}`",
        "",
        "## Generated Candidates",
        "",
        "| candidate | status | score | environment | behavior | next action |",
        "|---|---|---|---|---|---|",
    ]
    curation_by_id = {record["candidate_id"]: record for record in payload["curation"]}
    for candidate in payload["candidates"]:
        record = curation_by_id[candidate["candidate_id"]]
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(candidate["candidate_id"]),
                    _cell(record["curation_status"]),
                    _cell(record["score"]),
                    _cell(candidate["environment_recipe"]["template_id"]),
                    _cell(candidate["behavior_plan"]["behavior_id"]),
                    _cell(record["next_action"]),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Prompt Plans", ""])
    for plan in payload["plans"]:
        lines.append(f"### `{plan['plan_id']}`")
        lines.append("")
        lines.append(f"- Prompt: {plan['brief']['prompt']}")
        lines.append(f"- Environment: `{plan['environment_template_id']}`")
        lines.append(f"- Behavior: `{plan['behavior_template_id']}`")
        lines.append(f"- Memory query: `{', '.join(plan['memory_query'])}`")
        lines.append(f"- Safe behavior: {plan['safe_behavior_principle']}")
        if not plan["validation"]["passes"]:
            lines.append(f"- Validation errors: `{plan['validation']['errors']}`")
        lines.append("")
    lines.extend(["## Claim Boundaries", ""])
    for boundary in payload["claim_boundaries"]:
        lines.append(f"- `{boundary}`")
    lines.append("")
    return "\n".join(lines)


def _has_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|")


_ENVIRONMENT_FAMILIES = {
    "construction_lane_closure": "construction",
    "roadside_market_occlusion": "regional_market",
    "flooded_road": "weather_surface",
    "night_rain_fog": "visibility",
    "dense_regional_traffic": "regional_traffic",
    "school_zone_unstructured_crossing": "pedestrian_occlusion",
}

_ENVIRONMENT_ASSET_TAGS = {
    "construction_lane_closure": ("road_cones", "work_barrier", "debris"),
    "roadside_market_occlusion": ("food_cart", "market_crates", "shoulder_clutter"),
    "flooded_road": ("flood_barrier", "waterlogged_debris", "low_obstacle"),
    "night_rain_fog": ("reflective_sign", "glare_artifact"),
    "dense_regional_traffic": ("scooter_cluster", "shoulder_clutter"),
    "school_zone_unstructured_crossing": ("school_crossing_board", "parked_van", "dropped_school_bag"),
}

_BEHAVIOR_KINDS = {
    "no_signal_cut_in": "vehicle",
    "sudden_brake": "vehicle",
    "motorcycle_filtering": "motorcycle",
    "wrong_way_shoulder_creep": "vehicle",
    "informal_right_of_way_push": "vehicle",
    "stunt_motorcycle_proxy": "motorcycle",
    "double_parked_door_swerve": "vehicle",
    "unsignaled_u_turn": "vehicle",
}


__all__ = [
    "DatasetCurationRecord",
    "ScenarioBrief",
    "ScenarioStudioCandidate",
    "ScenarioStudioConfig",
    "ScenarioStudioPlan",
    "StudioValidationReport",
    "compile_scenario_prompt",
    "expand_studio_plan",
    "generate_studio_batch",
    "load_scenario_studio_config",
    "score_studio_candidate",
    "validate_studio_plan",
    "write_scenario_studio_batch",
]
