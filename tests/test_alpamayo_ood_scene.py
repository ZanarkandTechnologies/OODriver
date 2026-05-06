import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.pipeline import AlpamayoOodSceneInputs, build_alpamayo_ood_scene_report


def _write_package(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "frame_name": "driverx::scenario-001",
                "map_name": "Town13",
                "camera_windows": [],
            }
        ),
        encoding="utf-8",
    )


def _write_decision(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "policy_decision": {
                    "policy_id": "alpamayo-live",
                    "adapter_kind": "alpamayo_open_loop",
                    "latency_ms": 101234.5,
                    "reason_summary": "The vehicle should slow for the filtering motorcycle before proceeding.",
                    "intent": {"scene_type": "generated-demo"},
                    "action": {
                        "trajectory": {
                            "points_xy": [[0.0, 0.0], [1.0, 0.2], [2.0, 0.3]]
                        },
                        "control": {"vram_peak_mb": 24881.0},
                    },
                },
                "prediction_summary": {
                    "model_id": "nvidia/Alpamayo-1.5-10B",
                    "latency_ms": 101234.5,
                    "vram_peak_mb": 24881.0,
                },
            }
        ),
        encoding="utf-8",
    )


def _write_video(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "status": "passed",
                "scenario_id": "scenario-001",
                "video_path": "scenario-001.mp4",
                "duration_s": 20.0,
                "worst_risk": {"distance_m": 1.2},
            }
        ),
        encoding="utf-8",
    )


class AlpamayoOodSceneTest(unittest.TestCase):
    def test_build_report_links_reasoning_trajectory_and_video(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package.json"
            decision = root / "decision.json"
            video = root / "video.json"
            _write_package(package)
            _write_decision(decision)
            _write_video(video)

            result = build_alpamayo_ood_scene_report(
                root / "run",
                AlpamayoOodSceneInputs(
                    package_path=package,
                    policy_decision_path=decision,
                    video_evidence_path=video,
                ),
            )

            self.assertEqual(result["scenario_id"], "scenario-001")
            self.assertTrue(result["open_loop_policy_evaluation"])
            self.assertFalse(result["closed_loop_control"])
            self.assertEqual(result["latency_ms"], 101234.5)
            self.assertEqual(result["vram_peak_mb"], 24881.0)
            self.assertIn("filtering motorcycle", result["cot_snippet"])
            self.assertEqual(result["trajectory_summary"]["point_count"], 3)
            self.assertEqual(result["video"]["duration_s"], 20.0)
            self.assertEqual(result["package_scenario_id"], "driverx::scenario-001")
            self.assertEqual(result["video_scenario_id"], "scenario-001")
            self.assertTrue(result["linkage_warnings"])
            self.assertTrue(Path(result["json_path"]).exists())
            self.assertTrue(Path(result["report_path"]).exists())

    def test_missing_policy_decision_is_actionable_but_reportable(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package.json"
            _write_package(package)

            result = build_alpamayo_ood_scene_report(
                root / "run",
                AlpamayoOodSceneInputs(package_path=package),
            )

            self.assertEqual(result["scenario_id"], "driverx::scenario-001")
            self.assertIn("not supplied", result["setup_blocker"])
            self.assertIsNone(result["trajectory_summary"])

    def test_report_preserves_mismatched_evidence_ids(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package.json"
            package.write_text(
                json.dumps(
                    {
                        "scenario_id": "fixture-001",
                        "frame_name": "fixture-001",
                        "map_name": "Town13",
                    }
                ),
                encoding="utf-8",
            )
            scenario = root / "scenario.json"
            scenario.write_text(
                json.dumps({"recipe_id": "generated-001", "status": "failed"}),
                encoding="utf-8",
            )
            video = root / "video.json"
            video.write_text(
                json.dumps(
                    {
                        "scenario_id": "fixture-video-001",
                        "source_kind": "fixture",
                        "video_path": "fixture.mp4",
                    }
                ),
                encoding="utf-8",
            )

            result = build_alpamayo_ood_scene_report(
                root / "run",
                AlpamayoOodSceneInputs(
                    package_path=package,
                    scenario_report_path=scenario,
                    video_evidence_path=video,
                ),
            )

        self.assertEqual(result["scenario_id"], "fixture-001")
        self.assertEqual(result["scenario_report_id"], "generated-001")
        self.assertEqual(result["video_scenario_id"], "fixture-video-001")
        self.assertEqual(len(result["linkage_warnings"]), 3)


if __name__ == "__main__":
    unittest.main()
