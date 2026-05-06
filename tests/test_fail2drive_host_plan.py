import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.simulators.fail2drive_host_plan import (
    Fail2DriveHostPlanConfig,
    build_fail2drive_host_plan,
    classify_graphics_host_diagnostics,
    write_fail2drive_host_plan,
)


class Fail2DriveHostPlanTest(unittest.TestCase):
    def test_classifier_blocks_cuda_only_host_without_graphics(self) -> None:
        suitability = classify_graphics_host_diagnostics(
            {"nvidia_smi": "RTX 6000 Ada", "logs": "CARLA did not open port"}
        )

        self.assertEqual(suitability.state, "blocked")
        self.assertTrue(suitability.cuda_ready)
        self.assertFalse(suitability.graphics_ready)
        self.assertIn("graphics runtime", suitability.blockers[0])

    def test_host_plan_writes_commands_and_pullback_policy(self) -> None:
        with TemporaryDirectory() as tmp:
            plan = build_fail2drive_host_plan(
                Fail2DriveHostPlanConfig(remote="root@example", ssh_opts="-p 22"),
                diagnostics_payload={"status": "vulkan ready", "carla_server_ready": True},
            )
            summary = write_fail2drive_host_plan(Path(tmp) / "plan", plan)
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertEqual(summary["suitability"]["state"], "ready")
        self.assertIn("root@example", "\n".join(summary["commands"]))
        self.assertIn("Pullback Policy", report)
        self.assertIn("videos unless explicitly requested", report)

    def test_host_plan_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            diagnostics = root / "diagnostics.json"
            diagnostics.write_text(json.dumps({"status": "llvmpipe"}), encoding="utf-8")
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "plan-full-fail2drive-score-host",
                        "--diagnostics",
                        str(diagnostics),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "plan",
                    ]
            )
            result = json.loads(stream.getvalue())
            json_exists = Path(result["json_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["suitability"]["state"], "blocked")
        self.assertTrue(json_exists)


if __name__ == "__main__":
    unittest.main()
