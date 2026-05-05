"""Command-line entrypoints for 0xDriver."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from driverx.core.config import DriverConfig, OutputConfig, load_config


def _add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/mock.yaml"),
        help="Path to a driverx YAML or JSON config.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help="Override output.root from config.",
    )
    parser.add_argument(
        "--run-id",
        help="Override output.run_id from config.",
    )


def _load_config_from_args(args: argparse.Namespace) -> DriverConfig:
    config = load_config(args.config)
    if args.output_root is None and args.run_id is None:
        return config
    return replace(
        config,
        output=OutputConfig(
            root=args.output_root or config.output.root,
            run_id=args.run_id if args.run_id is not None else config.output.run_id,
        ),
    )


def _command_inspect_scene(args: argparse.Namespace) -> int:
    from driverx.pipeline.scene_run import inspect_scene

    config = _load_config_from_args(args)
    result = inspect_scene(config)
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_run_scene(args: argparse.Namespace) -> int:
    from driverx.pipeline.scene_run import run_scene

    config = _load_config_from_args(args)
    result = run_scene(config)
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_run_batch(args: argparse.Namespace) -> int:
    from driverx.pipeline.batch_run import run_batch

    config = _load_config_from_args(args)
    result = run_batch(
        config,
        fixture_names=args.fixtures,
        frame_start=args.frame_start,
        frame_count=args.frame_count,
    )
    print(json.dumps(result, indent=2))
    return 0


def _command_run_experiment(args: argparse.Namespace) -> int:
    from driverx.pipeline.experiment_run import run_experiment

    config = _load_config_from_args(args)
    result = run_experiment(
        config,
        frame_start=args.frame_start,
        frame_count=args.frame_count,
    )
    print(json.dumps(result, indent=2))
    return 0


def _command_evaluate(args: argparse.Namespace) -> int:
    from driverx.evaluation.reports import evaluate_run_dir

    report = evaluate_run_dir(args.run_dir)
    print(json.dumps(report, indent=2))
    return 0


def _command_package_submission(args: argparse.Namespace) -> int:
    from driverx.submission.waymo_packager import package_run_dir

    package = package_run_dir(args.run_dir, output_path=args.output, official=args.official)
    print(json.dumps(package, indent=2))
    return 0


def _mapping_output(raw: dict, default_run_id: str) -> OutputConfig:
    from driverx.core.config import OutputConfig

    output = raw.get("output", {})
    if not isinstance(output, dict):
        raise ValueError("Config field 'output' must be a mapping.")
    return OutputConfig(
        root=Path(str(output.get("root", "artifacts/runs"))),
        run_id=str(output.get("run_id", default_run_id)),
    )


def _command_forge_scenarios(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.core.config import read_config_mapping
    from driverx.scenarios import (
        MutationPolicy,
        generate_scenario_recipes,
        load_scenario_seeds,
        write_scenario_suite,
    )

    raw = read_config_mapping(args.config)
    scenario = raw.get("scenario", {})
    if not isinstance(scenario, dict):
        raise ValueError("Config field 'scenario' must be a mapping.")
    output = _mapping_output(raw, "scenario-forge")
    if args.output_root is not None or args.run_id is not None:
        output = OutputConfig(
            root=args.output_root or output.root,
            run_id=args.run_id if args.run_id is not None else output.run_id,
        )
    seed_path = Path(str(scenario.get("seeds_path", "tests/fixtures/fail2drive_like/seeds.json")))
    count = args.count if args.count is not None else int(scenario.get("count", 8))
    random_seed = args.seed if args.seed is not None else int(scenario.get("random_seed", 7))
    mutations_raw = str(
        scenario.get(
            "mutations",
            "obstacle_substitution,occlusion,visual_noise,lane_blockage,regional_driving_behavior",
        )
    )
    mutations = tuple(item.strip() for item in mutations_raw.split(",") if item.strip())
    seeds = load_scenario_seeds(seed_path)
    recipes = generate_scenario_recipes(
        seeds,
        MutationPolicy(mutations=mutations),
        count=count,
        random_seed=random_seed,
    )
    run_dir = prepare_run_dir(output.root, output.run_id)
    summary = write_scenario_suite(run_dir, seeds, recipes)
    print(json.dumps(summary, indent=2))
    return 0


def _command_build_memory(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.memory import build_memory_bank, write_memory_bank
    from driverx.scenarios import load_scenario_results

    results = load_scenario_results(args.results)
    bank = build_memory_bank(results)
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_memory_bank(run_dir, bank)
    print(json.dumps(summary, indent=2))
    return 0


def _select_recipe_payload(
    recipes: list[dict[str, object]],
    recipe_id: str | None,
    path: Path,
) -> dict[str, object]:
    if not recipes:
        raise ValueError(f"No recipes found in {path}")
    if recipe_id is not None:
        for recipe in recipes:
            if str(recipe.get("recipe_id")) == recipe_id:
                return recipe
        raise ValueError(f"Recipe id not found in {path}: {recipe_id}")
    if len(recipes) == 1:
        return recipes[0]
    raise ValueError(
        f"{path} contains {len(recipes)} recipes; pass --recipe-id to plan one explicit route."
    )


def _load_recipe(path: Path, recipe_id: str | None):
    from driverx.scenarios import ScenarioRecipe

    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return ScenarioRecipe.from_jsonable(
            _select_recipe_payload([dict(recipe) for recipe in raw], recipe_id, path)
        )
    if isinstance(raw, dict) and "recipes" in raw:
        recipes = raw.get("recipes", [])
        return ScenarioRecipe.from_jsonable(
            _select_recipe_payload([dict(recipe) for recipe in recipes], recipe_id, path)
        )
    if isinstance(raw, dict):
        if recipe_id is not None and str(raw.get("recipe_id")) != recipe_id:
            raise ValueError(f"Recipe id not found in {path}: {recipe_id}")
        return ScenarioRecipe.from_jsonable(raw)
    raise ValueError(f"Unsupported recipe JSON: {path}")


def _load_recipes(path: Path) -> list[object]:
    from driverx.scenarios import ScenarioRecipe

    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [ScenarioRecipe.from_jsonable(dict(recipe)) for recipe in raw]
    if isinstance(raw, dict) and "recipes" in raw:
        return [
            ScenarioRecipe.from_jsonable(dict(recipe))
            for recipe in list(raw.get("recipes", []))
        ]
    if isinstance(raw, dict):
        return [ScenarioRecipe.from_jsonable(raw)]
    raise ValueError(f"Unsupported recipe JSON: {path}")


def _command_plan_carla_run(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.simulators import load_carla_run_config, plan_fail2drive_run

    config = load_carla_run_config(args.config)
    recipe = _load_recipe(args.recipe, args.recipe_id)
    plan = plan_fail2drive_run(config, recipe)
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    path = run_dir / "carla_command_plan.json"
    payload = plan.to_jsonable()
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["plan_path"] = str(path)
    print(json.dumps(payload, indent=2))
    return 0


def _command_plan_fail2drive_video_smoke(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.simulators import (
        Fail2DriveVideoSmokeConfig,
        load_carla_run_config,
        plan_fail2drive_video_smoke,
        write_fail2drive_video_smoke_plan,
    )

    run_dir = prepare_run_dir(args.output_root, args.run_id)
    config = load_carla_run_config(args.config)
    smoke_config = Fail2DriveVideoSmokeConfig.from_carla_config(
        config,
        output_dir=run_dir / "fail2drive_outputs",
        live_visu=not args.no_live_visu,
        method_name=args.method_name,
        agent_config=args.agent_config,
        traffic_manager_port=args.traffic_manager_port,
    )
    summary = write_fail2drive_video_smoke_plan(
        run_dir,
        plan_fail2drive_video_smoke(smoke_config),
    )
    print(json.dumps(summary, indent=2))
    return 0


def _command_export_bench2drive_suite(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.simulators import (
        build_bench2drive_route_suite,
        load_simlingo_run_config,
        plan_simlingo_run,
        write_bench2drive_route_suite,
        write_simlingo_plan,
    )

    recipes = [_load_recipe(args.recipe, args.recipe_id)] if args.recipe_id else _load_recipes(args.recipe)
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    suite = build_bench2drive_route_suite(
        run_dir,
        recipes,
        route_root=args.route_root,
        behavior_id=args.behavior_id,
    )
    simlingo_summary = None
    if not args.no_simlingo_plan:
        config = load_simlingo_run_config(args.config)
        config = replace(
            config,
            route_path=suite.route_suite_path.resolve(),
            output_dir=run_dir / "simlingo_outputs",
        )
        simlingo_summary = write_simlingo_plan(run_dir, plan_simlingo_run(config))
    summary = write_bench2drive_route_suite(
        run_dir,
        suite,
        simlingo_plan=simlingo_summary,
    )
    print(json.dumps(summary, indent=2))
    return 0


def _command_plan_overlay_injection(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.simulators import (
        compact_overlay_injection_summary,
        compile_overlay_injection_plan,
        write_overlay_injection_plan,
    )

    run_dir = prepare_run_dir(args.output_root, args.run_id)
    plan = compile_overlay_injection_plan(
        args.route_pack,
        run_dir,
        behavior_id=args.behavior_id,
    )
    summary = write_overlay_injection_plan(run_dir, plan)
    print(json.dumps(compact_overlay_injection_summary(summary), indent=2))
    return 0


def _command_run_overlay_injection(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.simulators import (
        CarlaOverlayInjectionConfig,
        load_carla_run_config,
        run_overlay_injection_plan,
        write_overlay_injection_run,
    )

    config = load_carla_run_config(args.config)
    injection_config = CarlaOverlayInjectionConfig(
        host=args.host if args.host is not None else config.host,
        port=args.port if args.port is not None else config.port,
        timeout_s=args.timeout_s if args.timeout_s is not None else config.timeout_s,
        route_limit=args.route_limit,
        tick_limit=args.tick_limit,
        wait_for_tick=not args.no_wait_for_tick,
    )
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    result = run_overlay_injection_plan(
        injection_config,
        args.plan,
        run_dir,
    )
    summary = write_overlay_injection_run(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0


def _command_build_overlay_evidence(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.simulators import (
        OverlayEvidenceInputs,
        build_overlay_evidence,
    )

    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = build_overlay_evidence(
        run_dir,
        OverlayEvidenceInputs(
            overlay_plan_path=args.overlay_plan,
            overlay_run_path=args.overlay_run,
            route_evidence_path=args.route_evidence,
        ),
    )
    print(json.dumps(summary, indent=2))
    return 0


def _command_smoke_carla(args: argparse.Namespace) -> int:
    from driverx.simulators import load_carla_run_config, smoke_carla_server

    config = load_carla_run_config(args.config)
    result = smoke_carla_server(config.host, config.port, config.timeout_s)
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_probe_carla(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.simulators import CarlaProbeConfig, load_carla_run_config
    from driverx.simulators import probe_carla_client, write_carla_probe

    config = load_carla_run_config(args.config)
    probe_config = CarlaProbeConfig(
        host=args.host if args.host is not None else config.host,
        port=args.port if args.port is not None else config.port,
        timeout_s=args.timeout_s if args.timeout_s is not None else config.timeout_s,
    )
    result = probe_carla_client(probe_config)
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_carla_probe(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0


def _command_spawn_ego_smoke(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.simulators import CarlaEgoSmokeConfig, load_carla_run_config
    from driverx.simulators import run_ego_spawn_smoke, write_ego_smoke

    config = load_carla_run_config(args.config)
    smoke_config = CarlaEgoSmokeConfig(
        host=args.host if args.host is not None else config.host,
        port=args.port if args.port is not None else config.port,
        timeout_s=args.timeout_s if args.timeout_s is not None else config.timeout_s,
        tick_count=args.tick_count,
        camera_width=args.camera_width,
        camera_height=args.camera_height,
    )
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    result = run_ego_spawn_smoke(smoke_config, run_dir)
    summary = write_ego_smoke(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0


def _command_generate_behaviors(args: argparse.Namespace) -> int:
    from driverx.behaviors import default_behavior_plans, simulate_behavior
    from driverx.behaviors import write_behavior_suite
    from driverx.core.artifacts import prepare_run_dir

    traces = [simulate_behavior(plan) for plan in default_behavior_plans()]
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_behavior_suite(run_dir, traces)
    print(json.dumps(summary, indent=2))
    return 0


def _command_compile_carla_script(args: argparse.Namespace) -> int:
    from driverx.behaviors import default_behavior_plans, simulate_behavior
    from driverx.core.artifacts import prepare_run_dir
    from driverx.simulators import compile_carla_script_plan, write_carla_script_plan

    recipe = _load_recipe(args.recipe, args.recipe_id)
    plans = {
        plan.behavior_id: plan
        for plan in default_behavior_plans()
    }
    if args.behavior_id not in plans:
        raise ValueError(f"Unknown behavior id: {args.behavior_id}")
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    trace = simulate_behavior(plans[args.behavior_id])
    plan = compile_carla_script_plan(recipe, trace, run_dir)
    summary = write_carla_script_plan(run_dir, plan)
    print(json.dumps(summary, indent=2))
    return 0


def _command_plan_assets(args: argparse.Namespace) -> int:
    from driverx.assets import (
        attach_assets_to_recipes,
        default_asset_requests,
        generate_assets_with_provider,
        write_asset_plan,
    )
    from driverx.core.artifacts import prepare_run_dir

    requests = default_asset_requests()
    manifests = generate_assets_with_provider(
        requests,
        args.provider,
        api_key=args.api_key,
    )
    recipes = attach_assets_to_recipes(_load_recipes(args.recipe), manifests) if args.recipe else None
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_asset_plan(run_dir, manifests, recipes)
    print(json.dumps(summary, indent=2))
    return 0


def _command_run_policy_fixture(args: argparse.Namespace) -> int:
    from driverx.policies import (
        memory_entries_from_json,
        run_policy_fixture,
        sample_memory_entries,
    )

    memory_entries = None
    if args.memory:
        memory_entries = memory_entries_from_json(args.memory)
    elif args.with_memory:
        memory_entries = sample_memory_entries()
    summary = run_policy_fixture(
        policy=args.policy,
        fixture=args.fixture,
        output_root=args.output_root,
        run_id=args.run_id,
        memory_entries=memory_entries,
        memory_aware=args.with_memory,
    )
    print(json.dumps(summary, indent=2))
    return 0


def _command_run_rag_comparison(args: argparse.Namespace) -> int:
    from driverx.pipeline.rag_comparison import run_rag_comparison

    summary = run_rag_comparison(
        policy=args.policy,
        fixture=args.fixture,
        behavior_id=args.behavior_id,
        output_root=args.output_root,
        run_id=args.run_id,
    )
    print(json.dumps(summary, indent=2))
    return 0


def _command_build_ood_suite_report(args: argparse.Namespace) -> int:
    from driverx.core.artifacts import prepare_run_dir
    from driverx.pipeline.ood_suite_report import build_ood_suite_report

    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = build_ood_suite_report(
        run_dir,
        scenario_summary_path=args.scenario_summary,
        route_pack_path=args.route_pack,
        overlay_plan_path=args.overlay_plan,
        sidecar_plan_path=args.sidecar_plan,
        sidecar_run_path=args.sidecar_run,
        rag_comparison_path=args.rag_comparison,
        simlingo_result_path=args.simlingo_result,
        blockers_path=args.blockers,
    )
    print(json.dumps(summary, indent=2))
    return 0


def _command_show_config(args: argparse.Namespace) -> int:
    config = _load_config_from_args(args)
    print(json.dumps(config.to_jsonable(), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="driverx",
        description="Run the 0xDriver fixture-backed autonomy pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect-scene",
        help="Render one configured scene without running the planner.",
    )
    _add_config_arg(inspect_parser)
    inspect_parser.set_defaults(func=_command_inspect_scene)

    run_parser = subparsers.add_parser(
        "run-scene",
        help="Run one scene through reasoning, planning, evaluation, and artifacts.",
    )
    _add_config_arg(run_parser)
    run_parser.set_defaults(func=_command_run_scene)

    batch_parser = subparsers.add_parser(
        "run-batch",
        help="Run a tiny validation batch over fixture scenes or Waymo frames.",
    )
    _add_config_arg(batch_parser)
    batch_parser.add_argument(
        "--fixtures",
        nargs="+",
        default=None,
        help="Fixture names to run. Defaults to two fixtures for fixture configs.",
    )
    batch_parser.add_argument(
        "--frame-start",
        type=int,
        help="First global Waymo frame index to stream for dataset.kind=waymo.",
    )
    batch_parser.add_argument(
        "--frame-count",
        type=int,
        help="Number of Waymo frames to stream for dataset.kind=waymo.",
    )
    batch_parser.set_defaults(func=_command_run_batch)

    experiment_parser = subparsers.add_parser(
        "run-experiment",
        help="Compare trajectory strategies over fixture or Waymo frames.",
    )
    _add_config_arg(experiment_parser)
    experiment_parser.add_argument(
        "--frame-start",
        type=int,
        help="First global Waymo frame index to stream for dataset.kind=waymo.",
    )
    experiment_parser.add_argument(
        "--frame-count",
        type=int,
        help="Number of Waymo frames to stream. Defaults to 10 for dataset.kind=waymo.",
    )
    experiment_parser.set_defaults(func=_command_run_experiment)

    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate an existing run directory.",
    )
    evaluate_parser.add_argument("--run-dir", type=Path, required=True)
    evaluate_parser.set_defaults(func=_command_evaluate)

    package_parser = subparsers.add_parser(
        "package-submission",
        help="Create a dry-run Waymo-style submission package from a run directory.",
    )
    package_parser.add_argument("--run-dir", type=Path, required=True)
    package_parser.add_argument("--output", type=Path)
    package_parser.add_argument(
        "--official",
        action="store_true",
        help="Use official Waymo protobuf serialization when optional deps are installed.",
    )
    package_parser.set_defaults(func=_command_package_submission)

    forge_parser = subparsers.add_parser(
        "forge-scenarios",
        help="Generate deterministic OOD scenario recipes from Fail2Drive-style seeds.",
    )
    forge_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/scenario_forge.sample.yaml"),
    )
    forge_parser.add_argument("--count", type=int)
    forge_parser.add_argument("--seed", type=int)
    forge_parser.add_argument("--output-root", type=Path)
    forge_parser.add_argument("--run-id")
    forge_parser.set_defaults(func=_command_forge_scenarios)

    memory_parser = subparsers.add_parser(
        "build-memory",
        help="Build compact safety memory from scenario result records.",
    )
    memory_parser.add_argument("--results", type=Path, required=True)
    memory_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    memory_parser.add_argument("--run-id", default="memory-bank")
    memory_parser.set_defaults(func=_command_build_memory)

    plan_parser = subparsers.add_parser(
        "plan-carla-run",
        help="Write a dry-run CARLA/Fail2Drive command plan for one recipe.",
    )
    plan_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/carla_local.sample.yaml"),
    )
    plan_parser.add_argument("--recipe", type=Path, required=True)
    plan_parser.add_argument(
        "--recipe-id",
        help="Recipe id to select when --recipe points at a multi-recipe suite.",
    )
    plan_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    plan_parser.add_argument("--run-id", default="carla-plan")
    plan_parser.set_defaults(func=_command_plan_carla_run)

    video_smoke_parser = subparsers.add_parser(
        "plan-fail2drive-video-smoke",
        help="Write a dry-run Fail2Drive route and video artifact plan.",
    )
    video_smoke_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/carla_local.sample.yaml"),
    )
    video_smoke_parser.add_argument("--agent-config", type=Path)
    video_smoke_parser.add_argument("--traffic-manager-port", type=int)
    video_smoke_parser.add_argument("--method-name", default="DriverXRouteSmoke")
    video_smoke_parser.add_argument("--no-live-visu", action="store_true")
    video_smoke_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    video_smoke_parser.add_argument("--run-id", default="fail2drive-video-smoke")
    video_smoke_parser.set_defaults(func=_command_plan_fail2drive_video_smoke)

    route_export_parser = subparsers.add_parser(
        "export-bench2drive-suite",
        help="Export generated recipes as stock-compatible Bench2Drive route XML plus overlays.",
    )
    route_export_parser.add_argument("--recipe", type=Path, required=True)
    route_export_parser.add_argument("--recipe-id")
    route_export_parser.add_argument("--route-root", type=Path, default=Path("."))
    route_export_parser.add_argument("--behavior-id", default="no_signal_cut_in")
    route_export_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/simlingo.sample.yaml"),
    )
    route_export_parser.add_argument(
        "--no-simlingo-plan",
        action="store_true",
        help="Skip writing a SimLingo command plan beside the generated route suite.",
    )
    route_export_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    route_export_parser.add_argument("--run-id", default="bench2drive-route-pack")
    route_export_parser.set_defaults(func=_command_export_bench2drive_suite)

    overlay_parser = subparsers.add_parser(
        "plan-overlay-injection",
        help="Compile DriverX route-pack overlays into dry-run companion CARLA scripts.",
    )
    overlay_parser.add_argument("--route-pack", type=Path, required=True)
    overlay_parser.add_argument(
        "--behavior-id",
        help="Override the behavior id stored in the route-pack overlays.",
    )
    overlay_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    overlay_parser.add_argument("--run-id", default="overlay-injection")
    overlay_parser.set_defaults(func=_command_plan_overlay_injection)

    overlay_run_parser = subparsers.add_parser(
        "run-overlay-injection",
        help="Run companion CARLA overlay actors from a TASK-021 plan.",
    )
    overlay_run_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/carla_local.sample.yaml"),
    )
    overlay_run_parser.add_argument("--plan", type=Path, required=True)
    overlay_run_parser.add_argument("--host")
    overlay_run_parser.add_argument("--port", type=int)
    overlay_run_parser.add_argument("--timeout-s", type=float)
    overlay_run_parser.add_argument("--route-limit", type=int)
    overlay_run_parser.add_argument("--tick-limit", type=int)
    overlay_run_parser.add_argument("--no-wait-for-tick", action="store_true")
    overlay_run_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    overlay_run_parser.add_argument("--run-id", default="overlay-injection-run")
    overlay_run_parser.set_defaults(func=_command_run_overlay_injection)

    overlay_evidence_parser = subparsers.add_parser(
        "build-overlay-evidence",
        help="Bundle overlay injection run evidence with recipe and behavior assertions.",
    )
    overlay_evidence_parser.add_argument("--overlay-plan", type=Path, required=True)
    overlay_evidence_parser.add_argument("--overlay-run", type=Path)
    overlay_evidence_parser.add_argument("--route-evidence", type=Path)
    overlay_evidence_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    overlay_evidence_parser.add_argument("--run-id", default="overlay-evidence")
    overlay_evidence_parser.set_defaults(func=_command_build_overlay_evidence)

    smoke_parser = subparsers.add_parser(
        "smoke-carla",
        help="Check whether a CARLA server TCP port is reachable.",
    )
    smoke_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/carla_local.sample.yaml"),
    )
    smoke_parser.set_defaults(func=_command_smoke_carla)

    probe_parser = subparsers.add_parser(
        "probe-carla",
        help="Collect CARLA Python API state into JSON/Markdown artifacts.",
    )
    probe_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/carla_local.sample.yaml"),
    )
    probe_parser.add_argument("--host")
    probe_parser.add_argument("--port", type=int)
    probe_parser.add_argument("--timeout-s", type=float)
    probe_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    probe_parser.add_argument("--run-id", default="carla-probe")
    probe_parser.set_defaults(func=_command_probe_carla)

    ego_parser = subparsers.add_parser(
        "spawn-ego-smoke",
        help="Spawn one CARLA ego vehicle and camera, capture tracks, then clean up.",
    )
    ego_parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/carla_local.sample.yaml"),
    )
    ego_parser.add_argument("--host")
    ego_parser.add_argument("--port", type=int)
    ego_parser.add_argument("--timeout-s", type=float)
    ego_parser.add_argument("--tick-count", type=int, default=5)
    ego_parser.add_argument("--camera-width", type=int, default=320)
    ego_parser.add_argument("--camera-height", type=int, default=180)
    ego_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    ego_parser.add_argument("--run-id", default="ego-smoke")
    ego_parser.set_defaults(func=_command_spawn_ego_smoke)

    behavior_parser = subparsers.add_parser(
        "generate-behaviors",
        help="Generate deterministic OOD behavior traces and metrics.",
    )
    behavior_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    behavior_parser.add_argument("--run-id", default="behavior-suite")
    behavior_parser.set_defaults(func=_command_generate_behaviors)

    script_parser = subparsers.add_parser(
        "compile-carla-script",
        help="Compile one scenario recipe and behavior into a CARLA script plan.",
    )
    script_parser.add_argument("--recipe", type=Path, required=True)
    script_parser.add_argument("--recipe-id")
    script_parser.add_argument("--behavior-id", default="no_signal_cut_in")
    script_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    script_parser.add_argument("--run-id", default="carla-script")
    script_parser.set_defaults(func=_command_compile_carla_script)

    asset_parser = subparsers.add_parser(
        "plan-assets",
        help="Plan generated OOD assets and optional scenario recipe references.",
    )
    asset_parser.add_argument("--provider", choices=["dry_run", "meshy"], default="dry_run")
    asset_parser.add_argument("--api-key")
    asset_parser.add_argument("--recipe", type=Path)
    asset_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    asset_parser.add_argument("--run-id", default="asset-plan")
    asset_parser.set_defaults(func=_command_plan_assets)

    policy_parser = subparsers.add_parser(
        "run-policy-fixture",
        help="Run one fixture through a selected policy adapter.",
    )
    policy_parser.add_argument(
        "--policy",
        choices=["mock", "mock-memory", "hybrid", "vlm-api", "simlingo", "carllava", "alpamayo"],
        default="mock",
    )
    policy_parser.add_argument("--fixture", default="construction_merge")
    policy_parser.add_argument("--with-memory", action="store_true")
    policy_parser.add_argument("--memory", type=Path)
    policy_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    policy_parser.add_argument("--run-id", default="policy-fixture")
    policy_parser.set_defaults(func=_command_run_policy_fixture)

    rag_parser = subparsers.add_parser(
        "run-rag-comparison",
        help="Compare one policy with and without retrieved safety memory.",
    )
    rag_parser.add_argument(
        "--policy",
        choices=["mock", "hybrid", "vlm-api", "simlingo", "carllava", "alpamayo"],
        default="mock",
    )
    rag_parser.add_argument("--fixture", default="construction_merge")
    rag_parser.add_argument("--behavior-id", default="motorcycle_filtering")
    rag_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    rag_parser.add_argument("--run-id", default="rag-comparison")
    rag_parser.set_defaults(func=_command_run_rag_comparison)

    ood_report_parser = subparsers.add_parser(
        "build-ood-suite-report",
        help="Build one JSON/Markdown manifest from generated OOD suite evidence artifacts.",
    )
    ood_report_parser.add_argument("--scenario-summary", type=Path)
    ood_report_parser.add_argument("--route-pack", type=Path)
    ood_report_parser.add_argument("--overlay-plan", type=Path)
    ood_report_parser.add_argument("--sidecar-plan", type=Path)
    ood_report_parser.add_argument("--sidecar-run", type=Path)
    ood_report_parser.add_argument("--rag-comparison", type=Path)
    ood_report_parser.add_argument("--simlingo-result", type=Path)
    ood_report_parser.add_argument("--blockers", type=Path)
    ood_report_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    ood_report_parser.add_argument("--run-id", default="ood-suite-report")
    ood_report_parser.set_defaults(func=_command_build_ood_suite_report)

    from driverx.pipeline.submission_dossier_cli import register_submission_dossier_parser
    from driverx.pipeline.submission_demo_pack_cli import register_submission_demo_pack_parser
    from driverx.pipeline.generated_ood_suite_cli import register_generated_ood_suite_parser
    from driverx.pipeline.route_evidence_cli import register_route_evidence_parser
    from driverx.policies.alpamayo_input_cli import register_alpamayo_input_parser
    from driverx.policies.alpamayo_offline_cli import register_alpamayo_offline_parser
    from driverx.policies.alpamayo_probe_cli import register_alpamayo_probe_parser
    from driverx.policies.alpamayo_release_cli import register_alpamayo_release_parser
    from driverx.policies.alpamayo_shape_probe_cli import register_alpamayo_shape_probe_parser
    from driverx.policies.alpamayo_trajectory_cli import register_alpamayo_trajectory_parser
    from driverx.policies.runtime_matrix_cli import register_policy_runtime_matrix_parser
    from driverx.remote.runpod_cli import register_runpod_remote_parser
    from driverx.simulators.simlingo_cli import register_simlingo_parsers
    from driverx.simulators.carla_alpamayo_capture_cli import register_carla_alpamayo_capture_parser
    from driverx.simulators.gpu_host_cli import register_gpu_host_parser
    from driverx.simulators.route_video_assembly_cli import register_route_video_assembly_parser
    from driverx.simulators.fail2drive_route_runner_cli import register_fail2drive_route_runner_parser

    register_generated_ood_suite_parser(subparsers)
    register_route_evidence_parser(subparsers)
    register_alpamayo_input_parser(subparsers)
    register_alpamayo_offline_parser(subparsers)
    register_alpamayo_probe_parser(subparsers)
    register_alpamayo_shape_probe_parser(subparsers)
    register_alpamayo_release_parser(subparsers)
    register_alpamayo_trajectory_parser(subparsers)
    register_policy_runtime_matrix_parser(subparsers)
    register_runpod_remote_parser(subparsers)
    register_simlingo_parsers(subparsers)
    register_carla_alpamayo_capture_parser(subparsers)
    register_gpu_host_parser(subparsers)
    register_route_video_assembly_parser(subparsers)
    register_fail2drive_route_runner_parser(subparsers)
    register_submission_dossier_parser(subparsers)
    register_submission_demo_pack_parser(subparsers)

    config_parser = subparsers.add_parser(
        "show-config",
        help="Print the resolved config.",
    )
    _add_config_arg(config_parser)
    config_parser.set_defaults(func=_command_show_config)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (FileNotFoundError, ImportError, IndexError, OSError, ValueError) as exc:
        print(f"driverx error: {exc}", file=sys.stderr)
        return 2


__all__ = ["DriverConfig", "build_parser", "main"]
