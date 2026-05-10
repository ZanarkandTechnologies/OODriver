from __future__ import annotations

import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.evaluation.closed_loop_video_score import score_closed_loop_video
from driverx.pipeline.closed_loop_video import ClosedLoopVideoInputs, build_closed_loop_video
from driverx.pipeline.closed_loop_video import _reasoning_line
from driverx.scenarios.studio_product_helpers import cot_from_prediction
from driverx.simulators.carla_closed_loop_runner import PausedClosedLoopConfig, run_paused_closed_loop


class ClosedLoopVideoTests(unittest.TestCase):
    def test_video_score_blocks_fake_only_trace(self) -> None:
        if shutil.which("ffmpeg") is None:
            self.skipTest("ffmpeg is required for MP4 rendering")
        try:
            import PIL  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Pillow is required for overlay rendering")
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "fake"
            trace = run_paused_closed_loop(PausedClosedLoopConfig(run_id="fake", steps=2), run_dir)
            video = build_closed_loop_video(
                ClosedLoopVideoInputs(
                    trace_path=Path(str(trace["json_path"])),
                    output_root=Path(tmp),
                    run_id="video",
                    duration_s=2.0,
                    fps=6,
                )
            )

            report = score_closed_loop_video(
                trace_path=Path(str(trace["json_path"])),
                manifest_path=Path(video.manifest_path),
                video_path=Path(str(video.video_path)),
            )

            self.assertEqual(video.status, "passed")
            self.assertEqual(report.status, "blocked")
            self.assertIn("live CARLA provenance is required for hero promotion", report.blockers)

    def test_video_score_passes_synthetic_live_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "hero.mp4"
            video.write_bytes(b"not a real mp4 but manifest provides contract metrics")
            trace_path = root / "closed_loop_trace.json"
            manifest_path = root / "closed_loop_video_manifest.json"
            steps = []
            for index in range(2):
                (root / f"infer_{index}.json").write_text(
                    json.dumps({"mode": "remote-kasm", "status": "cached", "prediction_json_path": str(root / f"pred_{index}.json")}),
                    encoding="utf-8",
                )
                steps.append(
                    {
                        "step_index": index,
                        "input_frame_id": 10 + index * 4,
                        "post_action_frame_id": 14 + index * 4,
                        "applied_control_count": 4,
                        "pre_rgb_frame_paths": [str(root / f"pre_{index}.png")],
                        "post_rgb_frame_paths": [str(root / f"post_{index}.png")],
                        "visual_rgb_frame_paths": [str(root / f"visual_{index}_{frame}.png") for frame in range(4)],
                        "action_rgb_frame_paths": [str(root / f"action_{index}_{frame}.png") for frame in range(2)],
                        "inference_result_path": str(root / f"infer_{index}.json"),
                        "planned_vs_actual_error_m": 0.5,
                        "ego_vehicle_visible": True,
                        "visual_camera_role": "third_person_chase",
                    }
                )
            trace_path.write_text(
                json.dumps(
                    {
                        "run_id": "live",
                        "scenario_id": "case",
                        "mode": "paused_receding_horizon",
                        "backend": "carla-live",
                        "policy": "alpamayo-remote",
                        "steps": steps,
                        "control_applied_count": 8,
                        "observed_after_action_count": 2,
                        "source_frame_count": 8,
                        "action_rgb_frame_count": 4,
                        "ego_vehicle_visible": True,
                        "visual_camera_role": "third_person_chase",
                        "visible_ood_object": True,
                        "entity_tracks_path": str(root / "entity_tracks.json"),
                        "claim_boundaries": [
                            "closed_loop_vla_control=paused_receding_horizon",
                            "real_time_vla_control=false",
                            "time_warped_offline_demo=true",
                            "live_carla_provenance=true",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            manifest_path.write_text(
                json.dumps(
                    {
                        "status": "passed",
                        "output_video": str(video),
                        "sample_frame_paths": [str(root / "sample.png")],
                        "frame_count": 720,
                        "duration_s": 4.0,
                        "source_frame_count": 8,
                        "seconds_per_source_frame": 0.5,
                        "action_rgb_frame_count": 4,
                        "ego_vehicle_visible": True,
                        "visual_camera_role": "third_person_chase",
                        "backend": "carla-live",
                        "live_carla_provenance": True,
                        "recurrence_visible": True,
                        "claim_boundaries": ["real_time_vla_control=false", "time_warped_offline_demo=true"],
                    }
                ),
                encoding="utf-8",
            )

            report = score_closed_loop_video(
                trace_path=trace_path,
                manifest_path=manifest_path,
                video_path=video,
            )

            self.assertEqual(report.status, "passed")
            self.assertGreaterEqual(report.closed_loop_video_score, report.threshold)

    def test_reasoning_line_falls_back_to_local_prediction_sibling(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            inference = root / "alpamayo_inference_result.json"
            prediction = root / "alpamayo_live_prediction.json"
            inference.write_text(
                json.dumps(
                    {
                        "mode": "remote-kasm",
                        "status": "passed",
                        "prediction_json_path": "/workspace/remote/alpamayo_live_prediction.json",
                    }
                ),
                encoding="utf-8",
            )
            prediction.write_text(
                json.dumps(
                    {
                        "cached_prior_prediction": True,
                        "reasoning_snippet": "Keep distance to the lead vehicle.",
                    }
                ),
                encoding="utf-8",
            )

            line = _reasoning_line({"inference_result_path": str(inference)})

        self.assertIn("cached Alpamayo", line)
        self.assertIn("Keep distance", line)

    def test_cot_from_prediction_accepts_cached_alpamayo_summary_fields(self) -> None:
        self.assertEqual(
            cot_from_prediction({"cot_summary": "Yield before entering the blocked lane."}),
            "Yield before entering the blocked lane.",
        )
        self.assertEqual(
            cot_from_prediction({"reasoning_snippet": "Keep distance to the lead vehicle."}),
            "Keep distance to the lead vehicle.",
        )


if __name__ == "__main__":
    unittest.main()
