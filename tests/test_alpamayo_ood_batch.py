import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline.alpamayo_ood_batch import (
    AlpamayoOodBatchConfig,
    AlpamayoRemoteConfig,
    plan_remote_alpamayo_case,
    run_alpamayo_ood_batch,
)


class AlpamayoOodBatchTest(unittest.TestCase):
    def test_plan_mode_reuses_existing_comparison_metrics(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)

            result = run_alpamayo_ood_batch(
                AlpamayoOodBatchConfig(
                    output_root=root,
                    run_id="batch",
                    package_paths=(paths["package"],),
                    comparison_paths=(paths["comparison"],),
                    limit=1,
                )
            )
            record = result["records"][0]

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["case_count"], 1)
        self.assertEqual(record["trajectory_final_l2_m"], 2.5)
        self.assertEqual(record["vram_peak_mb"], [100.0, 120.0])
        self.assertEqual(result["mean_vram_peak_mb"], 110.0)
        self.assertEqual(result["max_vram_peak_mb"], 120.0)
        self.assertEqual(result["reasoning_changed_count"], 1)
        self.assertEqual(result["memory_case_count"], 1)
        self.assertEqual(result["open_loop_case_count"], 1)
        self.assertEqual(result["closed_loop_case_count"], 0)
        self.assertEqual(record["latency_delta_ms"], -2.0)
        self.assertEqual(record["safety_flags"], {"open_loop_only": True})
        self.assertEqual(record["remote_command"]["command"][0:2], ["bash", "scripts/run_remote_alpamayo_carla_inference.sh"])
        self.assertEqual(record["status"], "passed")

    def test_missing_campaign_package_is_blocked_precisely(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            campaign = root / "campaign.json"
            campaign.write_text(
                json.dumps({"cases": [{"case_id": "case-1", "scenario_id": "scene-1"}]}),
                encoding="utf-8",
            )

            result = run_alpamayo_ood_batch(
                AlpamayoOodBatchConfig(
                    output_root=root,
                    run_id="batch",
                    campaign_summary_path=campaign,
                    limit=1,
                )
            )

        self.assertEqual(result["status"], "blocked")
        self.assertIn("No Alpamayo package path", result["records"][0]["blockers"][0])

    def test_batch_cli_plan_mode(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "run-alpamayo-ood-batch",
                        "--package",
                        str(paths["package"]),
                        "--comparison",
                        str(paths["comparison"]),
                        "--limit",
                        "1",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "batch",
                    ]
                )
            result = json.loads(stream.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["passed_count"], 1)

    def test_remote_command_is_secret_safe_and_rerunnable(self) -> None:
        with TemporaryDirectory() as tmp:
            package = Path(tmp) / "package.json"
            package.write_text(json.dumps({"scenario_id": "scene-1"}), encoding="utf-8")

            command = plan_remote_alpamayo_case(
                package,
                case_id="case-1",
                run_dir=Path(tmp) / "batch",
                config=AlpamayoOodBatchConfig(
                    remote=AlpamayoRemoteConfig(remote="root@example", ssh_opts="-p 22")
                ),
            ).to_jsonable()

        self.assertIn("scripts/run_remote_alpamayo_carla_inference.sh", command["command"])
        self.assertNotIn("hf_", json.dumps(command))
        self.assertEqual(command["env"]["ALPAMAYO_ATTN_IMPLEMENTATION"], "eager")


def _write_inputs(root: Path) -> dict[str, Path]:
    package = root / "package.json"
    package.write_text(json.dumps({"scenario_id": "scene-1"}), encoding="utf-8")
    comparison = root / "comparison.json"
    comparison.write_text(
        json.dumps(
            {
                "trajectory_delta": {"final_l2_m": 2.5},
                "reasoning_delta": {"changed": True},
                "latency_delta_ms": -2.0,
                "safety_flags": {"open_loop_only": True},
                "open_loop_policy_evaluation": True,
                "closed_loop_control": False,
                "memory_ids": ["mem-1"],
                "records": [
                    {"mode": "alpamayo", "latency_ms": 10.0, "vram_peak_mb": 100.0},
                    {"mode": "alpamayo+memory", "latency_ms": 12.0, "vram_peak_mb": 120.0},
                ],
            }
        ),
        encoding="utf-8",
    )
    return {"package": package, "comparison": comparison}


if __name__ == "__main__":
    unittest.main()
