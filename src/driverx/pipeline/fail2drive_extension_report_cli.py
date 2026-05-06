"""CLI for Fail2Drive reference/extension reporting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.pipeline.fail2drive_extension_report import (
    Fail2DriveExtensionReportConfig,
    run_fail2drive_extension_report,
)


def register_fail2drive_extension_report_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "build-fail2drive-extension-report",
        help="Map DriverX generated OOD cases to Fail2Drive reference families and memory entries.",
    )
    parser.add_argument("--source", type=Path, action="append", required=True)
    parser.add_argument("--fail2drive-root", type=Path)
    parser.add_argument("--memory-bank", type=Path)
    parser.add_argument("--fixture-seeds", type=Path, default=Path("tests/fixtures/fail2drive_like/seeds.json"))
    parser.add_argument("--fixture-results", type=Path, default=Path("tests/fixtures/fail2drive_like/results.json"))
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="fail2drive-extension-report")
    parser.set_defaults(func=_command_build_fail2drive_extension_report)


def _command_build_fail2drive_extension_report(args: argparse.Namespace) -> int:
    summary = run_fail2drive_extension_report(
        Fail2DriveExtensionReportConfig(
            generated_source_paths=tuple(args.source),
            output_root=args.output_root,
            run_id=args.run_id,
            fail2drive_root=args.fail2drive_root,
            memory_bank_path=args.memory_bank,
            fixture_seeds_path=args.fixture_seeds,
            fixture_results_path=args.fixture_results,
        )
    )
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_fail2drive_extension_report_parser"]
