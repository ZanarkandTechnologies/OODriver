"""Types for deterministic CARLA environment packs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RoadFrameHint:
    lane_width_m: float = 3.5
    right_shoulder_y_m: float = -4.2
    left_adjacent_lane_y_m: float = 3.5

    def to_jsonable(self) -> dict[str, float]:
        return {
            "lane_width_m": self.lane_width_m,
            "right_shoulder_y_m": self.right_shoulder_y_m,
            "left_adjacent_lane_y_m": self.left_adjacent_lane_y_m,
        }


@dataclass(frozen=True)
class EnvironmentAssetLayout:
    asset_id: str
    role: str
    semantic_tags: list[str]
    dimensions_m: dict[str, float]
    collision_proxy: dict[str, Any]
    base_placement: dict[str, Any]
    prompt: str
    blueprint_hint: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "role": self.role,
            "semantic_tags": self.semantic_tags,
            "dimensions_m": self.dimensions_m,
            "collision_proxy": self.collision_proxy,
            "base_placement": self.base_placement,
            "prompt": self.prompt,
            "blueprint_hint": self.blueprint_hint,
        }

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "EnvironmentAssetLayout":
        return cls(
            asset_id=str(payload["asset_id"]),
            role=str(payload.get("role", "ood_artifact")),
            semantic_tags=[str(tag) for tag in list(payload.get("semantic_tags", []))],
            dimensions_m={
                str(key): float(value)
                for key, value in dict(payload.get("dimensions_m", {})).items()
            },
            collision_proxy=dict(payload.get("collision_proxy", {})),
            base_placement=dict(payload.get("base_placement", {})),
            prompt=str(payload.get("prompt", "")),
            blueprint_hint=(
                str(payload["blueprint_hint"])
                if payload.get("blueprint_hint") is not None
                else None
            ),
        )


@dataclass(frozen=True)
class EnvironmentTemplate:
    template_id: str
    family: str
    description: str
    tags: list[str]
    weather: dict[str, float | str]
    lighting: dict[str, float | str]
    traffic: dict[str, float | str]
    assets: list[EnvironmentAssetLayout]
    expected_policy_pressure: str
    meshy_prompts: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.template_id:
            raise ValueError("EnvironmentTemplate template_id is required.")
        if not self.family:
            raise ValueError("EnvironmentTemplate family is required.")

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "family": self.family,
            "description": self.description,
            "tags": self.tags,
            "weather": self.weather,
            "lighting": self.lighting,
            "traffic": self.traffic,
            "assets": [asset.to_jsonable() for asset in self.assets],
            "expected_policy_pressure": self.expected_policy_pressure,
            "meshy_prompts": self.meshy_prompts,
        }

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "EnvironmentTemplate":
        return cls(
            template_id=str(payload["template_id"]),
            family=str(payload.get("family", payload["template_id"])),
            description=str(payload.get("description", "")),
            tags=[str(tag) for tag in list(payload.get("tags", []))],
            weather=dict(payload.get("weather", {})),
            lighting=dict(payload.get("lighting", {})),
            traffic=dict(payload.get("traffic", {})),
            assets=[
                EnvironmentAssetLayout.from_jsonable(dict(asset))
                for asset in list(payload.get("assets", []))
            ],
            expected_policy_pressure=str(payload.get("expected_policy_pressure", "")),
            meshy_prompts=[str(prompt) for prompt in list(payload.get("meshy_prompts", []))],
        )


@dataclass(frozen=True)
class EnvironmentRecipe:
    recipe_id: str
    template_id: str
    family: str
    severity: int
    random_seed: int
    tags: list[str]
    weather: dict[str, float | str]
    lighting: dict[str, float | str]
    traffic: dict[str, float | str]
    assets: list[EnvironmentAssetLayout]
    expected_policy_pressure: str
    meshy_prompts: list[str]

    def __post_init__(self) -> None:
        if self.severity < 1 or self.severity > 5:
            raise ValueError("EnvironmentRecipe severity must be in [1, 5].")

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "template_id": self.template_id,
            "family": self.family,
            "severity": self.severity,
            "random_seed": self.random_seed,
            "tags": self.tags,
            "weather": self.weather,
            "lighting": self.lighting,
            "traffic": self.traffic,
            "assets": [asset.to_jsonable() for asset in self.assets],
            "expected_policy_pressure": self.expected_policy_pressure,
            "meshy_prompts": self.meshy_prompts,
        }

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "EnvironmentRecipe":
        return cls(
            recipe_id=str(payload["recipe_id"]),
            template_id=str(payload["template_id"]),
            family=str(payload.get("family", payload["template_id"])),
            severity=int(payload.get("severity", 3)),
            random_seed=int(payload.get("random_seed", 0)),
            tags=[str(tag) for tag in list(payload.get("tags", []))],
            weather=dict(payload.get("weather", {})),
            lighting=dict(payload.get("lighting", {})),
            traffic=dict(payload.get("traffic", {})),
            assets=[
                EnvironmentAssetLayout.from_jsonable(dict(asset))
                for asset in list(payload.get("assets", []))
            ],
            expected_policy_pressure=str(payload.get("expected_policy_pressure", "")),
            meshy_prompts=[str(prompt) for prompt in list(payload.get("meshy_prompts", []))],
        )


@dataclass(frozen=True)
class EnvironmentSuiteConfig:
    template_ids: tuple[str, ...] = (
        "construction_lane_closure",
        "roadside_market_occlusion",
        "flooded_road",
        "night_rain_fog",
        "dense_regional_traffic",
        "school_zone_unstructured_crossing",
    )
    severity: int = 3
    count: int = 6
    random_seed: int = 7
    output_root: Path = Path("artifacts/runs")
    run_id: str = "environment-forge"


__all__ = [
    "EnvironmentAssetLayout",
    "EnvironmentRecipe",
    "EnvironmentSuiteConfig",
    "EnvironmentTemplate",
    "RoadFrameHint",
]
