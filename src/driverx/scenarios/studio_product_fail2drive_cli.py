"""OODrive Fail2Drive extension commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.fail2drive.assets import (
    load_fail2drive_asset_catalog,
    qa_fail2drive_route_assets,
    write_fail2drive_asset_catalog_report,
    write_fail2drive_asset_qa,
)
from driverx.fail2drive.catalog import load_fail2drive_catalog, write_fail2drive_catalog_report
from driverx.fail2drive.demo_video import Fail2DriveDemoVideoConfig, run_fail2drive_demo_video
from driverx.fail2drive.model_reaction import Fail2DriveModelReactionConfig, run_fail2drive_model_reaction_suite
from driverx.fail2drive.reasoning import Fail2DriveReasoningRequest, run_fail2drive_reasoning
from driverx.fail2drive.route_authoring import (
    example_fail2drive_route_spec,
    load_fail2drive_route_spec,
    write_fail2drive_route_write_report,
    write_fail2drive_route_xml,
)
from driverx.fail2drive.route_validation import validate_fail2drive_route, write_fail2drive_route_validation
from driverx.fail2drive.run_wrapper import Fail2DriveRouteRunRequest, run_fail2drive_route_workflow


DEFAULT_F2D_ROOT = Path("third_party/fail2drive")


def register_fail2drive_commands(subparsers: Any) -> None:
    assets = subparsers.add_parser("f2d-assets", help="Emit the agent-readable Fail2Drive asset/blueprint catalog.")
    assets.add_argument("--fail2drive-root", type=Path, default=DEFAULT_F2D_ROOT)
    assets.add_argument("--scenario-hub-root", type=Path)
    assets.add_argument("--format", choices=["json", "md", "both"], default="both")
    assets.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    assets.add_argument("--run-id", default="oodrive-f2d-assets")
    assets.add_argument("--metric-only", action="store_true")
    assets.set_defaults(func=_command_f2d_assets)

    asset_qa = subparsers.add_parser("f2d-qa-assets", help="Gate a Fail2Drive route/render against prompt-required assets.")
    asset_qa.add_argument("--route", type=Path, required=True)
    asset_qa.add_argument("--prompt", required=True)
    asset_qa.add_argument("--fail2drive-root", type=Path, default=DEFAULT_F2D_ROOT)
    asset_qa.add_argument("--scenario-hub-root", type=Path)
    asset_qa.add_argument("--evidence-frame", type=Path, action="append", default=[])
    asset_qa.add_argument("--require-asset", action="append", default=[])
    asset_qa.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    asset_qa.add_argument("--run-id", default="oodrive-f2d-asset-qa")
    asset_qa.add_argument("--metric-only", action="store_true")
    asset_qa.set_defaults(func=_command_f2d_qa_assets)

    catalog = subparsers.add_parser("f2d-catalog", help="Emit the agent-readable Fail2Drive scenario catalog.")
    catalog.add_argument("--fail2drive-root", type=Path, default=DEFAULT_F2D_ROOT)
    catalog.add_argument("--format", choices=["json", "md", "both"], default="both")
    catalog.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    catalog.add_argument("--run-id", default="oodrive-f2d-catalog")
    catalog.add_argument("--metric-only", action="store_true")
    catalog.set_defaults(func=_command_f2d_catalog)

    validate = subparsers.add_parser("f2d-validate-route", help="Validate Fail2Drive route XML for agent-authored scenarios.")
    validate.add_argument("--route", type=Path, required=True)
    validate.add_argument("--fail2drive-root", type=Path, default=DEFAULT_F2D_ROOT)
    validate.add_argument("--strict", action="store_true")
    validate.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    validate.add_argument("--run-id", default="oodrive-f2d-validate-route")
    validate.add_argument("--metric-only", action="store_true")
    validate.set_defaults(func=_command_f2d_validate_route)

    write_route = subparsers.add_parser("f2d-write-route", help="Compile a JSON route spec into Fail2Drive XML.")
    write_route.add_argument("--spec", type=Path)
    write_route.add_argument("--example")
    write_route.add_argument("--output", type=Path)
    write_route.add_argument("--fail2drive-root", type=Path, default=DEFAULT_F2D_ROOT)
    write_route.add_argument("--validate", action="store_true")
    write_route.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    write_route.add_argument("--run-id", default="oodrive-f2d-write-route")
    write_route.add_argument("--metric-only", action="store_true")
    write_route.set_defaults(func=_command_f2d_write_route)

    run_route = subparsers.add_parser("f2d-run-route", help="Plan or run a Fail2Drive evaluator route with OODrive evidence.")
    run_route.add_argument("--route", type=Path, required=True)
    run_route.add_argument("--fail2drive-root", type=Path, default=DEFAULT_F2D_ROOT)
    run_route.add_argument("--agent", choices=["oodrive-capture", "pdm-lite", "human", "transfuser", "custom"], default="oodrive-capture")
    run_route.add_argument("--agent-path", type=Path)
    run_route.add_argument("--agent-config", type=Path)
    run_route.add_argument("--host", default="127.0.0.1")
    run_route.add_argument("--port", type=int, default=2000)
    run_route.add_argument("--track", default="MAP")
    run_route.add_argument("--live", action="store_true")
    run_route.add_argument("--dry-run", action="store_true")
    run_route.add_argument("--skip-validate", action="store_true")
    run_route.add_argument("--timeout-s", type=float, default=120.0)
    run_route.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    run_route.add_argument("--run-id", default="oodrive-f2d-run-route")
    run_route.add_argument("--metric-only", action="store_true")
    run_route.set_defaults(func=_command_f2d_run_route)

    reason = subparsers.add_parser("f2d-reason", help="Attach sampled Alpamayo-style reasoning to Fail2Drive route evidence.")
    reason.add_argument("--evidence", type=Path, required=True)
    reason.add_argument("--route", type=Path, required=True)
    reason.add_argument("--mode", choices=["fake", "cached", "alpamayo-local", "alpamayo-remote"], default="fake")
    reason.add_argument("--cached-reasoning", type=Path)
    reason.add_argument("--keyframes", type=int, default=6)
    reason.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    reason.add_argument("--run-id", default="oodrive-f2d-reason")
    reason.add_argument("--metric-only", action="store_true")
    reason.set_defaults(func=_command_f2d_reason)

    demo_video = subparsers.add_parser("f2d-demo-video", help="Export a Fail2Drive route/reasoning demo video report.")
    demo_video.add_argument("--evidence", type=Path, required=True)
    demo_video.add_argument("--reasoning", type=Path, required=True)
    demo_video.add_argument("--route", type=Path, required=True)
    demo_video.add_argument("--input-video", type=Path)
    demo_video.add_argument("--rgb-folder", type=Path)
    demo_video.add_argument("--speed-factor", type=float, default=4.0)
    demo_video.add_argument("--target-duration-s", type=float, default=90.0)
    demo_video.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    demo_video.add_argument("--run-id", default="oodrive-f2d-demo-video")
    demo_video.add_argument("--metric-only", action="store_true")
    demo_video.set_defaults(func=_command_f2d_demo_video)

    evaluate = subparsers.add_parser("f2d-evaluate-model", help="Build a Fail2Drive model-reaction matrix over route XML files.")
    evaluate.add_argument("--routes", type=Path, action="append", required=True)
    evaluate.add_argument("--fail2drive-root", type=Path, default=DEFAULT_F2D_ROOT)
    evaluate.add_argument("--agent", choices=["oodrive-capture", "pdm-lite", "human", "transfuser", "custom"], default="oodrive-capture")
    evaluate.add_argument("--limit", type=int)
    evaluate.add_argument("--reason", action="store_true")
    evaluate.add_argument("--demo-video", action="store_true")
    evaluate.add_argument("--live", action="store_true")
    evaluate.add_argument("--dry-run", action="store_true")
    evaluate.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    evaluate.add_argument("--run-id", default="oodrive-f2d-evaluate-model")
    evaluate.add_argument("--metric-only", action="store_true")
    evaluate.set_defaults(func=_command_f2d_evaluate_model)


def _command_f2d_assets(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    catalog = load_fail2drive_asset_catalog(args.fail2drive_root, scenario_hub_root=args.scenario_hub_root)
    summary = write_fail2drive_asset_catalog_report(run_dir, catalog, fmt=args.format)
    if args.metric_only:
        print(f"METRIC f2d_asset_count={summary['asset_count']}")
        return 0
    print(json.dumps(summary, indent=2))
    return 0


def _command_f2d_qa_assets(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    catalog = load_fail2drive_asset_catalog(args.fail2drive_root, scenario_hub_root=args.scenario_hub_root)
    qa = qa_fail2drive_route_assets(
        args.route,
        prompt=args.prompt,
        catalog=catalog,
        evidence_frames=tuple(args.evidence_frame),
        required_assets=tuple(args.require_asset),
    )
    summary = write_fail2drive_asset_qa(run_dir, qa)
    if args.metric_only:
        print(f"METRIC f2d_asset_qa_missing_requirements={len(summary.get('missing_requirements', []))}")
        return 0 if summary["status"] == "passed" else 1
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "passed" else 1


def _command_f2d_catalog(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    summary = write_fail2drive_catalog_report(run_dir, load_fail2drive_catalog(args.fail2drive_root), fmt=args.format)
    if args.metric_only:
        print(f"METRIC f2d_catalog_scenario_count={summary['scenario_count']}")
        return 0
    print(json.dumps(summary, indent=2))
    return 0


def _command_f2d_validate_route(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    catalog = load_fail2drive_catalog(args.fail2drive_root)
    summary = write_fail2drive_route_validation(run_dir, validate_fail2drive_route(args.route, catalog, strict=args.strict))
    if args.metric_only:
        print(f"METRIC f2d_route_validation_errors={summary['error_count']}")
        return 0 if summary["ok"] else 1
    print(json.dumps(summary, indent=2))
    return 0 if summary["ok"] else 1


def _command_f2d_write_route(args: argparse.Namespace) -> int:
    run_dir = prepare_run_dir(args.output_root, args.run_id)
    catalog = load_fail2drive_catalog(args.fail2drive_root)
    if args.example:
        spec = example_fail2drive_route_spec(args.example)
        spec_path = run_dir / "route_spec.json"
        spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    elif args.spec:
        spec_path = args.spec
        spec = load_fail2drive_route_spec(args.spec)
    else:
        raise ValueError("Pass --spec or --example.")
    output = args.output or (run_dir / "route.xml")
    result = write_fail2drive_route_xml(spec, output, catalog=catalog, validate=args.validate, spec_path=spec_path)
    summary = write_fail2drive_route_write_report(run_dir, result)
    if args.metric_only:
        validation = summary.get("validation") if isinstance(summary.get("validation"), dict) else {}
        print(f"METRIC f2d_route_write_validation_errors={validation.get('error_count', 0)}")
        return 0 if not validation or validation.get("ok") else 1
    print(json.dumps(summary, indent=2))
    validation = summary.get("validation") if isinstance(summary.get("validation"), dict) else None
    return 0 if validation is None or validation.get("ok") else 1


def _command_f2d_run_route(args: argparse.Namespace) -> int:
    summary = run_fail2drive_route_workflow(
        Fail2DriveRouteRunRequest(
            route_path=args.route,
            fail2drive_root=args.fail2drive_root,
            output_root=args.output_root,
            run_id=args.run_id,
            agent_kind=args.agent,
            agent_path=args.agent_path,
            agent_config=args.agent_config,
            host=args.host,
            port=args.port,
            track=args.track,
            live=bool(args.live and not args.dry_run),
            timeout_s=args.timeout_s,
            skip_validate=args.skip_validate,
        )
    )
    if args.metric_only:
        print(f"METRIC f2d_route_run_blockers={len(summary.get('blockers', []))}")
        return 0
    print(json.dumps(summary, indent=2))
    return 0


def _command_f2d_reason(args: argparse.Namespace) -> int:
    summary = run_fail2drive_reasoning(
        Fail2DriveReasoningRequest(
            evidence_path=args.evidence,
            route_path=args.route,
            output_root=args.output_root,
            run_id=args.run_id,
            mode=args.mode,
            keyframes=args.keyframes,
            cached_reasoning_path=args.cached_reasoning,
        )
    )
    if args.metric_only:
        print(f"METRIC f2d_reasoning_event_count={summary.get('metrics', {}).get('reasoning_event_count', 0)}")
        return 0
    print(json.dumps(summary, indent=2))
    return 0


def _command_f2d_demo_video(args: argparse.Namespace) -> int:
    summary = run_fail2drive_demo_video(
        Fail2DriveDemoVideoConfig(
            evidence_path=args.evidence,
            reasoning_path=args.reasoning,
            route_path=args.route,
            input_video_path=args.input_video,
            rgb_folder=args.rgb_folder,
            output_root=args.output_root,
            run_id=args.run_id,
            speed_factor=args.speed_factor,
            target_duration_s=args.target_duration_s,
        )
    )
    if args.metric_only:
        print(f"METRIC f2d_demo_readability_score={summary.get('metrics', {}).get('readability_score', 0.0)}")
        return 0 if summary.get("status") == "passed" else 1
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("status") == "passed" else 1


def _command_f2d_evaluate_model(args: argparse.Namespace) -> int:
    summary = run_fail2drive_model_reaction_suite(
        Fail2DriveModelReactionConfig(
            routes=tuple(args.routes),
            fail2drive_root=args.fail2drive_root,
            output_root=args.output_root,
            run_id=args.run_id,
            agent_kind=args.agent,
            limit=args.limit,
            live=bool(args.live and not args.dry_run),
            reason=args.reason,
            demo_video=args.demo_video,
        )
    )
    if args.metric_only:
        print(f"METRIC f2d_model_reaction_coverage={summary.get('metrics', {}).get('f2d_model_reaction_coverage', 0.0)}")
        return 0
    print(json.dumps(summary, indent=2))
    return 0


__all__ = ["register_fail2drive_commands"]
