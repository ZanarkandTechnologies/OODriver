"""CARLA ScenarioRunner OODrive CLI registration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_scenario_runner_runtime import (
    run_studio_scenario_runner_package,
    run_studio_scenario_runner_run,
)


def register_scenario_runner_commands(nested: argparse._SubParsersAction) -> None:
    package = nested.add_parser("scenario-runner-package", help="Package OODrive artifacts for CARLA ScenarioRunner.")
    package.add_argument("--scenario-graph", type=Path)
    package.add_argument("--osc2", type=Path)
    package.add_argument("--sidecar", type=Path)
    package.add_argument("--output-root", type=Path)
    package.add_argument("--run-id", default="oodrive-scenario-runner-package")
    package.set_defaults(func=_command_scenario_runner_package)

    run = nested.add_parser("scenario-runner-run", help="Run a ScenarioRunner package if ScenarioRunner is installed.")
    run.add_argument("--package", type=Path, required=True)
    run.add_argument("--scenario-runner-root", type=Path)
    run.add_argument("--timeout-s", type=float, default=120.0)
    run.add_argument("--output-root", type=Path)
    run.add_argument("--run-id", default="oodrive-scenario-runner-run")
    run.set_defaults(func=_command_scenario_runner_run)


def _print(result: StudioCommandResult) -> int:
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_scenario_runner_package(args: argparse.Namespace) -> int:
    return _print(
        run_studio_scenario_runner_package(
            scenario_graph_path=args.scenario_graph,
            osc2_path=args.osc2,
            sidecar_path=args.sidecar,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_scenario_runner_run(args: argparse.Namespace) -> int:
    return _print(
        run_studio_scenario_runner_run(
            package_path=args.package,
            scenario_runner_root=args.scenario_runner_root,
            timeout_s=args.timeout_s,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


__all__ = ["register_scenario_runner_commands"]
