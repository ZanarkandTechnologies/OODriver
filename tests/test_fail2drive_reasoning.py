from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.fail2drive.reasoning import Fail2DriveReasoningRequest, run_fail2drive_reasoning


class Fail2DriveReasoningTest(unittest.TestCase):
    def test_fake_reasoning_writes_events_with_claim_boundaries(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = run_fail2drive_reasoning(
                Fail2DriveReasoningRequest(
                    evidence_path=Path("tests/fixtures/fail2drive_evidence/run_evidence.json"),
                    route_path=Path("tests/fixtures/fail2drive_routes/valid_roadblocked.xml"),
                    output_root=Path(tmp),
                    run_id="reason",
                    mode="fake",
                    keyframes=3,
                )
            )

            self.assertEqual(summary["status"], "passed")
            self.assertGreaterEqual(summary["metrics"]["reasoning_event_count"], 3)
            self.assertIn("closed_loop_vla_control=false", summary["claim_boundaries"])
            self.assertTrue(Path(summary["json_path"]).exists())


if __name__ == "__main__":
    unittest.main()
