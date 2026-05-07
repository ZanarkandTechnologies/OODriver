from __future__ import annotations

import json
import shutil
import subprocess
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from oodrive.cli import main as oodrive_main


class HeroDemoScoreTest(unittest.TestCase):
    def test_weak_fixture_blocks_and_target_fixture_passes(self) -> None:
        weak = _run_score_fixture("candidate_demo.json")
        target = _run_score_fixture("target_demo.json")

        self.assertEqual(weak["status"], "blocked")
        self.assertLess(weak["summary"]["hero_demo_score"], weak["summary"]["threshold"])
        self.assertIn("frame_time_overlay_coverage", " ".join(weak["blockers"]))
        self.assertEqual(target["status"], "passed")
        self.assertEqual(target["summary"]["hero_demo_score"], 100.0)

    def test_metric_only_emits_primary_metric_line(self) -> None:
        stream = StringIO()
        with redirect_stdout(stream):
            exit_code = oodrive_main(
                [
                    "score-demo",
                    "--score-input",
                    "qa/fixtures/hero_demo_score/candidate_demo.json",
                    "--metric-only",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stream.getvalue().strip(), "METRIC hero_demo_score=30.4889")

    def test_demo_video_renders_frame_time_reasoning_and_rag_overlay(self) -> None:
        if shutil.which("ffmpeg") is None:
            self.skipTest("ffmpeg unavailable")
        try:
            import PIL  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Pillow unavailable")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = _write_db(root)
            run_path = _write_run(root)
            evaluation_path = _write_evaluation(root)
            input_video = _write_tiny_video(root)
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = oodrive_main(
                    [
                        "demo-video",
                        "--db",
                        str(db_path),
                        "--run",
                        str(run_path),
                        "--evaluation",
                        str(evaluation_path),
                        "--input-video",
                        str(input_video),
                        "--output-root",
                        str(root / "demo-videos"),
                        "--run-id",
                        "demo",
                        "--speed-factor",
                        "1",
                    ]
                )
            result = json.loads(stream.getvalue())
            overlay_report = Path(result["artifacts"]["hero_demo_video_json_path"])
            overlay_payload = json.loads(overlay_report.read_text(encoding="utf-8"))
            output_exists = Path(result["artifacts"]["hero_demo_video_path"]).exists()
            sample_exists = Path(overlay_payload["sample_frame_path"]).exists()

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["status"], "passed")
            self.assertTrue(output_exists)
            self.assertEqual(overlay_payload["frame_time_overlay_coverage"], 1.0)
            self.assertGreaterEqual(overlay_payload["event_count"], 1)
            self.assertTrue(sample_exists)


def _run_score_fixture(name: str) -> dict[str, object]:
    stream = StringIO()
    with redirect_stdout(stream):
        exit_code = oodrive_main(
            [
                "score-demo",
                "--score-input",
                f"qa/fixtures/hero_demo_score/{name}",
                "--output-root",
                "artifacts/runs",
                "--run-id",
                f"test-{Path(name).stem}",
            ]
        )
    result = json.loads(stream.getvalue())
    assert exit_code == 0
    return result


def _write_db(root: Path) -> Path:
    from driverx.scenarios.studio_db import new_studio_db, write_studio_db

    db_path = root / "scenario_studio_db.json"
    write_studio_db(db_path, new_studio_db("test-demo"))
    return db_path


def _write_run(root: Path) -> Path:
    tracks_path = root / "entity_tracks.json"
    tracks_path.write_text(json.dumps(_tracks()), encoding="utf-8")
    run_path = root / "run_manifest.json"
    run_path.write_text(
        json.dumps(
            {
                "run_id": "run",
                "scenario_id": "scenario-1",
                "candidate_id": "candidate-1",
                "artifacts": {"tracks_path": str(tracks_path)},
                "claim_boundaries": ["sampled_open_loop_reasoning=true", "real_time_vla_control=false"],
            }
        ),
        encoding="utf-8",
    )
    return run_path


def _write_evaluation(root: Path) -> Path:
    path = root / "policy_evaluation.json"
    path.write_text(
        json.dumps(
            {
                "scenario_id": "scenario-1",
                "cot_summary": "Slow for the filtering actor and keep escape space.",
                "memory_ids": ["tag:motorcycle_filtering", "tag:roadwork"],
                "claim_boundaries": ["sampled_open_loop_reasoning=true", "real_time_vla_control=false"],
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_tiny_video(root: Path) -> Path:
    video_path = root / "input.mp4"
    proc = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=320x180:rate=6",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stderr)
    return video_path


def _tracks() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for tick in range(6):
        out.append(
            {
                "actor_ref": "ego",
                "actor_id": 1,
                "type_id": "vehicle.ego",
                "tick": tick,
                "t_s": tick * 0.2,
                "location": {"x": tick * 1.0, "y": 0.0, "z": 0.0},
                "rotation": {"yaw": 0.0},
                "velocity": {"x": 5.0, "y": 0.0, "z": 0.0},
            }
        )
        out.append(
            {
                "actor_ref": "generated_asset_motorcycle_filtering",
                "actor_id": 2,
                "type_id": "vehicle.kawasaki.ninja",
                "tick": tick,
                "t_s": tick * 0.2,
                "location": {"x": tick * 1.0 + 4.0, "y": 0.5, "z": 0.0},
                "rotation": {"yaw": 0.0},
                "velocity": {"x": 2.0, "y": 0.0, "z": 0.0},
            }
        )
    return out


if __name__ == "__main__":
    unittest.main()
