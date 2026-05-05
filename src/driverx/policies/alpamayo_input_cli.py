"""CLI glue for Alpamayo input package manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.datasets.fixtures import load_fixture_frame
from driverx.policies.alpamayo_input import (
    build_alpamayo_input_package,
    write_alpamayo_input_package,
)
from driverx.policies.runner import memory_entries_from_json, sample_memory_entries


def command_build_alpamayo_input(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    memory_entries = None
    if args.memory:
        memory_entries = memory_entries_from_json(args.memory)
    elif args.with_memory:
        memory_entries = sample_memory_entries()
    package = build_alpamayo_input_package(
        load_fixture_frame(args.fixture),
        nav_text=args.nav_text,
        memory_entries=memory_entries,
    )
    summary = write_alpamayo_input_package(run_dir, package)
    print(json.dumps(summary, indent=2))
    return 0


def register_alpamayo_input_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "build-alpamayo-input",
        help="Build an Alpamayo-shaped input manifest from a fixture frame.",
    )
    parser.add_argument("--fixture", default="construction_merge")
    parser.add_argument("--nav-text")
    parser.add_argument("--with-memory", action="store_true")
    parser.add_argument("--memory", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="alpamayo-input")
    parser.set_defaults(func=command_build_alpamayo_input)


__all__ = [
    "command_build_alpamayo_input",
    "register_alpamayo_input_parser",
]
