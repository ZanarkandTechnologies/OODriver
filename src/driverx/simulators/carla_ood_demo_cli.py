"""CLI registration for the scripted CARLA OOD demo runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.assets import default_asset_requests, generate_assets_dry_run
from driverx.behaviors import default_behavior_plans, simulate_behavior
from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios import MutationPolicy, generate_scenario_recipes, load_scenario_seeds
from driverx.simulators.carla_ood_demo import (
    load_carla_ood_demo_config,
    run_carla_ood_demo,
    write_carla_ood_demo,
)


def register_carla_ood_demo_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "run-carla-ood-demo",
        help="Run a DriverX-owned scripted CARLA OOD demo and record RGB/tracks.",
    )
    parser.add_argument("--config", type=Path, default=Path("configs/carla_ood_demo.local.sample.yaml"))
    parser.add_argument("--recipe", type=Path)
    parser.add_argument("--recipe-id")
    parser.add_argument("--seeds", type=Path, default=Path("tests/fixtures/fail2drive_like/seeds.json"))
    parser.add_argument("--behavior-id")
    parser.add_argument("--tick-count", type=int)
    parser.add_argument(
        "--no-default-assets",
        action="store_true",
        help="Disable the default stock-proxy OOD asset manifests.",
    )
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="carla-ood-demo")
    parser.set_defaults(func=_command_run_carla_ood_demo)


def _command_run_carla_ood_demo(args: argparse.Namespace) -> int:
    from driverx.cli import _load_recipe

    config = load_carla_ood_demo_config(args.config)
    if args.tick_count is not None:
        config = type(config)(**{**config.__dict__, "tick_count": args.tick_count})
    behavior_id = args.behavior_id or config.behavior_id
    plans = {plan.behavior_id: plan for plan in default_behavior_plans()}
    if behavior_id not in plans:
        raise ValueError(f"Unknown behavior id: {behavior_id}")
    recipe = (
        _load_recipe(args.recipe, args.recipe_id)
        if args.recipe is not None
        else generate_scenario_recipes(
            load_scenario_seeds(args.seeds),
            MutationPolicy(mutations=("regional_driving_behavior",)),
            count=1,
            random_seed=7,
        )[0]
    )
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    result = run_carla_ood_demo(
        config,
        run_dir,
        recipe=recipe,
        behavior=simulate_behavior(plans[behavior_id]),
        asset_manifests=(
            []
            if args.no_default_assets
            else generate_assets_dry_run(default_asset_requests())
        ),
    )
    summary = write_carla_ood_demo(run_dir, result)
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_carla_ood_demo_parser"]
