"""Map generated asset manifests onto stock CARLA prop blueprints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from driverx.assets.types import AssetManifest


@dataclass(frozen=True)
class CarlaObjectSpawnSpec:
    asset_id: str
    actor_ref: str
    blueprint_filter: str
    spawn_transform: dict[str, dict[str, float]]
    collision_proxy: dict[str, Any]
    semantic_tags: list[str]
    source_status: str
    coordinate_frame: str = "road_local"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "actor_ref": self.actor_ref,
            "blueprint_filter": self.blueprint_filter,
            "spawn_transform": self.spawn_transform,
            "coordinate_frame": self.coordinate_frame,
            "collision_proxy": self.collision_proxy,
            "semantic_tags": self.semantic_tags,
            "source_status": self.source_status,
        }


BLUEPRINT_BY_TAG: tuple[tuple[set[str], str], ...] = (
    ({"debris", "lane_obstacle", "unknown_object"}, "static.prop.dirtdebris01"),
    ({"barrier", "route_blockage", "flood", "construction"}, "static.prop.constructioncone"),
    ({"roadside_vendor", "occlusion", "regional_context"}, "static.prop.foodcart"),
    ({"pedestrian", "walker"}, "walker.pedestrian.*"),
    ({"motorcycle", "two_wheeler"}, "vehicle.kawasaki.ninja"),
)


def map_asset_to_carla_spawn(
    manifest: AssetManifest,
    *,
    index: int = 0,
) -> CarlaObjectSpawnSpec:
    """Convert a generated asset manifest into a stock CARLA spawn spec."""

    return CarlaObjectSpawnSpec(
        asset_id=manifest.asset_id,
        actor_ref=f"generated_asset_{_actor_safe(manifest.asset_id)}",
        blueprint_filter=_blueprint_for_manifest(manifest),
        spawn_transform=_transform_from_manifest(manifest, index=index),
        collision_proxy=dict(manifest.collision_proxy),
        semantic_tags=list(manifest.semantic_tags),
        source_status=manifest.status,
    )


def map_assets_to_carla_spawns(manifests: list[AssetManifest]) -> list[CarlaObjectSpawnSpec]:
    return [
        map_asset_to_carla_spawn(manifest, index=index)
        for index, manifest in enumerate(manifests)
        if manifest.status in {"planned", "generated"}
    ]


def validate_carla_asset_mappings(
    manifests: list[AssetManifest],
    blueprint_ids: list[str],
) -> dict[str, list[str]]:
    """Validate mapped stock CARLA blueprints against an available id list."""

    available = set(blueprint_ids)
    errors: dict[str, list[str]] = {}
    for manifest in manifests:
        if manifest.status not in {"planned", "generated"}:
            errors[manifest.asset_id] = [
                f"asset status {manifest.status!r} is not spawnable"
            ]
            continue
        spec = map_asset_to_carla_spawn(manifest)
        if not _blueprint_available(spec.blueprint_filter, available):
            errors.setdefault(manifest.asset_id, []).append(
                f"blueprint {spec.blueprint_filter!r} was not available"
            )
    return errors


def _blueprint_for_manifest(manifest: AssetManifest) -> str:
    metadata_blueprint = manifest.metadata.get("placeholder_carla_blueprint")
    if isinstance(metadata_blueprint, str) and metadata_blueprint:
        return metadata_blueprint
    tags = {tag.lower() for tag in manifest.semantic_tags}
    for expected_tags, blueprint in BLUEPRINT_BY_TAG:
        if tags & expected_tags:
            return blueprint
    return "static.prop.dirtdebris01"


def _transform_from_manifest(
    manifest: AssetManifest,
    *,
    index: int,
) -> dict[str, dict[str, float]]:
    placement = dict(manifest.intended_placement)
    x = _float_or_default(placement.get("x_m"), 12.0 + index * 4.0)
    y = _float_or_default(placement.get("y_m"), _default_y(placement, index))
    z = _float_or_default(placement.get("z_m"), 0.2)
    yaw = _float_or_default(placement.get("yaw_deg"), 0.0)
    return {
        "location": {"x": x, "y": y, "z": z},
        "rotation": {"pitch": 0.0, "yaw": yaw, "roll": 0.0},
    }


def _float_or_default(value: object, default: float) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _default_y(placement: dict[str, Any], index: int) -> float:
    relative_to = str(placement.get("relative_to", "ego_lane"))
    if relative_to == "curb":
        return -4.0
    if relative_to == "lane_center":
        return 0.0
    return 0.5 + index * 0.75


def _blueprint_available(blueprint_filter: str, available: set[str]) -> bool:
    if blueprint_filter.endswith("*"):
        return any(item.startswith(blueprint_filter[:-1]) for item in available)
    return blueprint_filter in available


def _actor_safe(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")


__all__ = [
    "BLUEPRINT_BY_TAG",
    "CarlaObjectSpawnSpec",
    "map_asset_to_carla_spawn",
    "map_assets_to_carla_spawns",
    "validate_carla_asset_mappings",
]
