"""OODrive choreography CLI registration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_choreography_runtime import (
    run_studio_choreograph,
    run_studio_score_choreography,
)


def register_choreography_commands(nested: argparse._SubParsersAction) -> None:
    choreograph = nested.add_parser(
        "choreograph",
        help="Build timed actor/object choreography for bad-path CARLA scenarios.",
    )
    choreograph.add_argument("description", nargs="*", help="Choreography prompt.")
    choreograph.add_argument("--prompt", action="append", default=[])
    choreograph.add_argument("--case-id", action="append", default=[])
    choreograph.add_argument("--template-id", action="append", default=[])
    choreograph.add_argument("--behavior-id", action="append", default=[])
    choreograph.add_argument("--object-kind", action="append", default=[])
    choreograph.add_argument("--severity", type=int, default=4)
    choreograph.add_argument("--seed", type=int, default=41)
    choreograph.add_argument("--output-root", type=Path)
    choreograph.add_argument("--run-id", default="oodrive-choreography")
    choreograph.set_defaults(func=_command_choreograph)

    score = nested.add_parser(
        "score-choreography",
        help="Score a timed actor/object choreography manifest.",
    )
    score.add_argument("--choreography-manifest", type=Path, required=True)
    score.add_argument("--output-root", type=Path)
    score.add_argument("--run-id")
    score.add_argument("--metric-only", action="store_true")
    score.set_defaults(func=_command_score_choreography)


def _print(result: StudioCommandResult) -> int:
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_choreograph(args: argparse.Namespace) -> int:
    prompt_parts = [" ".join(args.description).strip(), *[item.strip() for item in args.prompt if item.strip()]]
    prompt = " ; ".join(part for part in prompt_parts if part)
    if not prompt:
        raise ValueError("Pass a choreography description or --prompt.")
    return _print(
        run_studio_choreograph(
            prompt=prompt,
            case_ids=tuple(args.case_id),
            template_ids=tuple(args.template_id) or ("construction_lane_closure",),
            behavior_ids=tuple(args.behavior_id),
            object_kinds=tuple(args.object_kind),
            severity=args.severity,
            seed=args.seed,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_score_choreography(args: argparse.Namespace) -> int:
    result = run_studio_score_choreography(
        choreography_manifest_path=args.choreography_manifest,
        output_root=args.output_root,
        run_id=args.run_id,
    )
    if args.metric_only:
        print(f"METRIC scenario_choreography_score={result.summary['scenario_choreography_score']:.4f}")
        return 0
    return _print(result)


__all__ = ["register_choreography_commands"]
