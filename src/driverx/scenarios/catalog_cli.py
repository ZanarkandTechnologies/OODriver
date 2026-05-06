"""CLI entrypoints for Scenario Studio catalog management."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.scenarios.catalog import (
    PromotionDecision,
    ScenarioQuery,
    filter_catalog,
    index_scenario_artifacts,
    load_scenario_catalog,
    promote_scenario,
    write_scenario_catalog_outputs,
    write_scenario_selection,
)


def register_scenario_catalog_parser(subparsers: argparse._SubParsersAction) -> None:
    index_parser = subparsers.add_parser(
        "index-scenarios",
        help="Index generated scenario evidence into a Scenario Studio catalog.",
    )
    index_parser.add_argument("--artifact-root", type=Path, action="append", required=True)
    index_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    index_parser.add_argument("--run-id", default="scenario-catalog")
    index_parser.set_defaults(func=_command_index_scenarios)

    list_parser = subparsers.add_parser(
        "list-scenarios",
        help="Filter and print records from a Scenario Studio catalog.",
    )
    list_parser.add_argument("--catalog", type=Path, required=True)
    _add_query_args(list_parser)
    list_parser.set_defaults(func=_command_list_scenarios)

    promote_parser = subparsers.add_parser(
        "promote-scenario",
        help="Update one scenario promotion decision in a catalog.",
    )
    promote_parser.add_argument("--catalog", type=Path, required=True)
    promote_parser.add_argument("--scenario-id", required=True)
    promote_parser.add_argument("--status", choices=["candidate", "hero", "failure_case", "rejected", "blocked"], required=True)
    promote_parser.add_argument("--reason")
    promote_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    promote_parser.add_argument("--run-id", default="scenario-catalog-promoted")
    promote_parser.set_defaults(func=_command_promote_scenario)

    selection_parser = subparsers.add_parser(
        "export-scenario-selection",
        help="Write a durable selection manifest from a filtered catalog.",
    )
    selection_parser.add_argument("--catalog", type=Path, required=True)
    _add_query_args(selection_parser)
    selection_parser.add_argument("--selection-id", default="scenario-selection")
    selection_parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    selection_parser.add_argument("--run-id", default="scenario-selection")
    selection_parser.set_defaults(func=_command_export_scenario_selection)


def _add_query_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--tag")
    parser.add_argument("--behavior-id")
    parser.add_argument("--status", choices=["candidate", "hero", "failure_case", "rejected", "blocked"])
    parser.add_argument("--requires-video", action="store_true")
    parser.add_argument("--requires-model-reasoning", action="store_true")
    parser.add_argument("--requires-road-aligned", action="store_true")


def _query_from_args(args: argparse.Namespace) -> ScenarioQuery:
    return ScenarioQuery(
        tag=args.tag,
        behavior_id=args.behavior_id,
        promotion_status=args.status,
        requires_video=bool(args.requires_video),
        requires_model_reasoning=bool(args.requires_model_reasoning),
        requires_road_aligned=bool(args.requires_road_aligned),
    )


def _command_index_scenarios(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    catalog = index_scenario_artifacts(list(args.artifact_root))
    summary = write_scenario_catalog_outputs(catalog, run_dir)
    print(json.dumps(summary, indent=2))
    return 0


def _command_list_scenarios(args: argparse.Namespace) -> int:
    catalog = load_scenario_catalog(args.catalog)
    records = filter_catalog(catalog, _query_from_args(args))
    print(json.dumps({"record_count": len(records), "records": [record.to_jsonable() for record in records]}, indent=2))
    return 0


def _command_promote_scenario(args: argparse.Namespace) -> int:
    catalog = load_scenario_catalog(args.catalog)
    updated = promote_scenario(
        catalog,
        args.scenario_id,
        PromotionDecision(status=args.status, reason=args.reason),
    )
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_scenario_catalog_outputs(updated, run_dir)
    print(json.dumps(summary, indent=2))
    return 0


def _command_export_scenario_selection(args: argparse.Namespace) -> int:
    catalog = load_scenario_catalog(args.catalog)
    records = filter_catalog(catalog, _query_from_args(args))
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_scenario_selection(records, run_dir, selection_id=args.selection_id)
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_scenario_catalog_parser"]
