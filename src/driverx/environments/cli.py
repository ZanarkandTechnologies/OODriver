"""CLI entrypoint for deterministic environment forge runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.environments import EnvironmentSuiteConfig, load_environment_suite_config, run_environment_forge


def register_environment_forge_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "forge-environments",
        help="Generate deterministic CARLA environment variants and stock-proxy assets.",
    )
    parser.add_argument("--config", type=Path, default=Path("configs/environment_forge.sample.yaml"))
    parser.add_argument("--template-id", action="append")
    parser.add_argument("--severity", type=int)
    parser.add_argument("--count", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--run-id")
    parser.set_defaults(func=_command_forge_environments)


def _command_forge_environments(args: argparse.Namespace) -> int:
    config = load_environment_suite_config(args.config)
    overrides = {
        "template_ids": tuple(args.template_id) if args.template_id else config.template_ids,
        "severity": args.severity if args.severity is not None else config.severity,
        "count": args.count if args.count is not None else config.count,
        "random_seed": args.seed if args.seed is not None else config.random_seed,
        "output_root": args.output_root if args.output_root is not None else config.output_root,
        "run_id": args.run_id if args.run_id is not None else config.run_id,
    }
    summary = run_environment_forge(EnvironmentSuiteConfig(**overrides))
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_environment_forge_parser"]
