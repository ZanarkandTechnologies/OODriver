"""Agent-facing catalog of CARLA towns and OODrive composition controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from driverx.behaviors import default_behavior_templates
from driverx.environments.library import load_environment_pack


@dataclass(frozen=True)
class CarlaTownProfile:
    town_id: str
    map_names: tuple[str, ...]
    summary: str
    best_for: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "town_id": self.town_id,
            "map_names": list(self.map_names),
            "summary": self.summary,
            "best_for": list(self.best_for),
        }


WEATHER_PRESETS: dict[str, dict[str, float]] = {
    "clear_day": {
        "cloudiness": 5.0,
        "precipitation": 0.0,
        "precipitation_deposits": 0.0,
        "fog_density": 0.0,
        "sun_altitude_angle": 55.0,
        "sun_azimuth_angle": 15.0,
    },
    "wet_overcast": {
        "cloudiness": 80.0,
        "precipitation": 45.0,
        "precipitation_deposits": 75.0,
        "fog_density": 5.0,
        "sun_altitude_angle": 25.0,
        "sun_azimuth_angle": 30.0,
    },
    "night_rain_fog": {
        "cloudiness": 100.0,
        "precipitation": 70.0,
        "precipitation_deposits": 85.0,
        "fog_density": 45.0,
        "sun_altitude_angle": -12.0,
        "sun_azimuth_angle": 0.0,
    },
    "low_sun_glare": {
        "cloudiness": 25.0,
        "precipitation": 0.0,
        "precipitation_deposits": 10.0,
        "fog_density": 0.0,
        "sun_altitude_angle": 8.0,
        "sun_azimuth_angle": 85.0,
    },
    "flooded_surface": {
        "cloudiness": 90.0,
        "precipitation": 85.0,
        "precipitation_deposits": 100.0,
        "fog_density": 12.0,
        "sun_altitude_angle": 18.0,
        "sun_azimuth_angle": 45.0,
    },
}

OBJECT_KIND_SUMMARIES: dict[str, str] = {
    "construction_debris": "low lane obstacle mapped to stock debris/construction props",
    "roadside_vendor": "roadside food-cart occluder mapped to stock CARLA food cart when available",
    "lane_cone": "cone/barrier proxy that narrows or blocks part of a lane",
    "rolling_object": "round/unknown debris proxy for accident or collision-course cases",
}


def default_carla_town_profiles() -> list[CarlaTownProfile]:
    """Return concise town profiles for agent-side scenario selection."""

    return [
        CarlaTownProfile(
            town_id="Town01",
            map_names=("Town01", "Town01_Opt"),
            summary="Basic small-town road layout dominated by T junctions.",
            best_for=("simple intersections", "lane-blocker smoke tests", "low-cost sanity checks"),
        ),
        CarlaTownProfile(
            town_id="Town02",
            map_names=("Town02", "Town02_Opt"),
            summary="Smaller version of the basic town layout.",
            best_for=("quick rendering", "compact obstacle tests", "fast CI-style probes"),
        ),
        CarlaTownProfile(
            town_id="Town03",
            map_names=("Town03", "Town03_Opt"),
            summary="Complex urban medley with larger junctions, roundabout, unevenness, and tunnel.",
            best_for=("junction reasoning", "roundabout pressure", "occlusion-rich bad paths"),
        ),
        CarlaTownProfile(
            town_id="Town04",
            map_names=("Town04", "Town04_Opt"),
            summary="Looping highway plus small-town setting.",
            best_for=("highway merges", "blocked shoulder", "speed-change hazards"),
        ),
        CarlaTownProfile(
            town_id="Town05",
            map_names=("Town05", "Town05_Opt"),
            summary="Squared grid with bridges and multi-lane roads.",
            best_for=("lane changes", "alternate route pressure", "multi-lane obstacle avoidance"),
        ),
        CarlaTownProfile(
            town_id="Town06",
            map_names=("Town06", "Town06_Opt"),
            summary="Long highways with entrances, exits, and a Michigan-left style turn.",
            best_for=("merge conflicts", "exit-ramp blockers", "high-speed slowdowns"),
        ),
        CarlaTownProfile(
            town_id="Town07",
            map_names=("Town07", "Town07_Opt"),
            summary="Rural/narrow-road environment with fewer traffic lights and barn-like surroundings.",
            best_for=("rural minimal-shot transfer", "narrow-road blockers", "low-signage navigation"),
        ),
        CarlaTownProfile(
            town_id="Town10HD",
            map_names=("Town10", "Town10_Opt", "Town10HD", "Town10HD_Opt"),
            summary="Dense downtown with skyscrapers, residential blocks, junction variety, and ocean promenade.",
            best_for=("hero visuals", "urban occlusion", "pedestrian crossings", "regional traffic overlays"),
        ),
    ]


def build_agent_carla_catalog() -> dict[str, Any]:
    """Build a JSON-ready catalog of controllable CARLA composition dimensions."""

    environments = load_environment_pack()
    behaviors = default_behavior_templates()
    return {
        "kind": "oodrive_agent_carla_catalog",
        "towns": [town.to_jsonable() for town in default_carla_town_profiles()],
        "weather_presets": WEATHER_PRESETS,
        "environment_templates": [
            {
                "template_id": template.template_id,
                "family": template.family,
                "description": template.description,
                "tags": template.tags,
                "asset_count": len(template.assets),
                "asset_blueprints": [asset.blueprint_hint for asset in template.assets],
            }
            for template in environments
        ],
        "behavior_templates": [
            {
                "behavior_id": behavior.template_id,
                "actor_kind": behavior.actor_kind,
                "tags": behavior.tags,
                "expected_pressure": behavior.expected_pressure,
            }
            for behavior in behaviors
        ],
        "object_kinds": OBJECT_KIND_SUMMARIES,
        "composition_controls": [
            "town/map_name",
            "load_map",
            "weather_preset",
            "environment_template",
            "road_anchor_spawn_index",
            "background_vehicle_count",
            "background_pedestrian_count",
            "behavior_id",
            "object_kind",
            "backend=dry-run|fake-carla|carla-live",
        ],
        "claim_boundaries": [
            "carla_world_generation=false",
            "carla_existing_map_composition=true",
            "weather_and_actor_spawn_composition=true",
            "custom_unreal_map_import=false",
        ],
        "sources": [
            "CARLA 0.9.16 maps documentation: https://carla.readthedocs.io/en/0.9.16/core_map/",
            "CARLA Town10 documentation: https://carla.readthedocs.io/en/latest/map_town10/",
        ],
    }


def resolve_map_name(town: str | None, map_name: str | None = None) -> str:
    """Resolve a friendly town selector to a concrete CARLA map name."""

    if map_name:
        return map_name
    selected = (town or "Town10HD_Opt").strip()
    for profile in default_carla_town_profiles():
        values = {profile.town_id.lower(), *[item.lower() for item in profile.map_names]}
        if selected.lower() in values:
            return profile.map_names[-1] if selected.lower() == profile.town_id.lower() else selected
    return selected


def weather_preset(name: str | None) -> dict[str, float]:
    """Return a named weather preset, defaulting to wet overcast."""

    key = (name or "wet_overcast").strip()
    if key not in WEATHER_PRESETS:
        raise ValueError(f"Unknown weather preset: {key}")
    return dict(WEATHER_PRESETS[key])


__all__ = [
    "OBJECT_KIND_SUMMARIES",
    "WEATHER_PRESETS",
    "CarlaTownProfile",
    "build_agent_carla_catalog",
    "default_carla_town_profiles",
    "resolve_map_name",
    "weather_preset",
]
