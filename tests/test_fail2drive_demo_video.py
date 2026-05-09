from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.fail2drive.demo_video import Fail2DriveDemoVideoConfig, run_fail2drive_demo_video


class Fail2DriveDemoVideoTest(unittest.TestCase):
    def test_demo_video_report_copies_source_and_scores_readability(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = run_fail2drive_demo_video(
                Fail2DriveDemoVideoConfig(
                    evidence_path=Path("tests/fixtures/fail2drive_evidence/run_evidence.json"),
                    reasoning_path=Path("tests/fixtures/fail2drive_reasoning/f2d_reasoning.json"),
                    route_path=Path("tests/fixtures/fail2drive_routes/valid_roadblocked.xml"),
                    input_video_path=Path("tests/fixtures/fail2drive_evidence/source.mp4"),
                    output_root=Path(tmp),
                    run_id="demo",
                )
            )

            self.assertEqual(summary["status"], "passed")
            self.assertTrue(Path(summary["video_path"]).exists())
            self.assertGreaterEqual(summary["metrics"]["readability_score"], 90.0)


if __name__ == "__main__":
    unittest.main()
