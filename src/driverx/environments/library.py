"""Default environment packs for CARLA OOD generation."""

from __future__ import annotations

import json
from pathlib import Path

from driverx.environments.types import EnvironmentAssetLayout, EnvironmentTemplate


def load_environment_pack(path: Path | None = None) -> list[EnvironmentTemplate]:
    if path is None:
        return default_environment_templates()
    payload = json.loads(path.read_text(encoding="utf-8"))
    templates = payload.get("templates", payload) if isinstance(payload, dict) else payload
    return [
        EnvironmentTemplate.from_jsonable(dict(template))
        for template in list(templates)
    ]


def default_environment_templates() -> list[EnvironmentTemplate]:
    return [
        EnvironmentTemplate(
            template_id="construction_lane_closure",
            family="construction",
            description="Lane closure with cones, concrete barrier proxy, and work-zone clutter.",
            tags=["construction", "lane_closure", "cones", "work_zone"],
            weather={"cloudiness": 30.0, "precipitation": 0.0, "fog_density": 0.0},
            lighting={"sun_altitude_angle": 45.0, "sun_azimuth_angle": 10.0},
            traffic={"target_speed_multiplier": 0.55, "density_multiplier": 0.8},
            assets=[
                _asset(
                    "construction-cone-line",
                    role="lane_boundary",
                    tags=["construction", "barrier", "lane_obstacle"],
                    dims={"length": 0.35, "width": 0.35, "height": 0.7},
                    placement={"relative_to": "ego_lane", "x_m": 14.0, "y_m": 1.4, "yaw_deg": 0.0},
                    prompt="orange construction cones forming a taper into one lane, game-ready prop set",
                    blueprint="static.prop.constructioncone",
                ),
                _asset(
                    "portable-work-barrier",
                    role="partial_blocker",
                    tags=["construction", "barrier", "route_blockage"],
                    dims={"length": 2.4, "width": 0.35, "height": 1.0},
                    placement={"relative_to": "lane_center", "x_m": 24.0, "y_m": 0.9, "yaw_deg": 8.0},
                    prompt="portable orange and white road-work barrier blocking part of a lane",
                    blueprint="static.prop.constructioncone",
                ),
            ],
            expected_policy_pressure="Slow down, bias away from closure, and avoid overreacting to cones outside the drivable corridor.",
            meshy_prompts=[
                "game-ready Malaysian roadwork barrier with reflective strips, low-poly GLB",
                "cluster of worn construction cones with dirt and tropical road grime, GLB",
            ],
        ),
        EnvironmentTemplate(
            template_id="roadside_market_occlusion",
            family="regional_market",
            description="Roadside food cart and clutter near the shoulder occluding a crossing hazard.",
            tags=["regional_context", "roadside_market", "occlusion", "malaysian_driving"],
            weather={"cloudiness": 45.0, "precipitation": 0.0, "fog_density": 0.0},
            lighting={"sun_altitude_angle": 35.0, "sun_azimuth_angle": 25.0},
            traffic={"target_speed_multiplier": 0.65, "density_multiplier": 1.35},
            assets=[
                _asset(
                    "roadside-food-cart",
                    role="occluder",
                    tags=["roadside_vendor", "occlusion", "regional_context"],
                    dims={"length": 2.2, "width": 1.1, "height": 2.1},
                    placement={"relative_to": "curb", "x_m": 16.0, "y_m": -4.2, "yaw_deg": -3.0},
                    prompt="small Malaysian roadside food cart with umbrella and metal counter, static game prop",
                    blueprint="static.prop.foodcart",
                ),
                _asset(
                    "market-plastic-crates",
                    role="distractor_clutter",
                    tags=["unknown_object", "roadside_vendor", "occlusion"],
                    dims={"length": 1.2, "width": 0.8, "height": 0.6},
                    placement={"relative_to": "curb", "x_m": 19.0, "y_m": -3.5, "yaw_deg": 12.0},
                    prompt="stack of colorful plastic market crates near curb, game-ready prop",
                    blueprint="static.prop.dirtdebris01",
                ),
            ],
            expected_policy_pressure="Creep around occlusion and preserve clearance around shoulder clutter.",
            meshy_prompts=[
                "Malaysian roadside nasi lemak food cart with umbrella, game-ready GLB",
                "stacked plastic market crates and sacks on road shoulder, low-poly GLB",
            ],
        ),
        EnvironmentTemplate(
            template_id="flooded_road",
            family="weather_surface",
            description="Wet/flooded lane with reflective barrier and low-contrast water patch proxies.",
            tags=["flood", "wet_road", "weather", "reduced_friction"],
            weather={"cloudiness": 85.0, "precipitation": 80.0, "precipitation_deposits": 90.0, "fog_density": 8.0},
            lighting={"sun_altitude_angle": 18.0, "sun_azimuth_angle": 45.0},
            traffic={"target_speed_multiplier": 0.45, "density_multiplier": 0.7},
            assets=[
                _asset(
                    "reflective-flood-barrier",
                    role="route_warning",
                    tags=["flood", "barrier", "route_blockage"],
                    dims={"length": 3.0, "width": 0.35, "height": 0.7},
                    placement={"relative_to": "lane_center", "x_m": 18.0, "y_m": -0.4, "yaw_deg": 4.0},
                    prompt="portable reflective flood warning barrier across part of a wet road",
                    blueprint="static.prop.constructioncone",
                ),
                _asset(
                    "waterlogged-cargo-sack",
                    role="low_obstacle",
                    tags=["debris", "flood", "unknown_object", "lane_obstacle"],
                    dims={"length": 1.4, "width": 0.8, "height": 0.35},
                    placement={"relative_to": "ego_lane", "x_m": 27.0, "y_m": 0.2, "yaw_deg": -10.0},
                    prompt="waterlogged cargo sack lying in shallow flood water on a road",
                    blueprint="static.prop.dirtdebris01",
                ),
            ],
            expected_policy_pressure="Reduce speed for wet surface and route around low-profile waterlogged obstacles.",
            meshy_prompts=[
                "reflective flood barrier on wet tropical road, low-poly GLB",
                "waterlogged cargo sack half submerged in shallow road water, GLB",
            ],
        ),
        EnvironmentTemplate(
            template_id="night_rain_fog",
            family="visibility",
            description="Night rain and fog with high glare and low contrast.",
            tags=["night", "rain", "fog", "glare", "visibility"],
            weather={"cloudiness": 100.0, "precipitation": 65.0, "precipitation_deposits": 70.0, "fog_density": 45.0},
            lighting={"sun_altitude_angle": -12.0, "sun_azimuth_angle": 0.0},
            traffic={"target_speed_multiplier": 0.5, "density_multiplier": 0.9},
            assets=[
                _asset(
                    "glare-warning-board",
                    role="visual_distractor",
                    tags=["visual_noise", "signage", "glare"],
                    dims={"length": 1.8, "width": 0.2, "height": 1.3},
                    placement={"relative_to": "curb", "x_m": 22.0, "y_m": -4.5, "yaw_deg": -12.0},
                    prompt="bright reflective temporary warning sign in rain and fog",
                    blueprint="static.prop.constructioncone",
                ),
            ],
            expected_policy_pressure="Maintain lane discipline despite glare and avoid treating reflective clutter as a drivable target.",
            meshy_prompts=["reflective warning board glowing in tropical rain at night, game-ready GLB"],
        ),
        EnvironmentTemplate(
            template_id="dense_regional_traffic",
            family="regional_traffic",
            description="Dense urban regional driving with lane-splitting two-wheelers and weak lane discipline.",
            tags=["malaysian_driving", "dense_traffic", "motorcycle_filtering", "low_lane_discipline"],
            weather={"cloudiness": 55.0, "precipitation": 5.0, "fog_density": 0.0},
            lighting={"sun_altitude_angle": 38.0, "sun_azimuth_angle": 65.0},
            traffic={"target_speed_multiplier": 0.6, "density_multiplier": 1.8, "lane_discipline": "low"},
            assets=[
                _asset(
                    "parked-scooter-cluster",
                    role="shoulder_clutter",
                    tags=["motorcycle", "two_wheeler", "occlusion", "regional_context"],
                    dims={"length": 2.0, "width": 1.4, "height": 1.2},
                    placement={"relative_to": "curb", "x_m": 13.0, "y_m": -4.1, "yaw_deg": 5.0},
                    prompt="cluster of parked scooters on a busy Malaysian road shoulder",
                    blueprint="vehicle.kawasaki.ninja",
                ),
            ],
            expected_policy_pressure="Account for unsignaled lateral motion and two-wheelers appearing in small gaps.",
            meshy_prompts=["parked scooter cluster beside Malaysian urban road, low-poly GLB"],
        ),
        EnvironmentTemplate(
            template_id="school_zone_unstructured_crossing",
            family="pedestrian_occlusion",
            description="School-zone clutter with temporary signage and shoulder occlusion near an unsignalized crossing.",
            tags=[
                "school_zone",
                "pedestrian_occlusion",
                "unsignalized_crossing",
                "regional_context",
                "malaysian_driving",
            ],
            weather={"cloudiness": 40.0, "precipitation": 0.0, "fog_density": 0.0},
            lighting={"sun_altitude_angle": 32.0, "sun_azimuth_angle": 80.0},
            traffic={"target_speed_multiplier": 0.38, "density_multiplier": 1.25, "yield_pressure": "high"},
            assets=[
                _asset(
                    "school-crossing-board",
                    role="yield_context",
                    tags=["school_zone", "signage", "pedestrian_occlusion"],
                    dims={"length": 1.2, "width": 0.18, "height": 1.6},
                    placement={"relative_to": "curb", "x_m": 15.0, "y_m": -4.3, "yaw_deg": -7.0},
                    prompt="temporary school crossing warning board beside tropical urban road, game-ready prop",
                    blueprint="static.prop.warningconstruction",
                ),
                _asset(
                    "parked-van-occluder",
                    role="occluder",
                    tags=["parked_vehicle", "pedestrian_occlusion", "regional_context"],
                    dims={"length": 4.8, "width": 1.9, "height": 2.2},
                    placement={"relative_to": "curb", "x_m": 21.0, "y_m": -3.9, "yaw_deg": 2.0},
                    prompt="parked white delivery van partly blocking view of a school crossing, game-ready vehicle prop",
                    blueprint="vehicle.ford.ambulance",
                ),
                _asset(
                    "loose-school-bag",
                    role="small_unknown_object",
                    tags=["unknown_object", "school_zone", "low_obstacle"],
                    dims={"length": 0.55, "width": 0.35, "height": 0.28},
                    placement={"relative_to": "ego_lane", "x_m": 26.0, "y_m": -0.6, "yaw_deg": 18.0},
                    prompt="small colorful school bag dropped near a lane edge, low-poly road prop",
                    blueprint="static.prop.dirtdebris01",
                ),
            ],
            expected_policy_pressure=(
                "Anticipate a hidden pedestrian near the crossing, slow early, and avoid swerving toward the dropped object."
            ),
            meshy_prompts=[
                "temporary Malaysian school crossing board with reflective paint, game-ready GLB",
                "parked delivery van occluding a crosswalk in a tropical street, low-poly GLB",
                "small dropped school bag at road edge, game-ready GLB",
            ],
        ),
    ]


def _asset(
    asset_id: str,
    *,
    role: str,
    tags: list[str],
    dims: dict[str, float],
    placement: dict[str, float | str],
    prompt: str,
    blueprint: str,
) -> EnvironmentAssetLayout:
    return EnvironmentAssetLayout(
        asset_id=asset_id,
        role=role,
        semantic_tags=tags,
        dimensions_m=dims,
        collision_proxy={"kind": "box", **dims},
        base_placement=dict(placement),
        prompt=prompt,
        blueprint_hint=blueprint,
    )


__all__ = ["default_environment_templates", "load_environment_pack"]
