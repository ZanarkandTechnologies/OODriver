import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline import RouteEvidenceInputs, build_route_evidence


def _write_result(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "_checkpoint": {
                    "global_record": {
                        "status": "Completed",
                        "scores_mean": {
                            "score_composed": 71.5,
                            "score_route": 88.0,
                            "score_penalty": 0.81,
                        },
                        "meta": {"duration_game": 12.0, "duration_system": 16.5},
                        "infractions": {"collisions_vehicle": [], "red_light": ["red"]},
                    },
                    "progress": [1, 1],
                    "records": [
                        {
                            "route_id": "1088",
                            "scenario_name": "PedestriansOnRoad",
                            "town_name": "Town10HD",
                            "status": "Completed",
                            "scores": {
                                "score_composed": 71.5,
                                "score_route": 88.0,
                                "score_penalty": 0.81,
                            },
                            "meta": {"duration_game": 12.0, "duration_system": 16.5},
                            "infractions": {
                                "collisions_vehicle": [],
                                "red_light": ["ran red light"],
                            },
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )


def _write_tracks(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "actor_ref": "companion_actor_0",
                    "samples": [
                        {"t_s": 0.0, "x": 1.0, "y": 2.0},
                        {"t_s": 0.1, "x": 1.5, "y": 2.0},
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )


def _write_plan(path: Path, *, result: Path, tracks: Path, video: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "run_command": ["python", "leaderboard_evaluator_local.py"],
                "video_command": ["python", "tools/generate_video.py", "-f", "rgb"],
                "expected_outputs": {
                    "result": str(result),
                    "entity_tracks": str(tracks),
                    "video": str(video),
                },
                "live_blockers": [],
            }
        ),
        encoding="utf-8",
    )


def _write_plan_with_live_blockers(path: Path, *, result: Path, video: Path, rgb_folder: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "run_command": ["python", "leaderboard_evaluator_local.py"],
                "video_command": ["python", "tools/generate_video.py", "-f", "rgb"],
                "expected_outputs": {
                    "result": str(result),
                    "rgb_folder": str(rgb_folder),
                    "video": str(video),
                },
                "live_blockers": [
                    "Fail2Drive video tool not found: /workspace/fail2drive/tools/generate_video.py",
                    f"RGB folder does not exist yet; run the route command with SAVE_PATH before generating video: {rgb_folder}",
                    "Some remaining plan blocker.",
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_route_run(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "status": "blocked",
                "timeout_s": 300.0,
                "duration_s": 300.5,
                "exit_code": None,
                "route_blockers": ["Fail2Drive route command timed out."],
                "error": "Timed out after 300.0 seconds.",
            }
        ),
        encoding="utf-8",
    )


class RouteEvidenceTest(unittest.TestCase):
    def test_build_route_evidence_summarizes_result_tracks_and_video(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = tmp_path / "result.json"
            tracks = tmp_path / "entity_tracks.json"
            video = tmp_path / "route.mp4"
            screenshot = tmp_path / "screen.png"
            log = tmp_path / "route.log"
            plan = tmp_path / "plan.json"
            _write_result(result)
            _write_tracks(tracks)
            video.write_bytes(b"fake mp4")
            screenshot.write_bytes(b"png")
            log.write_text("line 1\nline 2\n", encoding="utf-8")
            _write_plan(plan, result=result, tracks=tracks, video=video)

            summary = build_route_evidence(
                tmp_path / "run",
                RouteEvidenceInputs(
                    plan_path=plan,
                    screenshot_paths=(screenshot,),
                    log_paths=(log,),
                    video_duration_s=3.5,
                ),
            )
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertEqual(summary["status"], "ready")
        self.assertEqual(summary["metrics"]["driving_score"], 71.5)
        self.assertEqual(summary["metrics"]["route_completion"], 88.0)
        self.assertEqual(summary["metrics"]["track_count"], 1)
        self.assertEqual(summary["metrics"]["actor_refs"], ["companion_actor_0"])
        self.assertEqual(summary["video"]["duration_s"], 3.5)
        self.assertEqual(summary["blockers"], [])
        self.assertIn("Route Evidence", report)

    def test_build_route_evidence_surfaces_missing_expected_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan = tmp_path / "plan.json"
            _write_plan(
                plan,
                result=tmp_path / "missing_result.json",
                tracks=tmp_path / "missing_tracks.json",
                video=tmp_path / "missing_video.mp4",
            )

            summary = build_route_evidence(tmp_path / "run", RouteEvidenceInputs(plan_path=plan))

        blockers = "\n".join(summary["blockers"])
        self.assertEqual(summary["status"], "blocked")
        self.assertIn("Missing route result", blockers)
        self.assertIn("Missing entity tracks", blockers)
        self.assertIn("Missing route video", blockers)

    def test_build_route_evidence_suppresses_stale_plan_blockers_when_video_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = tmp_path / "result.json"
            video = tmp_path / "route.mp4"
            rgb = tmp_path / "rgb"
            plan = tmp_path / "plan.json"
            _write_result(result)
            video.write_bytes(b"fake mp4")
            rgb.mkdir()
            (rgb / "00000.png").write_bytes(b"fake image")
            _write_plan_with_live_blockers(plan, result=result, video=video, rgb_folder=rgb)

            summary = build_route_evidence(
                tmp_path / "run",
                RouteEvidenceInputs(
                    plan_path=plan,
                    video_duration_s=3.5,
                ),
            )

        blockers = "\n".join(summary["blockers"])
        self.assertNotIn("video tool not found", blockers)
        self.assertNotIn("RGB folder does not exist yet", blockers)
        self.assertIn("Some remaining plan blocker", blockers)

    def test_build_route_evidence_surfaces_route_run_timeout(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = tmp_path / "result.json"
            video = tmp_path / "route.mp4"
            route_run = tmp_path / "route_run.json"
            plan = tmp_path / "plan.json"
            _write_result(result)
            video.write_bytes(b"fake mp4")
            _write_route_run(route_run)
            _write_plan(plan, result=result, tracks=tmp_path / "missing_tracks.json", video=video)

            summary = build_route_evidence(
                tmp_path / "run",
                RouteEvidenceInputs(plan_path=plan, route_run_path=route_run),
            )

        blockers = "\n".join(summary["blockers"])
        self.assertEqual(summary["status"], "partial")
        self.assertIn("Fail2Drive route command timed out.", blockers)
        self.assertIn("Timed out after 300.0 seconds.", blockers)
        self.assertEqual(summary["route_run"]["summary"]["timeout_s"], 300.0)

    def test_build_route_evidence_cli_writes_json_and_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = tmp_path / "result.json"
            tracks = tmp_path / "entity_tracks.json"
            video = tmp_path / "route.mp4"
            plan = tmp_path / "plan.json"
            _write_result(result)
            _write_tracks(tracks)
            video.write_bytes(b"fake mp4")
            _write_plan(plan, result=result, tracks=tracks, video=video)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-route-evidence",
                        "--plan",
                        str(plan),
                        "--route-run",
                        str(tmp_path / "missing_route_run.json"),
                        "--video-duration-s",
                        "4.25",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "route-evidence",
                    ]
                )
            summary = json.loads(stream.getvalue())
            json_exists = Path(summary["json_path"]).exists()
            report_exists = Path(summary["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["status"], "ready")
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)
        self.assertEqual(summary["video"]["duration_s"], 4.25)


if __name__ == "__main__":
    unittest.main()
