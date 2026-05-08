from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.pipeline.keyframe_analysis import build_keyframe_analysis, select_carla_keyframes
from driverx.scenarios.studio_product_keyframe_runtime import run_studio_analyze_keyframes


class KeyframeAnalysisTests(unittest.TestCase):
    def test_fake_backend_analyzes_same_lineage_preview_and_rgb_frames(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            rgb = root / "rgb"
            rgb.mkdir()
            for index in range(6):
                (rgb / f"frame_{index:06d}.png").write_bytes(b"fake-png")
            preview = root / "preview.png"
            preview.write_bytes(b"fake-preview")
            carla_report = root / "carla_ood_demo.json"
            carla_report.write_text(json.dumps({"frame_count": 6, "duration_s": 0.6}), encoding="utf-8")
            run_manifest = root / "run_manifest.json"
            run_manifest.write_text(
                json.dumps({"artifacts": {"rgb_folder": str(rgb), "carla_ood_demo_json": str(carla_report)}}),
                encoding="utf-8",
            )
            visual_proof = root / "env_carla_proof_manifest.json"
            visual_proof.write_text(
                json.dumps(
                    {
                        "same_lineage": True,
                        "environment_recipe_id": "env-roadside-market-occlusion-s4-0032",
                        "family": "regional_market",
                        "scenario_id": "scenario-1",
                        "preview_image_path": str(preview),
                        "run_manifest_path": str(run_manifest),
                    }
                ),
                encoding="utf-8",
            )

            result = build_keyframe_analysis(
                visual_proof_path=visual_proof,
                db_path=root / "scenario_studio_db.json",
                run_manifest_path=run_manifest,
                backend="fake",
                keyframe_count=4,
                output_root=root,
                run_id="analysis",
            )

            self.assertEqual(result["status"], "passed")
            self.assertTrue(result["same_lineage"])
            self.assertEqual(result["keyframe_count"], 4)
            self.assertEqual(result["reasoned_keyframe_count"], 4)
            self.assertFalse(result["model_evidence"])
            self.assertTrue(Path(result["json_path"]).exists())
            self.assertTrue(all(item["backend"] == "fake" for item in result["analyses"]))
            self.assertIn("sampled_open_loop_reasoning=true", result["claim_boundaries"])

    def test_missing_frames_blocks_cleanly(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_manifest = root / "run_manifest.json"
            run_manifest.write_text(json.dumps({"artifacts": {}}), encoding="utf-8")
            visual_proof = root / "env_carla_proof_manifest.json"
            visual_proof.write_text(
                json.dumps({"same_lineage": False, "run_manifest_path": str(run_manifest)}),
                encoding="utf-8",
            )

            result = run_studio_analyze_keyframes(
                visual_proof_path=visual_proof,
                db_path=root / "scenario_studio_db.json",
                run_manifest_path=run_manifest,
                backend="fake",
                output_root=root,
                run_id="analysis",
            )

            self.assertEqual(result.status, "blocked")
            self.assertEqual(result.summary["keyframe_count"], 0)
            self.assertTrue(result.blockers)
            self.assertIn("render-env --live", result.blockers[0])

    def test_select_keyframes_uses_uniform_sample(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            rgb = root / "rgb"
            rgb.mkdir()
            for index in range(10):
                (rgb / f"frame_{index:06d}.png").write_bytes(b"fake-png")
            run_manifest = root / "run_manifest.json"
            run_manifest.write_text(json.dumps({"artifacts": {"rgb_folder": str(rgb)}}), encoding="utf-8")
            visual_proof = root / "env_carla_proof_manifest.json"
            visual_proof.write_text(json.dumps({"run_manifest_path": str(run_manifest)}), encoding="utf-8")

            frames = select_carla_keyframes(
                visual_proof_path=visual_proof,
                run_manifest_path=run_manifest,
                limit=4,
            )

            self.assertEqual(len(frames), 4)
            self.assertEqual([frame["frame_index"] for frame in frames], [0, 3, 6, 9])


if __name__ == "__main__":
    unittest.main()
