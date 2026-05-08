"""CARLA composer OODrive CLI registration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_carla_composer_runtime import (
    run_studio_carla_catalog,
    run_studio_carla_compose,
    run_studio_carla_control,
    run_studio_carla_matrix,
    run_studio_carla_suite,
    run_studio_score_carla_suite,
)


def register_carla_composer_commands(nested: argparse._SubParsersAction) -> None:
    carla_catalog = nested.add_parser(
        "carla-catalog",
        help="Show agent-facing CARLA town, weather, environment, behavior, and object controls.",
    )
    carla_catalog.set_defaults(func=_command_carla_catalog)

    carla_matrix = nested.add_parser(
        "carla-matrix",
        help="Write the installed CARLA capability matrix used to constrain generated suites.",
    )
    carla_matrix.add_argument("--output-root", type=Path)
    carla_matrix.add_argument("--run-id", default="oodrive-carla-capability-matrix")
    carla_matrix.set_defaults(func=_command_carla_matrix)

    carla_control = nested.add_parser(
        "carla-control",
        help="Directly control live CARLA maps, weather, and screenshot capture for agents.",
    )
    carla_control.add_argument("--host", default="127.0.0.1")
    carla_control.add_argument("--port", type=int, default=2000)
    carla_control.add_argument("--timeout-s", type=float, default=30.0)
    carla_control.add_argument("--town")
    carla_control.add_argument("--map-name")
    carla_control.add_argument("--load-map", action="store_true")
    carla_control.add_argument(
        "--weather-preset",
        choices=["clear_day", "wet_overcast", "night_rain_fog", "low_sun_glare", "flooded_surface"],
    )
    carla_control.add_argument("--capture", action="store_true")
    carla_control.add_argument("--spawn-index", type=int, default=0)
    carla_control.add_argument("--output-root", type=Path)
    carla_control.add_argument("--run-id", default="oodrive-carla-control")
    carla_control.set_defaults(func=_command_carla_control)

    carla_compose = nested.add_parser(
        "carla-compose",
        help="Compose a varied CARLA scenario from town, weather, props, behaviors, and background traffic.",
    )
    carla_compose.add_argument("description", nargs="*", help="Scenario composition prompt.")
    carla_compose.add_argument("--prompt", action="append", default=[], help="Additional prompt text. Useful for scripts.")
    carla_compose.add_argument("--town", help="Friendly CARLA town selector, e.g. Town03 or Town10HD.")
    carla_compose.add_argument("--map-name", help="Exact CARLA map name, e.g. Town05_Opt.")
    carla_compose.add_argument("--load-map", action="store_true", help="Ask CARLA to load the selected map in live mode.")
    carla_compose.add_argument("--weather-preset", default="wet_overcast")
    carla_compose.add_argument("--template-id", action="append", default=[])
    carla_compose.add_argument("--behavior-id", action="append", default=[])
    carla_compose.add_argument("--object-kind", action="append", default=[])
    carla_compose.add_argument("--severity", type=int, default=4)
    carla_compose.add_argument("--seed", type=int, default=41)
    carla_compose.add_argument("--road-anchor-spawn-index", type=int, default=0)
    carla_compose.add_argument("--background-vehicle-count", type=int, default=6)
    carla_compose.add_argument("--background-pedestrian-count", type=int, default=4)
    carla_compose.add_argument("--backend", choices=["dry-run", "fake-carla", "carla-live"], default="dry-run")
    carla_compose.add_argument("--output-root", type=Path)
    carla_compose.add_argument("--run-id", default="oodrive-carla-composition")
    carla_compose.set_defaults(func=_command_carla_compose)

    carla_suite = nested.add_parser(
        "carla-suite",
        help="Generate a capability-matrix-gated 10-case CARLA scenario suite.",
    )
    carla_suite.add_argument("--capability-matrix", type=Path)
    carla_suite.add_argument("--probe-capabilities", action="store_true")
    carla_suite.add_argument("--count", type=int, default=10)
    carla_suite.add_argument("--seed", type=int, default=41)
    carla_suite.add_argument("--backend", choices=["dry-run", "fake-carla", "carla-live"], default="fake-carla")
    carla_suite.add_argument("--output-root", type=Path)
    carla_suite.add_argument("--run-id", default="oodrive-carla-suite")
    carla_suite.set_defaults(func=_command_carla_suite)

    score_suite = nested.add_parser(
        "score-carla-suite",
        help="Score a CARLA capability matrix and generated suite manifest.",
    )
    score_suite.add_argument("--suite-manifest", type=Path, required=True)
    score_suite.add_argument("--capability-matrix", type=Path)
    score_suite.add_argument("--output-root", type=Path)
    score_suite.add_argument("--run-id", default="oodrive-carla-suite-score")
    score_suite.add_argument("--metric-only", action="store_true")
    score_suite.set_defaults(func=_command_score_carla_suite)


def _print(result: StudioCommandResult) -> int:
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_carla_catalog(args: argparse.Namespace) -> int:
    del args
    return _print(run_studio_carla_catalog())


def _command_carla_matrix(args: argparse.Namespace) -> int:
    return _print(
        run_studio_carla_matrix(
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_carla_control(args: argparse.Namespace) -> int:
    return _print(
        run_studio_carla_control(
            town=args.town,
            map_name=args.map_name,
            load_map=args.load_map,
            weather_preset_name=args.weather_preset,
            capture=args.capture,
            spawn_index=args.spawn_index,
            host=args.host,
            port=args.port,
            timeout_s=args.timeout_s,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_carla_compose(args: argparse.Namespace) -> int:
    prompt_parts = [" ".join(args.description).strip(), *[item.strip() for item in args.prompt if item.strip()]]
    prompt = " ; ".join(part for part in prompt_parts if part)
    if not prompt:
        raise ValueError("Pass a CARLA composition description or --prompt.")
    return _print(
        run_studio_carla_compose(
            prompt=prompt,
            town=args.town,
            map_name=args.map_name,
            load_map=args.load_map,
            weather_preset_name=args.weather_preset,
            template_ids=tuple(args.template_id),
            behavior_ids=tuple(args.behavior_id),
            object_kinds=tuple(args.object_kind),
            severity=args.severity,
            seed=args.seed,
            road_anchor_spawn_index=args.road_anchor_spawn_index,
            background_vehicle_count=args.background_vehicle_count,
            background_pedestrian_count=args.background_pedestrian_count,
            backend=args.backend,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_carla_suite(args: argparse.Namespace) -> int:
    return _print(
        run_studio_carla_suite(
            capability_matrix_path=args.capability_matrix,
            probe_capabilities=args.probe_capabilities,
            count=args.count,
            seed=args.seed,
            backend=args.backend,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_score_carla_suite(args: argparse.Namespace) -> int:
    result = run_studio_score_carla_suite(
        suite_manifest_path=args.suite_manifest,
        capability_matrix_path=args.capability_matrix,
        output_root=args.output_root,
        run_id=args.run_id,
    )
    if args.metric_only:
        print(f"METRIC carla_capability_suite_score={result.summary['carla_capability_suite_score']:.4f}")
        return 0
    return _print(result)


__all__ = ["register_carla_composer_commands"]
