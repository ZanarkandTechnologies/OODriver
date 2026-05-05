import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from driverx.cli import main
from driverx.simulators.fail2drive_route_runner import (
    Fail2DriveRouteRunConfig,
    run_fail2drive_route,
    write_fail2drive_route_run,
)


class Fail2DriveRouteRunnerTest(unittest.TestCase):
    def test_dry_run_ignores_video_blockers_and_validates_route_inputs(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = _write_plan(root)

            result = run_fail2drive_route(
                Fail2DriveRouteRunConfig(
                    plan_path=plan,
                    run_dir=root / "run",
                    dry_run=True,
                )
            )

        self.assertEqual(result.status, "planned")
        self.assertEqual(result.route_blockers, [])
        self.assertIsNone(result.exit_code)

    def test_missing_route_prerequisites_block_before_execution(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = _write_plan(root)
            (root / "route.xml").unlink()

            result = run_fail2drive_route(
                Fail2DriveRouteRunConfig(plan_path=plan, run_dir=root / "run")
            )

        self.assertEqual(result.status, "blocked")
        self.assertIn("route_path not found", "\n".join(result.route_blockers))

    def test_runner_executes_command_and_writes_logs(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = _write_plan(root, command=["python3", "-c", "print('route-ok')"])
            result = run_fail2drive_route(
                Fail2DriveRouteRunConfig(plan_path=plan, run_dir=root / "run")
            )
            summary = write_fail2drive_route_run(root / "run", result)
            stdout = Path(result.stdout_path).read_text(encoding="utf-8")
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.exit_code, 0)
        self.assertIn("route-ok", stdout)
        self.assertIn("Fail2Drive Route Run", report)

    def test_runner_falls_back_from_python_to_python3(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = _write_plan(root, command=["python", "-c", "print('fallback-ok')"])
            with patch("driverx.simulators.fail2drive_route_runner.shutil.which") as which:
                which.side_effect = lambda name: None if name == "python" else "python3"
                result = run_fail2drive_route(
                    Fail2DriveRouteRunConfig(plan_path=plan, run_dir=root / "run", dry_run=True)
                )

        self.assertEqual(result.command[0], "python3")

    def test_runner_names_missing_python_dependency(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            command = [
                "python3",
                "-c",
                "raise ModuleNotFoundError(\"No module named 'numpy'\")",
            ]
            plan = _write_plan(root, command=command)
            result = run_fail2drive_route(
                Fail2DriveRouteRunConfig(plan_path=plan, run_dir=root / "run")
            )

        self.assertEqual(result.status, "blocked")
        self.assertIn("numpy", result.route_blockers[0])

    def test_cli_writes_route_run_summary(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = _write_plan(root, command=["python3", "-c", "print('cli-ok')"])
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "run-fail2drive-route",
                        "--plan",
                        str(plan),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "cli",
                    ]
                )
            summary = json.loads(stream.getvalue())
            json_exists = Path(summary["json_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(json_exists)
        self.assertEqual(summary["status"], "passed")


def _write_plan(root: Path, *, command: list[str] | None = None) -> Path:
    for name in ("evaluator.py", "route.xml", "agent.py"):
        (root / name).write_text("# fixture\n", encoding="utf-8")
    output = root / "out"
    payload = {
        "route_path": str(root / "route.xml"),
        "agent_path": str(root / "agent.py"),
        "evaluator_path": str(root / "evaluator.py"),
        "cwd": str(root),
        "run_command": command or ["python3", "-c", "print('ok')"],
        "env": {"SAVE_PATH": str(output / "visualizations"), "LIVE_VISU": "1"},
        "expected_outputs": {
            "result": str(output / "route_res.json"),
            "rgb_folder": str(output / "visualizations" / "Route" / "rgb"),
            "video": str(output / "Route.mp4"),
        },
        "live_blockers": ["Fail2Drive video tool not found", "RGB folder does not exist yet"],
    }
    path = root / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
