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


if __name__ == "__main__":
    unittest.main()
