import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.policies import (
    classify_alpamayo_probe_artifacts,
    expected_alpamayo_schema,
    write_alpamayo_probe_report,
)


class AlpamayoProbeTest(unittest.TestCase):
    def test_schema_names_camera_inputs_and_waypoint_output(self) -> None:
        schema = expected_alpamayo_schema("example/alpamayo")
        input_names = {item["name"] for item in schema["inputs"]}
        output_names = {item["name"] for item in schema["outputs"]}

        self.assertEqual(schema["status"], "unverified_adapter_stub")
        self.assertIn("camera_views", input_names)
        self.assertIn("ego_state", input_names)
        self.assertIn("trajectory", output_names)
        self.assertIn("20 x 2", json.dumps(schema))

    def test_classifier_redacts_auth_token_and_marks_auth_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "probe.log").write_text(
                "401 Unauthorized HF_TOKEN=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\n",
                encoding="utf-8",
            )

            summary = classify_alpamayo_probe_artifacts(root)

        self.assertEqual(summary["status"], "auth_blocked")
        self.assertTrue(summary["blocked"])
        self.assertNotIn("hf_Drh", summary["redacted_excerpt"])
        self.assertIn("[REDACTED]", summary["redacted_excerpt"])

    def test_classifier_detects_oom_and_memory_artifact(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "alpamayo_probe.json").write_text(
                json.dumps({"model_load_state": "failed", "error": "CUDA out of memory"}),
                encoding="utf-8",
            )
            (root / "memory_usage.json").write_text(
                json.dumps({"torch": {"vram_peak_mb": 91234}}),
                encoding="utf-8",
            )

            summary = classify_alpamayo_probe_artifacts(root)

        self.assertEqual(summary["status"], "oom")
        self.assertEqual(summary["vram_peak_mb"], 91234.0)
        self.assertIn("GPU memory", summary["blockers"][0])

    def test_classifier_detects_successful_shape_observation(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "alpamayo_probe.json").write_text(
                json.dumps(
                    {
                        "model_load_state": "loaded",
                        "latency_ms": 321.5,
                        "trajectory_shape": [20, 2],
                    }
                ),
                encoding="utf-8",
            )

            summary = classify_alpamayo_probe_artifacts(root)

        self.assertEqual(summary["status"], "shape_observed")
        self.assertFalse(summary["blocked"])
        self.assertEqual(summary["latency_ms"], 321.5)
        self.assertEqual(summary["observed_shape"], {"trajectory_shape": [20, 2]})

    def test_report_writer_and_cli_emit_json_and_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            artifact_root = tmp_path / "remote"
            artifact_root.mkdir()
            (artifact_root / "alpamayo_probe.json").write_text(
                json.dumps({"model_load_state": "blocked", "error": "missing checkpoint"}),
                encoding="utf-8",
            )

            summary = write_alpamayo_probe_report(
                tmp_path / "report",
                artifact_root=artifact_root,
            )
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "probe-alpamayo",
                        "--artifact-root",
                        str(artifact_root),
                        "--output-root",
                        str(tmp_path),
                        "--run-id",
                        "cli-report",
                    ]
                )
            cli_summary = json.loads(stream.getvalue())
            report_json_exists = Path(summary["json_path"]).exists()
            report_md_exists = Path(summary["report_path"]).exists()
            cli_json_exists = Path(cli_summary["json_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(report_json_exists)
        self.assertTrue(report_md_exists)
        self.assertTrue(cli_json_exists)
        self.assertEqual(cli_summary["status"], "runtime_blocked")

    def test_remote_probe_script_is_secret_safe_and_download_gated(self) -> None:
        script = Path("scripts/run_remote_alpamayo_probe.sh").read_text(encoding="utf-8")

        self.assertIn("ALPAMAYO_DOWNLOAD", script)
        self.assertIn("ALPAMAYO_LOAD", script)
        self.assertIn("HF_TOKEN", script)
        self.assertIn("GPU_SSH_OPTS", script)
        self.assertIn("DRIVERX_ENV_FILE", script)
        self.assertIn("rsync", script)
        self.assertNotIn("set -x", script)
        self.assertIn(".hf_token", script)


if __name__ == "__main__":
    unittest.main()
