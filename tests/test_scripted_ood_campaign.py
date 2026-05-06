import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline.scripted_ood_campaign import (
    ScriptedOodCampaignConfig,
    run_scripted_ood_campaign,
)


class ScriptedOodCampaignTest(unittest.TestCase):
    def test_fake_campaign_aggregates_best_and_worst_cases(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_scripted_ood_campaign(
                ScriptedOodCampaignConfig(
                    scenario_config_path=Path("configs/scenario_forge.sample.yaml"),
                    carla_ood_config_path=Path("configs/carla_ood_demo.local.sample.yaml"),
                    output_root=Path(tmp),
                    run_id="campaign",
                    count=3,
                    live=False,
                )
            )
            cases = result["cases"]

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["case_count"], 3)
        self.assertEqual(result["live_case_count"], 0)
        self.assertIsNotNone(result["worst_case"])
        self.assertIsNotNone(result["best_case"])
        self.assertEqual(len(cases), 3)
        self.assertTrue(all(case["tracks_path"] for case in cases))

    def test_campaign_cli_honors_limit(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "campaign.yaml"
            config.write_text(
                "scripted_ood_campaign:\n"
                "  scenario_config_path: configs/scenario_forge.sample.yaml\n"
                "  carla_ood_config_path: configs/carla_ood_demo.local.sample.yaml\n"
                "  behavior_ids: motorcycle_filtering,sudden_brake\n"
                "  count: 3\n"
                "  live: false\n",
                encoding="utf-8",
            )
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "run-scripted-ood-campaign",
                        "--config",
                        str(config),
                        "--limit",
                        "2",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "campaign",
                    ]
                )
            result = json.loads(stream.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["case_count"], 2)
        self.assertEqual(result["behavior_ids"], ["motorcycle_filtering", "sudden_brake"])

    def test_resume_reuses_existing_case_and_video_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = run_scripted_ood_campaign(
                ScriptedOodCampaignConfig(
                    scenario_config_path=Path("configs/scenario_forge.sample.yaml"),
                    carla_ood_config_path=Path("configs/carla_ood_demo.local.sample.yaml"),
                    output_root=root,
                    run_id="campaign",
                    count=1,
                    live=False,
                    resume=True,
                )
            )
            case = first["cases"][0]
            case_dir = root / "campaign" / "cases" / case["case_id"]
            video_dir = case_dir / "local-video"
            video_dir.mkdir(parents=True)
            (video_dir / "ood_video_evidence.json").write_text(
                json.dumps(
                    {
                        "status": "passed",
                        "json_path": str(video_dir / "ood_video_evidence.json"),
                        "report_path": str(video_dir / "ood_video_evidence.md"),
                        "video_path": str(video_dir / "case.mp4"),
                    }
                ),
                encoding="utf-8",
            )

            second = run_scripted_ood_campaign(
                ScriptedOodCampaignConfig(
                    scenario_config_path=Path("configs/scenario_forge.sample.yaml"),
                    carla_ood_config_path=Path("configs/carla_ood_demo.local.sample.yaml"),
                    output_root=root,
                    run_id="campaign",
                    count=1,
                    live=False,
                    resume=True,
                )
            )

        self.assertEqual(second["cases"][0]["video_status"], "passed")
        self.assertIn("local-video", second["cases"][0]["video_evidence_path"])
        self.assertEqual(second["cases"][0]["video_path"], str(video_dir / "case.mp4"))


if __name__ == "__main__":
    unittest.main()
