"""CLI for building the flagship OODrive scenario contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios.flagship import (
    build_flagship_scenario,
    load_flagship_config,
    write_flagship_scenario,
)


def register_flagship_scenario_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "build-flagship-oodrive-scenario",
        help="Write the flagship OODrive scenario contract and runtime command plan.",
    )
    parser.add_argument("--config", type=Path, default=Path("configs/oodrive_flagship_malaysia.yaml"))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--run-id")
    parser.set_defaults(func=_command_build_flagship_scenario)


def _command_build_flagship_scenario(args: argparse.Namespace) -> int:
    config = load_flagship_config(args.config)
    if args.output_root is not None or args.run_id is not None:
        config = type(config)(
            **{
                **config.__dict__,
                "output_root": args.output_root or config.output_root,
                "run_id": args.run_id or config.run_id,
            }
        )
    run_dir = prepare_run_dir(config.output_root, config.run_id)
    summary = write_flagship_scenario(run_dir, build_flagship_scenario(config))
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_flagship_scenario_parser"]
