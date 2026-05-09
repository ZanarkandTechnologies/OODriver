from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.fail2drive.run_wrapper import Fail2DriveRouteRunRequest, run_fail2drive_route_workflow


class Fail2DriveRunWrapperTest(unittest.TestCase):
    def test_default_agent_is_oodrive_capture_agent(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = run_fail2drive_route_workflow(
                Fail2DriveRouteRunRequest(
                    route_path=Path("tests/fixtures/fail2drive_routes/valid_roadblocked.xml"),
                    fail2drive_root=Path("third_party/fail2drive"),
                    output_root=Path(tmp),
                    run_id="capture-default",
                    skip_validate=True,
                )
            )

        self.assertEqual(summary["agent_kind"], "oodrive-capture")
        self.assertIn("oodrive_capture_agent.py", summary["agent_path"])
        self.assertIn("OODRIVE_CAPTURE_EVERY", summary["plan"]["env"])
        self.assertIn("VIZ_PATH", summary["plan"]["env"])

    def test_explicit_oodrive_capture_agent_kind(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = run_fail2drive_route_workflow(
                Fail2DriveRouteRunRequest(
                    route_path=Path("tests/fixtures/fail2drive_routes/valid_roadblocked.xml"),
                    fail2drive_root=Path("third_party/fail2drive"),
                    output_root=Path(tmp),
                    run_id="capture-kind",
                    agent_kind="oodrive-capture",
                    skip_validate=True,
                )
            )

        self.assertEqual(summary["agent_kind"], "oodrive-capture")
        self.assertIn("oodrive_capture_agent.py", summary["agent_path"])


if __name__ == "__main__":
    unittest.main()
