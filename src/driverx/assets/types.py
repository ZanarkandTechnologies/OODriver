"""Types for generated OOD assets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

AssetProviderName = Literal["dry_run", "local_procedural", "meshy", "external_manifest", "external_blocked"]
AssetStatus = Literal["planned", "blocked", "pending", "generated", "qa_failed"]
CollisionProxyKind = Literal["box", "cylinder", "sphere"]


@dataclass(frozen=True)
class AssetRequest:
    asset_id: str
    prompt: str
    semantic_tags: list[str]
    dimensions_m: dict[str, float]
    collision_proxy: dict[str, Any]
    intended_placement: dict[str, Any]
    license: str
    source_recipe_id: str | None = None
    provider: AssetProviderName = "dry_run"

    def __post_init__(self) -> None:
        if not self.asset_id:
            raise ValueError("AssetRequest asset_id is required.")
        if not self.prompt:
            raise ValueError("AssetRequest prompt is required.")

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "prompt": self.prompt,
            "semantic_tags": self.semantic_tags,
            "dimensions_m": self.dimensions_m,
            "collision_proxy": self.collision_proxy,
            "intended_placement": self.intended_placement,
            "license": self.license,
            "source_recipe_id": self.source_recipe_id,
            "provider": self.provider,
        }

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "AssetRequest":
        return cls(
            asset_id=str(payload["asset_id"]),
            prompt=str(payload["prompt"]),
            semantic_tags=[str(tag) for tag in list(payload.get("semantic_tags", []))],
            dimensions_m={
                str(key): float(value)
                for key, value in dict(payload.get("dimensions_m", {})).items()
            },
            collision_proxy=dict(payload.get("collision_proxy", {})),
            intended_placement=dict(payload.get("intended_placement", {})),
            license=str(payload.get("license", "")),
            source_recipe_id=(
                str(payload["source_recipe_id"])
                if payload.get("source_recipe_id") is not None
                else None
            ),
            provider=str(payload.get("provider", "dry_run")),  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class AssetManifest:
    asset_id: str
    provider: AssetProviderName
    status: AssetStatus
    prompt: str
    semantic_tags: list[str]
    dimensions_m: dict[str, float]
    collision_proxy: dict[str, Any]
    intended_placement: dict[str, Any]
    license: str
    source_recipe_id: str | None = None
    local_path: str | None = None
    external_uri: str | None = None
    setup_guidance: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "provider": self.provider,
            "status": self.status,
            "prompt": self.prompt,
            "semantic_tags": self.semantic_tags,
            "dimensions_m": self.dimensions_m,
            "collision_proxy": self.collision_proxy,
            "intended_placement": self.intended_placement,
            "license": self.license,
            "source_recipe_id": self.source_recipe_id,
            "local_path": self.local_path,
            "external_uri": self.external_uri,
            "setup_guidance": self.setup_guidance,
            "metadata": self.metadata,
        }

    @classmethod
    def from_request(
        cls,
        request: AssetRequest,
        *,
        status: AssetStatus,
        provider: AssetProviderName | None = None,
        local_path: str | None = None,
        external_uri: str | None = None,
        setup_guidance: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "AssetManifest":
        return cls(
            asset_id=request.asset_id,
            provider=provider or request.provider,
            status=status,
            prompt=request.prompt,
            semantic_tags=request.semantic_tags,
            dimensions_m=request.dimensions_m,
            collision_proxy=request.collision_proxy,
            intended_placement=request.intended_placement,
            license=request.license,
            source_recipe_id=request.source_recipe_id,
            local_path=local_path,
            external_uri=external_uri,
            setup_guidance=setup_guidance,
            metadata=metadata or {},
        )
