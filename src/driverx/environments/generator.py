"""Deterministic environment recipe generation."""

from __future__ import annotations

import json
import random
import re
from dataclasses import replace
from pathlib import Path
from typing import Any

from driverx.assets.types import AssetRequest
from driverx.core.artifacts import prepare_run_dir
from driverx.core.config import read_config_mapping
from driverx.environments.library import load_environment_pack
from driverx.environments.types import (
    EnvironmentAssetLayout,
    EnvironmentRecipe,
    EnvironmentSuiteConfig,
    EnvironmentTemplate,
    RoadFrameHint,
)
from driverx.scenarios.types import ScenarioRecipe


def generate_environment_recipe(
    template_id: str,
    severity: int,
    random_seed: int,
    *,
    templates: list[EnvironmentTemplate] | None = None,
) -> EnvironmentRecipe:
    template = _template_by_id(template_id, templates or load_environment_pack())
    severity = max(1, min(5, severity))
    rng = random.Random(f"{template_id}:{severity}:{random_seed}")
    assets = [
        _vary_asset(asset, severity=severity, rng=rng, index=index)
        for index, asset in enumerate(template.assets)
    ]
    recipe_id = f"env-{_slug(template.template_id)}-s{severity}-{random_seed:04d}"
    return EnvironmentRecipe(
        recipe_id=recipe_id,
        template_id=template.template_id,
        family=template.family,
        severity=severity,
        random_seed=random_seed,
        tags=sorted(set([*template.tags, f"severity_{severity}"])),
        weather=_scale_environment_values(template.weather, severity=severity),
        lighting=dict(template.lighting),
        traffic=_scale_environment_values(template.traffic, severity=severity),
        assets=assets,
        expected_policy_pressure=template.expected_policy_pressure,
        meshy_prompts=list(template.meshy_prompts),
    )


def generate_environment_suite(
    template_ids: tuple[str, ...],
    *,
    severity: int,
    count: int,
    random_seed: int,
    templates: list[EnvironmentTemplate] | None = None,
) -> list[EnvironmentRecipe]:
    if count <= 0:
        raise ValueError("count must be positive.")
    available = templates or load_environment_pack()
    selected = template_ids or tuple(template.template_id for template in available)
    recipes: list[EnvironmentRecipe] = []
    for index in range(count):
        template_id = selected[index % len(selected)]
        recipes.append(
            generate_environment_recipe(
                template_id,
                severity=severity,
                random_seed=random_seed + index,
                templates=available,
            )
        )
    return recipes


def attach_environment_to_recipe(
    recipe: ScenarioRecipe,
    environment: EnvironmentRecipe,
) -> ScenarioRecipe:
    merged_environment = {
        **recipe.environment,
        "environment_recipe_id": environment.recipe_id,
        "environment_template_id": environment.template_id,
        "environment_family": environment.family,
        "environment_tags": environment.tags,
        "weather": environment.weather,
        "lighting": environment.lighting,
        "traffic": environment.traffic,
        "generated_asset_ids": [
            *[str(item) for item in list(recipe.environment.get("generated_asset_ids", []))],
            *[asset.asset_id for asset in environment.assets],
        ],
        "meshy_prompts": environment.meshy_prompts,
    }
    actors = [
        *recipe.actors,
        *[
            {
                "actor_id": f"environment_asset_{_slug(asset.asset_id)}",
                "kind": "static_asset",
                "asset_id": asset.asset_id,
                "role": asset.role,
                "placement": asset.base_placement,
            }
            for asset in environment.assets
        ],
    ]
    return ScenarioRecipe(
        recipe_id=recipe.recipe_id,
        parent_seed_id=recipe.parent_seed_id,
        mutation=recipe.mutation,
        actors=actors,
        environment=merged_environment,
        expected_failure_mode=(
            f"{recipe.expected_failure_mode} Environment pressure: "
            f"{environment.expected_policy_pressure}"
        ),
        memory_query=[*recipe.memory_query, *environment.tags],
        solvability_assumption=recipe.solvability_assumption,
        route_path=recipe.route_path,
    )


def environment_to_asset_requests(
    recipe: EnvironmentRecipe,
    road_frame_hint: RoadFrameHint | None = None,
) -> list[AssetRequest]:
    hint = road_frame_hint or RoadFrameHint()
    requests: list[AssetRequest] = []
    for asset in recipe.assets:
        placement = _road_adjusted_placement(asset.base_placement, hint)
        requests.append(
            AssetRequest(
                asset_id=f"{recipe.recipe_id}-{asset.asset_id}",
                prompt=asset.prompt,
                semantic_tags=list(asset.semantic_tags),
                dimensions_m=dict(asset.dimensions_m),
                collision_proxy=dict(asset.collision_proxy),
                intended_placement=placement,
                license="generated-for-0xdriver-demo",
                source_recipe_id=recipe.recipe_id,
                provider="dry_run",
            )
        )
    return requests


def environment_to_carla_weather(recipe: EnvironmentRecipe) -> dict[str, float | str]:
    return dict(recipe.weather)


def run_environment_forge(config: EnvironmentSuiteConfig) -> dict[str, Any]:
    run_dir = prepare_run_dir(config.output_root, config.run_id)
    recipes = generate_environment_suite(
        config.template_ids,
        severity=config.severity,
        count=config.count,
        random_seed=config.random_seed,
    )
    return write_environment_suite_report(recipes, run_dir)


def load_environment_suite_config(path: Path) -> EnvironmentSuiteConfig:
    raw = read_config_mapping(path)
    section = raw.get("environment", raw)
    if not isinstance(section, dict):
        raise ValueError("Config field 'environment' must be a mapping.")
    return EnvironmentSuiteConfig(
        template_ids=_csv_tuple(
            section.get("template_ids"),
            (
                "construction_lane_closure",
                "roadside_market_occlusion",
                "flooded_road",
                "night_rain_fog",
                "dense_regional_traffic",
                "school_zone_unstructured_crossing",
            ),
        ),
        severity=max(1, min(5, int(section.get("severity", 3)))),
        count=max(1, int(section.get("count", 6))),
        random_seed=int(section.get("random_seed", 7)),
        output_root=Path(str(_mapping(raw.get("output")).get("root", section.get("output_root", "artifacts/runs")))),
        run_id=str(_mapping(raw.get("output")).get("run_id", section.get("run_id", "environment-forge"))),
    )


def write_environment_suite_report(
    recipes: list[EnvironmentRecipe],
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    recipes_path = output_dir / "environment_recipes.json"
    summary_path = output_dir / "environment_suite_summary.json"
    report_path = output_dir / "environment_suite_report.md"
    asset_requests = [
        request
        for recipe in recipes
        for request in environment_to_asset_requests(recipe)
    ]
    payload = {
        "num_recipes": len(recipes),
        "num_asset_requests": len(asset_requests),
        "families": sorted({recipe.family for recipe in recipes}),
        "tags": sorted({tag for recipe in recipes for tag in recipe.tags}),
        "recipes": [recipe.to_jsonable() for recipe in recipes],
        "asset_requests": [request.to_jsonable() for request in asset_requests],
        "recipes_path": str(recipes_path),
        "summary_path": str(summary_path),
        "report_path": str(report_path),
    }
    recipes_path.write_text(
        json.dumps([recipe.to_jsonable() for recipe in recipes], indent=2),
        encoding="utf-8",
    )
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_environment_markdown(payload), encoding="utf-8")
    return payload


def _template_by_id(template_id: str, templates: list[EnvironmentTemplate]) -> EnvironmentTemplate:
    for template in templates:
        if template.template_id == template_id:
            return template
    raise ValueError(f"Unknown environment template_id: {template_id}")


def _vary_asset(
    asset: EnvironmentAssetLayout,
    *,
    severity: int,
    rng: random.Random,
    index: int,
) -> EnvironmentAssetLayout:
    placement = dict(asset.base_placement)
    lateral_jitter = rng.uniform(-0.25, 0.25) * severity
    forward_jitter = rng.uniform(-0.8, 0.8) * severity
    placement["x_m"] = round(float(placement.get("x_m", 12.0 + index * 4.0)) + forward_jitter, 3)
    placement["y_m"] = round(float(placement.get("y_m", 0.0)) + lateral_jitter, 3)
    placement["yaw_deg"] = round(float(placement.get("yaw_deg", 0.0)) + rng.uniform(-4.0, 4.0) * severity, 3)
    return replace(asset, base_placement=placement)


def _scale_environment_values(
    values: dict[str, float | str],
    *,
    severity: int,
) -> dict[str, float | str]:
    scaled: dict[str, float | str] = {}
    multiplier = 0.7 + severity * 0.1
    for key, value in values.items():
        if isinstance(value, (int, float)):
            if key in {"density_multiplier", "target_speed_multiplier"}:
                scaled[key] = round(float(value), 4)
            else:
                scaled[key] = round(min(100.0, max(0.0, float(value) * multiplier)), 4)
        else:
            scaled[key] = value
    return scaled


def _road_adjusted_placement(
    placement: dict[str, Any],
    hint: RoadFrameHint,
) -> dict[str, Any]:
    adjusted = dict(placement)
    relative_to = str(adjusted.get("relative_to", "ego_lane"))
    if "y_m" not in adjusted:
        if relative_to == "curb":
            adjusted["y_m"] = hint.right_shoulder_y_m
        elif relative_to == "left_adjacent_lane":
            adjusted["y_m"] = hint.left_adjacent_lane_y_m
        else:
            adjusted["y_m"] = 0.0
    adjusted.setdefault("coordinate_frame", "road_local")
    adjusted.setdefault("surface", "road")
    return adjusted


def _environment_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Environment Forge",
        "",
        f"- environment_recipes: `{payload.get('num_recipes')}`",
        f"- asset_requests: `{payload.get('num_asset_requests')}`",
        f"- families: `{', '.join(list(payload.get('families', [])))}`",
        "",
        "| recipe | family | severity | assets | pressure |",
        "|---|---|---|---|---|",
    ]
    for recipe in list(payload.get("recipes", [])):
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(recipe.get("recipe_id")),
                    _cell(recipe.get("family")),
                    _cell(recipe.get("severity")),
                    _cell(len(list(recipe.get("assets", [])))),
                    _cell(recipe.get("expected_policy_pressure")),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _csv_tuple(value: object, default: tuple[str, ...]) -> tuple[str, ...]:
    if value in (None, ""):
        return default
    if isinstance(value, (list, tuple)):
        items = tuple(str(item).strip() for item in value if str(item).strip())
    else:
        items = tuple(item.strip() for item in str(value).split(",") if item.strip())
    return items or default


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _cell(value: object) -> str:
    return "" if value is None else str(value).replace("|", "\\|")


__all__ = [
    "attach_environment_to_recipe",
    "environment_to_asset_requests",
    "environment_to_carla_weather",
    "generate_environment_recipe",
    "generate_environment_suite",
    "load_environment_suite_config",
    "run_environment_forge",
    "write_environment_suite_report",
]
