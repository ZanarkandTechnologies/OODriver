import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.simulators import (
    CarlaRunConfig,
    Fail2DriveVideoSmokeConfig,
    plan_fail2drive_video_smoke,
    write_fail2drive_video_smoke_plan,
)


ROUTE_NAME = "Generalization_PedestriansOnRoad_1088.xml"


def _fake_fail2drive_root(root: Path, *, include_video_tool: bool = True) -> None:
    (root / "leaderboard" / "leaderboard").mkdir(parents=True)
    (root / "leaderboard" / "leaderboard" / "leaderboard_evaluator_local.py").write_text(
        "# fake evaluator\n",
        encoding="utf-8",
    )
    (root / "team_code").mkdir()
    (root / "team_code" / "visu_agent.py").write_text("# fake agent\n", encoding="utf-8")
    (root / "fail2drive_split").mkdir()
    (root / "fail2drive_split" / ROUTE_NAME).write_text(
        '<routes><route id="0" town="Town10HD_Opt" /></routes>\n',
        encoding="utf-8",
    )
    if include_video_tool:
        (root / "tools").mkdir()
        (root / "tools" / "generate_video.py").write_text("# fake video tool\n", encoding="utf-8")


def _carla_config(root: Path, output_dir: Path) -> CarlaRunConfig:
    return CarlaRunConfig(
        host="host.docker.internal",
        port=2000,
        timeout_s=0.25,
        carla_root=None,
        fail2drive_root=root,
        route_path=Path("fail2drive_split") / ROUTE_NAME,
        agent_path=Path("team_code/visu_agent.py"),
        output_dir=output_dir,
        track="MAP",
    )


class Fail2DriveVideoSmokeTest(unittest.TestCase):
    def test_plan_includes_route_video_and_output_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "fail2drive"
            output_dir = tmp_path / "outputs"
            _fake_fail2drive_root(root)
            (output_dir / "visualizations" / Path(ROUTE_NAME).stem / "rgb").mkdir(parents=True)

            config = Fail2DriveVideoSmokeConfig.from_carla_config(
                _carla_config(root, output_dir),
                timeout_s=900.0,
                traffic_manager_port=8000,
            )
            plan = plan_fail2drive_video_smoke(config)

        self.assertTrue(plan.dry_run)
        self.assertEqual(plan.cwd, root.resolve())
        self.assertEqual(plan.env["LIVE_VISU"], "1")
        self.assertEqual(plan.env["REPETITION"], "0")
        self.assertEqual(plan.env["SAVE_PATH"], str((output_dir / "visualizations").resolve()))
        self.assertEqual(plan.env["SCENARIO_RUNNER_ROOT"], str((root / "scenario_runner").resolve()))
        self.assertEqual(plan.env["TOWN"], "Town10HD_Opt")
        self.assertEqual(
            plan.env["VIZ_PATH"],
            str((output_dir / "visualizations" / Path(ROUTE_NAME).stem / "rgb").resolve()),
        )
        self.assertIn("leaderboard_evaluator_local.py", " ".join(plan.run_command))
        self.assertIn("--routes", plan.run_command)
        self.assertIn("--checkpoint", plan.run_command)
        self.assertIn("--host", plan.run_command)
        self.assertIn("--traffic-manager-port", plan.run_command)
        self.assertIn("900", plan.run_command)
        self.assertIn("generate_video.py", " ".join(plan.video_command))
        self.assertIn("-f", plan.video_command)
        self.assertEqual(plan.expected_outputs["video"].suffix, ".mp4")
        self.assertEqual(plan.live_blockers, [])

    def test_plan_surfaces_missing_files_as_actionable_blockers(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "fail2drive"
            output_dir = tmp_path / "outputs"
            _fake_fail2drive_root(root, include_video_tool=False)
            (root / "team_code" / "visu_agent.py").unlink()
            (root / "fail2drive_split" / ROUTE_NAME).unlink()

            plan = plan_fail2drive_video_smoke(
                Fail2DriveVideoSmokeConfig.from_carla_config(_carla_config(root, output_dir))
            )

        blockers = "\n".join(plan.live_blockers)
        self.assertIn("Fail2Drive route not found", blockers)
        self.assertIn("Fail2Drive agent not found", blockers)
        self.assertIn("Fail2Drive video tool not found", blockers)
        self.assertIn("RGB folder does not exist yet", blockers)

    def test_write_plan_outputs_json_and_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "fail2drive"
            output_dir = tmp_path / "outputs"
            _fake_fail2drive_root(root)
            plan = plan_fail2drive_video_smoke(
                Fail2DriveVideoSmokeConfig.from_carla_config(
                    _carla_config(root, output_dir),
                    live_visu=False,
                )
            )
            summary = write_fail2drive_video_smoke_plan(tmp_path / "run", plan)
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertNotIn("LIVE_VISU", payload["env"])
        self.assertIn("run_command", payload)
        self.assertIn("video_command", payload)
        self.assertIn("Fail2Drive Video Smoke Plan", report)
        self.assertIn("RGB folder does not exist yet", report)


if __name__ == "__main__":
    unittest.main()
