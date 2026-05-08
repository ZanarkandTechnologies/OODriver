from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.environments import EnvironmentSuiteConfig, run_environment_forge
from driverx.pipeline.environment_demo_pack import build_environment_demo_pack
from oodrive.cli import main as oodrive_main


class EnvironmentDemoPackTest(unittest.TestCase):
    def test_build_environment_demo_pack_writes_recordable_app_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = run_environment_forge(
                EnvironmentSuiteConfig(
                    severity=4,
                    count=6,
                    random_seed=31,
                    output_root=root,
                    run_id="env",
                )
            )
            hero_video = root / "hero.mp4"
            submission_pack = root / "submission_manifest.json"
            hero_video.write_bytes(b"mp4")
            submission_pack.write_text(json.dumps({"product_name": "OODrive"}), encoding="utf-8")

            pack = build_environment_demo_pack(
                environment_summary_path=Path(summary["summary_path"]),
                hero_video_path=hero_video,
                submission_pack_path=submission_pack,
                output_root=root / "packs",
                run_id="demo",
            )
            html = Path(pack["environment_demo_index_path"]).read_text(encoding="utf-8")
            manifest = json.loads(Path(pack["environment_demo_manifest_path"]).read_text(encoding="utf-8"))
            storyboard = Path(pack["environment_demo_storyboard_path"]).read_text(encoding="utf-8")

            self.assertEqual(pack["product_name"], "OODrive")
            self.assertEqual(pack["family_count"], 6)
            self.assertGreaterEqual(pack["asset_request_count"], 10)
            self.assertTrue(Path(pack["environment_demo_commands_path"]).exists())
            self.assertIn("OODrive Environment Studio", html)
            self.assertIn("road-local placement", html)
            self.assertIn("Target length: 1-5 minutes", storyboard)
            self.assertEqual(len(manifest["cards"]), 6)
            self.assertEqual(manifest["hero_video"]["status"], "local_file")

    def test_oodrive_environment_demo_command_flow_scores_over_90(self) -> None:
        with TemporaryDirectory() as tmp:
            generate_stream = StringIO()
            with redirect_stdout(generate_stream):
                self.assertEqual(
                    oodrive_main(
                        [
                            "generate-envs",
                            "--output-root",
                            tmp,
                            "--run-id",
                            "env",
                            "--count",
                            "6",
                            "--severity",
                            "4",
                            "--seed",
                            "31",
                        ]
                    ),
                    0,
                )
            generated = json.loads(generate_stream.getvalue())
            summary_path = Path(generated["artifacts"]["environment_summary_path"])
            hero_video = Path(tmp) / "hero.mp4"
            hero_video.write_bytes(b"mp4")

            export_stream = StringIO()
            with redirect_stdout(export_stream):
                self.assertEqual(
                    oodrive_main(
                        [
                            "export-env-demo",
                            "--environment-summary",
                            str(summary_path),
                            "--hero-video",
                            str(hero_video),
                            "--output-root",
                            str(Path(tmp) / "packs"),
                            "--run-id",
                            "demo",
                        ]
                    ),
                    0,
                )
            exported = json.loads(export_stream.getvalue())
            manifest_path = Path(exported["artifacts"]["environment_demo_manifest_path"])

            score_stream = StringIO()
            with redirect_stdout(score_stream):
                self.assertEqual(
                    oodrive_main(
                        [
                            "score-env-demo",
                            "--environment-summary",
                            str(summary_path),
                            "--demo-manifest",
                            str(manifest_path),
                            "--metric-only",
                        ]
                    ),
                    0,
                )

            self.assertIn("METRIC environment_demo_readiness_score=97.0000", score_stream.getvalue())


if __name__ == "__main__":
    unittest.main()
