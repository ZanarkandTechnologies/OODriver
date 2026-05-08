from __future__ import annotations

import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import build_parser, main
from oodrive.cli import main as oodrive_main


class OODriveCliTests(unittest.TestCase):
    def test_help_group_accepts_oodrive_and_legacy_aliases(self) -> None:
        parser = build_parser()

        oodrive_args = parser.parse_args(["oodrive", "init", "--run-id", "x"])
        oodriver_args = parser.parse_args(["oodriver", "init", "--run-id", "x"])
        studio_args = parser.parse_args(["studio", "init", "--run-id", "x"])

        self.assertTrue(callable(oodrive_args.func))
        self.assertTrue(callable(oodriver_args.func))
        self.assertTrue(callable(studio_args.func))

    def test_oodrive_quickstart_writes_database_and_pack(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "oodrive",
                        "quickstart",
                        "--prompt",
                        "Malaysian wet roadwork: motorbike filters between cars while a lorry brakes without signal",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "smoke",
                        "--count",
                        "2",
                        "--seed",
                        "19",
                    ]
                )
            result = json.loads(stream.getvalue())
            db_path = Path(result["artifacts"]["db_path"])
            export_path = Path(result["artifacts"]["export"])
            bundle_path = Path(result["artifacts"]["bundle"])

            db = json.loads(db_path.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(result["product"], "OODrive")
            self.assertEqual(result["status"], "partial")
            self.assertTrue(db_path.exists())
            self.assertTrue(export_path.exists())
            self.assertTrue(bundle_path.exists())
            self.assertEqual(db["product_name"], "OODrive")
            self.assertEqual(len(db["briefs"]), 1)
            self.assertEqual(len(db["candidates"]), 2)
            self.assertEqual(len(db["queue"]), 2)
            self.assertEqual(len(db["runs"]), 1)
            self.assertEqual(len(db["evaluations"]), 1)
            self.assertEqual(len(db["bundles"]), 1)
            self.assertEqual(len(db["exports"]), 1)
            self.assertIn("cli_is_database_control_plane=true", db["claim_boundaries"])

    def test_alias_sequence_supports_cached_alpamayo_evaluation(self) -> None:
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "alias" / "scenario_studio_db.json"
            fake_prediction = Path(tmp) / "fake_prediction.json"
            fake_prediction.write_text(
                json.dumps(
                    {
                        "cot": "A scooter is filtering through wet roadwork; slow down, hold lane, and leave merge space.",
                        "pred_xyz_shape": [1, 1, 1, 64, 3],
                        "latency_ms": 812.5,
                    }
                ),
                encoding="utf-8",
            )
            commands = [
                ["studio", "init", "--output-root", tmp, "--run-id", "alias", "--force"],
                [
                    "studio",
                    "ingest-brief",
                    "--db",
                    str(db_path),
                    "--prompt",
                    "Night market scooter shoulder pass with sudden brake and roadside vendor occlusion",
                    "--author",
                    "codex",
                ],
                ["studio", "compile", "--db", str(db_path), "--count", "2", "--seed", "4"],
                ["studio", "queue", "--db", str(db_path), "--accept", "top:1"],
                ["studio", "run", "--db", str(db_path), "--policy", "mock", "--run-id", "mock-run"],
            ]
            for command in commands:
                stream = StringIO()
                with redirect_stdout(stream):
                    self.assertEqual(main(command), 0)
            db = json.loads(db_path.read_text(encoding="utf-8"))
            run_manifest = db["runs"][0]["json_path"]
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "studio",
                        "evaluate",
                        "--db",
                        str(db_path),
                        "--run",
                        run_manifest,
                        "--prediction-json",
                        str(fake_prediction),
                    ]
                )
            evaluation = json.loads(stream.getvalue())
            with redirect_stdout(StringIO()):
                self.assertEqual(
                    main(["studio", "replay", "--db", str(db_path), "--evaluation", evaluation["artifacts"]["json_path"]]),
                    0,
                )
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["studio", "export", "--db", str(db_path)]), 0)
            db = json.loads(db_path.read_text(encoding="utf-8"))

            self.assertEqual(exit_code, 0)
            self.assertEqual(evaluation["status"], "passed")
            self.assertEqual(db["evaluations"][-1]["reasoning_mode"], "cached_open_loop")
            self.assertEqual(db["evaluations"][-1]["latency_ms"], 812.5)
            self.assertTrue(Path(db["exports"][-1]["html_path"]).exists())

    def test_product_oodrive_entrypoint_runs_without_driverx_prefix(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = oodrive_main(
                    [
                        "quickstart",
                        "--prompt",
                        "Malaysian wet roadwork with motorcycle filtering and an unsignaled lorry brake",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "product",
                        "--count",
                        "2",
                        "--seed",
                        "19",
                    ]
                )
            result = json.loads(stream.getvalue())

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["product"], "OODrive")
            self.assertTrue(Path(result["artifacts"]["db_path"]).exists())
            self.assertTrue(Path(result["artifacts"]["export"]).exists())

    def test_product_demo_quality_commands_are_registered(self) -> None:
        for command in (
            "score-demo",
            "demo-video",
            "score-submission",
            "export-submission",
            "generate-envs",
            "generate-run",
            "carla-catalog",
            "carla-matrix",
            "carla-control",
            "carla-compose",
            "carla-suite",
            "score-carla-suite",
            "choreograph",
            "score-choreography",
            "render-env",
            "stress-demo",
            "analyze-keyframes",
            "env-demo-video",
            "score-env-proof",
            "score-generator-runtime",
            "scenario-pack",
            "generate-assets",
            "install-assets",
            "compile-scenario",
            "run-scenario",
            "score-research-generator",
            "workbench",
            "export-library",
            "closed-loop-run",
            "closed-loop-video",
            "infer",
            "score-closed-loop",
            "score-closed-loop-integration",
            "score-closed-loop-video",
            "memory-ledger",
            "reasoning-diff",
            "evidence-panel",
            "ancestry-cards",
            "export-env-demo",
            "score-env-demo",
        ):
            stream = StringIO()
            with self.assertRaises(SystemExit) as raised, redirect_stdout(stream):
                oodrive_main([command, "--help"])

            self.assertEqual(raised.exception.code, 0)
            self.assertIn(command, stream.getvalue())

    def test_ai_generate_creates_provider_briefs_and_uses_product_next_commands(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            err_stream = StringIO()
            with redirect_stdout(stream), redirect_stderr(err_stream):
                exit_code = oodrive_main(
                    [
                        "ai-generate",
                        "--prompt",
                        "Malaysian wet night roadwork chaos with scooter filtering",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "ai",
                        "--count",
                        "4",
                        "--seed",
                        "11",
                        "--compile",
                        "--queue",
                    ]
                )
            result = json.loads(stream.getvalue())
            db = json.loads(Path(result["artifacts"]["db_path"]).read_text(encoding="utf-8"))

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["summary"]["generated_count"], 4)
            self.assertEqual(result["summary"]["candidate_count"], 4)
            self.assertEqual(result["summary"]["queue_count"], 4)
            self.assertEqual({brief["author"] for brief in db["briefs"]}, {"provider"})
            self.assertEqual({brief["provider"] for brief in db["briefs"]}, {"codex-template"})
            self.assertTrue(all(command.startswith("PYTHONPATH=src python3 -m oodrive") for command in result["next_commands"]))
            self.assertFalse(any("driverx oodrive" in command for command in result["next_commands"]))
            self.assertIn("scenario_generation_ai_assisted=true", result["claim_boundaries"])
            self.assertIn("scenario_generation_ai_provider=codex-template", db["claim_boundaries"])
            self.assertFalse(
                any(boundary.startswith("scenario_generation_ai_provider=false") for boundary in db["claim_boundaries"])
            )

    def test_ai_generate_queue_without_compile_fails_before_writing_db(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            err_stream = StringIO()
            with redirect_stdout(stream), redirect_stderr(err_stream):
                exit_code = oodrive_main(
                    [
                        "ai-generate",
                        "--prompt",
                        "wet roadwork",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "bad",
                        "--queue",
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertIn("Pass --compile", err_stream.getvalue())
            self.assertFalse((Path(tmp) / "bad" / "scenario_studio_db.json").exists())

    def test_generate_writes_carla_placement_plan(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = oodrive_main(
                    [
                        "generate",
                        "Malaysian",
                        "wet",
                        "roadwork",
                        "with",
                        "motorcycle",
                        "filtering",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "generate",
                        "--count",
                        "2",
                        "--seed",
                        "11",
                    ]
                )
            result = json.loads(stream.getvalue())
            placement_path = Path(result["artifacts"]["placement_plan_path"])
            placement = json.loads(placement_path.read_text(encoding="utf-8"))

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["command"], "oodrive generate")
            self.assertEqual(result["status"], "passed")
            self.assertTrue(placement_path.exists())
            self.assertTrue(Path(result["artifacts"]["placement_report_path"]).exists())
            self.assertGreaterEqual(len(placement["object_spawn_specs"]), 1)
            self.assertIn("blueprint_filter", placement["object_spawn_specs"][0])
            self.assertIn("spawn_transform", placement["object_spawn_specs"][0])
            self.assertTrue(any("place --db" in command for command in result["next_commands"]))
            self.assertIn("oodrive_generate_to_carla_placement_plan=true", result["claim_boundaries"])

    def test_generate_place_reason_cached_product_flow(self) -> None:
        with TemporaryDirectory() as tmp:
            fake_prediction = Path(tmp) / "fake_alpamayo_prediction.json"
            fake_prediction.write_text(
                json.dumps(
                    {
                        "cot": "The roadwork lane is narrowed by market clutter; the ego should slow, hold margin, and yield to the filtering motorcycle.",
                        "pred_xyz_shape": [1, 1, 1, 64, 3],
                        "latency_ms": 901.25,
                    }
                ),
                encoding="utf-8",
            )
            generate_stream = StringIO()
            with redirect_stdout(generate_stream):
                self.assertEqual(
                    oodrive_main(
                        [
                            "generate",
                            "Malaysian wet roadwork with roadside vendor occlusion and scooter filtering",
                            "--output-root",
                            tmp,
                            "--run-id",
                            "flow",
                            "--count",
                            "2",
                            "--seed",
                            "13",
                        ]
                    ),
                    0,
                )
            generated = json.loads(generate_stream.getvalue())
            db_path = Path(generated["artifacts"]["db_path"])
            placement_path = Path(generated["artifacts"]["placement_plan_path"])

            place_stream = StringIO()
            with redirect_stdout(place_stream):
                self.assertEqual(
                    oodrive_main(
                        [
                            "place",
                            "--db",
                            str(db_path),
                            "--placement",
                            str(placement_path),
                            "--run-id",
                            "dry-place",
                        ]
                    ),
                    0,
                )
            placed = json.loads(place_stream.getvalue())
            run_manifest_path = Path(placed["artifacts"]["json_path"])
            run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))

            reason_stream = StringIO()
            with redirect_stdout(reason_stream):
                self.assertEqual(
                    oodrive_main(
                        [
                            "reason",
                            "--db",
                            str(db_path),
                            "--run",
                            str(run_manifest_path),
                            "--prediction-json",
                            str(fake_prediction),
                            "--run-id",
                            "cached-reason",
                        ]
                    ),
                    0,
                )
            reasoned = json.loads(reason_stream.getvalue())
            evaluation_path = Path(reasoned["artifacts"]["evaluation_path"])
            bundle_path = Path(reasoned["artifacts"]["bundle_path"])
            evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))

            self.assertEqual(placed["status"], "passed")
            self.assertFalse(placed["summary"]["objects_placed"])
            self.assertEqual(run_manifest["runtime"], "carla-placement-dry-run")
            self.assertEqual(run_manifest["status"], "planned")
            self.assertIn(reasoned["status"], {"passed", "partial"})
            self.assertTrue(evaluation_path.exists())
            self.assertTrue(bundle_path.exists())
            self.assertEqual(evaluation["reasoning_mode"], "cached_open_loop")
            self.assertIn("roadwork lane", evaluation["cot_summary"])
            self.assertTrue(reasoned["summary"]["sampled_open_loop_reasoning"])
            self.assertTrue(any("closed_loop_vla_control=false" in item for item in reasoned["claim_boundaries"]))


if __name__ == "__main__":
    unittest.main()
