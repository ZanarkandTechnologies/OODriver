"""Quality checks for generated asset artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from driverx.assets.pipeline import validate_asset_manifest
from driverx.assets.types import AssetManifest


@dataclass(frozen=True)
class AssetQualityReport:
    asset_id: str
    passes: bool
    mesh_path_exists: bool
    mesh_format: str | None
    thumbnail_path: str | None
    dimensions_match: bool
    collision_proxy_valid: bool
    license_present: bool
    blockers: list[str]

    def to_jsonable(self) -> dict[str, object]:
        return {
            "asset_id": self.asset_id,
            "passes": self.passes,
            "mesh_path_exists": self.mesh_path_exists,
            "mesh_format": self.mesh_format,
            "thumbnail_path": self.thumbnail_path,
            "dimensions_match": self.dimensions_match,
            "collision_proxy_valid": self.collision_proxy_valid,
            "license_present": self.license_present,
            "blockers": self.blockers,
        }


def validate_generated_asset_artifact(manifest: AssetManifest) -> AssetQualityReport:
    blockers = validate_asset_manifest(manifest)
    mesh_path = Path(manifest.local_path).expanduser() if manifest.local_path else None
    mesh_path_exists = bool(mesh_path and mesh_path.exists())
    mesh_format = mesh_path.suffix.lower().lstrip(".") if mesh_path else None
    if not mesh_path_exists:
        blockers.append(f"{manifest.asset_id}: generated mesh file is missing")
    if mesh_format not in {"obj", "glb", "gltf", "fbx"}:
        blockers.append(f"{manifest.asset_id}: unsupported mesh format {mesh_format!r}")
    thumbnail = manifest.metadata.get("thumbnail_path")
    thumbnail_path = str(thumbnail) if isinstance(thumbnail, str) and thumbnail else None
    collision_proxy_valid = not any("collision_proxy" in item for item in blockers)
    dimensions_match = not any("dimensions_m" in item for item in blockers)
    license_present = bool(manifest.license)
    if not license_present:
        blockers.append(f"{manifest.asset_id}: license is missing")
    return AssetQualityReport(
        asset_id=manifest.asset_id,
        passes=not blockers,
        mesh_path_exists=mesh_path_exists,
        mesh_format=mesh_format,
        thumbnail_path=thumbnail_path,
        dimensions_match=dimensions_match,
        collision_proxy_valid=collision_proxy_valid,
        license_present=license_present,
        blockers=blockers,
    )


__all__ = ["AssetQualityReport", "validate_generated_asset_artifact"]
