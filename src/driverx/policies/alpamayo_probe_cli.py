"""CLI glue for Alpamayo offline probe reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.policies.alpamayo_probe import (
    DEFAULT_ALPAMAYO_MODEL_ID,
    write_alpamayo_probe_report,
)


def command_probe_alpamayo(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_alpamayo_probe_report(
        run_dir,
        artifact_root=args.artifact_root,
        model_id=args.model_id,
    )
    print(json.dumps(summary, indent=2))
    return 0


def register_alpamayo_probe_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "probe-alpamayo",
        help="Summarize remote Alpamayo probe artifacts and expected adapter schema.",
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        help="Directory containing pulled remote probe artifacts. Defaults to the new run dir.",
    )
    parser.add_argument("--model-id", default=DEFAULT_ALPAMAYO_MODEL_ID)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="alpamayo-probe")
    parser.set_defaults(func=command_probe_alpamayo)


__all__ = [
    "command_probe_alpamayo",
    "register_alpamayo_probe_parser",
]
