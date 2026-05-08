from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.environments import EnvironmentSuiteConfig, run_environment_forge
from driverx.evaluation.environment_demo_score import (
    EnvironmentDemoReadinessInputs,
    load_environment_demo_readiness_inputs,
    score_environment_demo_readiness,
)
from driverx.pipeline.environment_demo_pack import build_environment_demo_pack


class EnvironmentDemoScoreTest(unittest.TestCase):
    def test_weak_environment_demo_blocks_when_not_product_visible(self) -> None:
        result = score_environment_demo_readiness(
            EnvironmentDemoReadinessInputs(
                family_count=6,
                recipe_count=6,
                asset_request_count=11,
                weather_ready_count=6,
                traffic_ready_count=6,
                road_local_asset_count=11,
                expected_policy_pressure_count=6,
            )
        )

        self.assertEqual(result.status, "blocked")
        self.assertLess(result.environment_demo_readiness_score, result.threshold)
        self.assertIn("Environment Studio index.html is missing", result.blockers)

    def test_generated_demo_pack_scores_as_ready(self) -> None:
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
            hero_video.write_bytes(b"mp4")
            pack = build_environment_demo_pack(
                environment_summary_path=Path(summary["summary_path"]),
                hero_video_path=hero_video,
                output_root=root / "packs",
                run_id="demo",
            )
            inputs = load_environment_demo_readiness_inputs(
                environment_summary_path=Path(summary["summary_path"]),
                demo_manifest_path=Path(pack["environment_demo_manifest_path"]),
            )
            result = score_environment_demo_readiness(inputs)

        self.assertEqual(result.status, "passed")
        self.assertGreaterEqual(result.environment_demo_readiness_score, 90.0)
        self.assertEqual(result.components["generation_substance"], 30.0)
        self.assertEqual(result.components["product_surface"], 20.0)

    def test_score_input_fixture_can_be_loaded(self) -> None:
        with TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "target.json"
            html = Path(tmp) / "index.html"
            commands = Path(tmp) / "commands.sh"
            storyboard = Path(tmp) / "video_storyboard.md"
            for path in (html, commands):
                path.write_text("x", encoding="utf-8")
            storyboard.write_text("Target length: 1-5 minutes", encoding="utf-8")
            fixture.write_text(
                json.dumps(
                    {
                        "environment_summary_path": "environment_suite_summary.json",
                        "demo_manifest_path": "environment_demo_manifest.json",
                        "family_count": 6,
                        "recipe_count": 6,
                        "asset_request_count": 11,
                        "weather_ready_count": 6,
                        "traffic_ready_count": 6,
                        "road_local_asset_count": 11,
                        "expected_policy_pressure_count": 6,
                        "command_names": [
                            "oodrive generate-envs",
                            "oodrive export-env-demo",
                            "oodrive score-env-demo",
                        ],
                        "html_path": str(html),
                        "commands_path": str(commands),
                        "storyboard_path": str(storyboard),
                        "hero_video_status": "local_file",
                        "submission_pack_status": "local_file",
                        "card_count": 6,
                        "claim_boundaries": [
                            "closed_loop_vla_control=false",
                            "real_time_vla_control=false",
                            "sampled_open_loop_reasoning=true",
                            "time_warped_offline_demo=true",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            inputs = load_environment_demo_readiness_inputs(score_input_path=fixture)
            result = score_environment_demo_readiness(inputs)

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.environment_demo_readiness_score, 100.0)


if __name__ == "__main__":
    unittest.main()
