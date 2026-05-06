"""Generated asset planning for OOD scenario novelty."""

from driverx.assets.pipeline import (
    attach_assets_to_recipes,
    default_asset_requests,
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
from driverx.assets.types import AssetManifest, AssetProviderName, AssetRequest

__all__ = [
    "AssetManifest",
    "AssetProviderName",
    "AssetRequest",
    "CarlaObjectSpawnSpec",
    "attach_assets_to_recipes",
    "default_asset_requests",
    "generate_assets_dry_run",
    "generate_assets_with_provider",
    "map_asset_to_carla_spawn",
    "map_assets_to_carla_spawns",
    "validate_asset_manifest",
    "validate_asset_manifests",
    "validate_carla_asset_mappings",
    "write_asset_plan",
]
