from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.fail2drive.model_reaction import Fail2DriveModelReactionConfig, run_fail2drive_model_reaction_suite


class Fail2DriveModelReactionTest(unittest.TestCase):
    def test_batch_matrix_scores_route_diversity(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = run_fail2drive_model_reaction_suite(
                Fail2DriveModelReactionConfig(
                    routes=(Path("tests/fixtures/fail2drive_routes"),),
                    fail2drive_root=Path("third_party/fail2drive"),
                    output_root=Path(tmp),
                    run_id="matrix",
                    limit=2,
                    live=False,
                    reason=True,
                    demo_video=True,
                )
            )

            self.assertEqual(summary["status"], "passed")
            self.assertEqual(summary["metrics"]["route_count"], 2)
            self.assertEqual(summary["metrics"]["reasoning_case_count"], 2)
            self.assertEqual(summary["metrics"]["demo_video_requested_count"], 2)
            self.assertGreater(summary["metrics"]["f2d_model_reaction_coverage"], 0)
            self.assertTrue(Path(summary["json_path"]).exists())


if __name__ == "__main__":
    unittest.main()
