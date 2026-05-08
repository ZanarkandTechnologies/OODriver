"""CARLA generated-asset registry and blueprint resolution."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.assets.carla_mapping import map_asset_to_carla_spawn
from driverx.assets.types import AssetManifest


@dataclass(frozen=True)
class CarlaBlueprintResolution:
    asset_id: str
    blueprint_filter: str
    custom_asset: bool
    stock_proxy: bool
    claim_boundary: str

    def to_jsonable(self) -> dict[str, object]:
        return {
            "asset_id": self.asset_id,
            "blueprint_filter": self.blueprint_filter,
            "custom_asset": self.custom_asset,
            "stock_proxy": self.stock_proxy,
            "claim_boundary": self.claim_boundary,
        }


def expected_generated_blueprint_id(asset_id: str) -> str:
    clean = "".join(ch if ch.isalnum() else "_" for ch in asset_id.lower()).strip("_")
    return f"driverx.generated.{clean or 'asset'}"


def build_carla_asset_registry(
    manifests: list[AssetManifest],
    *,
    installed_blueprints: list[str] | None = None,
) -> dict[str, Any]:
    installed = set(installed_blueprints or [])
    entries: list[dict[str, Any]] = []
    for manifest in manifests:
        expected = expected_generated_blueprint_id(manifest.asset_id)
        fallback = map_asset_to_carla_spawn(manifest).blueprint_filter
        is_installed = expected in installed
        entries.append(
            {
                "asset_id": manifest.asset_id,
                "mesh_path": manifest.local_path,
                "expected_blueprint_id": expected,
                "installed": is_installed,
                "fallback_blueprint": fallback,
                "import_status": "installed" if is_installed else "planned",
                "claim_boundary": (
                    "custom_asset_imported_in_carla=true"
                    if is_installed
                    else "custom_asset_imported_in_carla=false; stock_proxy_fallback=true"
                ),
            }
        )
    return {
        "schema_version": "oodrive.carla_asset_registry.v1",
        "entries": entries,
        "installed_blueprint_count": sum(1 for entry in entries if entry["installed"]),
        "stock_proxy_fallback_count": sum(1 for entry in entries if not entry["installed"]),
        "claim_boundaries": sorted({str(entry["claim_boundary"]) for entry in entries}),
    }


def write_carla_asset_registry(run_dir: Path, registry: dict[str, Any]) -> dict[str, str]:
    path = run_dir / "carla_asset_registry.json"
    report_path = run_dir / "carla_asset_registry.md"
    path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    report_path.write_text(_registry_markdown(registry), encoding="utf-8")
    return {"json_path": str(path), "report_path": str(report_path)}


def load_carla_asset_registry(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"CARLA asset registry must be a JSON object: {path}")
    return payload


def resolve_carla_blueprint_for_asset(
    manifest: AssetManifest,
    registry: dict[str, Any] | None,
) -> CarlaBlueprintResolution:
    if registry:
        for entry in list(registry.get("entries", [])):
            if not isinstance(entry, dict):
                continue
            if str(entry.get("asset_id")) != manifest.asset_id:
                continue
            if entry.get("installed") is True and entry.get("expected_blueprint_id"):
                return CarlaBlueprintResolution(
                    asset_id=manifest.asset_id,
                    blueprint_filter=str(entry["expected_blueprint_id"]),
                    custom_asset=True,
                    stock_proxy=False,
                    claim_boundary="custom_asset_imported_in_carla=true",
                )
            fallback = str(entry.get("fallback_blueprint") or map_asset_to_carla_spawn(manifest).blueprint_filter)
            return CarlaBlueprintResolution(
                asset_id=manifest.asset_id,
                blueprint_filter=fallback,
                custom_asset=False,
                stock_proxy=True,
                claim_boundary="custom_asset_imported_in_carla=false; stock_proxy_fallback=true",
            )
    return CarlaBlueprintResolution(
        asset_id=manifest.asset_id,
        blueprint_filter=map_asset_to_carla_spawn(manifest).blueprint_filter,
        custom_asset=False,
        stock_proxy=True,
        claim_boundary="custom_asset_imported_in_carla=false; stock_proxy_fallback=true",
    )


def _registry_markdown(registry: dict[str, Any]) -> str:
    lines = [
        "# CARLA Asset Registry",
        "",
        f"- installed generated blueprints: {registry.get('installed_blueprint_count', 0)}",
        f"- stock proxy fallbacks: {registry.get('stock_proxy_fallback_count', 0)}",
        "",
        "| asset | blueprint | installed | fallback |",
        "| --- | --- | --- | --- |",
    ]
    for entry in list(registry.get("entries", [])):
        if isinstance(entry, dict):
            lines.append(
                f"| {entry.get('asset_id')} | `{entry.get('expected_blueprint_id')}` | "
                f"{entry.get('installed')} | `{entry.get('fallback_blueprint')}` |"
            )
    return "\n".join(lines) + "\n"


__all__ = [
    "CarlaBlueprintResolution",
    "build_carla_asset_registry",
    "expected_generated_blueprint_id",
    "load_carla_asset_registry",
    "resolve_carla_blueprint_for_asset",
    "write_carla_asset_registry",
]
