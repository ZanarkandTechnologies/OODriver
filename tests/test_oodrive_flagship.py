from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.scenarios.flagship import (
    build_flagship_scenario,
    load_flagship_config,
    write_flagship_scenario,
)


class OODriveFlagshipTests(unittest.TestCase):
    def test_default_flagship_pack_has_complex_ood_pressures(self) -> None:
        config = load_flagship_config(Path("configs/oodrive_flagship_malaysia.yaml"))
        pack = build_flagship_scenario(config).to_jsonable()

        actor_ids = {actor["actor_id"] for actor in pack["actors"]}
        self.assertIn("lead_lorry", actor_ids)
        self.assertIn("filtering_motorcycle", actor_ids)
        self.assertIn("roadside_vendor_occluder", actor_ids)
        self.assertIn("roadwork_debris_and_cones", actor_ids)
        self.assertIn("wrong_way_scooter", actor_ids)
        self.assertEqual(len(pack["planned_checkpoints"]), 10)
        self.assertIn("motorcycle_filtering", pack["behavior_sequence"])
        self.assertTrue(pack["quality_targets"]["require_planned_vs_actual_path"])
        self.assertIn("real_time_vla_control=false", pack["claim_boundaries"])

    def test_runtime_command_plan_names_future_h100_steps(self) -> None:
        config = load_flagship_config(Path("configs/oodrive_flagship_malaysia.yaml"))
        pack = build_flagship_scenario(config).to_jsonable()
        commands = {command["command_id"]: command for command in pack["runtime_commands"]}

        self.assertIn("run_carla_campaign_baseline", commands)
        self.assertIn("capture_checkpoints", commands)
        self.assertIn("run_alpamayo_checkpoints", commands)
        self.assertIn("replay_alpamayo_trajectory", commands)
        self.assertIn("build_final_pack", commands)
        self.assertIn("run-flagship-carla-capture", commands["capture_checkpoints"]["command"])
        self.assertIn("run-alpamayo-checkpoint-batch", commands["run_alpamayo_checkpoints"]["command"])

    def test_write_flagship_scenario_outputs_json_and_markdown(self) -> None:
        config = load_flagship_config(Path("configs/oodrive_flagship_malaysia.yaml"))
        with TemporaryDirectory() as tmp:
            summary = write_flagship_scenario(Path(tmp), build_flagship_scenario(config))
            json_path = Path(summary["json_path"])
            report_path = Path(summary["report_path"])

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual(payload["scenario_id"], "flagship-malaysia-wet-roadwork")
        self.assertIn("Malaysian wet night roadwork chaos", report)
        self.assertIn("Runtime Command Plan", report)

    def test_cli_builds_flagship_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-flagship-oodrive-scenario",
                        "--config",
                        "configs/oodrive_flagship_malaysia.yaml",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "flagship-smoke",
                    ]
                )
            result = json.loads(stream.getvalue())
            json_exists = Path(result["json_path"]).exists()
            report_exists = Path(result["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["scenario_id"], "flagship-malaysia-wet-roadwork")
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)


if __name__ == "__main__":
    unittest.main()
