import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from driverx.cli import main
from driverx.simulators.route_video_assembly import (
    plan_route_video_assembly,
    run_route_video_assembly,
    write_route_video_assembly,
)


class RouteVideoAssemblyTest(unittest.TestCase):
    def test_plan_scans_frames_and_builds_ffmpeg_command(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            rgb = root / "visualizations" / "RouteA" / "rgb"
            rgb.mkdir(parents=True)
            for name in ("000002.png", "000001.png", "note.txt"):
                (rgb / name).write_text("frame\n", encoding="utf-8")

            plan = plan_route_video_assembly(rgb, ffmpeg_path="/usr/bin/ffmpeg")

        self.assertEqual(plan.frame_count, 2)
        self.assertEqual(plan.live_blockers, [])
        self.assertEqual(plan.output_video.name, "RouteA.mp4")
        self.assertIn("-pattern_type", plan.command)
        self.assertIn("/usr/bin/ffmpeg", plan.command[0])

    def test_plan_reports_missing_folder_frames_and_ffmpeg(self) -> None:
        with TemporaryDirectory() as tmp:
            with patch("driverx.simulators.route_video_assembly.shutil.which", return_value=None):
                plan = plan_route_video_assembly(Path(tmp) / "missing")

        blockers = "\n".join(plan.live_blockers)
        self.assertIn("RGB folder not found", blockers)
        self.assertIn("ffmpeg not found", blockers)
        self.assertEqual(plan.command, [])

    def test_run_uses_fake_ffmpeg_when_requested(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_ffmpeg = root / "ffmpeg"
            fake_ffmpeg.write_text("#!/usr/bin/env sh\necho ffmpeg-ok\nexit 0\n", encoding="utf-8")
            fake_ffmpeg.chmod(0o755)
            rgb = root / "vis" / "RouteB" / "rgb"
            rgb.mkdir(parents=True)
            (rgb / "000001.jpg").write_text("frame\n", encoding="utf-8")

            plan = plan_route_video_assembly(rgb, ffmpeg_path=str(fake_ffmpeg))
            result = run_route_video_assembly(plan)

        self.assertTrue(result.executed)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.status, "passed")
        self.assertIn("ffmpeg-ok", result.stdout)

    def test_writer_and_cli_emit_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            rgb = root / "vis" / "RouteC" / "rgb"
            rgb.mkdir(parents=True)
            (rgb / "000001.png").write_text("frame\n", encoding="utf-8")
            plan = plan_route_video_assembly(rgb, ffmpeg_path="/bin/echo")
            summary = write_route_video_assembly(root / "written", plan)
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "assemble-route-video",
                        "--rgb-folder",
                        str(rgb),
                        "--ffmpeg-path",
                        "/bin/echo",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "cli",
                    ]
                )
            cli_summary = json.loads(stream.getvalue())
            report_exists = Path(summary["report_path"]).exists()
            cli_json_exists = Path(cli_summary["json_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(report_exists)
        self.assertTrue(cli_json_exists)
        self.assertEqual(cli_summary["status"], "planned")


if __name__ == "__main__":
    unittest.main()
