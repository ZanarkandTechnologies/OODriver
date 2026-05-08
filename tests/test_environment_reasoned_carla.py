from __future__ import annotations

import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from driverx.evaluation.environment_reasoned_carla_score import score_environment_reasoned_carla
from driverx.pipeline.environment_reasoned_carla_video import build_environment_reasoned_carla_video
from driverx.scenarios.studio_product_env_video_runtime import run_studio_score_env_proof


class EnvironmentReasonedCarlaTests(unittest.TestCase):
    def test_story_pack_renders_mp4_from_preview_and_keyframes(self) -> None:
        if shutil.which("ffmpeg") is None:
            self.skipTest("ffmpeg unavailable")
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow unavailable")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            preview = root / "preview.png"
            frame = root / "frame_000005.png"
            Image.new("RGB", (640, 360), (20, 60, 90)).save(preview)
            Image.new("RGB", (640, 360), (90, 60, 20)).save(frame)
            env = root / "environment_suite_summary.json"
            env.write_text(
                json.dumps({"families": ["regional_market"], "recipes": [{"recipe_id": "env-1"}], "asset_requests": []}),
                encoding="utf-8",
            )
            visual = root / "env_carla_proof_manifest.json"
            visual.write_text(
                json.dumps(
                    {
                        "status": "passed",
                        "same_lineage": True,
                        "environment_recipe_id": "env-1",
                        "scenario_id": "scenario-1",
                        "preview_image_path": str(preview),
                        "claim_boundaries": [],
                    }
                ),
                encoding="utf-8",
            )
            keyframes = root / "keyframe_analysis.json"
            keyframes.write_text(
                json.dumps(
                    {
                        "same_lineage": True,
                        "analyses": [
                            {
                                "frame_index": 5,
                                "source_time_s": 0.5,
                                "image_path": str(frame),
                                "vla_reasoning": "Slow for the roadside occlusion and keep clearance.",
                            }
                        ],
                        "claim_boundaries": [],
                    }
                ),
                encoding="utf-8",
            )

            output = build_environment_reasoned_carla_video(
                environment_summary_path=env,
                visual_proof_path=visual,
                keyframe_analysis_path=keyframes,
                output_root=root,
                run_id="video",
                target_duration_s=12.0,
            )

            self.assertEqual(output["status"], "passed")
            self.assertTrue(Path(str(output["video_path"])).exists())
            self.assertEqual(output["duration_s"], 12.0)
            self.assertEqual(output["video_render"]["frame_count"], 48)
            self.assertEqual(output["video_render"]["status"], "passed")

    def test_story_pack_blocks_without_preview_or_keyframes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = root / "environment_suite_summary.json"
            env.write_text(
                json.dumps({"families": ["regional_market"], "recipes": [{"recipe_id": "env-1"}], "asset_requests": []}),
                encoding="utf-8",
            )
            visual = root / "env_carla_proof_manifest.json"
            visual.write_text(json.dumps({"same_lineage": False, "claim_boundaries": []}), encoding="utf-8")
            keyframes = root / "keyframe_analysis.json"
            keyframes.write_text(json.dumps({"same_lineage": False, "analyses": [], "claim_boundaries": []}), encoding="utf-8")

            output = build_environment_reasoned_carla_video(
                environment_summary_path=env,
                visual_proof_path=visual,
                keyframe_analysis_path=keyframes,
                output_root=root,
                run_id="video",
            )

            self.assertEqual(output["status"], "blocked")
            self.assertIsNone(output["video_path"])
            self.assertTrue(Path(output["overlay_report_path"]).exists())
            self.assertTrue(output["blockers"])
            self.assertIn("time_warped_offline_demo=true", output["claim_boundaries"])

    def test_score_rewards_target_same_lineage_fixture(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            preview = root / "preview.png"
            preview.write_bytes(b"fake")
            video = root / "demo.mp4"
            video.write_bytes(b"fake")
            commands = root / "commands.sh"
            commands.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            report = root / "report.md"
            report.write_text("report", encoding="utf-8")
            env = root / "environment_suite_summary.json"
            env.write_text(
                json.dumps(
                    {
                        "families": ["a", "b", "c", "d"],
                        "recipes": [{"recipe_id": str(index)} for index in range(6)],
                        "asset_requests": [{"asset_id": str(index)} for index in range(6)],
                        "summary_path": str(env),
                    }
                ),
                encoding="utf-8",
            )
            visual = root / "env_carla_proof_manifest.json"
            visual.write_text(
                json.dumps(
                    {
                        "status": "passed",
                        "same_lineage": True,
                        "preview_image_path": str(preview),
                        "run_manifest_path": str(root / "run_manifest.json"),
                        "placement_plan_path": str(root / "placement.json"),
                        "db_path": str(root / "db.json"),
                        "commands_path": str(commands),
                    }
                ),
                encoding="utf-8",
            )
            for path in ("run_manifest.json", "placement.json", "db.json"):
                (root / path).write_text("{}", encoding="utf-8")
            keyframes = root / "keyframe_analysis.json"
            keyframes.write_text(
                json.dumps(
                    {
                        "same_lineage": True,
                        "reasoned_keyframe_count": 5,
                        "report_path": str(report),
                        "commands_path": str(commands),
                        "claim_boundaries": ["sampled_open_loop_reasoning=true"],
                        "analyses": [
                            {
                                "image_path": str(preview),
                                "vla_reasoning": "reason",
                                "source_time_s": float(index),
                                "backend": "alpamayo-local",
                                "status": "passed",
                            }
                            for index in range(5)
                        ],
                    }
                ),
                encoding="utf-8",
            )
            overlay = root / "environment_reasoned_carla_demo.json"
            overlay.write_text(
                json.dumps(
                    {
                        "video_path": str(video),
                        "duration_s": 120.0,
                        "commands_path": str(commands),
                        "claim_boundaries": ["time_warped_offline_demo=true"],
                        "timeline_segments": [
                            {"kind": "cli_generation"},
                            {"kind": "carla_preview"},
                            {"kind": "keyframe_reasoning"},
                            {"kind": "claim_boundary"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            score = score_environment_reasoned_carla(
                environment_summary_path=env,
                visual_proof_path=visual,
                keyframe_analysis_path=keyframes,
                overlay_report_path=overlay,
                video_path=video,
            )

            self.assertEqual(score.status, "passed")
            self.assertGreaterEqual(score.environment_to_reasoned_carla_score, 90.0)
            self.assertFalse(score.blockers)

    def test_score_env_proof_returns_blocked_without_video(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = root / "environment_suite_summary.json"
            env.write_text(json.dumps({"families": [], "recipes": [], "asset_requests": []}), encoding="utf-8")
            visual = root / "env_carla_proof_manifest.json"
            visual.write_text(json.dumps({"claim_boundaries": []}), encoding="utf-8")
            keyframes = root / "keyframe_analysis.json"
            keyframes.write_text(json.dumps({"claim_boundaries": [], "analyses": []}), encoding="utf-8")

            result = run_studio_score_env_proof(
                environment_summary_path=env,
                visual_proof_path=visual,
                keyframe_analysis_path=keyframes,
                output_root=root,
                run_id="score",
            )

            self.assertEqual(result.status, "blocked")
            self.assertTrue(result.blockers)


if __name__ == "__main__":
    unittest.main()
