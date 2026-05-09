from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from oodrive.cli import main as oodrive_main
from driverx.evaluation.visual_fidelity_score import score_visual_fidelity


class VisualFidelityScoreTests(unittest.TestCase):
    def test_strong_media_manifest_passes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame_paths = []
            for index in range(5):
                path = root / f"frame_{index}.png"
                path.write_bytes(b"fake")
                frame_paths.append(str(path))
            video_path = root / "demo.mp4"
            video_path.write_bytes(b"fake")
            osc2_path = root / "scenario.osc"
            osc2_path.write_text("scenario static_blocker:\n  do:\n    wait elapsed(1s)\n", encoding="utf-8")
            sidecar_path = root / "scenario_sidecar.json"
            sidecar_path.write_text("{}", encoding="utf-8")
            commands_path = root / "commands.sh"
            commands_path.write_text("oodrive validate-osc2\n", encoding="utf-8")
            manifest_path = root / "media_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "prompt": "Wet urban lane with static blocker and moving hazard.",
                        "map": "Town03_Opt",
                        "weather": {"rain": 0.7, "wetness": 0.9},
                        "video_path": str(video_path),
                        "frames": frame_paths,
                        "duration_s": 45,
                        "frame_count": 180,
                        "expected_visual_tags": ["wet_road", "static_obstacle", "moving_hazard", "urban_lane"],
                        "visible_visual_tags": ["wet_road", "static_obstacle", "moving_hazard", "urban_lane", "ego_vehicle"],
                        "static_obstacle_count": 2,
                        "moving_actor_count": 1,
                        "background_actor_count": 3,
                        "environment_variation_count": 2,
                        "behavior_events": ["slow_down", "hold_lane", "stop_before_hazard", "resume_when_clear"],
                        "risk_event_count": 4,
                        "lane_alignment_pass": True,
                        "dynamic_actor_motion_proved": True,
                        "ego_action_trace_present": True,
                        "reasoning_snippet_count": 3,
                        "rag_callout_count": 3,
                        "frame_time_overlay_present": True,
                        "hud_congestion_ratio": 0.24,
                        "osc2_path": str(osc2_path),
                        "sidecar_path": str(sidecar_path),
                        "commands_path": str(commands_path),
                        "claim_boundaries": [
                            "agent_authored_scenario=true",
                            "closed_loop_vla_control=false",
                            "arbitrary_mesh_spawn=false_until_live_spawn_proof_exists",
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = score_visual_fidelity(manifest_path)

            self.assertEqual(report.status, "passed")
            self.assertGreaterEqual(report.visual_fidelity_score, 90.0)
            self.assertFalse(report.blockers)

    def test_missing_motion_blocks_moving_hazard_claim(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = root / "frame.png"
            frame.write_bytes(b"fake")
            manifest_path = root / "media_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "prompt": "A moving object is about to collide with the ego car.",
                        "preview_image_path": str(frame),
                        "expected_visual_tags": ["moving_hazard"],
                        "visible_visual_tags": ["moving_hazard"],
                        "moving_actor_count": 1,
                        "dynamic_actor_motion_proved": False,
                    }
                ),
                encoding="utf-8",
            )

            report = score_visual_fidelity(manifest_path)

            self.assertEqual(report.status, "blocked")
            self.assertIn("moving hazard requested but no dynamic actor motion proof exists", report.blockers)

    def test_lane_departure_duplicate_and_false_custom_claims_block(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = root / "frame.png"
            frame.write_bytes(b"fake")
            manifest_path = root / "media_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "prompt": "A generated crane blocks a custom construction map.",
                        "preview_image_path": str(frame),
                        "expected_visual_tags": ["static_obstacle"],
                        "visible_visual_tags": ["static_obstacle"],
                        "lane_departure_detected": True,
                        "duplicate_gallery_match": True,
                        "custom_asset_requested": True,
                        "custom_map_requested": True,
                        "claim_boundaries": ["arbitrary_mesh_spawn=true", "custom_unreal_map_import=true"],
                    }
                ),
                encoding="utf-8",
            )

            report = score_visual_fidelity(manifest_path)

            self.assertEqual(report.status, "blocked")
            self.assertIn("lane departure detected in visual/behavior proof", report.blockers)
            self.assertIn("scene is visually duplicate of an existing gallery artifact", report.blockers)
            self.assertIn("custom asset requested but no custom CARLA spawn proof exists", report.blockers)
            self.assertIn("custom map requested but no CARLA map load proof exists", report.blockers)
            self.assertIn("false custom-asset claim: arbitrary mesh spawn is not proved", report.blockers)
            self.assertIn("false custom-map claim: custom Unreal map import is not proved", report.blockers)

    def test_cli_metric_only_emits_score(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = root / "frame.png"
            frame.write_bytes(b"fake")
            manifest_path = root / "media_manifest.json"
            manifest_path.write_text(
                json.dumps({"prompt": "simple scene", "preview_image_path": str(frame), "visible_visual_tags": ["ego_vehicle"]}),
                encoding="utf-8",
            )
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = oodrive_main(
                    [
                        "score-visual-fidelity",
                        "--media-manifest",
                        str(manifest_path),
                        "--output-root",
                        str(root),
                        "--run-id",
                        "score",
                        "--metric-only",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("METRIC visual_fidelity_score=", stream.getvalue())
            self.assertTrue((root / "score" / "visual_fidelity_score.json").exists())


if __name__ == "__main__":
    unittest.main()
