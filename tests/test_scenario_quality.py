import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.scenarios import (
    ScenarioQualityThresholds,
    evaluate_scenario_quality,
    select_quality_passed_cases,
    write_scenario_quality_outputs,
)


class ScenarioQualityTest(unittest.TestCase):
    def test_quality_report_passes_valid_campaign_case(self) -> None:
        with TemporaryDirectory() as tmp:
            alignment_path = Path(tmp) / "road_alignment_report.json"
            alignment_path.write_text(json.dumps({"passes": True}), encoding="utf-8")
            report = evaluate_scenario_quality(
                {
                    "case_id": "case-1",
                    "recipe_id": "scenario-1",
                    "duration_s": 24.0,
                    "frame_count": 120,
                    "min_distance_m": 2.2,
                    "video_status": "passed",
                    "road_alignment_path": str(alignment_path),
                },
                ScenarioQualityThresholds(
                    min_duration_s=10.0,
                    min_frame_count=100,
                    require_video=True,
                    require_road_alignment=True,
                ),
            )

        self.assertTrue(report.passes)
        self.assertEqual(report.metrics["road_aligned"], True)

    def test_quality_report_blocks_missing_conflict_and_short_video(self) -> None:
        report = evaluate_scenario_quality(
            {
                "case_id": "case-2",
                "recipe_id": "scenario-2",
                "duration_s": 1.0,
                "frame_count": 5,
                "min_distance_m": 14.0,
            },
            ScenarioQualityThresholds(min_duration_s=5.0, min_frame_count=20),
        )

        self.assertFalse(report.passes)
        self.assertGreaterEqual(len(report.blockers), 5)

    def test_writes_quality_outputs_and_selects_passed_cases(self) -> None:
        with TemporaryDirectory() as tmp:
            alignment_path = Path(tmp) / "road_alignment_report.json"
            alignment_path.write_text(json.dumps({"passes": True}), encoding="utf-8")
            reports = [
                evaluate_scenario_quality(
                    {
                        "case_id": "case-1",
                        "recipe_id": "scenario-1",
                        "duration_s": 8.0,
                        "frame_count": 30,
                        "min_distance_m": 3.0,
                        "video_status": "passed",
                        "road_alignment_path": str(alignment_path),
                    }
                ),
                evaluate_scenario_quality(
                    {
                        "case_id": "case-2",
                        "recipe_id": "scenario-2",
                        "duration_s": 2.0,
                        "frame_count": 5,
                        "min_distance_m": 10.0,
                    }
                ),
            ]
            summary = write_scenario_quality_outputs(reports, Path(tmp))

            self.assertEqual(select_quality_passed_cases(reports), ["case-1"])
            self.assertEqual(summary["passed_count"], 1)
            self.assertTrue(Path(summary["json_path"]).exists())
            self.assertTrue(Path(summary["report_path"]).exists())


if __name__ == "__main__":
    unittest.main()
