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
