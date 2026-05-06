"""CLI entrypoint for Scenario Studio prompt-to-OOD generation."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from driverx.scenarios.studio import (
    ScenarioStudioConfig,
    generate_studio_batch,
    load_scenario_studio_config,
)


def register_scenario_studio_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "generate-scenario-studio",
        help="Compile natural-language OOD briefs into curated DriverX scenario candidates.",
    )
    parser.add_argument("--config", type=Path, default=Path("configs/scenario_studio.sample.json"))
    parser.add_argument("--prompt", action="append")
    parser.add_argument("--count-per-prompt", type=int)
    parser.add_argument("--severity", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--run-id")
    parser.set_defaults(func=_command_generate_scenario_studio)


def _command_generate_scenario_studio(args: argparse.Namespace) -> int:
    config = load_scenario_studio_config(args.config)
    if args.prompt:
        config = replace(config, prompts=tuple(args.prompt))
    if args.count_per_prompt is not None:
        config = replace(config, count_per_prompt=max(1, args.count_per_prompt))
    if args.severity is not None:
        config = replace(config, severity=max(1, min(5, args.severity)))
    if args.seed is not None:
        config = replace(config, random_seed=args.seed)
    if args.catalog is not None:
        config = replace(config, catalog_path=args.catalog)
    if args.output_root is not None:
        config = replace(config, output_root=args.output_root)
    if args.run_id is not None:
        config = replace(config, run_id=args.run_id)
    summary = generate_studio_batch(config)
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_scenario_studio_parser"]
