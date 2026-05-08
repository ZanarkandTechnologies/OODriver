"""Closed-loop OODrive CLI registration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_closed_loop_runtime import (
    run_studio_closed_loop_video,
    run_studio_closed_loop_run,
    run_studio_infer,
    run_studio_score_closed_loop,
    run_studio_score_closed_loop_integration,
    run_studio_score_closed_loop_video,
)


def register_closed_loop_commands(nested: argparse._SubParsersAction) -> None:
    closed_loop_run = nested.add_parser(
        "closed-loop-run",
        help="Run a paused receding-horizon closed-loop CARLA policy trace.",
    )
    closed_loop_run.add_argument("--db", type=Path)
    closed_loop_run.add_argument("--scenario-id")
    closed_loop_run.add_argument("--backend", choices=["fake-carla", "carla-live"], default="fake-carla")
    closed_loop_run.add_argument(
        "--policy",
        choices=["fake-trajectory", "cached-decision", "alpamayo-remote"],
        default="fake-trajectory",
    )
    closed_loop_run.add_argument("--output-root", type=Path)
    closed_loop_run.add_argument("--run-id", default="oodrive-closed-loop-run")
    closed_loop_run.add_argument("--steps", type=int, default=3)
    closed_loop_run.add_argument("--control-ticks-per-step", type=int, default=4)
    closed_loop_run.add_argument("--host", default="127.0.0.1")
    closed_loop_run.add_argument("--port", type=int, default=2000)
    closed_loop_run.add_argument("--timeout-s", type=float, default=45.0)
    closed_loop_run.add_argument("--town")
    closed_loop_run.add_argument("--map-name")
    closed_loop_run.add_argument("--load-map", action="store_true")
    closed_loop_run.add_argument("--weather-preset")
    closed_loop_run.add_argument("--camera-width", type=int, default=640)
    closed_loop_run.add_argument("--camera-height", type=int, default=360)
    closed_loop_run.add_argument("--camera-fov", type=float, default=90.0)
    closed_loop_run.add_argument("--cache-root", type=Path)
    closed_loop_run.add_argument("--remote-output-root")
    closed_loop_run.add_argument("--alpamayo-python", type=Path)
    closed_loop_run.add_argument("--alpamayo-command")
    closed_loop_run.set_defaults(func=_command_closed_loop_run)

    infer = nested.add_parser(
        "infer",
        help="Run or prepare a fake/cached/remote Alpamayo inference request for one checkpoint package.",
    )
    infer.add_argument("--package", dest="package_path", type=Path, required=True)
    infer.add_argument("--mode", choices=["fake", "cached-json", "remote-kasm"], default="fake")
    infer.add_argument("--prediction-json", type=Path)
    infer.add_argument("--cache-root", type=Path)
    infer.add_argument("--remote-output-root")
    infer.add_argument("--alpamayo-python", type=Path)
    infer.add_argument("--alpamayo-command")
    infer.add_argument("--timeout-s", type=float, default=180.0)
    infer.add_argument("--retries", type=int, default=0)
    infer.add_argument("--output-root", type=Path)
    infer.add_argument("--run-id", default="oodrive-infer")
    infer.set_defaults(func=_command_infer)

    score_closed_loop = nested.add_parser(
        "score-closed-loop",
        help="Score whether a trace honestly proves closed-loop policy control.",
    )
    score_closed_loop.add_argument("--trace", dest="trace_path", type=Path, required=True)
    score_closed_loop.add_argument("--output-root", type=Path)
    score_closed_loop.add_argument("--run-id")
    score_closed_loop.add_argument("--metric-only", action="store_true")
    score_closed_loop.set_defaults(func=_command_score_closed_loop)

    score_closed_loop_integration = nested.add_parser(
        "score-closed-loop-integration",
        help="Score hardened closed-loop integration readiness.",
    )
    score_closed_loop_integration.add_argument("--trace", dest="trace_path", type=Path, required=True)
    score_closed_loop_integration.add_argument("--output-root", type=Path)
    score_closed_loop_integration.add_argument("--run-id")
    score_closed_loop_integration.add_argument("--metric-only", action="store_true")
    score_closed_loop_integration.set_defaults(func=_command_score_closed_loop_integration)

    closed_loop_video = nested.add_parser(
        "closed-loop-video",
        help="Render a compact paused closed-loop hero MP4 from trace frames.",
    )
    closed_loop_video.add_argument("--trace", dest="trace_path", type=Path, required=True)
    closed_loop_video.add_argument("--rgb-folder", type=Path)
    closed_loop_video.add_argument("--source-video", type=Path)
    closed_loop_video.add_argument("--scenario-pack", type=Path)
    closed_loop_video.add_argument("--output-video", type=Path)
    closed_loop_video.add_argument("--output-root", type=Path)
    closed_loop_video.add_argument("--run-id", default="closed-loop-video")
    closed_loop_video.add_argument("--fps", type=int, default=24)
    closed_loop_video.add_argument("--duration-s", type=float, default=0.0)
    closed_loop_video.set_defaults(func=_command_closed_loop_video)

    score_closed_loop_video = nested.add_parser(
        "score-closed-loop-video",
        help="Score whether a closed-loop MP4 is strong enough for live hero promotion.",
    )
    score_closed_loop_video.add_argument("--trace", dest="trace_path", type=Path, required=True)
    score_closed_loop_video.add_argument("--manifest", dest="manifest_path", type=Path)
    score_closed_loop_video.add_argument("--video", dest="video_path", type=Path)
    score_closed_loop_video.add_argument("--output-root", type=Path)
    score_closed_loop_video.add_argument("--run-id")
    score_closed_loop_video.add_argument("--metric-only", action="store_true")
    score_closed_loop_video.set_defaults(func=_command_score_closed_loop_video)


def _print(result: StudioCommandResult) -> int:
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_closed_loop_run(args: argparse.Namespace) -> int:
    return _print(
        run_studio_closed_loop_run(
            db_path=args.db,
            scenario_id=args.scenario_id,
            backend=args.backend,
            policy=args.policy,
            output_root=args.output_root,
            run_id=args.run_id,
            steps=args.steps,
            control_ticks_per_step=args.control_ticks_per_step,
            host=args.host,
            port=args.port,
            timeout_s=args.timeout_s,
            town=args.town,
            map_name=args.map_name,
            load_map=args.load_map,
            weather_preset=args.weather_preset,
            camera_width=args.camera_width,
            camera_height=args.camera_height,
            camera_fov=args.camera_fov,
            cache_root=args.cache_root,
            remote_output_root=args.remote_output_root,
            alpamayo_python=args.alpamayo_python,
            alpamayo_command=args.alpamayo_command,
        )
    )


def _command_infer(args: argparse.Namespace) -> int:
    return _print(
        run_studio_infer(
            package_path=args.package_path,
            mode=args.mode,
            prediction_json=args.prediction_json,
            cache_root=args.cache_root,
            remote_output_root=args.remote_output_root,
            alpamayo_python=args.alpamayo_python,
            alpamayo_command=args.alpamayo_command,
            timeout_s=args.timeout_s,
            retries=args.retries,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_score_closed_loop(args: argparse.Namespace) -> int:
    result = run_studio_score_closed_loop(
        trace_path=args.trace_path,
        output_root=args.output_root,
        run_id=args.run_id,
        metric_only=args.metric_only,
    )
    if args.metric_only:
        return 0 if result.status in {"passed", "blocked"} else 1
    return _print(result)


def _command_score_closed_loop_integration(args: argparse.Namespace) -> int:
    result = run_studio_score_closed_loop_integration(
        trace_path=args.trace_path,
        output_root=args.output_root,
        run_id=args.run_id,
        metric_only=args.metric_only,
    )
    if args.metric_only:
        return 0 if result.status in {"passed", "blocked"} else 1
    return _print(result)


def _command_closed_loop_video(args: argparse.Namespace) -> int:
    return _print(
        run_studio_closed_loop_video(
            trace_path=args.trace_path,
            rgb_folder=args.rgb_folder,
            source_video=args.source_video,
            scenario_pack=args.scenario_pack,
            output_video=args.output_video,
            output_root=args.output_root,
            run_id=args.run_id,
            fps=args.fps,
            duration_s=args.duration_s,
        )
    )


def _command_score_closed_loop_video(args: argparse.Namespace) -> int:
    result = run_studio_score_closed_loop_video(
        trace_path=args.trace_path,
        manifest_path=args.manifest_path,
        video_path=args.video_path,
        output_root=args.output_root,
        run_id=args.run_id,
        metric_only=args.metric_only,
    )
    if args.metric_only:
        return 0 if result.status in {"passed", "blocked"} else 1
    return _print(result)


__all__ = ["register_closed_loop_commands"]
