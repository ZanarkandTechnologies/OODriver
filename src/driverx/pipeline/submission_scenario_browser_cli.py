"""CLI for V6 scenario browser and submission pack generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.pipeline.submission_scenario_browser import (
    SubmissionBrowserInputs,
    build_submission_scenario_browser,
)


def register_submission_scenario_browser_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "build-submission-scenario-browser",
        help="Build static scenario browser, V6 dossier, and video script from catalog evidence.",
    )
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--policy-evaluation", type=Path)
    parser.add_argument("--blockers", type=Path, default=Path("blockers.md"))
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="submission-scenario-browser")
    parser.set_defaults(func=_command_build_submission_scenario_browser)


def _command_build_submission_scenario_browser(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    outputs = build_submission_scenario_browser(
        SubmissionBrowserInputs(
            catalog_path=args.catalog,
            policy_evaluation_path=args.policy_evaluation,
            blockers_path=args.blockers,
        ),
        run_dir,
    )
    print(json.dumps(outputs.to_jsonable(), indent=2))
    return 0


__all__ = ["register_submission_scenario_browser_parser"]
