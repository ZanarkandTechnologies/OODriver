"""CLI entrypoints for Scenario Workbench artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.workbench.bundle import ScenarioRunBundleInputs, build_scenario_run_bundle
from driverx.workbench.report import write_scenario_run_bundle


def register_scenario_workbench_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "build-scenario-workbench-bundle",
        help="Link Scenario Studio, CARLA, Alpamayo/RAG, risk, and curation artifacts into one bundle.",
    )
    parser.add_argument("--studio-batch", type=Path)
    parser.add_argument("--video-evidence", type=Path)
    parser.add_argument("--alpamayo-batch", type=Path)
    parser.add_argument("--final-pack", type=Path)
    parser.add_argument("--risk-timeline", type=Path)
    parser.add_argument("--memory-events", type=Path)
    parser.add_argument("--reasoning-events", type=Path)
    parser.add_argument("--scenario-id")
    parser.add_argument("--behavior-id")
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="scenario-workbench-bundle-v1")
    parser.set_defaults(func=_command_build_scenario_workbench_bundle)


def _command_build_scenario_workbench_bundle(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    bundle = build_scenario_run_bundle(
        ScenarioRunBundleInputs(
            studio_batch_path=args.studio_batch,
            video_evidence_path=args.video_evidence,
            alpamayo_batch_path=args.alpamayo_batch,
            final_pack_path=args.final_pack,
            risk_timeline_path=args.risk_timeline,
            memory_events_path=args.memory_events,
            reasoning_events_path=args.reasoning_events,
            scenario_id=args.scenario_id,
            behavior_id=args.behavior_id,
        )
    )
    summary = write_scenario_run_bundle(run_dir, bundle)
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_scenario_workbench_parser"]
