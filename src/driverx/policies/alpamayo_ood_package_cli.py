"""CLI glue for building Alpamayo packages from OOD demo captures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.policies.alpamayo_ood_package import (
    AlpamayoOodPackageInputs,
    build_alpamayo_package_from_ood_demo,
    write_alpamayo_ood_package,
)
from driverx.policies.runner import memory_entries_from_json, sample_memory_entries


def command_build_alpamayo_ood_package(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    memory_context: list[dict[str, Any]] = []
    if args.memory:
        memory_context = [entry.to_jsonable() for entry in memory_entries_from_json(args.memory)]
    elif args.with_memory:
        memory_context = [entry.to_jsonable() for entry in sample_memory_entries()]
    package = build_alpamayo_package_from_ood_demo(
        AlpamayoOodPackageInputs(
            rgb_folder=args.rgb_folder,
            tracks_path=args.tracks,
            scenario_report_path=args.scenario_report,
            video_evidence_path=args.video_evidence,
            scenario_id=args.scenario_id,
            behavior_id=args.behavior_id,
            center_frame=args.center_frame,
            nav_text=args.nav_text,
            memory_context=memory_context,
        )
    )
    summary = write_alpamayo_ood_package(
        run_dir,
        package,
        source={
            "rgb_folder": str(args.rgb_folder),
            "tracks_path": str(args.tracks),
            "scenario_report_path": str(args.scenario_report) if args.scenario_report else None,
            "video_evidence_path": str(args.video_evidence) if args.video_evidence else None,
        },
    )
    print(json.dumps(summary, indent=2))
    return 0


def register_alpamayo_ood_package_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "build-alpamayo-ood-package",
        help="Build an Alpamayo package from live DriverX CARLA OOD frames.",
    )
    parser.add_argument("--rgb-folder", type=Path, required=True)
    parser.add_argument("--tracks", type=Path, required=True)
    parser.add_argument("--scenario-report", type=Path)
    parser.add_argument("--video-evidence", type=Path)
    parser.add_argument("--scenario-id")
    parser.add_argument("--behavior-id")
    parser.add_argument("--center-frame", type=int)
    parser.add_argument("--nav-text")
    parser.add_argument("--with-memory", action="store_true")
    parser.add_argument("--memory", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="alpamayo-ood-package")
    parser.set_defaults(func=command_build_alpamayo_ood_package)


__all__ = [
    "command_build_alpamayo_ood_package",
    "register_alpamayo_ood_package_parser",
]
