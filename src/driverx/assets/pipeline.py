"""Generated asset planning and provider readiness checks."""

from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

from driverx.assets.types import AssetManifest, AssetProviderName, AssetRequest
from driverx.scenarios import ScenarioRecipe


def default_asset_requests() -> list[AssetRequest]:
    return [
        AssetRequest(
            asset_id="asset-fallen-cargo-sack",
            prompt=(
                "weathered blue construction cargo sack lying partly in a driving lane, "
                "low-poly game-ready mesh, realistic road scale"
            ),
            semantic_tags=["debris", "construction", "lane_obstacle"],
            dimensions_m={"length": 1.4, "width": 0.8, "height": 0.5},
            collision_proxy={"kind": "box", "length": 1.4, "width": 0.8, "height": 0.5},
            intended_placement={"surface": "road", "relative_to": "ego_lane", "x_m": 22.0, "y_m": 0.4},
            license="generated-for-0xdriver-demo",
        ),
        AssetRequest(
            asset_id="asset-roadside-food-cart",
            prompt=(
                "small Malaysian roadside food cart with umbrella wheels and metal counter, "
                "static prop, game-ready mesh"
            ),
            semantic_tags=["roadside_vendor", "occlusion", "regional_context"],
            dimensions_m={"length": 2.2, "width": 1.2, "height": 2.0},
            collision_proxy={"kind": "box", "length": 2.2, "width": 1.2, "height": 2.0},
            intended_placement={"surface": "shoulder", "relative_to": "curb", "x_m": 14.0, "y_m": -4.0},
            license="generated-for-0xdriver-demo",
        ),
        AssetRequest(
            asset_id="asset-reflective-flood-barrier",
            prompt=(
                "portable reflective flood barrier across part of a road after heavy rain, "
                "orange and white, game-ready mesh"
            ),
            semantic_tags=["flood", "barrier", "route_blockage", "weather"],
            dimensions_m={"length": 3.0, "width": 0.35, "height": 0.7},
            collision_proxy={"kind": "box", "length": 3.0, "width": 0.35, "height": 0.7},
            intended_placement={"surface": "road", "relative_to": "lane_center", "x_m": 18.0, "y_m": -0.2},
            license="generated-for-0xdriver-demo",
        ),
    ]


def generate_assets_dry_run(requests: list[AssetRequest]) -> list[AssetManifest]:
    manifests: list[AssetManifest] = []
    for request in requests:
        manifests.append(
            AssetManifest.from_request(
                replace(request, provider="dry_run"),
                status="planned",
                local_path=f"generated_assets/{request.asset_id}.glb",
                metadata={
                    "dry_run": True,
                    "placeholder_carla_blueprint": _placeholder_blueprint(request.semantic_tags),
                    "notes": "Manifest only; no mesh was generated in local dry-run mode.",
                },
            )
        )
    return manifests


def generate_assets_with_provider(
    requests: list[AssetRequest],
    provider: AssetProviderName,
    *,
    api_key: str | None = None,
) -> list[AssetManifest]:
    if provider == "dry_run":
        return generate_assets_dry_run(requests)
    if provider != "meshy":
        raise ValueError(f"Unsupported asset provider: {provider}")
    key = api_key or os.environ.get("MESHY_API_KEY")
    if not key:
        guidance = (
            "Set MESHY_API_KEY and rerun plan-assets --provider meshy. "
            "Live generation is intentionally disabled without credentials."
        )
        return [
            AssetManifest.from_request(
                replace(request, provider="meshy"),
                status="blocked",
                setup_guidance=guidance,
                metadata={"missing_secret": "MESHY_API_KEY"},
            )
            for request in requests
        ]
    return [
        AssetManifest.from_request(
            replace(request, provider="meshy"),
            status="blocked",
            setup_guidance=(
                "MESHY_API_KEY is present, but live Meshy submission is not implemented in TASK-012. "
                "Use this manifest contract for the TASK-012 follow-up provider."
            ),
            metadata={"api_key_present": True},
        )
        for request in requests
    ]


def validate_asset_manifest(manifest: AssetManifest) -> list[str]:
    errors: list[str] = []
    if not manifest.asset_id:
        errors.append("asset_id is required")
    if not manifest.prompt:
        errors.append(f"{manifest.asset_id}: prompt is required")
    if not manifest.semantic_tags:
        errors.append(f"{manifest.asset_id}: semantic_tags are required")
    if not manifest.license:
        errors.append(f"{manifest.asset_id}: license is required")
    for key in ("length", "width", "height"):
        value = manifest.dimensions_m.get(key)
        if value is None or value <= 0.0:
            errors.append(f"{manifest.asset_id}: dimensions_m.{key} must be positive")
    proxy_kind = str(manifest.collision_proxy.get("kind", ""))
    if proxy_kind not in {"box", "cylinder", "sphere"}:
        errors.append(f"{manifest.asset_id}: collision_proxy.kind is unsupported or missing")
    for key in ("length", "width", "height"):
        if proxy_kind == "box":
            value = manifest.collision_proxy.get(key)
            if value is None or float(value) <= 0.0:
                errors.append(f"{manifest.asset_id}: collision_proxy.{key} must be positive")
    if not manifest.intended_placement:
        errors.append(f"{manifest.asset_id}: intended_placement is required")
    return errors


def validate_asset_manifests(manifests: list[AssetManifest]) -> dict[str, list[str]]:
    return {
        manifest.asset_id: errors
        for manifest in manifests
        if (errors := validate_asset_manifest(manifest))
    }


def attach_assets_to_recipes(
    recipes: list[ScenarioRecipe],
    manifests: list[AssetManifest],
) -> list[ScenarioRecipe]:
    if not manifests:
        return recipes
    valid_asset_ids = [
        manifest.asset_id
        for manifest in manifests
        if manifest.status in {"planned", "generated"} and not validate_asset_manifest(manifest)
    ]
    if not valid_asset_ids:
        return recipes
    updated: list[ScenarioRecipe] = []
    for index, recipe in enumerate(recipes):
        asset_id = valid_asset_ids[index % len(valid_asset_ids)]
        environment = dict(recipe.environment)
        existing_ids = [str(item) for item in list(environment.get("generated_asset_ids", []))]
        environment["generated_asset_ids"] = [*existing_ids, asset_id]
        actors = [
            *recipe.actors,
            {
                "actor_id": f"generated_asset_{asset_id}",
                "kind": "static_asset",
                "asset_id": asset_id,
                "role": "ood_artifact",
            },
        ]
        updated.append(
            ScenarioRecipe(
                recipe_id=recipe.recipe_id,
                parent_seed_id=recipe.parent_seed_id,
                mutation=recipe.mutation,
                actors=actors,
                environment=environment,
                expected_failure_mode=recipe.expected_failure_mode,
                memory_query=[*recipe.memory_query, asset_id],
                solvability_assumption=recipe.solvability_assumption,
                route_path=recipe.route_path,
            )
        )
    return updated


def write_asset_plan(
    run_dir: Path,
    manifests: list[AssetManifest],
    recipes: list[ScenarioRecipe] | None = None,
) -> dict[str, object]:
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "asset_manifests.json"
    summary_path = run_dir / "asset_summary.json"
    report_path = run_dir / "asset_report.md"
    manifest_path.write_text(
        json.dumps([manifest.to_jsonable() for manifest in manifests], indent=2),
        encoding="utf-8",
    )
    validation_errors = validate_asset_manifests(manifests)
    summary: dict[str, object] = {
        "num_assets": len(manifests),
        "status_counts": _status_counts(manifests),
        "validation_errors": validation_errors,
        "manifest_path": str(manifest_path),
        "summary_path": str(summary_path),
        "report_path": str(report_path),
    }
    if recipes is not None:
        recipe_path = run_dir / "asset_augmented_recipes.json"
        recipe_path.write_text(
            json.dumps([recipe.to_jsonable() for recipe in recipes], indent=2),
            encoding="utf-8",
        )
        summary["recipe_path"] = str(recipe_path)
        summary["num_recipes"] = len(recipes)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path.write_text(_asset_markdown(manifests, validation_errors, recipes), encoding="utf-8")
    return summary


def _status_counts(manifests: list[AssetManifest]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for manifest in manifests:
        counts[manifest.status] = counts.get(manifest.status, 0) + 1
    return counts


def _placeholder_blueprint(tags: list[str]) -> str:
    lowered = {tag.lower() for tag in tags}
    if "barrier" in lowered:
        return "static.prop.constructioncone"
    if "roadside_vendor" in lowered:
        return "static.prop.foodcart"
    return "static.prop.dirtdebris01"


def _asset_markdown(
    manifests: list[AssetManifest],
    validation_errors: dict[str, list[str]],
    recipes: list[ScenarioRecipe] | None,
) -> str:
    lines = ["# Asset Plan", "", f"- Assets: `{len(manifests)}`"]
    lines.append(f"- Validation failures: `{len(validation_errors)}`")
    if recipes is not None:
        lines.append(f"- Asset-augmented recipes: `{len(recipes)}`")
    lines.append("")
    for manifest in manifests:
        lines.extend(
            [
                f"## {manifest.asset_id}",
                "",
                f"- provider: `{manifest.provider}`",
                f"- status: `{manifest.status}`",
                f"- tags: `{', '.join(manifest.semantic_tags)}`",
                f"- license: `{manifest.license}`",
                f"- dimensions_m: `{manifest.dimensions_m}`",
                f"- collision_proxy: `{manifest.collision_proxy}`",
            ]
        )
        if manifest.setup_guidance:
            lines.append(f"- setup_guidance: {manifest.setup_guidance}")
        if manifest.asset_id in validation_errors:
            lines.append(f"- validation_errors: `{validation_errors[manifest.asset_id]}`")
        lines.append("")
    return "\n".join(lines)


__all__ = [
    "attach_assets_to_recipes",
    "default_asset_requests",
    "generate_assets_dry_run",
    "generate_assets_with_provider",
    "validate_asset_manifest",
    "validate_asset_manifests",
    "write_asset_plan",
]
