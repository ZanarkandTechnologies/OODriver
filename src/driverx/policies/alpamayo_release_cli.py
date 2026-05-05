"""CLI glue for Alpamayo release contract extraction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.policies.alpamayo_probe import DEFAULT_ALPAMAYO_MODEL_ID
from driverx.policies.alpamayo_release import (
    DEFAULT_ALPAMAYO_RELEASE_ROOT,
    write_alpamayo_release_contract,
)


def command_inspect_alpamayo_release(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_alpamayo_release_contract(
        run_dir,
        release_root=args.repo,
        model_id=args.model_id,
    )
    print(json.dumps(summary, indent=2))
    return 0


def register_alpamayo_release_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "inspect-alpamayo-release",
        help="Extract Alpamayo release input/output/runtime contract without loading weights.",
    )
    parser.add_argument("--repo", type=Path, default=DEFAULT_ALPAMAYO_RELEASE_ROOT)
    parser.add_argument("--model-id", default=DEFAULT_ALPAMAYO_MODEL_ID)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="alpamayo-release-contract")
    parser.set_defaults(func=command_inspect_alpamayo_release)


__all__ = [
    "command_inspect_alpamayo_release",
    "register_alpamayo_release_parser",
]
