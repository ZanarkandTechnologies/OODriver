"""OODrive CARLA scenario composition commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.evaluation.carla_suite_score import (
    load_carla_suite_score_inputs,
    score_carla_suite,
    write_carla_suite_score,
)
from driverx.scenarios.generated_runtime import (
    GeneratorRuntimeBackend,
    build_generated_scenario_runtime_spec,
    run_generated_scenario_runtime,
)
from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_helpers import artifact_paths, oodrive_command
from driverx.simulators.carla_control import (
    CarlaControlConfig,
    control_carla_world,
    write_carla_control_report,
)
from driverx.simulators.carla_catalog import (
    OBJECT_KIND_SUMMARIES,
    WEATHER_PRESETS,
    build_agent_carla_catalog,
    resolve_map_name,
    weather_preset,
)

LIVE_PROVED_MAPS: tuple[str, ...] = (
    "Town01",
    "Town01_Opt",
    "Town02",
    "Town02_Opt",
    "Town03",
    "Town03_Opt",
    "Town04",
    "Town04_Opt",
    "Town05",
    "Town05_Opt",
    "Town10HD",
    "Town10HD_Opt",
)

CAMERA_ANCHOR_MODES: tuple[str, ...] = (
    "wide_context",
    "hood_forward",
    "intersection_oblique",
    "roadside_low",
)

BLUEPRINT_FAMILIES: tuple[str, ...] = (
    "static.prop.dirtdebris01",
    "static.prop.foodcart",
    "static.prop.constructioncone",
    "vehicle.*",
    "walker.pedestrian.*",
)


def run_studio_carla_catalog() -> StudioCommandResult:
    """Return the agent-facing CARLA composition catalog."""

    catalog = build_agent_carla_catalog()
    return StudioCommandResult(
        command="oodrive carla-catalog",
        run_id="carla-catalog",
        status="passed",
        artifacts={},
        summary=catalog,
        claim_boundaries=[str(item) for item in catalog["claim_boundaries"]],
        blockers=[],
    )


def run_studio_carla_matrix(
    *,
    output_root: Path | None = None,
    run_id: str = "oodrive-carla-capability-matrix",
) -> StudioCommandResult:
    """Write the installed CARLA capability matrix used by suite generation."""

    run_dir = prepare_run_dir(output_root or Path("artifacts/runs"), run_id)
    matrix = build_carla_capability_matrix()
    json_path = run_dir / "carla_capability_matrix.json"
    report_path = run_dir / "carla_capability_matrix.md"
    matrix["json_path"] = str(json_path)
    matrix["report_path"] = str(report_path)
    json_path.write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    report_path.write_text(_capability_matrix_markdown(matrix), encoding="utf-8")
    return StudioCommandResult(
        command="oodrive carla-matrix",
        run_id=run_dir.name,
        status="passed",
        artifacts=artifact_paths(
            {
                "capability_matrix_path": str(json_path),
                "capability_matrix_report_path": str(report_path),
            }
        ),
        next_commands=[oodrive_command(f"carla-suite --capability-matrix {json_path} --run-id task166-ten-case-suite")],
        summary={
            "available_map_count": len(matrix["available_maps"]),
            "weather_preset_count": len(matrix["weather_presets"]),
            "camera_anchor_mode_count": len(matrix["camera_anchor_modes"]),
            "blueprint_family_count": len(matrix["blueprint_families"]),
        },
        claim_boundaries=[str(item) for item in matrix["claim_boundaries"]],
        blockers=[],
    )


def run_studio_carla_control(
    *,
    town: str | None = None,
    map_name: str | None = None,
    load_map: bool = False,
    weather_preset_name: str | None = None,
    capture: bool = False,
    spawn_index: int = 0,
    host: str = "127.0.0.1",
    port: int = 2000,
    timeout_s: float = 30.0,
    output_root: Path | None = None,
    run_id: str = "oodrive-carla-control",
) -> StudioCommandResult:
    """Directly control the live CARLA world for agent probes."""

    run_dir = prepare_run_dir(output_root or Path("artifacts/runs"), run_id)
    result = control_carla_world(
        CarlaControlConfig(
            host=host,
            port=port,
            timeout_s=timeout_s,
            town=town,
            map_name=map_name,
            load_map=load_map,
            weather_preset_name=weather_preset_name,
            capture=capture,
            spawn_index=spawn_index,
        ),
        run_dir,
    )
    summary = write_carla_control_report(run_dir, result)
    return StudioCommandResult(
        command="oodrive carla-control",
        run_id=run_dir.name,
        status=result.status,
        artifacts=artifact_paths(
            {
                "carla_control_json_path": summary["json_path"],
                "carla_control_report_path": summary["report_path"],
                "screenshot_path": summary.get("screenshot_path"),
            }
        ),
        summary={
            "connected": result.connected,
            "map_before": result.map_before,
            "map_after": result.map_after,
            "requested_map": result.requested_map,
            "weather_preset": result.weather_preset_name,
            "screenshot_path": result.screenshot_path,
            "available_map_count": len(result.available_maps),
        },
        claim_boundaries=[str(item) for item in list(summary.get("claim_boundaries", []))],
        blockers=[str(item) for item in result.blockers],
    )


def build_carla_capability_matrix() -> dict[str, Any]:
    """Build a CARLA capability matrix from the installed/proved runtime facts."""

    catalog = build_agent_carla_catalog()
    return {
        "kind": "oodrive_carla_capability_matrix",
        "available_maps": list(LIVE_PROVED_MAPS),
        "weather_presets": list(WEATHER_PRESETS.keys()),
        "weather_controls": [
            "cloudiness",
            "precipitation",
            "precipitation_deposits",
            "fog_density",
            "sun_altitude_angle",
            "sun_azimuth_angle",
        ],
        "camera_anchor_modes": list(CAMERA_ANCHOR_MODES),
        "blueprint_families": list(BLUEPRINT_FAMILIES),
        "object_kinds": dict(OBJECT_KIND_SUMMARIES),
        "catalog_town_profiles": list(catalog.get("towns", [])),
        "live_facts": [
            "Available maps on this install: Town01, Town02, Town03, Town04, Town05, Town10HD, plus _Opt variants.",
            "Town03_Opt loaded from Town10HD_Opt.",
            "Town05_Opt loaded from Town03_Opt.",
            "Weather was applied through the CARLA API.",
            "Screenshots are live CARLA captures, not generated 2D mockups.",
        ],
        "can": [
            "load installed maps",
            "switch towns",
            "control sun/rain/fog/wetness",
            "spawn installed blueprints",
            "spawn vehicles/pedestrians/props",
            "move cameras",
            "capture frames",
            "render videos",
        ],
        "cannot": [
            "prompt-generate brand-new city/map geometry at runtime",
            "spawn arbitrary generated 3D meshes without Unreal/CARLA import and blueprint registration",
            "simulate true flood water physics from weather alone",
        ],
        "claim_labels": {
            "carla_existing_map_composition": True,
            "custom_unreal_map_import": False,
            "arbitrary_mesh_spawn": False,
            "true_flood_physics": False,
            "live_screenshots_required_for_gallery": True,
        },
        "claim_boundaries": [
            "carla_existing_map_composition=true",
            "custom_unreal_map_import=false",
            "arbitrary_mesh_spawn=false",
            "true_flood_physics=false",
            "live_screenshots_required_for_gallery=true",
        ],
    }


def build_default_carla_suite(*, seed: int = 41, count: int = 10) -> list[dict[str, Any]]:
    """Return deterministic capability-grounded CARLA suite cases."""

    base_cases: list[dict[str, Any]] = [
        {
            "case_id": "case-01-town03-night-static-blocker",
            "prompt": "Town03 night rain urban junction with a static lane blocker and motorcycle filtering",
            "town": "Town03",
            "map_name": "Town03_Opt",
            "weather_preset": "night_rain_fog",
            "camera_pose": "intersection_oblique",
            "road_anchor_spawn_index": 7,
            "template_ids": ["construction_lane_closure"],
            "behavior_ids": ["motorcycle_filtering"],
            "object_kinds": ["construction_debris", "lane_cone"],
            "hazards": [
                {"kind": "static", "role": "lane blocker"},
                {"kind": "moving", "role": "filtering motorcycle"},
            ],
            "expected_policy_pressure": "slow_or_stop_for_blocker_then_yield_to_filtering_actor",
        },
        {
            "case_id": "case-02-town05-wet-cut-in",
            "prompt": "Town05 wet grid road with unsignaled cut-in vehicle and roadside debris",
            "town": "Town05",
            "map_name": "Town05_Opt",
            "weather_preset": "wet_overcast",
            "camera_pose": "wide_context",
            "road_anchor_spawn_index": 12,
            "template_ids": ["roadside_market_occlusion"],
            "behavior_ids": ["no_signal_cut_in"],
            "object_kinds": ["construction_debris"],
            "hazards": [
                {"kind": "moving", "role": "cut-in vehicle"},
                {"kind": "static", "role": "low debris"},
            ],
            "expected_policy_pressure": "slow_for_cut_in_and_keep_lane_margin",
        },
        {
            "case_id": "case-03-town10hd-market-occlusion",
            "prompt": "Town10HD roadside market occlusion with food cart and pedestrian crossing pressure",
            "town": "Town10HD",
            "map_name": "Town10HD_Opt",
            "weather_preset": "low_sun_glare",
            "camera_pose": "roadside_low",
            "road_anchor_spawn_index": 18,
            "template_ids": ["roadside_market_occlusion"],
            "behavior_ids": ["unsignaled_u_turn"],
            "object_kinds": ["roadside_vendor", "lane_cone"],
            "hazards": [
                {"kind": "static", "role": "food-cart occluder"},
                {"kind": "moving", "role": "pedestrian pressure"},
            ],
            "expected_policy_pressure": "creep_and_yield_around_occlusion",
        },
        {
            "case_id": "case-04-town04-highway-merge-blocker",
            "prompt": "Town04 highway merge with cone taper and sudden braking vehicle pressure",
            "town": "Town04",
            "map_name": "Town04_Opt",
            "weather_preset": "clear_day",
            "camera_pose": "hood_forward",
            "road_anchor_spawn_index": 24,
            "template_ids": ["construction_lane_closure"],
            "behavior_ids": ["no_signal_cut_in"],
            "object_kinds": ["lane_cone", "construction_debris"],
            "hazards": [
                {"kind": "static", "role": "cone taper"},
                {"kind": "moving", "role": "braking vehicle"},
            ],
            "expected_policy_pressure": "decelerate_early_and_merge_safely",
        },
        {
            "case_id": "case-05-town01-rolling-object",
            "prompt": "Town01 small junction where a rolling object enters the lane after a minor accident",
            "town": "Town01",
            "map_name": "Town01_Opt",
            "weather_preset": "wet_overcast",
            "camera_pose": "intersection_oblique",
            "road_anchor_spawn_index": 3,
            "template_ids": ["construction_lane_closure"],
            "behavior_ids": ["wrong_way_shoulder_creep"],
            "object_kinds": ["rolling_object", "lane_cone"],
            "hazards": [
                {"kind": "moving", "role": "rolling object"},
                {"kind": "static", "role": "accident cone"},
            ],
            "expected_policy_pressure": "yield_or_stop_for_unpredictable_object",
        },
        {
            "case_id": "case-06-town02-compact-static-obstacle",
            "prompt": "Town02 compact road with a stationary obstacle in the travel lane and background traffic",
            "town": "Town02",
            "map_name": "Town02_Opt",
            "weather_preset": "clear_day",
            "camera_pose": "wide_context",
            "road_anchor_spawn_index": 5,
            "template_ids": ["roadside_market_occlusion"],
            "behavior_ids": ["wrong_way_shoulder_creep"],
            "object_kinds": ["construction_debris", "roadside_vendor"],
            "hazards": [
                {"kind": "static", "role": "travel-lane obstacle"},
                {"kind": "moving", "role": "background traffic pressure"},
            ],
            "expected_policy_pressure": "stop_then_find_safe_gap",
        },
        {
            "case_id": "case-07-town03-fog-pedestrian-occlusion",
            "prompt": "Town03 foggy junction with pedestrian occlusion and roadside vendor",
            "town": "Town03",
            "map_name": "Town03_Opt",
            "weather_preset": "night_rain_fog",
            "camera_pose": "roadside_low",
            "road_anchor_spawn_index": 31,
            "template_ids": ["roadside_market_occlusion"],
            "behavior_ids": ["unsignaled_u_turn", "motorcycle_filtering"],
            "object_kinds": ["roadside_vendor"],
            "hazards": [
                {"kind": "static", "role": "vendor occlusion"},
                {"kind": "moving", "role": "pedestrian and motorcycle pressure"},
            ],
            "expected_policy_pressure": "creep_with_visibility_margin",
        },
        {
            "case_id": "case-08-town05-wet-detour",
            "prompt": "Town05 wet road with lane blocked by debris requiring slow alternate path selection",
            "town": "Town05",
            "map_name": "Town05_Opt",
            "weather_preset": "flooded_surface",
            "camera_pose": "wide_context",
            "road_anchor_spawn_index": 39,
            "template_ids": ["construction_lane_closure"],
            "behavior_ids": ["double_parked_door_swerve"],
            "object_kinds": ["construction_debris", "lane_cone"],
            "hazards": [
                {"kind": "static", "role": "blocked lane"},
                {"kind": "moving", "role": "adjacent lane traffic"},
            ],
            "expected_policy_pressure": "slow_replan_without_claiming_true_flood_physics",
        },
        {
            "case_id": "case-09-town10hd-dense-cut-in",
            "prompt": "Town10HD dense downtown with parked cart occlusion and unsignaled vehicle cut-in",
            "town": "Town10HD",
            "map_name": "Town10HD_Opt",
            "weather_preset": "wet_overcast",
            "camera_pose": "hood_forward",
            "road_anchor_spawn_index": 44,
            "template_ids": ["roadside_market_occlusion"],
            "behavior_ids": ["no_signal_cut_in", "unsignaled_u_turn"],
            "object_kinds": ["roadside_vendor", "rolling_object"],
            "hazards": [
                {"kind": "static", "role": "cart occluder"},
                {"kind": "moving", "role": "cut-in and crossing pressure"},
            ],
            "expected_policy_pressure": "slow_yield_and_hold_lane",
        },
        {
            "case_id": "case-10-town04-low-sun-compound",
            "prompt": "Town04 low sun compound case with static debris, cone taper, and braking vehicle",
            "town": "Town04",
            "map_name": "Town04_Opt",
            "weather_preset": "low_sun_glare",
            "camera_pose": "intersection_oblique",
            "road_anchor_spawn_index": 52,
            "template_ids": ["construction_lane_closure"],
            "behavior_ids": ["unsignaled_u_turn", "no_signal_cut_in"],
            "object_kinds": ["construction_debris", "lane_cone", "rolling_object"],
            "hazards": [
                {"kind": "static", "role": "debris and cone taper"},
                {"kind": "moving", "role": "brake-and-cut-in actor"},
            ],
            "expected_policy_pressure": "slow_stop_or_replan_under_compound_ood_pressure",
        },
    ]
    if count <= 0:
        raise ValueError("CARLA suite count must be at least 1.")
    offset = seed % len(base_cases)
    ordered = [*base_cases[offset:], *base_cases[:offset]]
    return [dict(case) for case in ordered[: min(count, len(base_cases))]]


def run_studio_carla_suite(
    *,
    capability_matrix_path: Path | None = None,
    probe_capabilities: bool = False,
    count: int = 10,
    seed: int = 41,
    backend: str = "fake-carla",
    output_root: Path | None = None,
    run_id: str = "oodrive-carla-suite",
) -> StudioCommandResult:
    """Generate a capability-grounded 10-case CARLA scenario suite."""

    if backend not in {"dry-run", "fake-carla", "carla-live"}:
        raise ValueError(f"Unsupported CARLA suite backend: {backend}")
    run_dir = prepare_run_dir(output_root or Path("artifacts/runs"), run_id)
    matrix = _load_or_build_matrix(capability_matrix_path)
    matrix_path = run_dir / "carla_capability_matrix.json"
    matrix_report_path = run_dir / "carla_capability_matrix.md"
    matrix["json_path"] = str(matrix_path)
    matrix["report_path"] = str(matrix_report_path)
    matrix_path.write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    matrix_report_path.write_text(_capability_matrix_markdown(matrix), encoding="utf-8")
    suite_cases = build_default_carla_suite(seed=seed, count=count)
    cases_root = run_dir / "cases"
    generated_cases: list[dict[str, Any]] = []
    for index, case in enumerate(suite_cases):
        case_run_id = str(case["case_id"])
        result = run_studio_carla_compose(
            prompt=str(case["prompt"]),
            town=str(case["town"]),
            map_name=str(case["map_name"]),
            load_map=False,
            weather_preset_name=str(case["weather_preset"]),
            template_ids=tuple(str(item) for item in list(case["template_ids"])),
            behavior_ids=tuple(str(item) for item in list(case["behavior_ids"])),
            object_kinds=tuple(str(item) for item in list(case["object_kinds"])),
            severity=4,
            seed=seed + index,
            road_anchor_spawn_index=int(case["road_anchor_spawn_index"]),
            background_vehicle_count=6 + (index % 4),
            background_pedestrian_count=2 + (index % 5),
            backend=backend,
            output_root=cases_root,
            run_id=case_run_id,
        )
        generated_cases.append(
            {
                **case,
                "status": result.status,
                "backend": backend,
                "composition_manifest_path": result.artifacts.get("composition_manifest_path"),
                "carla_config_path": result.artifacts.get("carla_config_path"),
                "runtime_manifest_path": result.artifacts.get("runtime_manifest_path"),
                "runtime_spec_path": result.artifacts.get("runtime_spec_path"),
                "blockers": list(result.blockers),
            }
        )
    manifest_path = run_dir / "carla_suite_manifest.json"
    report_path = run_dir / "carla_suite_report.md"
    storyboard_path = run_dir / "carla_suite_storyboard.html"
    manifest: dict[str, Any] = {
        "kind": "oodrive_carla_capability_suite",
        "status": "passed" if len(generated_cases) == count and not any(case["blockers"] for case in generated_cases) else "blocked",
        "run_id": run_dir.name,
        "seed": seed,
        "backend": backend,
        "probe_capabilities": bool(probe_capabilities),
        "capability_matrix_path": str(matrix_path),
        "capability_matrix_report_path": str(matrix_report_path),
        "capability_matrix": matrix,
        "cases": generated_cases,
        "diversity_summary": _suite_diversity_summary(generated_cases),
        "gallery_ready": False,
        "gallery_promotion_blocker": "TASK-167_live_image_diversity_score_required",
        "claim_boundaries": [
            "carla_existing_map_composition=true",
            "custom_unreal_map_import=false",
            "arbitrary_mesh_spawn=false",
            "true_flood_physics=false",
            "gallery_ready=false_until_live_image_diversity_passes",
        ],
        "blockers": [],
        "next_commands": [
            oodrive_command(f"score-carla-suite --suite-manifest {manifest_path} --metric-only"),
            oodrive_command(f"carla-suite-snapshots --suite-manifest {manifest_path} --run-id task167-live-snapshots"),
        ],
        "json_path": str(manifest_path),
        "report_path": str(report_path),
        "storyboard_path": str(storyboard_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report_path.write_text(_suite_markdown(manifest), encoding="utf-8")
    storyboard_path.write_text(_suite_storyboard_html(manifest), encoding="utf-8")
    return StudioCommandResult(
        command="oodrive carla-suite",
        run_id=run_dir.name,
        status=str(manifest["status"]),
        artifacts=artifact_paths(
            {
                "suite_manifest_path": str(manifest_path),
                "suite_report_path": str(report_path),
                "storyboard_path": str(storyboard_path),
                "capability_matrix_path": str(matrix_path),
                "capability_matrix_report_path": str(matrix_report_path),
            }
        ),
        next_commands=[str(item) for item in list(manifest["next_commands"])],
        summary={
            "case_count": len(generated_cases),
            "backend": backend,
            "diversity_summary": manifest["diversity_summary"],
            "gallery_ready": False,
        },
        claim_boundaries=[str(item) for item in list(manifest["claim_boundaries"])],
        blockers=[],
    )


def run_studio_score_carla_suite(
    *,
    suite_manifest_path: Path,
    capability_matrix_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str = "oodrive-carla-suite-score",
) -> StudioCommandResult:
    """Score a CARLA capability suite and write report artifacts."""

    inputs = load_carla_suite_score_inputs(
        suite_manifest_path,
        capability_matrix_path=capability_matrix_path,
    )
    report = score_carla_suite(inputs)
    run_dir = prepare_run_dir(output_root or Path("artifacts/runs"), run_id)
    written = write_carla_suite_score(run_dir, report)
    return StudioCommandResult(
        command="oodrive score-carla-suite",
        run_id=run_dir.name,
        status=report.status,
        artifacts=artifact_paths(
            {
                "carla_suite_score_path": written["json_path"],
                "carla_suite_score_report_path": written["report_path"],
            }
        ),
        summary=report.to_jsonable(),
        claim_boundaries=report.claim_boundaries,
        blockers=report.blockers,
    )


def run_studio_carla_compose(
    *,
    prompt: str,
    town: str | None = None,
    map_name: str | None = None,
    load_map: bool = False,
    weather_preset_name: str = "wet_overcast",
    template_ids: tuple[str, ...] = (),
    behavior_ids: tuple[str, ...] = (),
    object_kinds: tuple[str, ...] = (),
    severity: int = 4,
    seed: int = 41,
    road_anchor_spawn_index: int = 0,
    background_vehicle_count: int = 6,
    background_pedestrian_count: int = 4,
    backend: str = "dry-run",
    output_root: Path | None = None,
    run_id: str = "oodrive-carla-composition",
) -> StudioCommandResult:
    """Compose a varied CARLA scenario spec and optionally execute a backend."""

    if not prompt.strip():
        raise ValueError("Pass a scenario prompt for CARLA composition.")
    if backend not in {"dry-run", "fake-carla", "carla-live"}:
        raise ValueError(f"Unsupported CARLA composition backend: {backend}")
    run_dir = prepare_run_dir(output_root or Path("artifacts/runs"), run_id)
    concrete_map_name = resolve_map_name(town, map_name)
    weather = weather_preset(weather_preset_name)
    config_path = run_dir / "carla_ood_demo_config.yaml"
    _write_carla_config(
        config_path,
        map_name=concrete_map_name,
        load_map=load_map,
        weather=weather,
        road_anchor_spawn_index=road_anchor_spawn_index,
        background_vehicle_count=background_vehicle_count,
        background_pedestrian_count=background_pedestrian_count,
    )
    spec = build_generated_scenario_runtime_spec(
        prompt=prompt,
        template_ids=template_ids,
        behavior_ids=behavior_ids,
        object_kinds=object_kinds,
        severity=severity,
        seed=seed,
        config_path=config_path,
        output_root=run_dir,
        run_id="generated-runtime",
    )
    runtime = run_generated_scenario_runtime(
        spec,
        backend=backend,  # type: ignore[arg-type]
        config_path=config_path,
        output_root=Path(str(spec["run_dir"])),
        run_id="runtime",
    )
    command_path = run_dir / "agent_commands.sh"
    manifest_path = run_dir / "carla_composition_manifest.json"
    report_path = run_dir / "carla_composition_manifest.md"
    command_path.write_text(_agent_commands(prompt, manifest_path, runtime), encoding="utf-8")
    manifest: dict[str, Any] = {
        "kind": "oodrive_carla_composition",
        "status": runtime.get("status"),
        "run_id": run_dir.name,
        "prompt": prompt,
        "town": town,
        "map_name": concrete_map_name,
        "load_map": load_map,
        "weather_preset": weather_preset_name,
        "weather": weather,
        "road_anchor_spawn_index": road_anchor_spawn_index,
        "background_vehicle_count": background_vehicle_count,
        "background_pedestrian_count": background_pedestrian_count,
        "template_ids": list(template_ids),
        "behavior_ids": list(behavior_ids),
        "object_kinds": list(object_kinds),
        "backend": backend,
        "config_path": str(config_path),
        "spec_path": spec.get("spec_path"),
        "runtime_manifest_path": runtime.get("json_path"),
        "agent_commands_path": str(command_path),
        "runtime_summary": {
            "scenario_id": runtime.get("scenario_id"),
            "template_id": runtime.get("template_id"),
            "behavior_case_count": runtime.get("behavior_case_count"),
            "object_spawn_spec_count": runtime.get("object_spawn_spec_count"),
            "runtime_proof": runtime.get("runtime_proof", {}),
        },
        "claim_boundaries": [
            "carla_world_generation=false",
            "carla_existing_map_composition=true",
            "weather_and_actor_spawn_composition=true",
            "programmed_vehicle_and_pedestrian_pressure=true",
            "custom_unreal_map_import=false",
            *[str(item) for item in list(runtime.get("claim_boundaries", []))],
        ],
        "blockers": list(runtime.get("blockers", [])),
        "next_commands": [
            oodrive_command(f"score-generator-runtime --runtime-manifest {runtime['json_path']} --metric-only"),
            oodrive_command(
                "carla-compose "
                f"{json.dumps(prompt)} --town {concrete_map_name} --load-map "
                f"--backend carla-live --run-id {run_dir.name}-live"
            ),
        ],
        "json_path": str(manifest_path),
        "report_path": str(report_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report_path.write_text(_manifest_markdown(manifest), encoding="utf-8")
    return StudioCommandResult(
        command="oodrive carla-compose",
        run_id=run_dir.name,
        status=str(runtime.get("status")),
        artifacts=artifact_paths(
            {
                "composition_manifest_path": str(manifest_path),
                "composition_report_path": str(report_path),
                "carla_config_path": str(config_path),
                "agent_commands_path": str(command_path),
                "runtime_manifest_path": runtime.get("json_path"),
                "runtime_report_path": runtime.get("report_path"),
                "runtime_spec_path": spec.get("spec_path"),
            }
        ),
        next_commands=[str(item) for item in list(manifest["next_commands"])],
        summary={
            "map_name": concrete_map_name,
            "weather_preset": weather_preset_name,
            "backend": backend,
            "behavior_case_count": runtime.get("behavior_case_count"),
            "object_spawn_spec_count": runtime.get("object_spawn_spec_count"),
            "background_vehicle_count": background_vehicle_count,
            "background_pedestrian_count": background_pedestrian_count,
        },
        claim_boundaries=[str(item) for item in manifest["claim_boundaries"]],
        blockers=[str(item) for item in list(manifest["blockers"])],
    )


def _write_carla_config(
    path: Path,
    *,
    map_name: str,
    load_map: bool,
    weather: dict[str, float],
    road_anchor_spawn_index: int,
    background_vehicle_count: int,
    background_pedestrian_count: int,
) -> None:
    lines = [
        "carla_ood_demo:",
        "  host: 127.0.0.1",
        "  port: 2000",
        "  timeout_s: 45",
        f"  map_name: {map_name}",
        f"  load_map: {_yaml_bool(load_map)}",
        "  tick_count: 450",
        "  fps: 5",
        "  camera_width: 1280",
        "  camera_height: 720",
        "  camera_fov: 105",
        "  behavior_id: motorcycle_filtering",
        "  ego_mode: scripted",
        "  ego_speed_mps: 5.0",
        "  coordinate_frame: road_local",
        f"  road_anchor_spawn_index: {max(0, int(road_anchor_spawn_index))}",
        "  road_anchor_forward_m: 0.0",
        "  road_anchor_lateral_m: 0.0",
        "  road_anchor_yaw_delta_deg: 0.0",
        "  road_lane_width_m: 3.5",
        "  road_max_lateral_offset_m: 6.0",
        "  fidelity_mode: high_fidelity",
        f"  background_vehicle_count: {max(0, int(background_vehicle_count))}",
        f"  background_pedestrian_count: {max(0, int(background_pedestrian_count))}",
        "  camera_preset: wide_context",
        "  ood_motion_smoothing: limit_step",
        "  ood_max_step_m: 1.2",
        "  cleanup: true",
    ]
    for key, value in weather.items():
        lines.append(f"  weather_{key}: {float(value)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _agent_commands(prompt: str, manifest_path: Path, runtime: dict[str, Any]) -> str:
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "",
            "# Inspect the composed CARLA scenario.",
            f"python3 -m json.tool {manifest_path}",
            "",
            "# Score the generated runtime proof.",
            f"PYTHONPATH=src python3 -m oodrive score-generator-runtime --runtime-manifest {runtime['json_path']} --metric-only",
            "",
            "# Re-run as live CARLA on a Kasm/RunPod host after CARLA is listening on 127.0.0.1:2000.",
            f"# PYTHONPATH=src python3 -m oodrive carla-compose {json.dumps(prompt)} --backend carla-live --load-map",
            "",
        ]
    )


def _load_or_build_matrix(path: Path | None) -> dict[str, Any]:
    if path is None:
        return build_carla_capability_matrix()
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"CARLA capability matrix must be a JSON object: {path}")
    return dict(payload)


def _suite_diversity_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "case_count": len(cases),
        "map_count": len({str(case.get("map_name")) for case in cases if case.get("map_name")}),
        "weather_preset_count": len(
            {str(case.get("weather_preset")) for case in cases if case.get("weather_preset")}
        ),
        "behavior_type_count": len(
            {
                str(item)
                for case in cases
                for item in list(case.get("behavior_ids", []))
                if item
            }
        ),
        "object_kind_count": len(
            {
                str(item)
                for case in cases
                for item in list(case.get("object_kinds", []))
                if item
            }
        ),
        "camera_pose_count": len({str(case.get("camera_pose")) for case in cases if case.get("camera_pose")}),
        "static_hazard_case_count": sum(
            1
            for case in cases
            if any(str(item.get("kind")) == "static" for item in list(case.get("hazards", [])) if isinstance(item, dict))
        ),
        "moving_hazard_case_count": sum(
            1
            for case in cases
            if any(str(item.get("kind")) == "moving" for item in list(case.get("hazards", [])) if isinstance(item, dict))
        ),
    }


def _capability_matrix_markdown(matrix: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OODrive CARLA Capability Matrix",
            "",
            "## Available Maps",
            *[f"- `{item}`" for item in list(matrix.get("available_maps", []))],
            "",
            "## Weather Presets",
            *[f"- `{item}`" for item in list(matrix.get("weather_presets", []))],
            "",
            "## Blueprint / Proxy Families",
            *[f"- `{item}`" for item in list(matrix.get("blueprint_families", []))],
            "",
            "## Can",
            *[f"- {item}" for item in list(matrix.get("can", []))],
            "",
            "## Cannot",
            *[f"- {item}" for item in list(matrix.get("cannot", []))],
            "",
            "## Claim Boundaries",
            *[f"- `{item}`" for item in list(matrix.get("claim_boundaries", []))],
            "",
        ]
    )


def _suite_markdown(manifest: dict[str, Any]) -> str:
    summary = manifest.get("diversity_summary", {})
    lines = [
        f"# OODrive CARLA Suite: {manifest.get('run_id')}",
        "",
        f"- status: `{manifest.get('status')}`",
        f"- case_count: `{summary.get('case_count')}`",
        f"- maps: `{summary.get('map_count')}`",
        f"- weather_presets: `{summary.get('weather_preset_count')}`",
        f"- behavior_types: `{summary.get('behavior_type_count')}`",
        f"- object_kinds: `{summary.get('object_kind_count')}`",
        f"- gallery_ready: `{manifest.get('gallery_ready')}`",
        f"- gallery_promotion_blocker: `{manifest.get('gallery_promotion_blocker')}`",
        "",
        "## Cases",
    ]
    for case in list(manifest.get("cases", [])):
        if not isinstance(case, dict):
            continue
        lines.extend(
            [
                f"- `{case.get('case_id')}`: {case.get('prompt')}",
                f"  - map/weather: `{case.get('map_name')}` / `{case.get('weather_preset')}`",
                f"  - hazards: {', '.join(str(item.get('role')) for item in list(case.get('hazards', [])) if isinstance(item, dict))}",
            ]
        )
    lines.extend(["", "## Claim Boundaries"])
    lines.extend([f"- `{item}`" for item in list(manifest.get("claim_boundaries", []))])
    return "\n".join(lines) + "\n"


def _suite_storyboard_html(manifest: dict[str, Any]) -> str:
    cards = []
    for case in list(manifest.get("cases", [])):
        if not isinstance(case, dict):
            continue
        hazards = ", ".join(
            f"{item.get('kind')}: {item.get('role')}" for item in list(case.get("hazards", [])) if isinstance(item, dict)
        )
        cards.append(
            "<section>"
            f"<h2>{case.get('case_id')}</h2>"
            f"<p>{case.get('prompt')}</p>"
            f"<p><strong>Map</strong> {case.get('map_name')} | <strong>Weather</strong> {case.get('weather_preset')} | "
            f"<strong>Camera</strong> {case.get('camera_pose')}</p>"
            f"<p><strong>Hazards</strong> {hazards}</p>"
            f"<p><strong>Expected behavior</strong> {case.get('expected_policy_pressure')}</p>"
            f"<p><strong>Gallery status</strong> blocked until TASK-167 live image diversity passes.</p>"
            "</section>"
        )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>OODrive CARLA Suite</title>"
        "<style>body{font-family:system-ui,sans-serif;margin:24px;background:#101114;color:#f4f4f0}"
        "main{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}"
        "section{border:1px solid #3a3d42;border-radius:8px;padding:14px;background:#181a20}"
        "h1,h2{margin-top:0}p{line-height:1.35}</style></head><body>"
        f"<h1>OODrive CARLA Suite: {manifest.get('run_id')}</h1>"
        "<p>Planning storyboard only. Gallery promotion requires live CARLA screenshots and image-diversity scoring.</p>"
        f"<main>{''.join(cards)}</main></body></html>"
    )


def _manifest_markdown(manifest: dict[str, Any]) -> str:
    summary = manifest.get("runtime_summary", {})
    return "\n".join(
        [
            f"# OODrive CARLA Composition: {manifest.get('run_id')}",
            "",
            f"- status: `{manifest.get('status')}`",
            f"- map: `{manifest.get('map_name')}`",
            f"- load_map: `{manifest.get('load_map')}`",
            f"- weather_preset: `{manifest.get('weather_preset')}`",
            f"- background vehicles: `{manifest.get('background_vehicle_count')}`",
            f"- background pedestrians: `{manifest.get('background_pedestrian_count')}`",
            f"- behavior cases: `{summary.get('behavior_case_count')}`",
            f"- object spawn specs: `{summary.get('object_spawn_spec_count')}`",
            "",
            "## Claim Boundaries",
            *[f"- `{item}`" for item in list(manifest.get("claim_boundaries", []))],
            "",
            "## Blockers",
            *[f"- {item}" for item in list(manifest.get("blockers", []))],
            "",
        ]
    )


def _yaml_bool(value: bool) -> str:
    return "true" if value else "false"


__all__ = [
    "build_carla_capability_matrix",
    "build_default_carla_suite",
    "run_studio_carla_catalog",
    "run_studio_carla_compose",
    "run_studio_carla_control",
    "run_studio_carla_matrix",
    "run_studio_carla_suite",
    "run_studio_score_carla_suite",
]
