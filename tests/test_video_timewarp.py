from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from driverx.simulators.video_timewarp import timewarp_video, write_video_timewarp


class VideoTimewarpTests(unittest.TestCase):
    def test_plans_timewarp_without_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.mp4"
            input_path.write_bytes(b"not-a-real-video")

            result = timewarp_video(
                input_path,
                root / "out.mp4",
                speed_factor=3.0,
                fps=12,
                ffmpeg_path="/usr/bin/ffmpeg",
                ffprobe_path="/usr/bin/true",
                run=False,
            )

            self.assertEqual(result.status, "planned")
            self.assertIn("setpts=PTS/3.0,fps=12", result.command)
            self.assertIn("time_warped_offline_demo=true", result.claim_boundaries)

    def test_blocks_missing_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = timewarp_video(
                Path(tmp) / "missing.mp4",
                Path(tmp) / "out.mp4",
                speed_factor=2.0,
                fps=10,
                ffmpeg_path="/usr/bin/ffmpeg",
                ffprobe_path="/usr/bin/true",
                run=True,
            )

            self.assertEqual(result.status, "blocked")
            self.assertTrue(result.blockers)

    def test_writes_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.mp4"
            input_path.write_bytes(b"not-a-real-video")
            result = timewarp_video(
                input_path,
                root / "out.mp4",
                speed_factor=2.0,
                fps=10,
                ffmpeg_path="/usr/bin/ffmpeg",
                ffprobe_path="/usr/bin/true",
                run=False,
            )
            summary = write_video_timewarp(root / "evidence", result)

            self.assertTrue(Path(summary["json_path"]).exists())
            self.assertIn("Video Timewarp", Path(summary["report_path"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
