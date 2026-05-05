import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline import EndToEndOodDemoConfig, run_end_to_end_ood_demo


class EndToEndOodDemoTest(unittest.TestCase):
    def test_end_to_end_demo_writes_complete_local_artifact_pack(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = run_end_to_end_ood_demo(
                EndToEndOodDemoConfig(
                    scenario_config_path=Path("configs/scenario_forge.sample.yaml"),
                    output_root=Path(tmp),
                    run_id="local-demo",
                )
            )
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))
            svg_exists = Path(payload["artifact_map"]["local_sim_svg"]).exists()
            html_exists = Path(payload["artifact_map"]["local_sim_html"]).exists()
            reaction_matrix_exists = Path(payload["artifact_map"]["reaction_matrix"]).exists()

        self.assertEqual(payload["status"], "ready")
        self.assertTrue(payload["claim_boundaries"]["local_2d_simulator"])
        self.assertFalse(payload["claim_boundaries"]["closed_loop_carla"])
        self.assertFalse(payload["claim_boundaries"]["live_vla"])
        self.assertIn("policy", payload["policy_decisions"])
        self.assertIn("policy+memory", payload["policy_decisions"])
        self.assertIn("hybrid", payload["policy_decisions"])
        self.assertTrue(payload["retrieved_memory_ids"])
        self.assertTrue(svg_exists)
        self.assertTrue(html_exists)
        self.assertTrue(reaction_matrix_exists)

    def test_cli_runs_end_to_end_demo(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "run-end-to-end-ood-demo",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "cli-local-demo",
                    ]
            )
            summary = json.loads(stream.getvalue())
            report_exists = Path(summary["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["demo_id"], "cli-local-demo")
        self.assertTrue(report_exists)
        self.assertIn("local_ood_sim", summary["artifact_map"]["local_sim_json"])
        self.assertIn("policy_reaction_matrix", summary["artifact_map"]["reaction_matrix"])


if __name__ == "__main__":
    unittest.main()
