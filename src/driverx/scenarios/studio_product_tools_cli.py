"""Agent-facing OODrive tool manifest CLI registration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_tools_runtime import run_studio_artifacts_list, run_studio_tools_manifest


def register_tools_commands(nested: argparse._SubParsersAction) -> None:
    tools = nested.add_parser("tools-manifest", help="Emit machine-readable OODrive tool contracts for coding agents.")
    tools.add_argument("--output-root", type=Path)
    tools.add_argument("--run-id", default="oodrive-tools-manifest")
    tools.add_argument("--stable-only", action="store_true")
    tools.set_defaults(func=_command_tools_manifest)

    artifacts = nested.add_parser("artifacts-list", help="Index recent OODrive artifacts for agent workflows.")
    artifacts.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    artifacts.add_argument("--run-id", default="oodrive-artifacts-index")
    artifacts.add_argument("--limit", type=int, default=50)
    artifacts.set_defaults(func=_command_artifacts_list)


def _print(result: StudioCommandResult) -> int:
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_tools_manifest(args: argparse.Namespace) -> int:
    return _print(
        run_studio_tools_manifest(
            output_root=args.output_root,
            run_id=args.run_id,
            include_experimental=not args.stable_only,
        )
    )


def _command_artifacts_list(args: argparse.Namespace) -> int:
    return _print(run_studio_artifacts_list(output_root=args.output_root, run_id=args.run_id, limit=args.limit))


__all__ = ["register_tools_commands"]
