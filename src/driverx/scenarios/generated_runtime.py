"""Generated OODrive scenario runtime specs and CARLA proof backends."""

from __future__ import annotations

import importlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from driverx.assets import (
    AssetManifest,
    AssetProviderName,
    AssetRequest,
    map_assets_to_carla_spawns,
    validate_carla_asset_mappings,
)
from driverx.assets.types import AssetStatus
from driverx.behaviors import (
    BehaviorPlan,
    generate_behavior_variants,
    simulate_behavior,
    validate_behavior_plan,
)
from driverx.core.artifacts import prepare_run_dir
from driverx.environments import (
    attach_environment_to_recipe,
    environment_to_asset_requests,
    generate_environment_recipe,
)
from driverx.scenarios.studio import compile_scenario_prompt
from driverx.scenarios.studio_product_helpers import oodrive_command
from driverx.scenarios.types import ScenarioRecipe
from driverx.simulators.carla_ood_demo import (
    CarlaOodDemoConfig,
    load_carla_ood_demo_config,
    run_carla_ood_demo,
    write_carla_ood_demo,
)

GeneratorRuntimeBackend = Literal["dry-run", "fake-carla", "carla-live"]


@dataclass(frozen=True)
class GeneratorRuntimeValidation:
    passes: bool
    behavior_case_count: int
    static_object_spawn_spec_count: int
    behavior_reports: list[dict[str, Any]]
    object_spawn_errors: dict[str, list[str]]
    blockers: list[str]
    warnings: list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "passes": self.passes,
            "behavior_case_count": self.behavior_case_count,
            "static_object_spawn_spec_count": self.static_object_spawn_spec_count,
            "behavior_reports": self.behavior_reports,
            "object_spawn_errors": self.object_spawn_errors,
            "blockers": self.blockers,
            "warnings": self.warnings,
        }


def build_generated_scenario_runtime_spec(
    *,
    prompt: str,
    template_ids: tuple[str, ...] = (),
    behavior_ids: tuple[str, ...] = (),
    object_kinds: tuple[str, ...] = (),
    severity: int = 4,
    seed: int = 41,
    config_path: Path = Path("configs/carla_ood_demo.local.sample.yaml"),
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-generated-runtime",
) -> dict[str, Any]:
    """Build and write a generated scenario runtime specification."""

    clean_prompt = prompt.strip()
    if not clean_prompt:
        raise ValueError("A prompt is required for generated runtime construction.")
    severity = max(1, min(5, int(severity)))
    run_dir = prepare_run_dir(output_root, run_id)
    plan = compile_scenario_prompt(clean_prompt, seed=seed)
    template_id = _first(template_ids) or plan.environment_template_id
    selected_behaviors = _dedupe([*behavior_ids] or [plan.behavior_template_id])
    environment = generate_environment_recipe(
        template_id,
        severity=severity,
        random_seed=seed,
    )
    behavior_cases = [
        _behavior_case(
            behavior_id=behavior_id,
            index=index,
            seed=seed + index,
            severity=severity,
            run_dir=run_dir,
        )
        for index, behavior_id in enumerate(selected_behaviors)
    ]
    base_recipe = _runtime_recipe(
        prompt=clean_prompt,
        run_id=run_dir.name,
        plan_id=plan.plan_id,
        environment_template_id=template_id,
        behavior_cases=behavior_cases,
        memory_query=plan.memory_query,
        expected_failure_mode=plan.expected_failure_mode,
        safe_behavior_principle=plan.safe_behavior_principle,
    )
    compiled_recipe = attach_environment_to_recipe(base_recipe, environment)
    asset_requests = [
        *environment_to_asset_requests(environment),
        *[
            _asset_request_for_object_kind(
                object_kind=object_kind,
                index=index,
                source_recipe_id=environment.recipe_id,
            )
            for index, object_kind in enumerate(_dedupe(object_kinds))
        ],
    ]
    asset_manifests = [
        AssetManifest.from_request(request, status="planned")
        for request in asset_requests
    ]
    object_spawn_specs = map_assets_to_carla_spawns(asset_manifests)
    validation = validate_generated_scenario_runtime_spec_payload(
        behavior_cases=behavior_cases,
        asset_manifests=asset_manifests,
        object_spawn_specs=[spec.to_jsonable() for spec in object_spawn_specs],
    )
    spec_path = run_dir / "generated_scenario_runtime_spec.json"
    report_path = run_dir / "generated_scenario_runtime_spec.md"
    payload: dict[str, Any] = {
        "kind": "generated_scenario_runtime_spec",
        "run_id": run_dir.name,
        "run_dir": str(run_dir),
        "scenario_id": f"{_slug(clean_prompt)}-{seed:04d}",
        "prompt": clean_prompt,
        "severity": severity,
        "seed": seed,
        "config_path": str(config_path),
        "environment_recipe": environment.to_jsonable(),
        "compiled_recipe": compiled_recipe.to_jsonable(),
        "behavior_cases": behavior_cases,
        "asset_requests": [request.to_jsonable() for request in asset_requests],
        "asset_manifests": [manifest.to_jsonable() for manifest in asset_manifests],
        "object_spawn_specs": [spec.to_jsonable() for spec in object_spawn_specs],
        "validation": validation.to_jsonable(),
        "claim_boundaries": [
            "generated_vehicle_behaviors=true",
            "generated_static_objects=true",
            "objects_spawned_in_carla=false_until_live_backend_passes",
            "closed_loop_vla_control=false",
            "real_time_vla_control=false",
        ],
        "next_commands": [
            oodrive_command(
                f"generate-run {json.dumps(clean_prompt)} --backend fake-carla --run-id {run_dir.name}"
            ),
            oodrive_command(
                f"score-generator-runtime --runtime-manifest {run_dir / 'generated_scenario_runtime.json'} --metric-only"
            ),
        ],
        "spec_path": str(spec_path),
        "spec_report_path": str(report_path),
    }
    spec_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_spec_markdown(payload), encoding="utf-8")
    return payload


def validate_generated_scenario_runtime_spec(
    spec: dict[str, Any],
    *,
    available_blueprint_ids: list[str] | None = None,
) -> GeneratorRuntimeValidation:
    """Validate a generated runtime spec loaded from a manifest."""

    return validate_generated_scenario_runtime_spec_payload(
        behavior_cases=[dict(item) for item in list(spec.get("behavior_cases", [])) if isinstance(item, dict)],
        asset_manifests=[
            _asset_manifest_from_jsonable(item)
            for item in list(spec.get("asset_manifests", []))
            if isinstance(item, dict)
        ],
        object_spawn_specs=[dict(item) for item in list(spec.get("object_spawn_specs", [])) if isinstance(item, dict)],
        available_blueprint_ids=available_blueprint_ids,
    )


def validate_generated_scenario_runtime_spec_payload(
    *,
    behavior_cases: list[dict[str, Any]],
    asset_manifests: list[AssetManifest],
    object_spawn_specs: list[dict[str, Any]],
    available_blueprint_ids: list[str] | None = None,
) -> GeneratorRuntimeValidation:
    blockers: list[str] = []
    warnings: list[str] = []
    behavior_reports = [dict(case.get("validation", {})) for case in behavior_cases]
    for report in behavior_reports:
        if report and report.get("passes") is not True:
            blockers.append(f"Behavior `{report.get('behavior_id', 'unknown')}` did not pass validation.")
    if not behavior_cases:
        blockers.append("No generated behavior cases were produced.")
    if len(object_spawn_specs) < 1:
        blockers.append("No generated object spawn specs were produced.")
    object_spawn_errors: dict[str, list[str]] = {}
    if available_blueprint_ids is not None:
        object_spawn_errors = validate_carla_asset_mappings(asset_manifests, available_blueprint_ids)
        if object_spawn_errors:
            blockers.append("One or more generated object CARLA blueprint mappings are unavailable.")
    elif len(object_spawn_specs) < 2:
        warnings.append("Fewer than two static/generated object spawn specs; fake/live proof will be less persuasive.")
    return GeneratorRuntimeValidation(
        passes=not blockers,
        behavior_case_count=len(behavior_cases),
        static_object_spawn_spec_count=len(object_spawn_specs),
        behavior_reports=behavior_reports,
        object_spawn_errors=object_spawn_errors,
        blockers=blockers,
        warnings=warnings,
    )


def run_generated_scenario_runtime(
    spec: dict[str, Any],
    *,
    backend: GeneratorRuntimeBackend = "dry-run",
    config_path: Path = Path("configs/carla_ood_demo.local.sample.yaml"),
    output_root: Path = Path("artifacts/runs"),
    run_id: str | None = None,
    carla_module: object | None = None,
) -> dict[str, Any]:
    """Run or block-record one generated scenario runtime spec."""

    if backend not in {"dry-run", "fake-carla", "carla-live"}:
        raise ValueError(f"Unsupported generator runtime backend: {backend}")
    run_dir = _existing_or_new_run_dir(spec, output_root, run_id)
    config = load_carla_ood_demo_config(config_path) if backend == "carla-live" else CarlaOodDemoConfig()
    proof = run_generated_runtime_backend(
        spec=spec,
        backend=backend,
        config=config,
        run_dir=run_dir,
        carla_module=carla_module,
    )
    claim_boundaries = _runtime_claim_boundaries(spec, proof)
    blockers = [
        *list(_mapping(spec.get("validation")).get("blockers", [])),
        *list(proof.get("blockers", [])),
    ]
    status = _runtime_status(spec, proof, blockers)
    json_path = run_dir / "generated_scenario_runtime.json"
    report_path = run_dir / "generated_scenario_runtime.md"
    payload: dict[str, Any] = {
        "kind": "generated_scenario_runtime",
        "status": status,
        "run_id": run_dir.name,
        "scenario_id": spec.get("scenario_id"),
        "prompt": spec.get("prompt"),
        "backend": backend,
        "severity": spec.get("severity"),
        "seed": spec.get("seed"),
        "config_path": str(config_path),
        "spec_path": spec.get("spec_path"),
        "environment_recipe_id": _mapping(spec.get("environment_recipe")).get("recipe_id"),
        "template_id": _mapping(spec.get("environment_recipe")).get("template_id"),
        "behavior_case_count": len(list(spec.get("behavior_cases", []))),
        "object_spawn_spec_count": len(list(spec.get("object_spawn_specs", []))),
        "behavior_cases": list(spec.get("behavior_cases", [])),
        "object_spawn_specs": list(spec.get("object_spawn_specs", [])),
        "validation": dict(spec.get("validation", {})),
        "runtime_proof": proof,
        "claim_boundaries": claim_boundaries,
        "blockers": blockers,
        "next_commands": [
            oodrive_command(f"score-generator-runtime --runtime-manifest {json_path} --metric-only"),
            oodrive_command(
                f"drive-loop --scenario-runtime {json_path} --backend fake --run-id task139-timewarped-vla-drive"
            ),
        ],
        "json_path": str(json_path),
        "report_path": str(report_path),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_runtime_markdown(payload), encoding="utf-8")
    return payload


def run_generated_runtime_backend(
    *,
    spec: dict[str, Any],
    backend: GeneratorRuntimeBackend,
    config: CarlaOodDemoConfig,
    run_dir: Path,
    carla_module: object | None = None,
) -> dict[str, Any]:
    """Execute the selected generated-runtime backend."""

    if backend == "dry-run":
        return _dry_run_proof(spec, run_dir)
    if backend == "fake-carla":
        return _fake_carla_proof(spec, run_dir)
    return _live_carla_proof(spec, config, run_dir, carla_module=carla_module)


def load_generated_scenario_runtime(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Generated scenario runtime must be a JSON object: {path}")
    return payload


def _behavior_case(
    *,
    behavior_id: str,
    index: int,
    seed: int,
    severity: int,
    run_dir: Path,
) -> dict[str, Any]:
    plan = generate_behavior_variants(
        behavior_id,
        count=1,
        random_seed=seed,
        severity=severity,
    )[0]
    trace = simulate_behavior(plan)
    validation = validate_behavior_plan(plan)
    trace_dir = run_dir / "behavior_traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_path = trace_dir / f"{index:02d}_{_slug(behavior_id)}.json"
    trace_path.write_text(json.dumps(trace.to_jsonable(), indent=2), encoding="utf-8")
    first = trace.samples[0]
    return {
        "case_id": f"behavior-{index:02d}-{_slug(behavior_id)}",
        "behavior_id": behavior_id,
        "behavior_plan": plan.to_jsonable(),
        "validation": validation.to_jsonable(),
        "dynamic_actor": {
            "actor_ref": f"generated_behavior_actor_{index}",
            "behavior_id": behavior_id,
            "actor_kind": plan.actor_kind,
            "blueprint_filter": _blueprint_for_actor_kind(plan.actor_kind),
            "sample_count": len(trace.samples),
            "trace_path": str(trace_path),
            "spawn_transform": _transform(first.x_m, first.y_m, 0.2, first.heading_deg),
        },
    }


def _runtime_recipe(
    *,
    prompt: str,
    run_id: str,
    plan_id: str,
    environment_template_id: str,
    behavior_cases: list[dict[str, Any]],
    memory_query: list[str],
    expected_failure_mode: str,
    safe_behavior_principle: str,
) -> ScenarioRecipe:
    actors = [
        {
            "actor_id": _mapping(case.get("dynamic_actor")).get("actor_ref"),
            "kind": _mapping(case.get("dynamic_actor")).get("actor_kind"),
            "role": "dynamic_ood_actor",
            "behavior_id": case.get("behavior_id"),
            "expected_pressure": _mapping(case.get("behavior_plan")).get("expected_pressure"),
        }
        for case in behavior_cases
    ]
    behavior_ids = [str(case.get("behavior_id")) for case in behavior_cases]
    return ScenarioRecipe(
        recipe_id=f"{run_id}-generated-runtime",
        parent_seed_id=plan_id,
        mutation="generated_behavior_object_runtime",
        actors=actors,
        environment={
            "studio_plan_id": plan_id,
            "environment_template_id": environment_template_id,
            "behavior_ids": behavior_ids,
            "source_prompt": prompt,
            "quality_targets": {
                "require_behavior_validation": True,
                "require_object_spawn_specs": True,
                "require_runtime_spawn_proof": True,
            },
        },
        expected_failure_mode=expected_failure_mode,
        memory_query=sorted(set([*memory_query, *behavior_ids, "generator_runtime"])),
        solvability_assumption=f"Safe behavior: {safe_behavior_principle}",
        route_path="generated-runtime-suite",
    )


def _asset_request_for_object_kind(
    *,
    object_kind: str,
    index: int,
    source_recipe_id: str,
) -> AssetRequest:
    spec = _object_kind_spec(object_kind)
    x_m = 15.0 + index * 4.5
    y_m = spec["y_m"]
    return AssetRequest(
        asset_id=f"{_slug(object_kind)}-{index:02d}",
        prompt=str(spec["prompt"]),
        semantic_tags=[str(tag) for tag in list(spec["semantic_tags"])],
        dimensions_m=dict(spec["dimensions_m"]),
        collision_proxy=dict(spec["collision_proxy"]),
        intended_placement={
            "coordinate_frame": "road_local",
            "relative_to": spec["relative_to"],
            "x_m": x_m,
            "y_m": y_m,
            "z_m": 0.2,
            "yaw_deg": float(index * 7.5),
        },
        license="generated-for-0xdriver-demo",
        source_recipe_id=source_recipe_id,
        provider="dry_run",
    )


def _object_kind_spec(object_kind: str) -> dict[str, Any]:
    key = _slug(object_kind).replace("-", "_")
    specs: dict[str, dict[str, Any]] = {
        "construction_debris": {
            "prompt": "roadwork debris and uneven construction material near the ego lane",
            "semantic_tags": ["debris", "lane_obstacle", "construction"],
            "dimensions_m": {"length": 1.4, "width": 0.9, "height": 0.35},
            "collision_proxy": {"kind": "box", "length": 1.4, "width": 0.9, "height": 0.35},
            "relative_to": "lane_center",
            "y_m": 0.15,
        },
        "roadside_vendor": {
            "prompt": "roadside food cart creating regional market occlusion",
            "semantic_tags": ["roadside_vendor", "occlusion", "regional_context"],
            "dimensions_m": {"length": 2.0, "width": 1.0, "height": 1.8},
            "collision_proxy": {"kind": "box", "length": 2.0, "width": 1.0, "height": 1.8},
            "relative_to": "curb",
            "y_m": -4.0,
        },
        "lane_cone": {
            "prompt": "construction cone narrowing the usable lane",
            "semantic_tags": ["construction", "barrier", "route_blockage"],
            "dimensions_m": {"length": 0.45, "width": 0.45, "height": 0.8},
            "collision_proxy": {"kind": "cylinder", "radius": 0.35, "height": 0.8},
            "relative_to": "lane_center",
            "y_m": 0.75,
        },
        "rolling_object": {
            "prompt": "round debris object that could roll from an accident scene",
            "semantic_tags": ["debris", "unknown_object", "lane_obstacle"],
            "dimensions_m": {"length": 0.9, "width": 0.9, "height": 0.9},
            "collision_proxy": {"kind": "sphere", "radius": 0.5},
            "relative_to": "lane_center",
            "y_m": -0.35,
        },
    }
    return specs.get(
        key,
        {
            "prompt": f"unknown generated OOD object: {object_kind}",
            "semantic_tags": ["debris", "unknown_object", "lane_obstacle"],
            "dimensions_m": {"length": 1.0, "width": 1.0, "height": 0.8},
            "collision_proxy": {"kind": "box", "length": 1.0, "width": 1.0, "height": 0.8},
            "relative_to": "lane_center",
            "y_m": 0.0,
        },
    )


def _dry_run_proof(spec: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    proof = {
        "backend": "dry-run",
        "status": "passed" if _mapping(spec.get("validation")).get("passes") is True else "blocked",
        "static_object_spawn_count": 0,
        "planned_static_object_spawn_count": len(list(spec.get("object_spawn_specs", []))),
        "dynamic_actor_spawn_count": 0,
        "planned_dynamic_actor_count": len(list(spec.get("behavior_cases", []))),
        "applied_behavior_tick_count": 0,
        "track_count": 0,
        "tracks_path": None,
        "rgb_folder": None,
        "spawned_actor_ids": [],
        "destroyed_actor_ids": [],
        "blockers": list(_mapping(spec.get("validation")).get("blockers", [])),
    }
    path = run_dir / "generated_runtime_dry_run_proof.json"
    path.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    return {**proof, "json_path": str(path)}


def _fake_carla_proof(spec: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    tracks: list[dict[str, Any]] = []
    spawned_ids: list[int] = []
    next_actor_id = 1
    object_specs = [dict(item) for item in list(spec.get("object_spawn_specs", [])) if isinstance(item, dict)]
    behavior_cases = [dict(item) for item in list(spec.get("behavior_cases", [])) if isinstance(item, dict)]
    for spec_index, object_spec in enumerate(object_specs):
        actor_id = next_actor_id
        next_actor_id += 1
        spawned_ids.append(actor_id)
        transform = _mapping(object_spec.get("spawn_transform"))
        tracks.append(
            _track(
                actor_ref=str(object_spec.get("actor_ref", f"generated_object_{spec_index}")),
                actor_id=actor_id,
                type_id=str(object_spec.get("blueprint_filter", "static.prop.dirtdebris01")),
                tick=0,
                t_s=0.0,
                transform=transform,
                velocity={"x": 0.0, "y": 0.0, "z": 0.0},
            )
        )
    applied_ticks = 0
    for case_index, case in enumerate(behavior_cases):
        actor_id = next_actor_id
        next_actor_id += 1
        spawned_ids.append(actor_id)
        dynamic_actor = _mapping(case.get("dynamic_actor"))
        trace = _load_trace(dynamic_actor.get("trace_path"))
        samples = list(_mapping(trace).get("samples", []))
        for tick, sample in enumerate(samples):
            sample_map = _mapping(sample)
            applied_ticks += 1
            tracks.append(
                _track(
                    actor_ref=str(dynamic_actor.get("actor_ref", f"generated_behavior_actor_{case_index}")),
                    actor_id=actor_id,
                    type_id=str(dynamic_actor.get("blueprint_filter", "vehicle.*")),
                    tick=tick,
                    t_s=float(sample_map.get("t_s", tick)),
                    transform=_transform(
                        float(sample_map.get("x_m", 0.0)),
                        float(sample_map.get("y_m", 0.0)),
                        0.2,
                        float(sample_map.get("heading_deg", 0.0)),
                    ),
                    velocity={"x": float(sample_map.get("speed_mps", 0.0)), "y": 0.0, "z": 0.0},
                )
            )
    tracks_path = run_dir / "entity_tracks.json"
    proof_path = run_dir / "generated_runtime_fake_carla_proof.json"
    tracks_path.write_text(json.dumps(tracks, indent=2), encoding="utf-8")
    proof = {
        "backend": "fake-carla",
        "status": "passed" if object_specs and behavior_cases and applied_ticks > 0 else "blocked",
        "static_object_spawn_count": len(object_specs),
        "dynamic_actor_spawn_count": len(behavior_cases),
        "applied_behavior_tick_count": applied_ticks,
        "track_count": len(tracks),
        "tracks_path": str(tracks_path),
        "rgb_folder": None,
        "spawned_actor_ids": spawned_ids,
        "destroyed_actor_ids": list(spawned_ids),
        "blockers": [] if object_specs and behavior_cases else ["Fake-CARLA proof requires object specs and behavior cases."],
    }
    proof_path.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    return {**proof, "json_path": str(proof_path)}


def _live_carla_proof(
    spec: dict[str, Any],
    config: CarlaOodDemoConfig,
    run_dir: Path,
    *,
    carla_module: object | None,
) -> dict[str, Any]:
    try:
        carla = carla_module or importlib.import_module("carla")
    except ImportError as exc:
        return _live_blocked(run_dir, f"CARLA Python package is unavailable: {exc}")
    behavior_cases = [dict(item) for item in list(spec.get("behavior_cases", [])) if isinstance(item, dict)]
    if not behavior_cases:
        return _live_blocked(run_dir, "No generated behavior cases are available for live CARLA.")
    object_manifests = [
        _asset_manifest_from_jsonable(item)
        for item in list(spec.get("asset_manifests", []))
        if isinstance(item, dict)
    ]
    case_results: list[dict[str, Any]] = []
    spawned_ids: list[int] = []
    destroyed_ids: list[int] = []
    blockers: list[str] = []
    frame_count = 0
    track_count = 0
    tracks_path: str | None = None
    rgb_folder: str | None = None
    for case in behavior_cases:
        case_dir = run_dir / "live_cases" / str(case.get("case_id", "case"))
        behavior_plan = _behavior_plan_from_case(case)
        behavior = simulate_behavior(behavior_plan)
        recipe = ScenarioRecipe.from_jsonable(dict(spec.get("compiled_recipe", {})))
        result = run_carla_ood_demo(
            config,
            case_dir,
            recipe=recipe,
            behavior=behavior,
            asset_manifests=object_manifests,
            carla_module=carla,
        )
        written = write_carla_ood_demo(case_dir, result)
        case_results.append(written)
        spawned_ids.extend(int(item) for item in result.spawned_actor_ids)
        destroyed_ids.extend(int(item) for item in result.destroyed_actor_ids)
        blockers.extend(str(item) for item in result.blockers)
        frame_count += result.frame_count
        if result.tracks_path and Path(result.tracks_path).exists():
            tracks = json.loads(Path(result.tracks_path).read_text(encoding="utf-8"))
            track_count += len(list(tracks)) if isinstance(tracks, list) else 0
            if tracks_path is None:
                tracks_path = result.tracks_path
        if rgb_folder is None and result.rgb_folder:
            rgb_folder = result.rgb_folder
    status = "passed" if case_results and frame_count > 0 and not blockers else "partial" if frame_count > 0 else "blocked"
    proof = {
        "backend": "carla-live",
        "status": status,
        "static_object_spawn_count": len(list(spec.get("object_spawn_specs", []))) if status in {"passed", "partial"} else 0,
        "dynamic_actor_spawn_count": len(case_results),
        "applied_behavior_tick_count": sum(_trace_sample_count(case) for case in behavior_cases),
        "track_count": track_count,
        "tracks_path": tracks_path,
        "frame_count": frame_count,
        "rgb_folder": rgb_folder,
        "spawned_actor_ids": spawned_ids,
        "destroyed_actor_ids": destroyed_ids,
        "case_results": case_results,
        "blockers": blockers,
    }
    path = run_dir / "generated_runtime_live_carla_proof.json"
    path.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    return {**proof, "json_path": str(path)}


def _live_blocked(run_dir: Path, blocker: str) -> dict[str, Any]:
    proof = {
        "backend": "carla-live",
        "status": "blocked",
        "static_object_spawn_count": 0,
        "dynamic_actor_spawn_count": 0,
        "applied_behavior_tick_count": 0,
        "track_count": 0,
        "frame_count": 0,
        "rgb_folder": None,
        "spawned_actor_ids": [],
        "destroyed_actor_ids": [],
        "blockers": [
            blocker,
            "Live CARLA proof needs the Kasm RunPod graphics path with CARLA 0.9.16 and the Python 3.12 CARLA client.",
        ],
        "setup_commands": [
            "cd /workspace/0xDriver && bash scripts/setup_runpod_carla_0916_graphics.sh",
            "PYTHONPATH=src python3 -m oodrive generate-run '<prompt>' --backend carla-live --config configs/carla_ood_demo.runpod.high_fidelity.yaml",
        ],
    }
    path = run_dir / "generated_runtime_live_carla_blocked.json"
    path.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    return {**proof, "json_path": str(path)}


def _runtime_claim_boundaries(spec: dict[str, Any], proof: dict[str, Any]) -> list[str]:
    backend = str(proof.get("backend", "dry-run"))
    live_passed = backend == "carla-live" and proof.get("status") in {"passed", "partial"}
    return _dedupe(
        [
            *list(spec.get("claim_boundaries", [])),
            "generated_vehicle_behaviors=true",
            "generated_static_objects=true",
            f"objects_spawned_in_carla={'true' if live_passed else 'false'}",
            f"objects_spawned_in_fake_carla={'true' if backend == 'fake-carla' and proof.get('status') == 'passed' else 'false'}",
            f"generator_runtime_backend={backend}",
            "closed_loop_vla_control=false",
            "real_time_vla_control=false",
        ]
    )


def _runtime_status(spec: dict[str, Any], proof: dict[str, Any], blockers: list[str]) -> str:
    if proof.get("status") == "passed" and not blockers:
        return "passed"
    if proof.get("status") == "partial":
        return "partial"
    if proof.get("backend") == "dry-run" and _mapping(spec.get("validation")).get("passes") is True:
        return "passed"
    return "blocked"


def _existing_or_new_run_dir(spec: dict[str, Any], output_root: Path, run_id: str | None) -> Path:
    desired = run_id or str(spec.get("run_id", "oodrive-generated-runtime"))
    spec_run_dir = Path(str(spec.get("run_dir", "")))
    if spec_run_dir.exists() and spec_run_dir.name == desired:
        return spec_run_dir
    if output_root.exists() and output_root.is_dir() and output_root.name == desired:
        return output_root
    return prepare_run_dir(output_root, desired)


def _behavior_plan_from_case(case: dict[str, Any]) -> BehaviorPlan:
    raw = dict(case.get("behavior_plan", {}))
    return BehaviorPlan(
        behavior_id=str(raw.get("behavior_id", case.get("behavior_id", "no_signal_cut_in"))),
        actor_kind=str(raw.get("actor_kind", "vehicle")),
        duration_s=float(raw.get("duration_s", 6.0)),
        dt_s=float(raw.get("dt_s", 0.25)),
        parameters=dict(raw.get("parameters", {})),
        tags=[str(tag) for tag in list(raw.get("tags", []))],
        expected_pressure=str(raw.get("expected_pressure", "")),
    )


def _asset_manifest_from_jsonable(item: dict[str, Any]) -> AssetManifest:
    return AssetManifest(
        asset_id=str(item.get("asset_id", "")),
        provider=_asset_provider(item.get("provider", "dry_run")),
        status=_asset_status(item.get("status", "planned")),
        prompt=str(item.get("prompt", "")),
        semantic_tags=[str(tag) for tag in list(item.get("semantic_tags", []))],
        dimensions_m={str(key): float(value) for key, value in dict(item.get("dimensions_m", {})).items()},
        collision_proxy=dict(item.get("collision_proxy", {})),
        intended_placement=dict(item.get("intended_placement", {})),
        license=str(item.get("license", "")),
        source_recipe_id=str(item["source_recipe_id"]) if item.get("source_recipe_id") else None,
        local_path=str(item["local_path"]) if item.get("local_path") else None,
        external_uri=str(item["external_uri"]) if item.get("external_uri") else None,
        setup_guidance=str(item["setup_guidance"]) if item.get("setup_guidance") else None,
        metadata=dict(item.get("metadata", {})),
    )


def _asset_provider(value: object) -> AssetProviderName:
    text = str(value)
    if text in {"dry_run", "meshy"}:
        return cast(AssetProviderName, text)
    return "dry_run"


def _asset_status(value: object) -> AssetStatus:
    text = str(value)
    if text in {"planned", "blocked", "generated"}:
        return cast(AssetStatus, text)
    return "planned"


def _trace_sample_count(case: dict[str, Any]) -> int:
    dynamic_actor = _mapping(case.get("dynamic_actor"))
    trace = _load_trace(dynamic_actor.get("trace_path"))
    return len(list(_mapping(trace).get("samples", [])))


def _load_trace(path_value: object) -> dict[str, Any]:
    if not path_value:
        return {}
    path = Path(str(path_value))
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, dict) else {}


def _track(
    *,
    actor_ref: str,
    actor_id: int,
    type_id: str,
    tick: int,
    t_s: float,
    transform: dict[str, Any],
    velocity: dict[str, float],
) -> dict[str, Any]:
    return {
        "actor_ref": actor_ref,
        "actor_id": actor_id,
        "type_id": type_id,
        "tick": tick,
        "t_s": round(t_s, 4),
        "location": dict(transform.get("location", {})),
        "rotation": dict(transform.get("rotation", {})),
        "velocity": velocity,
    }


def _spec_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Generated Scenario Runtime Spec",
        "",
        f"- Run: `{payload.get('run_id')}`",
        f"- Scenario: `{payload.get('scenario_id')}`",
        f"- Prompt: {payload.get('prompt')}",
        f"- Environment: `{_mapping(payload.get('environment_recipe')).get('recipe_id')}`",
        f"- Behavior cases: `{len(list(payload.get('behavior_cases', [])))}`",
        f"- Object spawn specs: `{len(list(payload.get('object_spawn_specs', [])))}`",
        "",
        "## Behavior Cases",
        "",
    ]
    for case in list(payload.get("behavior_cases", [])):
        dynamic = _mapping(_mapping(case).get("dynamic_actor"))
        validation = _mapping(_mapping(case).get("validation"))
        lines.append(
            f"- `{_mapping(case).get('behavior_id')}`: actor `{dynamic.get('actor_ref')}`, "
            f"samples `{dynamic.get('sample_count')}`, validation `{validation.get('passes')}`"
        )
    lines.extend(["", "## Claim Boundaries", ""])
    for boundary in list(payload.get("claim_boundaries", [])):
        lines.append(f"- `{boundary}`")
    lines.append("")
    return "\n".join(lines)


def _runtime_markdown(payload: dict[str, Any]) -> str:
    proof = _mapping(payload.get("runtime_proof"))
    lines = [
        "# Generated Scenario Runtime",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Backend: `{payload.get('backend')}`",
        f"- Scenario: `{payload.get('scenario_id')}`",
        f"- Behavior cases: `{payload.get('behavior_case_count')}`",
        f"- Object spawn specs: `{payload.get('object_spawn_spec_count')}`",
        f"- Static object spawns: `{proof.get('static_object_spawn_count')}`",
        f"- Dynamic actor spawns: `{proof.get('dynamic_actor_spawn_count')}`",
        f"- Tracks: `{proof.get('track_count')}`",
        "",
        "## Claim Boundaries",
        "",
    ]
    for boundary in list(payload.get("claim_boundaries", [])):
        lines.append(f"- `{boundary}`")
    blockers = list(payload.get("blockers", []))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        for blocker in blockers:
            lines.append(f"- {blocker}")
    lines.extend(["", "## Next Commands", ""])
    for command in list(payload.get("next_commands", [])):
        lines.append(f"- `{command}`")
    lines.append("")
    return "\n".join(lines)


def _transform(x_m: float, y_m: float, z_m: float, yaw_deg: float) -> dict[str, dict[str, float]]:
    return {
        "location": {"x": round(x_m, 4), "y": round(y_m, 4), "z": round(z_m, 4)},
        "rotation": {"pitch": 0.0, "yaw": round(yaw_deg, 4), "roll": 0.0},
    }


def _blueprint_for_actor_kind(actor_kind: str) -> str:
    if actor_kind == "motorcycle":
        return "vehicle.kawasaki.ninja"
    if actor_kind == "walker":
        return "walker.pedestrian.*"
    return "vehicle.*"


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _first(values: tuple[str, ...]) -> str | None:
    for value in values:
        text = str(value).strip()
        if text:
            return text
    return None


def _dedupe(values: list[Any] | tuple[Any, ...]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:72] or "generated-runtime"


__all__ = [
    "GeneratorRuntimeBackend",
    "GeneratorRuntimeValidation",
    "build_generated_scenario_runtime_spec",
    "load_generated_scenario_runtime",
    "run_generated_runtime_backend",
    "run_generated_scenario_runtime",
    "validate_generated_scenario_runtime_spec",
    "validate_generated_scenario_runtime_spec_payload",
]
