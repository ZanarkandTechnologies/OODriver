import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.policies import run_alpamayo_offline_fixture, sample_memory_entries


def _write_prediction(path: Path) -> None:
    points = [
        [round((index + 1) / 10.0, 4), 0.0, 0.0]
        for index in range(64)
    ]
    path.write_text(json.dumps({"pred_xyz": points}, indent=2), encoding="utf-8")


class AlpamayoOfflineTest(unittest.TestCase):
    def test_offline_runner_writes_input_trajectory_and_decision(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pred_path = tmp_path / "pred.json"
            _write_prediction(pred_path)

            summary = run_alpamayo_offline_fixture(
                fixture="construction_merge",
                prediction_json=pred_path,
                output_root=tmp_path,
                run_id="offline",
                nav_text="Turn left in 11m",
                memory_entries=sample_memory_entries(),
            )
            decision = json.loads(Path(summary["decision_path"]).read_text(encoding="utf-8"))
            input_exists = Path(summary["input_package_path"]).exists()
            trajectory_exists = Path(summary["trajectory_path"]).exists()

        self.assertEqual(summary["policy_id"], "alpamayo-offline")
        self.assertEqual(summary["target_points"], 20)
        self.assertEqual(summary["memory_ids"], ["mem-sample-motorcycle-filtering"])
        self.assertTrue(input_exists)
        self.assertTrue(trajectory_exists)
        self.assertEqual(decision["action"]["mode"], "trajectory_chunk")
        self.assertTrue(decision["action"]["control"]["offline_replay"])
        self.assertIn("Turn left", decision["reason_summary"])

    def test_cli_runs_offline_rehearsal(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pred_path = tmp_path / "pred.json"
            _write_prediction(pred_path)

            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "run-alpamayo-offline",
                        "--prediction-json",
                        str(pred_path),
                        "--with-memory",
                        "--output-root",
                        str(tmp_path),
                        "--run-id",
                        "cli-offline",
                    ]
                )
            summary = json.loads(stream.getvalue())
            report_exists = Path(summary["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(report_exists)
        self.assertEqual(summary["adapter_kind"], "alpamayo_saved_prediction")


if __name__ == "__main__":
    unittest.main()
