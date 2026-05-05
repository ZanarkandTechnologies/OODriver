"""CLI glue for Alpamayo tensor materialization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.policies.alpamayo_materializer import (
    materialize_alpamayo_input,
    write_alpamayo_tensor_materialization,
)


def command_materialize_alpamayo_input(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    manifest = materialize_alpamayo_input(args.package, image_root=args.image_root)
    summary = write_alpamayo_tensor_materialization(run_dir, manifest)
    print(json.dumps(summary, indent=2))
    return 0 if manifest.torch_ready else 2


def register_alpamayo_materializer_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "materialize-alpamayo-input",
        help="Validate a DriverX/CARLA Alpamayo package into a remote torch tensor contract.",
    )
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument(
        "--image-root",
        type=Path,
        help="Optional root for resolving relative image paths in the package.",
    )
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="alpamayo-materialized-input")
    parser.set_defaults(func=command_materialize_alpamayo_input)


__all__ = [
    "command_materialize_alpamayo_input",
    "register_alpamayo_materializer_parser",
]
