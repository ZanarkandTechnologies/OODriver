import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline.submission_demo_pack import build_submission_demo_pack


class SubmissionDemoPackTest(unittest.TestCase):
    def test_demo_pack_includes_storyboard_failure_and_declarations(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)

            summary = build_submission_demo_pack(
                root / "demo-pack",
                generated_suite_path=paths["suite"],
                policy_matrix_path=paths["policy"],
                alpamayo_probe_path=paths["alpamayo"],
                blockers_path=paths["blockers"],
                progress_path=paths["progress"],
            )
            report = Path(summary["report_path"]).read_text(encoding="utf-8")
            json_exists = Path(summary["json_path"]).exists()

        self.assertTrue(json_exists)
        self.assertEqual(len(summary["storyboard"]), 6)
        self.assertEqual(summary["failure_case"]["scenario_id"], "recipe-1")
        self.assertIn("1-5 Minute Demo Outline", report)
        self.assertIn("Model Declarations", report)
        self.assertIn("Short Write-Up Draft", report)
        self.assertTrue(any(item["name"] == "alpamayo-probe" for item in summary["model_declarations"]))

    def test_demo_pack_cli_writes_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-demo-pack",
                        "--generated-suite",
                        str(paths["suite"]),
                        "--policy-matrix",
                        str(paths["policy"]),
                        "--alpamayo-probe",
                        str(paths["alpamayo"]),
                        "--blockers",
                        str(paths["blockers"]),
                        "--progress",
                        str(paths["progress"]),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "demo",
                    ]
                )
            summary = json.loads(stream.getvalue())
            report_exists = Path(summary["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(report_exists)
        self.assertEqual(summary["artifact_map"]["route_pack_path"], "routes/generated.xml")


def _write_inputs(root: Path) -> dict[str, Path]:
    suite = root / "generated_ood_suite.json"
    suite.write_text(
        json.dumps(
            {
                "status": "blocked",
                "num_recipes": 1,
                "scenario_summary_path": "scenario_summary.json",
                "route_pack_path": "routes/generated.xml",
                "overlay_plan_path": "overlay_plan.json",
                "overlay_evidence_path": "overlay_evidence.json",
                "readiness": {"recipe_count": 1},
                "recipe_records": [
                    {
                        "recipe_id": "recipe-1",
                        "route_path": "fail2drive_split/Route.xml",
                        "route_evidence_status": "blocked",
                        "route_evidence_path": "route-evidence/run_evidence.json",
                        "video_smoke_plan_path": "video-plan.json",
                        "blockers": ["Missing route video"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    policy = root / "policy_runtime_matrix.json"
    policy.write_text(
        json.dumps(
            {
                "ready_count": 5,
                "rows": [
                    {"policy": "mock", "runtime_kind": "local", "ready_state": "ready"},
                    {"policy": "alpamayo", "runtime_kind": "vla", "ready_state": "blocked"},
                ],
            }
        ),
        encoding="utf-8",
    )
    alpamayo = root / "alpamayo_probe_report.json"
    alpamayo.write_text(
        json.dumps(
            {
                "status": "not_run",
                "model_id": "nvidia/Alpamayo-1.5-10B",
                "blockers": ["No Alpamayo probe artifacts found."],
            }
        ),
        encoding="utf-8",
    )
    blockers = root / "blockers.md"
    blockers.write_text("# Blockers\n\n## Open\n\n- Missing route video\n", encoding="utf-8")
    progress = root / "progress.md"
    progress.write_text("# Progress\n\n- TASK evidence\n", encoding="utf-8")
    return {
        "suite": suite,
        "policy": policy,
        "alpamayo": alpamayo,
        "blockers": blockers,
        "progress": progress,
    }


if __name__ == "__main__":
    unittest.main()
