import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.policies import (
    classify_alpamayo_shape_probe_artifacts,
    write_alpamayo_shape_probe_report,
)


class AlpamayoShapeProbeTest(unittest.TestCase):
    def test_classifier_detects_shape_observation(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "alpamayo_shape_probe.json").write_text(
                json.dumps(
                    {
                        "inference_state": "shape_observed",
                        "input_shapes": {
                            "image_frames": [4, 4, 3, 224, 224],
                            "ego_history_xyz": [1, 1, 16, 3],
                        },
                        "output_shapes": {
                            "pred_xyz": [1, 1, 1, 64, 3],
                            "pred_rot": [1, 1, 1, 64, 3, 3],
                            "extra.cot": [1, 1, 1],
                        },
                        "latency_ms": 1234.5,
                    }
                ),
                encoding="utf-8",
            )
            (root / "memory_usage.json").write_text(
                json.dumps({"torch": {"vram_peak_mb": 24576}}),
                encoding="utf-8",
            )

            summary = classify_alpamayo_shape_probe_artifacts(root)

        self.assertEqual(summary["status"], "shape_observed")
        self.assertFalse(summary["blocked"])
        self.assertEqual(summary["output_shapes"]["pred_xyz"], [1, 1, 1, 64, 3])
        self.assertEqual(summary["vram_peak_mb"], 24576.0)

    def test_classifier_keeps_success_when_dataset_fallback_logged_403(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "shape_probe.log").write_text(
                "403 Forbidden while loading dataset; synthetic fallback used\n",
                encoding="utf-8",
            )
            (root / "alpamayo_shape_probe.json").write_text(
                json.dumps(
                    {
                        "inference_state": "shape_observed",
                        "shape_source_used": "synthetic_after_dataset_blocker",
                        "output_shapes": {
                            "pred_xyz": [1, 1, 1, 64, 3],
                            "pred_rot": [1, 1, 1, 64, 3, 3],
                        },
                    }
                ),
                encoding="utf-8",
            )

            summary = classify_alpamayo_shape_probe_artifacts(root)

        self.assertEqual(summary["status"], "shape_observed")
        self.assertFalse(summary["blocked"])

    def test_classifier_marks_dataset_gate_blocker_and_redacts_token(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "shape_probe.log").write_text(
                "403 Forbidden HF_TOKEN=redaction_fixture_token while loading dataset\n",
                encoding="utf-8",
            )

            summary = classify_alpamayo_shape_probe_artifacts(root)

        self.assertEqual(summary["status"], "dataset_gate_blocked")
        self.assertTrue(summary["blocked"])
        self.assertNotIn("redaction_fixture_token", summary["redacted_excerpt"])
        self.assertIn("[REDACTED]", summary["redacted_excerpt"])

    def test_classifier_detects_completed_but_missing_shapes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "alpamayo_shape_probe.json").write_text(
                json.dumps(
                    {
                        "inference_state": "shape_observed",
                        "output_shapes": {"pred_xyz": [1, 1, 1, 64, 3]},
                    }
                ),
                encoding="utf-8",
            )

            summary = classify_alpamayo_shape_probe_artifacts(root)

        self.assertEqual(summary["status"], "shape_blocked")
        self.assertIn("required output shapes", summary["blockers"][0])

    def test_report_writer_and_cli_emit_summary(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            artifact_root = tmp_path / "remote"
            artifact_root.mkdir()
            (artifact_root / "alpamayo_shape_probe.json").write_text(
                json.dumps(
                    {
                        "inference_state": "shape_observed",
                        "input_shapes": {"camera_indices": [4]},
                        "output_shapes": {
                            "pred_xyz": [1, 1, 1, 64, 3],
                            "pred_rot": [1, 1, 1, 64, 3, 3],
                        },
                    }
                ),
                encoding="utf-8",
            )

            summary = write_alpamayo_shape_probe_report(
                tmp_path / "report",
                artifact_root=artifact_root,
            )
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "probe-alpamayo-shapes",
                        "--artifact-root",
                        str(artifact_root),
                        "--output-root",
                        str(tmp_path),
                        "--run-id",
                        "cli-report",
                    ]
                )
            cli_summary = json.loads(stream.getvalue())
            summary_json_exists = Path(summary["json_path"]).exists()
            summary_report_exists = Path(summary["report_path"]).exists()
            cli_json_exists = Path(cli_summary["json_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(summary_json_exists)
        self.assertTrue(summary_report_exists)
        self.assertTrue(cli_json_exists)
        self.assertEqual(cli_summary["status"], "shape_observed")

    def test_remote_shape_probe_script_is_secret_safe_and_eager(self) -> None:
        script = Path("scripts/run_remote_alpamayo_shape_probe.sh").read_text(encoding="utf-8")

        self.assertIn("ALPAMAYO_ATTN_IMPLEMENTATION", script)
        self.assertIn("ALPAMAYO_SHAPE_SOURCE", script)
        self.assertIn("synthetic_after_dataset_blocker", script)
        self.assertIn("sample_trajectories_from_data_with_vlm_rollout", script)
        self.assertIn("load_physical_aiavdataset", script)
        self.assertIn(".hf_token", script)
        self.assertNotIn("set -x", script)


if __name__ == "__main__":
    unittest.main()
