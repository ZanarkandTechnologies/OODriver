"""Product-facing OODrive CLI wrapper."""

from __future__ import annotations

import sys
from typing import Sequence

from driverx.scenarios.studio_product_cli import build_oodrive_parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the OODrive CLI without exposing the internal DriverX command group."""

    parser = build_oodrive_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (FileNotFoundError, ImportError, IndexError, OSError, ValueError) as exc:
        print(f"oodrive error: {exc}", file=sys.stderr)
        return 2


__all__ = ["main"]
