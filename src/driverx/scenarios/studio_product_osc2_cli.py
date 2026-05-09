"""OpenSCENARIO 2.0 OODrive CLI registration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_osc2_runtime import run_studio_run_osc2, run_studio_validate_osc2


def register_osc2_commands(nested: argparse._SubParsersAction) -> None:
    validate = nested.add_parser("validate-osc2", help="Validate an agent-authored ASAM OpenSCENARIO 2.0 .osc file.")
    validate.add_argument("--osc2", type=Path, required=True)
    validate.add_argument("--sidecar", type=Path)
    validate.add_argument("--output-root", type=Path)
    validate.add_argument("--run-id", default="oodrive-osc2-validation")
    validate.add_argument("--metric-only", action="store_true")
    validate.set_defaults(func=_command_validate_osc2)

    run = nested.add_parser("run-osc2", help="Run an OpenSCENARIO 2.0 .osc file through CARLA ScenarioRunner.")
    run.add_argument("--osc2", type=Path, required=True)
    run.add_argument("--scenario-runner-root", type=Path)
    run.add_argument("--timeout-s", type=float, default=120.0)
    run.add_argument("--output-root", type=Path)
    run.add_argument("--run-id", default="oodrive-osc2-run")
    run.set_defaults(func=_command_run_osc2)


def _print(result: StudioCommandResult) -> int:
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_validate_osc2(args: argparse.Namespace) -> int:
    result = run_studio_validate_osc2(
        osc2_path=args.osc2,
        sidecar_path=args.sidecar,
        output_root=args.output_root,
        run_id=args.run_id,
    )
    if args.metric_only:
        print(f"METRIC osc2_coverage_ratio={float(result.summary['coverage_ratio']):.4f}")
        print(f"METRIC osc2_status_passed={1.0 if result.status == 'passed' else 0.0:.4f}")
        return 0
    return _print(result)


def _command_run_osc2(args: argparse.Namespace) -> int:
    return _print(
        run_studio_run_osc2(
            osc2_path=args.osc2,
            scenario_runner_root=args.scenario_runner_root,
            timeout_s=args.timeout_s,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


__all__ = ["register_osc2_commands"]
