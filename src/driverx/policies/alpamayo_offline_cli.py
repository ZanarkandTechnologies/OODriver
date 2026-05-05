"""CLI glue for offline Alpamayo policy rehearsal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.policies.alpamayo_offline import run_alpamayo_offline_fixture
from driverx.policies.runner import memory_entries_from_json, sample_memory_entries


def command_run_alpamayo_offline(args: argparse.Namespace) -> int:
    memory_entries = None
    if args.memory:
        memory_entries = memory_entries_from_json(args.memory)
    elif args.with_memory:
        memory_entries = sample_memory_entries()
    summary = run_alpamayo_offline_fixture(
        fixture=args.fixture,
        prediction_json=args.prediction_json,
        output_root=args.output_root,
        run_id=args.run_id,
        nav_text=args.nav_text,
        memory_entries=memory_entries,
        sample_index=args.sample_index,
    )
    print(json.dumps(summary, indent=2))
    return 0


def register_alpamayo_offline_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "run-alpamayo-offline",
        help="Rehearse Alpamayo input/conversion/policy artifacts from saved pred_xyz JSON.",
    )
    parser.add_argument("--fixture", default="construction_merge")
    parser.add_argument("--prediction-json", type=Path, required=True)
    parser.add_argument("--nav-text")
    parser.add_argument("--with-memory", action="store_true")
    parser.add_argument("--memory", type=Path)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="alpamayo-offline-policy")
    parser.set_defaults(func=command_run_alpamayo_offline)


__all__ = [
    "command_run_alpamayo_offline",
    "register_alpamayo_offline_parser",
]
