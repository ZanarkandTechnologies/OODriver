"""Generated asset planning for OOD scenario novelty."""

from driverx.assets.pipeline import (
    attach_assets_to_recipes,
    default_asset_requests,
    environment_recipe_to_asset_requests,
    generate_assets_dry_run,
    generate_assets_with_provider,
    validate_asset_manifest,
    validate_asset_manifests,
    write_asset_plan,
)
from driverx.assets.carla_mapping import (
    CarlaObjectSpawnSpec,
    map_asset_to_carla_spawn,
    map_assets_to_carla_spawns,
    validate_carla_asset_mappings,
)
from driverx.assets.carla_registry import (
    build_carla_asset_registry,
    load_carla_asset_registry,
    resolve_carla_blueprint_for_asset,
    write_carla_asset_registry,
)
from driverx.assets.quality import AssetQualityReport, validate_generated_asset_artifact
from driverx.assets.types import AssetManifest, AssetProviderName, AssetRequest

__all__ = [
    "AssetQualityReport",
    "AssetManifest",
    "AssetProviderName",
    "AssetRequest",
    "CarlaObjectSpawnSpec",
    "attach_assets_to_recipes",
    "build_carla_asset_registry",
    "default_asset_requests",
    "environment_recipe_to_asset_requests",
    "generate_assets_dry_run",
    "generate_assets_with_provider",
    "load_carla_asset_registry",
    "map_asset_to_carla_spawn",
    "map_assets_to_carla_spawns",
    "resolve_carla_blueprint_for_asset",
    "validate_asset_manifest",
    "validate_asset_manifests",
    "validate_carla_asset_mappings",
    "validate_generated_asset_artifact",
    "write_carla_asset_registry",
    "write_asset_plan",
]
