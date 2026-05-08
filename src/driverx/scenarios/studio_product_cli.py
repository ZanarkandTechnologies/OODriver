"""Product CLI for the OODrive scenario database."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from driverx.scenarios.studio_product import (
    StudioCommandResult,
    run_studio_ai_generate,
    run_studio_compile,
    run_studio_evaluate,
    run_studio_export,
    run_studio_ingest_brief,
    run_studio_init,
    run_studio_queue,
    run_studio_quickstart,
    run_studio_replay,
    run_studio_run,
)
from driverx.scenarios.studio_product_ancestry_runtime import run_studio_ancestry_cards
from driverx.scenarios.studio_product_carla_composer_cli import register_carla_composer_commands
from driverx.scenarios.studio_product_choreography_cli import register_choreography_commands
from driverx.scenarios.studio_product_closed_loop_cli import register_closed_loop_commands
from driverx.scenarios.studio_product_evidence_panel_runtime import run_studio_evidence_panel
from driverx.scenarios.studio_product_runtime import (
    run_studio_demo_video,
    run_studio_generate,
    run_studio_place,
    run_studio_reason,
    run_studio_score_demo,
)
from driverx.scenarios.studio_product_environment_runtime import (
    run_studio_export_env_demo,
    run_studio_generate_envs,
    run_studio_render_env,
    run_studio_score_env_demo,
)
from driverx.scenarios.studio_product_env_video_runtime import (
    run_studio_env_demo_video,
    run_studio_score_env_proof,
)
from driverx.scenarios.studio_product_generated_runtime import (
    run_studio_generate_run,
    run_studio_score_generator_runtime,
)
from driverx.scenarios.studio_product_keyframe_runtime import run_studio_analyze_keyframes
from driverx.scenarios.studio_product_memory_runtime import run_studio_memory_ledger
from driverx.scenarios.studio_product_production_cli import register_production_commands
from driverx.scenarios.studio_product_reasoning_diff_runtime import run_studio_reasoning_diff
from driverx.scenarios.studio_product_submission_runtime import (
    run_studio_export_submission,
    run_studio_score_submission,
)
from driverx.scenarios.studio_product_stress_runtime import run_studio_stress_demo


def build_oodrive_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oodrive",
        description="OODrive scenario generation, queueing, evaluation, and evidence tooling.",
    )
    _register_commands(parser, "oodrive")
    return parser


def register_oodrive_parser(subparsers: argparse._SubParsersAction) -> None:
    _register_group(subparsers, "oodrive", "OODrive scenario DB and evaluation tool.")
    _register_group(subparsers, "oodriver", "Alias for `oodrive`.")
    _register_group(subparsers, "studio", "Alias for `oodrive`.")


def _register_group(subparsers: argparse._SubParsersAction, name: str, help_text: str) -> None:
    parser = subparsers.add_parser(name, help=help_text)
    _register_commands(parser, name)


def _register_commands(parser: argparse.ArgumentParser, name: str) -> None:
    nested = parser.add_subparsers(dest=f"{name}_command", required=True)

    generate = nested.add_parser("generate", help="Generate an OOD scenario and CARLA placement plan from text.")
    generate.add_argument("description", nargs="*", help="Scenario description, e.g. 'wet KL roadwork scooter filtering'.")
    generate.add_argument("--prompt", action="append", default=[], help="Additional prompt text. Useful for scripts.")
    generate.add_argument("--db", type=Path)
    generate.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    generate.add_argument("--run-id", default="oodrive-generated")
    generate.add_argument("--count", type=int, default=4)
    generate.add_argument("--seed", type=int, default=7)
    generate.add_argument("--provider", default="codex-template", choices=["codex-template"])
    generate.add_argument("--force", action="store_true")
    generate.add_argument("--severity", type=int, default=4)
    generate.add_argument("--accept", default="top:3")
    generate.add_argument("--config", type=Path, default=Path("configs/carla_ood_demo.local.sample.yaml"))
    generate.set_defaults(func=_command_generate)

    generate_run = nested.add_parser(
        "generate-run",
        help="Generate selectable vehicle behaviors and object spawns, then prove runtime readiness.",
    )
    generate_run.add_argument("description", nargs="*", help="Generated runtime prompt.")
    generate_run.add_argument("--prompt", action="append", default=[], help="Additional prompt text. Useful for scripts.")
    generate_run.add_argument("--template-id", action="append", default=[], help="Environment template id. Defaults from prompt.")
    generate_run.add_argument("--behavior-id", action="append", default=[], help="Behavior id to include. Repeat for a suite.")
    generate_run.add_argument("--object-kind", action="append", default=[], help="Generated object kind to spawn. Repeat for several.")
    generate_run.add_argument("--severity", type=int, default=4)
    generate_run.add_argument("--seed", type=int, default=41)
    generate_run.add_argument("--backend", choices=["dry-run", "fake-carla", "carla-live"], default="dry-run")
    generate_run.add_argument("--config", type=Path, default=Path("configs/carla_ood_demo.local.sample.yaml"))
    generate_run.add_argument("--output-root", type=Path)
    generate_run.add_argument("--run-id", default="oodrive-generated-runtime")
    generate_run.set_defaults(func=_command_generate_run)

    register_carla_composer_commands(nested)
    register_choreography_commands(nested)

    register_production_commands(nested)

    generate_envs = nested.add_parser(
        "generate-envs",
        help="Generate deterministic CARLA environment variants for judge-visible OOD demos.",
    )
    generate_envs.add_argument(
        "--template-id",
        action="append",
        default=[],
        help="Environment template id to include. Repeat to select several; defaults to all built-in packs.",
    )
    generate_envs.add_argument("--severity", type=int, default=4)
    generate_envs.add_argument("--count", type=int, default=6)
    generate_envs.add_argument("--seed", type=int, default=31)
    generate_envs.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    generate_envs.add_argument("--run-id", default="oodrive-environments")
    generate_envs.set_defaults(func=_command_generate_envs)

    render_env = nested.add_parser(
        "render-env",
        help="Render one generated environment recipe into same-lineage CARLA visual proof.",
    )
    render_env.add_argument("--environment-summary", type=Path, required=True)
    render_env.add_argument("--recipe-id")
    render_env.add_argument("--template-id")
    render_env.add_argument("--family")
    render_env.add_argument("--prompt", default="Generated OODrive environment visual proof")
    render_env.add_argument("--config", type=Path, default=Path("configs/carla_ood_demo.local.sample.yaml"))
    render_env.add_argument("--output-root", type=Path)
    render_env.add_argument("--run-id", default="oodrive-environment-carla-proof")
    render_env.add_argument("--live", action="store_true", help="Connect to CARLA and capture RGB frames for a preview image.")
    render_env.set_defaults(func=_command_render_env)

    stress_demo = nested.add_parser(
        "stress-demo",
        help="Build a bad-path stress reel showing blocker, hole, and rolling-object failures.",
    )
    stress_demo.add_argument(
        "--case",
        action="append",
        default=[],
        choices=[
            "static_blocker_stop",
            "road_hole_swerve_recover",
            "rolling_object_yield_swerve",
            "compound_obstacle_detour",
        ],
        help="Stress case id to include. Repeat to choose several; defaults to all three.",
    )
    stress_demo.add_argument("--output-root", type=Path)
    stress_demo.add_argument("--run-id", default="oodrive-bad-path-stress-demo")
    stress_demo.add_argument("--target-duration-s", type=float, default=60.0)
    stress_demo.add_argument("--fps", type=int, default=8)
    stress_demo.set_defaults(func=_command_stress_demo)

    init = nested.add_parser("init", help="Create an OODrive scenario database.")
    init.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    init.add_argument("--run-id", default="oodrive")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=_command_init)

    ingest = nested.add_parser("ingest-brief", help="Append a scenario-generation brief to the DB.")
    ingest.add_argument("--db", type=Path, required=True)
    ingest.add_argument("--prompt", required=True)
    ingest.add_argument("--author", default="human", choices=["human", "codex", "agent", "fixture", "provider"])
    ingest.add_argument("--tag", action="append", default=[])
    ingest.add_argument("--region")
    ingest.add_argument("--target-policy-pressure")
    ingest.set_defaults(func=_command_ingest)

    ai_generate = nested.add_parser("ai-generate", help="Generate OOD scenario briefs into the DB.")
    ai_generate.add_argument("--prompt", action="append", required=True)
    ai_generate.add_argument("--db", type=Path)
    ai_generate.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    ai_generate.add_argument("--run-id", default="oodrive-ai")
    ai_generate.add_argument("--count", type=int, default=4)
    ai_generate.add_argument("--seed", type=int, default=7)
    ai_generate.add_argument("--provider", default="codex-template", choices=["codex-template"])
    ai_generate.add_argument("--force", action="store_true")
    ai_generate.add_argument("--compile", action="store_true", dest="compile_candidates")
    ai_generate.add_argument("--queue", action="store_true", dest="queue_candidates")
    ai_generate.add_argument("--severity", type=int, default=4)
    ai_generate.add_argument("--accept", default="top:3")
    ai_generate.set_defaults(func=_command_ai_generate)

    compile_parser = nested.add_parser("compile", help="Compile DB briefs into curated scenario candidates.")
    compile_parser.add_argument("--db", type=Path, required=True)
    compile_parser.add_argument("--count", type=int, default=6)
    compile_parser.add_argument("--severity", type=int, default=3)
    compile_parser.add_argument("--seed", type=int, default=7)
    compile_parser.add_argument("--seeds-path", type=Path, default=Path("tests/fixtures/fail2drive_like/seeds.json"))
    compile_parser.add_argument("--catalog", type=Path)
    compile_parser.set_defaults(func=_command_compile)

    queue = nested.add_parser("queue", help="Select curated candidates into a runtime dataset queue.")
    queue.add_argument("--db", type=Path, required=True)
    queue.add_argument("--accept", default="top:3")
    queue.add_argument(
        "--policy-target",
        action="append",
        default=[],
        help="Policy target for queued scenarios. Repeat to add several.",
    )
    queue.set_defaults(func=_command_queue)

    run = nested.add_parser("run", help="Run or block-record one queued scenario.")
    run.add_argument("--db", type=Path, required=True)
    run.add_argument("--scenario-id")
    run.add_argument("--policy", choices=["mock", "carla-autopilot", "alpamayo-trajectory"], default="mock")
    run.add_argument("--config", type=Path)
    run.add_argument("--output-root", type=Path)
    run.add_argument("--run-id")
    run.set_defaults(func=_command_run)

    place = nested.add_parser("place", help="Place a generated scenario in CARLA or write a dry-run manifest.")
    place.add_argument("--db", type=Path, required=True)
    place.add_argument("--scenario-id")
    place.add_argument("--placement", type=Path)
    place.add_argument("--config", type=Path, default=Path("configs/carla_ood_demo.local.sample.yaml"))
    place.add_argument("--output-root", type=Path)
    place.add_argument("--run-id")
    place.add_argument("--live", action="store_true", help="Connect to CARLA and run the scripted OOD demo.")
    place.set_defaults(func=_command_place)

    reason = nested.add_parser("reason", help="Attach Alpamayo reasoning evidence to a CARLA/OODrive run.")
    reason.add_argument("--db", type=Path, required=True)
    reason.add_argument("--run", dest="run_manifest", type=Path)
    reason.add_argument("--prediction-json", type=Path)
    reason.add_argument("--package", dest="package_path", type=Path)
    reason.add_argument("--memory", default="auto", choices=["auto", "none"])
    reason.add_argument("--output-root", type=Path)
    reason.add_argument("--run-id")
    reason.set_defaults(func=_command_reason)

    memory_ledger = nested.add_parser(
        "memory-ledger",
        help="Write an auditable RAG/memory retrieval ledger for one generated scenario.",
    )
    memory_ledger.add_argument("--db", type=Path, required=True)
    memory_ledger.add_argument("--scenario-id")
    memory_ledger.add_argument("--memory-bank", type=Path)
    memory_ledger.add_argument("--output-root", type=Path)
    memory_ledger.add_argument("--run-id", default="oodrive-memory-ledger")
    memory_ledger.add_argument("--limit", type=int, default=6)
    memory_ledger.set_defaults(func=_command_memory_ledger)

    reasoning_diff = nested.add_parser(
        "reasoning-diff",
        help="Summarize how memory changes sampled Alpamayo open-loop reasoning.",
    )
    reasoning_diff.add_argument("--alpamayo-batch", type=Path, required=True)
    reasoning_diff.add_argument("--retrieval-ledger", type=Path, action="append", default=[])
    reasoning_diff.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    reasoning_diff.add_argument("--run-id", default="oodrive-reasoning-diff")
    reasoning_diff.set_defaults(func=_command_reasoning_diff)

    evidence_panel = nested.add_parser(
        "evidence-panel",
        help="Build a decongested reasoning/RAG evidence panel for judge review.",
    )
    evidence_panel.add_argument("--overlay-report", type=Path, required=True)
    evidence_panel.add_argument("--reasoning-diff", type=Path, required=True)
    evidence_panel.add_argument("--retrieval-ledger", type=Path, action="append", default=[])
    evidence_panel.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    evidence_panel.add_argument("--run-id", default="oodrive-reasoning-evidence-panel")
    evidence_panel.set_defaults(func=_command_evidence_panel)

    ancestry_cards = nested.add_parser(
        "ancestry-cards",
        help="Build reference-grounded cards linking generated scenarios to Fail2Drive-like seeds.",
    )
    ancestry_cards.add_argument("--db", type=Path, required=True)
    ancestry_cards.add_argument("--fail2drive-report", type=Path, required=True)
    ancestry_cards.add_argument("--retrieval-ledger", type=Path, action="append", default=[])
    ancestry_cards.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    ancestry_cards.add_argument("--run-id", default="oodrive-scenario-ancestry-cards")
    ancestry_cards.add_argument("--limit", type=int, default=8)
    ancestry_cards.set_defaults(func=_command_ancestry_cards)

    analyze_keyframes = nested.add_parser(
        "analyze-keyframes",
        help="Attach frame-by-frame Alpamayo-style analysis to CARLA keyframes.",
    )
    analyze_keyframes.add_argument("--visual-proof", type=Path, required=True)
    analyze_keyframes.add_argument("--db", type=Path, required=True)
    analyze_keyframes.add_argument("--run", dest="run_manifest", type=Path, required=True)
    analyze_keyframes.add_argument("--backend", choices=["fake", "blocked", "alpamayo-local"], default="fake")
    analyze_keyframes.add_argument("--keyframes", type=int, default=8)
    analyze_keyframes.add_argument("--output-root", type=Path)
    analyze_keyframes.add_argument("--run-id", default="oodrive-keyframe-analysis")
    analyze_keyframes.set_defaults(func=_command_analyze_keyframes)

    env_demo_video = nested.add_parser(
        "env-demo-video",
        help="Build a story/overlay pack for generated environment -> CARLA -> keyframe reasoning.",
    )
    env_demo_video.add_argument("--environment-summary", type=Path, required=True)
    env_demo_video.add_argument("--visual-proof", type=Path, required=True)
    env_demo_video.add_argument("--keyframe-analysis", type=Path, required=True)
    env_demo_video.add_argument("--output-root", type=Path)
    env_demo_video.add_argument("--run-id", default="environment-reasoned-carla-demo")
    env_demo_video.add_argument("--target-duration-s", type=float, default=120.0)
    env_demo_video.set_defaults(func=_command_env_demo_video)

    score_env_proof = nested.add_parser(
        "score-env-proof",
        help="Score generated-environment to reasoned-CARLA proof readiness.",
    )
    score_env_proof.add_argument("--environment-summary", type=Path, required=True)
    score_env_proof.add_argument("--visual-proof", type=Path, required=True)
    score_env_proof.add_argument("--keyframe-analysis", type=Path, required=True)
    score_env_proof.add_argument("--overlay-report", type=Path)
    score_env_proof.add_argument("--video", type=Path)
    score_env_proof.add_argument("--output-root", type=Path)
    score_env_proof.add_argument("--run-id", default="environment-reasoned-carla-score")
    score_env_proof.add_argument("--metric-only", action="store_true")
    score_env_proof.set_defaults(func=_command_score_env_proof)

    score_generator_runtime = nested.add_parser(
        "score-generator-runtime",
        help="Score generated behavior/object runtime usability.",
    )
    score_generator_runtime.add_argument("--runtime-manifest", type=Path, required=True)
    score_generator_runtime.add_argument("--output-root", type=Path)
    score_generator_runtime.add_argument("--run-id")
    score_generator_runtime.add_argument("--metric-only", action="store_true")
    score_generator_runtime.set_defaults(func=_command_score_generator_runtime)

    register_closed_loop_commands(nested)

    score_demo = nested.add_parser("score-demo", help="Score whether a demo video is submission-visible enough.")
    score_demo.add_argument("--db", type=Path)
    score_demo.add_argument("--run", dest="run_manifest", type=Path)
    score_demo.add_argument("--evaluation", type=Path)
    score_demo.add_argument("--video", type=Path)
    score_demo.add_argument("--overlay-report", type=Path)
    score_demo.add_argument("--score-input", type=Path)
    score_demo.add_argument("--output-root", type=Path)
    score_demo.add_argument("--run-id")
    score_demo.add_argument("--metric-only", action="store_true")
    score_demo.set_defaults(func=_command_score_demo)

    score_submission = nested.add_parser(
        "score-submission",
        help="Score whether the full OODrive evidence packet is SoTA Commission-ready.",
    )
    score_submission.add_argument("--db", type=Path)
    score_submission.add_argument("--run", dest="run_manifest", type=Path)
    score_submission.add_argument("--evaluation", type=Path)
    score_submission.add_argument("--hero-score", type=Path)
    score_submission.add_argument("--overlay-report", type=Path)
    score_submission.add_argument("--pack-manifest", type=Path)
    score_submission.add_argument("--checks-report", type=Path)
    score_submission.add_argument("--score-input", type=Path)
    score_submission.add_argument("--output-root", type=Path)
    score_submission.add_argument("--run-id")
    score_submission.add_argument("--metric-only", action="store_true")
    score_submission.set_defaults(func=_command_score_submission)

    export_submission = nested.add_parser(
        "export-submission",
        help="Build a judge-facing SoTA Commission submission pack.",
    )
    export_submission.add_argument("--db", type=Path, required=True)
    export_submission.add_argument("--run", dest="run_manifest", type=Path, required=True)
    export_submission.add_argument("--evaluation", type=Path, required=True)
    export_submission.add_argument("--hero-video", type=Path, required=True)
    export_submission.add_argument("--hero-score", type=Path, required=True)
    export_submission.add_argument("--readiness-score", type=Path)
    export_submission.add_argument("--environment-demo", type=Path)
    export_submission.add_argument("--output-root", type=Path)
    export_submission.add_argument("--run-id")
    export_submission.set_defaults(func=_command_export_submission)

    export_env_demo = nested.add_parser(
        "export-env-demo",
        help="Build a recordable static Environment Studio demo pack.",
    )
    export_env_demo.add_argument("--environment-summary", type=Path, required=True)
    export_env_demo.add_argument("--submission-pack", type=Path)
    export_env_demo.add_argument("--hero-video", type=Path)
    export_env_demo.add_argument("--output-root", type=Path)
    export_env_demo.add_argument("--run-id")
    export_env_demo.set_defaults(func=_command_export_env_demo)

    score_env_demo = nested.add_parser(
        "score-env-demo",
        help="Score whether the Environment Studio demo is judge-visible enough.",
    )
    score_env_demo.add_argument("--environment-summary", type=Path)
    score_env_demo.add_argument("--demo-manifest", type=Path)
    score_env_demo.add_argument("--score-input", type=Path)
    score_env_demo.add_argument("--output-root", type=Path)
    score_env_demo.add_argument("--run-id")
    score_env_demo.add_argument("--metric-only", action="store_true")
    score_env_demo.set_defaults(func=_command_score_env_demo)

    demo_video = nested.add_parser("demo-video", help="Build a frame/time + reasoning/RAG overlay demo video.")
    demo_video.add_argument("--db", type=Path, required=True)
    demo_video.add_argument("--run", dest="run_manifest", type=Path)
    demo_video.add_argument("--evaluation", type=Path)
    demo_video.add_argument("--input-video", type=Path, required=True)
    demo_video.add_argument("--output-video", type=Path)
    demo_video.add_argument("--output-root", type=Path)
    demo_video.add_argument("--run-id")
    demo_video.add_argument("--fps", type=int, default=15)
    demo_video.add_argument("--speed-factor", type=float, default=4.0)
    demo_video.add_argument("--show-frame-time", action="store_true", default=True)
    demo_video.add_argument("--hide-frame-time", action="store_false", dest="show_frame_time")
    demo_video.add_argument("--show-reasoning", action="store_true", default=True)
    demo_video.add_argument("--hide-reasoning", action="store_false", dest="show_reasoning")
    demo_video.add_argument("--show-rag", action="store_true", default=True)
    demo_video.add_argument("--hide-rag", action="store_false", dest="show_rag")
    demo_video.add_argument("--layout", choices=["dense", "compact"], default="dense")
    demo_video.set_defaults(func=_command_demo_video)

    evaluate = nested.add_parser("evaluate", help="Attach Alpamayo/cached policy evidence to a run.")
    evaluate.add_argument("--db", type=Path, required=True)
    evaluate.add_argument("--run", dest="run_manifest", type=Path)
    evaluate.add_argument("--policy", default="alpamayo-trajectory")
    evaluate.add_argument("--memory", default="auto", choices=["auto", "none"])
    evaluate.add_argument("--prediction-json", type=Path)
    evaluate.add_argument("--output-root", type=Path)
    evaluate.add_argument("--run-id")
    evaluate.set_defaults(func=_command_evaluate)

    replay = nested.add_parser("replay", help="Build a scenario replay bundle from DB evidence.")
    replay.add_argument("--db", type=Path, required=True)
    replay.add_argument("--run", dest="run_manifest", type=Path)
    replay.add_argument("--evaluation", type=Path)
    replay.add_argument("--output-root", type=Path)
    replay.add_argument("--run-id")
    replay.set_defaults(func=_command_replay)

    export = nested.add_parser("export", help="Build the OODrive CLI evidence pack.")
    export.add_argument("--db", type=Path, required=True)
    export.add_argument("--output-root", type=Path)
    export.add_argument("--run-id")
    export.set_defaults(func=_command_export)

    quickstart = nested.add_parser("quickstart", help="Run init -> ingest -> compile -> queue -> mock run -> export.")
    quickstart.add_argument("--prompt", action="append", required=True)
    quickstart.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    quickstart.add_argument("--run-id", default="oodrive-quickstart")
    quickstart.add_argument("--count", type=int, default=3)
    quickstart.add_argument("--severity", type=int, default=3)
    quickstart.add_argument("--seed", type=int, default=7)
    quickstart.add_argument("--policy", choices=["mock"], default="mock")
    quickstart.set_defaults(func=_command_quickstart)


def _print(result: StudioCommandResult) -> int:
    print(json.dumps(result.to_jsonable(), indent=2))
    return 0


def _command_init(args: argparse.Namespace) -> int:
    return _print(run_studio_init(args.output_root, args.run_id, force=args.force))


def _command_generate(args: argparse.Namespace) -> int:
    prompt_parts = [" ".join(args.description).strip(), *[item.strip() for item in args.prompt if item.strip()]]
    prompt = " ; ".join(part for part in prompt_parts if part)
    if not prompt:
        raise ValueError("Pass a scenario description or --prompt.")
    return _print(
        run_studio_generate(
            prompt=prompt,
            db_path=args.db,
            output_root=args.output_root,
            run_id=args.run_id,
            count=args.count,
            provider=args.provider,
            seed=args.seed,
            force=args.force,
            severity=args.severity,
            accept=args.accept,
            config_path=args.config,
        )
    )


def _command_generate_run(args: argparse.Namespace) -> int:
    prompt_parts = [" ".join(args.description).strip(), *[item.strip() for item in args.prompt if item.strip()]]
    prompt = " ; ".join(part for part in prompt_parts if part)
    if not prompt:
        raise ValueError("Pass a generated runtime description or --prompt.")
    return _print(
        run_studio_generate_run(
            prompt=prompt,
            template_ids=tuple(args.template_id),
            behavior_ids=tuple(args.behavior_id),
            object_kinds=tuple(args.object_kind),
            severity=args.severity,
            seed=args.seed,
            backend=args.backend,
            config_path=args.config,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_generate_envs(args: argparse.Namespace) -> int:
    return _print(
        run_studio_generate_envs(
            template_ids=tuple(args.template_id),
            severity=args.severity,
            count=args.count,
            random_seed=args.seed,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_render_env(args: argparse.Namespace) -> int:
    return _print(
        run_studio_render_env(
            environment_summary_path=args.environment_summary,
            recipe_id=args.recipe_id,
            template_id=args.template_id,
            family=args.family,
            prompt=args.prompt,
            config_path=args.config,
            output_root=args.output_root,
            run_id=args.run_id,
            live=args.live,
        )
    )


def _command_ingest(args: argparse.Namespace) -> int:
    return _print(
        run_studio_ingest_brief(
            args.db,
            prompt=args.prompt,
            author=args.author,
            requested_tags=args.tag,
            region=args.region,
            target_policy_pressure=args.target_policy_pressure,
        )
    )


def _command_ai_generate(args: argparse.Namespace) -> int:
    return _print(
        run_studio_ai_generate(
            prompts=args.prompt,
            db_path=args.db,
            output_root=args.output_root,
            run_id=args.run_id,
            count=args.count,
            provider=args.provider,
            seed=args.seed,
            force=args.force,
            compile_candidates=args.compile_candidates,
            queue_candidates=args.queue_candidates,
            severity=args.severity,
            accept=args.accept,
        )
    )


def _command_compile(args: argparse.Namespace) -> int:
    return _print(
        run_studio_compile(
            args.db,
            count=args.count,
            severity=args.severity,
            seed=args.seed,
            seeds_path=args.seeds_path,
            catalog_path=args.catalog,
        )
    )


def _command_queue(args: argparse.Namespace) -> int:
    policy_targets = tuple(args.policy_target) if args.policy_target else ("mock", "carla-autopilot", "alpamayo-trajectory")
    return _print(run_studio_queue(args.db, accept=args.accept, policy_targets=policy_targets))


def _command_run(args: argparse.Namespace) -> int:
    return _print(
        run_studio_run(
            args.db,
            scenario_id=args.scenario_id,
            policy=args.policy,
            config_path=args.config,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_place(args: argparse.Namespace) -> int:
    return _print(
        run_studio_place(
            args.db,
            scenario_id=args.scenario_id,
            placement_path=args.placement,
            config_path=args.config,
            output_root=args.output_root,
            run_id=args.run_id,
            live=args.live,
        )
    )


def _command_reason(args: argparse.Namespace) -> int:
    return _print(
        run_studio_reason(
            args.db,
            run_manifest_path=args.run_manifest,
            prediction_json=args.prediction_json,
            package_path=args.package_path,
            memory=args.memory,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_memory_ledger(args: argparse.Namespace) -> int:
    return _print(
        run_studio_memory_ledger(
            args.db,
            scenario_id=args.scenario_id,
            memory_bank_path=args.memory_bank,
            output_root=args.output_root,
            run_id=args.run_id,
            limit=args.limit,
        )
    )


def _command_reasoning_diff(args: argparse.Namespace) -> int:
    return _print(
        run_studio_reasoning_diff(
            alpamayo_batch_path=args.alpamayo_batch,
            retrieval_ledger_paths=tuple(args.retrieval_ledger),
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_evidence_panel(args: argparse.Namespace) -> int:
    return _print(
        run_studio_evidence_panel(
            overlay_report_path=args.overlay_report,
            reasoning_diff_path=args.reasoning_diff,
            retrieval_ledger_paths=tuple(args.retrieval_ledger),
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_ancestry_cards(args: argparse.Namespace) -> int:
    return _print(
        run_studio_ancestry_cards(
            args.db,
            fail2drive_report_path=args.fail2drive_report,
            retrieval_ledger_paths=tuple(args.retrieval_ledger),
            output_root=args.output_root,
            run_id=args.run_id,
            limit=args.limit,
        )
    )


def _command_stress_demo(args: argparse.Namespace) -> int:
    return _print(
        run_studio_stress_demo(
            output_root=args.output_root,
            run_id=args.run_id,
            case_ids=tuple(args.case),
            target_duration_s=args.target_duration_s,
            fps=args.fps,
        )
    )


def _command_analyze_keyframes(args: argparse.Namespace) -> int:
    return _print(
        run_studio_analyze_keyframes(
            visual_proof_path=args.visual_proof,
            db_path=args.db,
            run_manifest_path=args.run_manifest,
            backend=args.backend,
            keyframe_count=args.keyframes,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_env_demo_video(args: argparse.Namespace) -> int:
    return _print(
        run_studio_env_demo_video(
            environment_summary_path=args.environment_summary,
            visual_proof_path=args.visual_proof,
            keyframe_analysis_path=args.keyframe_analysis,
            output_root=args.output_root,
            run_id=args.run_id,
            target_duration_s=args.target_duration_s,
        )
    )


def _command_score_env_proof(args: argparse.Namespace) -> int:
    result = run_studio_score_env_proof(
        environment_summary_path=args.environment_summary,
        visual_proof_path=args.visual_proof,
        keyframe_analysis_path=args.keyframe_analysis,
        overlay_report_path=args.overlay_report,
        video_path=args.video,
        output_root=args.output_root,
        run_id=args.run_id,
        metric_only=args.metric_only,
    )
    if args.metric_only:
        return 0 if result.status in {"passed", "blocked"} else 1
    return _print(result)


def _command_score_generator_runtime(args: argparse.Namespace) -> int:
    result = run_studio_score_generator_runtime(
        runtime_manifest_path=args.runtime_manifest,
        output_root=args.output_root,
        run_id=args.run_id,
        metric_only=args.metric_only,
    )
    if args.metric_only:
        return 0 if result.status in {"passed", "blocked"} else 1
    return _print(result)


def _command_score_demo(args: argparse.Namespace) -> int:
    result = run_studio_score_demo(
        args.db,
        run_manifest_path=args.run_manifest,
        evaluation_path=args.evaluation,
        video_path=args.video,
        overlay_report_path=args.overlay_report,
        score_input_path=args.score_input,
        output_root=args.output_root,
        run_id=args.run_id,
        metric_only=args.metric_only,
    )
    if args.metric_only:
        return 0 if result.status in {"passed", "blocked"} else 1
    return _print(result)


def _command_score_submission(args: argparse.Namespace) -> int:
    result = run_studio_score_submission(
        args.db,
        run_manifest_path=args.run_manifest,
        evaluation_path=args.evaluation,
        hero_score_path=args.hero_score,
        overlay_report_path=args.overlay_report,
        pack_manifest_path=args.pack_manifest,
        checks_report_path=args.checks_report,
        score_input_path=args.score_input,
        output_root=args.output_root,
        run_id=args.run_id,
        metric_only=args.metric_only,
    )
    if args.metric_only:
        return 0 if result.status in {"passed", "blocked"} else 1
    return _print(result)


def _command_export_submission(args: argparse.Namespace) -> int:
    return _print(
        run_studio_export_submission(
            args.db,
            run_manifest_path=args.run_manifest,
            evaluation_path=args.evaluation,
            hero_video_path=args.hero_video,
            hero_score_path=args.hero_score,
            readiness_score_path=args.readiness_score,
            environment_demo_path=args.environment_demo,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_export_env_demo(args: argparse.Namespace) -> int:
    return _print(
        run_studio_export_env_demo(
            environment_summary_path=args.environment_summary,
            submission_pack_path=args.submission_pack,
            hero_video_path=args.hero_video,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_score_env_demo(args: argparse.Namespace) -> int:
    result = run_studio_score_env_demo(
        environment_summary_path=args.environment_summary,
        demo_manifest_path=args.demo_manifest,
        score_input_path=args.score_input,
        output_root=args.output_root,
        run_id=args.run_id,
        metric_only=args.metric_only,
    )
    if args.metric_only:
        return 0 if result.status in {"passed", "blocked"} else 1
    return _print(result)


def _command_demo_video(args: argparse.Namespace) -> int:
    return _print(
        run_studio_demo_video(
            args.db,
            input_video=args.input_video,
            run_manifest_path=args.run_manifest,
            evaluation_path=args.evaluation,
            output_video=args.output_video,
            output_root=args.output_root,
            run_id=args.run_id,
            fps=args.fps,
            speed_factor=args.speed_factor,
            show_frame_time=args.show_frame_time,
            show_reasoning=args.show_reasoning,
            show_rag=args.show_rag,
            layout=args.layout,
        )
    )


def _command_evaluate(args: argparse.Namespace) -> int:
    return _print(
        run_studio_evaluate(
            args.db,
            run_manifest_path=args.run_manifest,
            policy=args.policy,
            memory=args.memory,
            prediction_json=args.prediction_json,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_replay(args: argparse.Namespace) -> int:
    return _print(
        run_studio_replay(
            args.db,
            run_manifest_path=args.run_manifest,
            evaluation_path=args.evaluation,
            output_root=args.output_root,
            run_id=args.run_id,
        )
    )


def _command_export(args: argparse.Namespace) -> int:
    return _print(run_studio_export(args.db, output_root=args.output_root, run_id=args.run_id))


def _command_quickstart(args: argparse.Namespace) -> int:
    return _print(
        run_studio_quickstart(
            args.output_root,
            args.run_id,
            prompts=args.prompt,
            count=args.count,
            severity=args.severity,
            seed=args.seed,
            policy=args.policy,
        )
    )


register_oodriver_parser = register_oodrive_parser

__all__ = ["build_oodrive_parser", "register_oodrive_parser", "register_oodriver_parser"]
