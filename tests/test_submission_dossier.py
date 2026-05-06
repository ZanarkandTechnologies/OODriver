import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline.submission_dossier import build_submission_dossier


class SubmissionDossierTest(unittest.TestCase):
    def test_build_submission_dossier_combines_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)

            dossier = build_submission_dossier(
                root / "dossier",
                ood_suite_manifest_path=paths["ood"],
                gpu_host_suitability_path=paths["gpu"],
                progress_path=paths["progress"],
                blockers_path=paths["blockers"],
            )
            report = Path(dossier["report_path"]).read_text(encoding="utf-8")
            json_exists = Path(dossier["json_path"]).exists()

        self.assertTrue(json_exists)
        self.assertEqual(dossier["metric_highlights"]["rag_driving_score_delta"], 37.0)
        self.assertEqual(dossier["gpu_host"]["overall_state"], "blocked")
        self.assertIn("current blocker", dossier["demo_outline"][-1])
        self.assertIn("0xDriver Minimal-Shot OOD Driving Harness", report)
        self.assertIn("graphics-capable NVIDIA host", report)
        self.assertIn("TASK-020 CARLA graphics blocker", report)

    def test_build_submission_dossier_cli_writes_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-submission-dossier",
                        "--ood-suite-manifest",
                        str(paths["ood"]),
                        "--gpu-host-suitability",
                        str(paths["gpu"]),
                        "--progress",
                        str(paths["progress"]),
                        "--blockers",
                        str(paths["blockers"]),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "dossier",
                    ]
                )
            result = json.loads(stream.getvalue())
            report_exists = Path(result["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(report_exists)
        self.assertFalse(result["ood_readiness"]["live_policy_result_passed"])

    def test_build_submission_dossier_v5_optional_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)
            reasoning = root / "reasoning.json"
            campaign = root / "campaign.json"
            batch = root / "batch.json"
            replay = root / "replay.json"
            reasoning.write_text(
                json.dumps(
                    {
                        "scenario_id": "scene-1",
                        "video_path": "scene.mp4",
                        "html_path": "reasoning.html",
                        "latency": {"scene_latency_ms": 10.0},
                        "inputs": {
                            "ood_video_evidence_path": "ood_video_evidence.json",
                            "alpamayo_comparison_path": "alpamayo_ood_comparison.json",
                        },
                        "claim_boundaries": ["reasoning_pack_is_evidence_surface=true"],
                    }
                ),
                encoding="utf-8",
            )
            campaign.write_text(
                json.dumps(
                    {
                        "campaign_id": "camp-1",
                        "status": "passed",
                        "case_count": 3,
                        "live_case_count": 2,
                        "cases": [{"video_path": "case.mp4", "video_evidence_path": "case_video.json"}],
                    }
                ),
                encoding="utf-8",
            )
            batch.write_text(
                json.dumps(
                    {
                        "status": "passed",
                        "mean_latency_ms": 11.0,
                        "mean_vram_peak_mb": 100.0,
                        "max_vram_peak_mb": 120.0,
                    }
                ),
                encoding="utf-8",
            )
            replay.write_text(json.dumps({"status": "passed", "claim_boundaries": ["cached_alpamayo_replay=true"]}), encoding="utf-8")

            dossier = build_submission_dossier(
                root / "dossier",
                ood_suite_manifest_path=paths["ood"],
                gpu_host_suitability_path=paths["gpu"],
                reasoning_pack_path=reasoning,
                campaign_summary_path=campaign,
                alpamayo_batch_path=batch,
                cached_replay_path=replay,
                progress_path=paths["progress"],
                blockers_path=paths["blockers"],
            )
            script_exists = Path(dossier["video_script_path"]).exists()

        self.assertTrue(script_exists)
        self.assertIn("artifact_checklist", dossier)
        labels = {item["label"] for item in dossier["artifact_checklist"]}
        self.assertIn("Live OOD video evidence", labels)
        self.assertIn("Live OOD MP4", labels)
        self.assertIn("Alpamayo comparison artifact", labels)
        self.assertIn("Blocker ledger", labels)
        self.assertIn("cached_alpamayo_replay=true", dossier["claim_boundaries"])
        self.assertEqual(dossier["metric_highlights"]["alpamayo_batch_mean_vram_peak_mb"], 100.0)
        self.assertEqual(dossier["gpu_host"]["overall_state"], "blocked")
        self.assertEqual(dossier["slide_outline"][1]["title"], "Randomized Scenario Forge")


def _write_inputs(root: Path) -> dict[str, Path]:
    ood = root / "ood_suite_manifest.json"
    ood.write_text(
        json.dumps(
            {
                "readiness": {
                    "scenario_generation_ready": True,
                    "live_policy_result_passed": False,
                    "has_open_blockers": True,
                },
                "metric_highlights": {
                    "generated_recipe_count": 2,
                    "rag_driving_score_delta": 37.0,
                },
            }
        ),
        encoding="utf-8",
    )
    gpu = root / "gpu_host_suitability.json"
    gpu.write_text(
        json.dumps(
            {
                "overall_state": "blocked",
                "recommendation": "Use a graphics-capable NVIDIA host.",
                "blockers": ["CARLA graphics runtime is blocked."],
                "warnings": ["Root disk is small."],
            }
        ),
        encoding="utf-8",
    )
    progress = root / "progress.md"
    progress.write_text("# Progress\n\n- recent item\n", encoding="utf-8")
    blockers = root / "blockers.md"
    blockers.write_text(
        "# Blockers\n\n## Open\n\n- TASK-020 CARLA graphics blocker\n",
        encoding="utf-8",
    )
    return {"ood": ood, "gpu": gpu, "progress": progress, "blockers": blockers}


if __name__ == "__main__":
    unittest.main()
