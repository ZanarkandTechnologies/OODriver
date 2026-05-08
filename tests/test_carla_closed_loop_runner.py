from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
from tempfile import TemporaryDirectory
import unittest

from driverx.evaluation.closed_loop_control_score import score_closed_loop_control
from driverx.evaluation.closed_loop_integration_score import score_closed_loop_integration
from driverx.scenarios.studio_product_closed_loop_runtime import run_studio_closed_loop_run
from driverx.simulators.carla_closed_loop_runner import PausedClosedLoopConfig, run_paused_closed_loop


class CarlaClosedLoopRunnerTests(unittest.TestCase):
    def test_fake_runner_writes_scored_trace(self) -> None:
        with TemporaryDirectory() as tmp:
            payload = run_paused_closed_loop(PausedClosedLoopConfig(run_id="fake"), Path(tmp))
            trace_path = Path(payload["json_path"])

            control = score_closed_loop_control(trace_path)
            integration = score_closed_loop_integration(trace_path)

            self.assertEqual(control.status, "passed")
            self.assertEqual(integration.status, "passed")
            self.assertGreaterEqual(len(payload["steps"]), 3)
            self.assertIn("closed_loop_vla_control=paused_receding_horizon", payload["claim_boundaries"])
            self.assertTrue(Path(payload["rgb_folder"]).exists())
            self.assertTrue(all(step.get("pre_rgb_frame_paths") for step in payload["steps"]))
            self.assertTrue(all(step.get("post_rgb_frame_paths") for step in payload["steps"]))
            self.assertTrue(all(step.get("inference_result_path") for step in payload["steps"]))

    def test_cli_runtime_maps_live_config(self) -> None:
        with TemporaryDirectory() as tmp:
            captured: list[PausedClosedLoopConfig] = []

            def fake_run(config: PausedClosedLoopConfig, run_dir: Path) -> dict[str, object]:
                captured.append(config)
                trace_path = run_dir / "closed_loop_trace.json"
                report_path = run_dir / "closed_loop_trace.md"
                trace_path.write_text("{}", encoding="utf-8")
                report_path.write_text("# trace\n", encoding="utf-8")
                return {
                    "json_path": str(trace_path),
                    "report_path": str(report_path),
                    "mode": "none",
                    "backend": config.backend,
                    "policy": config.policy,
                    "steps": [],
                    "claim_boundaries": [],
                    "blockers": ["stub"],
                }

            with patch("driverx.scenarios.studio_product_closed_loop_runtime.run_paused_closed_loop", fake_run):
                result = run_studio_closed_loop_run(
                    backend="carla-live",
                    policy="alpamayo-remote",
                    output_root=Path(tmp),
                    run_id="live",
                    steps=2,
                    control_ticks_per_step=5,
                    host="10.0.0.2",
                    port=2100,
                    timeout_s=30.0,
                    map_name="Town03_Opt",
                    load_map=True,
                    weather_preset="WetCloudySunset",
                    camera_width=800,
                    camera_height=450,
                    camera_fov=100.0,
                    cache_root=Path(tmp) / "cache",
                    remote_output_root="/workspace/out",
                    alpamayo_python=Path("/workspace/venv/bin/python"),
                    alpamayo_command="{python} runner.py --package {package} --output {output}",
                )

            self.assertEqual(result.status, "blocked")
            self.assertEqual(len(captured), 1)
            config = captured[0]
            self.assertEqual(config.backend, "carla-live")
            self.assertEqual(config.policy, "alpamayo-remote")
            self.assertEqual(config.host, "10.0.0.2")
            self.assertEqual(config.port, 2100)
            self.assertEqual(config.map_name, "Town03_Opt")
            self.assertTrue(config.load_map)
            self.assertEqual(config.weather_preset, "WetCloudySunset")
            self.assertEqual(config.camera_width, 800)
            self.assertEqual(config.camera_height, 450)
            self.assertEqual(config.camera_fov, 100.0)
            self.assertEqual(config.remote_output_root, "/workspace/out")


if __name__ == "__main__":
    unittest.main()
