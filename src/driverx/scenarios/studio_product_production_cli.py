"""Production scenario generator OODrive CLI registration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.scenarios.studio_product import StudioCommandResult
from driverx.scenarios.studio_product_production_runtime import (
    run_studio_compile_scenario,
    run_studio_export_library,
    run_studio_generate_assets,
    run_studio_install_assets,
    run_studio_run_scenario,
    run_studio_scenario_pack,
    run_studio_score_research_generator,
    run_studio_workbench,
)


def register_production_commands(nested: argparse._SubParsersAction) -> None:
    scenario_pack = nested.add_parser(
        "scenario-pack",
        help="Build a production-grade generated scenario pack with assets and graph-ready specs.",
    )
    scenario_pack.add_argument("description", nargs="*", help="Production scenario prompt.")
    scenario_pack.add_argument("--prompt", action="append", default=[])
    scenario_pack.add_argument("--template-id", action="append", default=[])
    scenario_pack.add_argument("--behavior-id", action="append", default=[])
    scenario_pack.add_argument("--object-kind", action="append", default=[])
    scenario_pack.add_argument("--severity", type=int, default=4)
    scenario_pack.add_argument("--seed", type=int, default=41)
    scenario_pack.add_argument("--config", type=Path, default=Path("configs/carla_ood_demo.local.sample.yaml"))
    scenario_pack.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    scenario_pack.add_argument("--run-id", default="oodrive-production-pack")
    scenario_pack.set_defaults(func=_command_scenario_pack)

    generate_assets = nested.add_parser("generate-assets", help="Generate or ingest 3D assets for a scenario pack.")
    generate_assets.add_argument("--scenario-pack", type=Path, required=True)
    generate_assets.add_argument("--provider", default="local-procedural")
    generate_assets.add_argument("--output-root", type=Path)
    generate_assets.add_argument("--run-id", default="oodrive-generated-assets")
    generate_assets.set_defaults(func=_command_generate_assets)

    install_assets = nested.add_parser("install-assets", help="Plan/probe CARLA generated-asset installation.")
    install_assets.add_argument("--scenario-pack", type=Path, required=True)
    install_assets.add_argument("--mode", choices=["plan", "probe"], default="plan")
    install_assets.add_argument("--output-root", type=Path)
    install_assets.add_argument("--run-id", default="oodrive-carla-asset-registry")
    install_assets.set_defaults(func=_command_install_assets)

    compile_scenario = nested.add_parser("compile-scenario", help="Compile a production pack into a scenario graph.")
    compile_scenario.add_argument("--scenario-pack", type=Path, required=True)
    compile_scenario.add_argument("--asset-registry", type=Path)
    compile_scenario.add_argument("--output-root", type=Path)
    compile_scenario.add_argument("--run-id", default="oodrive-scenario-graph")
    compile_scenario.set_defaults(func=_command_compile_scenario)

    run_scenario = nested.add_parser("run-scenario", help="Run a production scenario graph in fake or live CARLA.")
    run_scenario.add_argument("--scenario-pack", type=Path, required=True)
    run_scenario.add_argument("--scenario-graph", type=Path)
    run_scenario.add_argument("--asset-registry", type=Path)
    run_scenario.add_argument("--backend", choices=["fake-carla", "carla-live"], default="fake-carla")
    run_scenario.add_argument("--config", type=Path, default=Path("configs/carla_ood_demo.local.sample.yaml"))
    run_scenario.add_argument("--output-root", type=Path)
    run_scenario.add_argument("--run-id", default="oodrive-scenario-run")
    run_scenario.set_defaults(func=_command_run_scenario)

    score_research_generator = nested.add_parser(
        "score-research-generator",
        help="Score the production research scenario-generator packet.",
    )
    score_research_generator.add_argument("--scenario-pack", type=Path)
    score_research_generator.add_argument("--asset-manifest", type=Path, action="append", default=[])
    score_research_generator.add_argument("--asset-registry", type=Path)
    score_research_generator.add_argument("--scenario-graph", type=Path)
    score_research_generator.add_argument("--run-manifest", type=Path, action="append", default=[])
    score_research_generator.add_argument("--workbench", type=Path)
    score_research_generator.add_argument("--library", type=Path)
    score_research_generator.add_argument("--video", type=Path)
    score_research_generator.add_argument("--image-qa-report", type=Path)
    score_research_generator.add_argument("--output-root", type=Path)
    score_research_generator.add_argument("--run-id", default="oodrive-research-generator-score")
    score_research_generator.add_argument("--metric-only", action="store_true")
    score_research_generator.set_defaults(func=_command_score_research_generator)

    workbench = nested.add_parser("workbench", help="Build a local researcher scenario workbench.")
    workbench.add_argument("--scenario-pack", type=Path, required=True)
    workbench.add_argument("--run-manifest", type=Path, action="append", default=[])
    workbench.add_argument("--score-report", type=Path, action="append", default=[])
    workbench.add_argument("--output-root", type=Path)
    workbench.add_argument("--run-id", default="oodrive-research-workbench")
    workbench.set_defaults(func=_command_workbench)

    export_library = nested.add_parser("export-library", help="Export a curated local scenario library.")
    export_library.add_argument("--workbench", type=Path, required=True)
    export_library.add_argument("--include-media", choices=["refs", "copy", "none"], default="refs")
    export_library.add_argument("--output-root", type=Path)
    export_library.add_argument("--run-id", default="oodrive-scenario-library")
    export_library.set_defaults(func=_command_export_library)


def _print(result: StudioCommandResult) -> int:
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_scenario_pack(args: argparse.Namespace) -> int:
    prompt_parts = [" ".join(args.description).strip(), *[item.strip() for item in args.prompt if item.strip()]]
    prompt = " ; ".join(part for part in prompt_parts if part)
    if not prompt:
        raise ValueError("Pass a production scenario description or --prompt.")
    return _print(
        run_studio_scenario_pack(
            prompt=prompt,
            template_ids=tuple(args.template_id),
            behavior_ids=tuple(args.behavior_id),
            object_kinds=tuple(args.object_kind),
            severity=args.severity,
            seed=args.seed,
            config_path=args.config,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_generate_assets(args: argparse.Namespace) -> int:
    return _print(
        run_studio_generate_assets(
            scenario_pack_path=args.scenario_pack,
            provider=args.provider,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_install_assets(args: argparse.Namespace) -> int:
    return _print(
        run_studio_install_assets(
            scenario_pack_path=args.scenario_pack,
            mode=args.mode,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_compile_scenario(args: argparse.Namespace) -> int:
    return _print(
        run_studio_compile_scenario(
            scenario_pack_path=args.scenario_pack,
            asset_registry_path=args.asset_registry,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_run_scenario(args: argparse.Namespace) -> int:
    return _print(
        run_studio_run_scenario(
            scenario_pack_path=args.scenario_pack,
            scenario_graph_path=args.scenario_graph,
            asset_registry_path=args.asset_registry,
            backend=args.backend,
            config_path=args.config,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_score_research_generator(args: argparse.Namespace) -> int:
    result = run_studio_score_research_generator(
        scenario_pack_path=args.scenario_pack,
        asset_manifest_paths=tuple(args.asset_manifest),
        asset_registry_path=args.asset_registry,
        scenario_graph_path=args.scenario_graph,
        run_manifest_paths=tuple(args.run_manifest),
        workbench_summary_path=args.workbench,
        library_path=args.library,
        video_path=args.video,
        image_qa_report_path=args.image_qa_report,
        output_root=args.output_root,
        run_id=args.run_id,
        metric_only=args.metric_only,
    )
    if args.metric_only:
        return 0 if result.status in {"passed", "partial", "blocked"} else 1
    return _print(result)


def _command_workbench(args: argparse.Namespace) -> int:
    return _print(
        run_studio_workbench(
            scenario_pack_path=args.scenario_pack,
            run_manifest_paths=tuple(args.run_manifest),
            score_report_paths=tuple(args.score_report),
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_export_library(args: argparse.Namespace) -> int:
    return _print(
        run_studio_export_library(
            workbench_summary_path=args.workbench,
            include_media=args.include_media,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


__all__ = ["register_production_commands"]
