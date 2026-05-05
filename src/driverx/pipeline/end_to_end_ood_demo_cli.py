"""CLI registration for the local OOD end-to-end demo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.pipeline.end_to_end_ood_demo import (
    EndToEndOodDemoConfig,
    run_end_to_end_ood_demo,
)


def register_end_to_end_ood_demo_parser(
    subparsers: argparse._SubParsersAction,
) -> None:
    parser = subparsers.add_parser(
        "run-end-to-end-ood-demo",
        help="Run a dependency-light generated OOD scenario through policy, controls, and local 2D simulation.",
    )
    parser.add_argument(
        "--scenario-config",
        type=Path,
        default=Path("configs/scenario_forge.sample.yaml"),
    )
    parser.add_argument("--fixture", default="construction_merge")
    parser.add_argument("--behavior-id", default="motorcycle_filtering")
    parser.add_argument("--mutation", default="regional_driving_behavior")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--memory-results",
        type=Path,
        default=Path("tests/fixtures/fail2drive_like/results.json"),
    )
    parser.add_argument("--memory-limit", type=int, default=3)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="local-ood-demo")
    parser.set_defaults(func=_command_run_end_to_end_ood_demo)


def _command_run_end_to_end_ood_demo(args: argparse.Namespace) -> int:
    summary = run_end_to_end_ood_demo(
        EndToEndOodDemoConfig(
            scenario_config_path=args.scenario_config,
            output_root=args.output_root,
            run_id=args.run_id,
            fixture=args.fixture,
            behavior_id=args.behavior_id,
            mutation=args.mutation,
            random_seed=args.seed,
            memory_results_path=args.memory_results,
            memory_limit=args.memory_limit,
        )
    )
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_end_to_end_ood_demo_parser"]
