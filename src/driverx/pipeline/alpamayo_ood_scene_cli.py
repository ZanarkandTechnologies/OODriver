"""CLI registration for scenario-linked Alpamayo OOD reasoning reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.pipeline.alpamayo_ood_scene import (
    AlpamayoOodSceneInputs,
    build_alpamayo_ood_scene_report,
)


def register_alpamayo_ood_scene_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "build-alpamayo-ood-scene",
        help="Build a scenario-linked Alpamayo reasoning report.",
    )
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--policy-decision", type=Path)
    parser.add_argument("--prediction", type=Path)
    parser.add_argument("--video-evidence", type=Path)
    parser.add_argument("--scenario-report", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="alpamayo-ood-scene")
    parser.set_defaults(func=_command_build_alpamayo_ood_scene)


def _command_build_alpamayo_ood_scene(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = build_alpamayo_ood_scene_report(
        run_dir,
        AlpamayoOodSceneInputs(
            package_path=args.package,
            policy_decision_path=args.policy_decision,
            prediction_path=args.prediction,
            video_evidence_path=args.video_evidence,
            scenario_report_path=args.scenario_report,
        ),
    )
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_alpamayo_ood_scene_parser"]
