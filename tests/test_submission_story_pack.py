from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from oodrive.cli import main as oodrive_main


class SubmissionStoryPackTest(unittest.TestCase):
    def test_export_submission_builds_required_pack_and_scores_over_90(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = _write_db(root)
            run_path = _write_run(root)
            evaluation_path = _write_evaluation(root)
            hero_score_path = _write_hero_score(root)
            hero_video_path = root / "oodrive_hero_demo.mp4"
            hero_video_path.write_bytes(b"fake mp4 placeholder")
            checks_path = _write_checks(root)

            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = oodrive_main(
                    [
                        "export-submission",
                        "--db",
                        str(db_path),
                        "--run",
                        str(run_path),
                        "--evaluation",
                        str(evaluation_path),
                        "--hero-video",
                        str(hero_video_path),
                        "--hero-score",
                        str(hero_score_path),
                        "--output-root",
                        str(root / "packs"),
                        "--run-id",
                        "pack",
                    ]
                )
            result = json.loads(stream.getvalue())
            manifest_path = Path(result["artifacts"]["submission_pack_manifest_path"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["command"], "oodrive export-submission")
            self.assertTrue(Path(result["artifacts"]["submission_pack_index_path"]).exists())
            self.assertTrue(Path(result["artifacts"]["submission_pack_readme_path"]).exists())
            self.assertTrue(Path(result["artifacts"]["submission_pack_claim_matrix_path"]).exists())
            self.assertTrue(Path(result["artifacts"]["submission_pack_commands_path"]).exists())
            self.assertTrue(Path(result["artifacts"]["submission_pack_artifact_inventory_path"]).exists())
            self.assertTrue(Path(result["artifacts"]["submission_pack_scorecard_path"]).exists())
            self.assertGreaterEqual(len(manifest["claim_matrix"]), 6)
            self.assertGreaterEqual(len(manifest["sections"]), 6)
            self.assertIn("closed_loop_vla_control=false", manifest["claim_boundaries"])
            self.assertIn("real_time_vla_control=false", manifest["claim_boundaries"])
            self.assertIn("sampled_open_loop_reasoning=true", manifest["claim_boundaries"])
            self.assertIn("time_warped_offline_demo=true", manifest["claim_boundaries"])

            score_stream = StringIO()
            with redirect_stdout(score_stream):
                self.assertEqual(
                    oodrive_main(
                        [
                            "score-submission",
                            "--db",
                            str(db_path),
                            "--run",
                            str(run_path),
                            "--evaluation",
                            str(evaluation_path),
                            "--hero-score",
                            str(hero_score_path),
                            "--pack-manifest",
                            str(manifest_path),
                            "--checks-report",
                            str(checks_path),
                        ]
                    ),
                    0,
                )
            score_result = json.loads(score_stream.getvalue())
            self.assertEqual(score_result["status"], "passed")
            self.assertGreaterEqual(score_result["summary"]["submission_readiness_score"], 90.0)

    def test_export_submission_help_is_registered(self) -> None:
        stream = StringIO()
        with self.assertRaises(SystemExit) as raised, redirect_stdout(stream):
            oodrive_main(["export-submission", "--help"])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn("export-submission", stream.getvalue())


def _write_db(root: Path) -> Path:
    path = root / "scenario_studio_db.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "oodrive.studio-db.v1",
                "product_name": "OODrive",
                "run_id": "commission",
                "briefs": [{"brief_id": "brief-1"}],
                "plans": [],
                "candidates": [{"candidate_id": f"candidate-{index}"} for index in range(4)],
                "curation": [],
                "queue": [],
                "runs": [],
                "evaluations": [],
                "bundles": [],
                "exports": [],
                "artifacts": {
                    "placement_plan_path": str(root / "placement.json"),
                    "carla_ood_demo_json": str(root / "carla.json"),
                },
                "command_log": [
                    {"command": "oodrive generate", "status": "passed", "artifacts": {}},
                    {"command": "oodrive place", "status": "passed", "artifacts": {}},
                    {"command": "oodrive reason", "status": "passed", "artifacts": {}},
                    {"command": "oodrive demo-video", "status": "passed", "artifacts": {}},
                    {"command": "oodrive score-demo", "status": "passed", "artifacts": {}},
                ],
                "claim_boundaries": [
                    "product_name=OODrive",
                    "carla_placement_plan=true",
                    "objects_placed_in_carla=true",
                    "scripted_carla_ood_demo=true",
                    "closed_loop_vla_control=false",
                    "real_time_vla_control=false",
                    "sampled_open_loop_reasoning=true",
                    "time_warped_offline_demo=true",
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_run(root: Path) -> Path:
    path = root / "run_manifest.json"
    path.write_text(
        json.dumps(
            {
                "run_id": "run",
                "scenario_id": "scenario-1",
                "runtime": "carla-scripted-ood-demo",
                "status": "passed",
                "artifacts": {"carla_ood_demo_json": str(root / "carla.json")},
                "claim_boundaries": [
                    "objects_placed_in_carla=true",
                    "scripted_carla_ood_demo=true",
                    "closed_loop_vla_control=false",
                    "real_time_vla_control=false",
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_evaluation(root: Path) -> Path:
    path = root / "policy_evaluation.json"
    path.write_text(
        json.dumps(
            {
                "scenario_id": "scenario-1",
                "cot_summary": "Slow and yield because the generated roadwork actors narrow the lane.",
                "memory_ids": ["tag:roadwork", "tag:wet", "tag:filtering"],
                "latency_ms": 90125.0,
                "claim_boundaries": [
                    "sampled_open_loop_reasoning=true",
                    "closed_loop_vla_control=false",
                    "real_time_vla_control=false",
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_hero_score(root: Path) -> Path:
    path = root / "hero_demo_score.json"
    path.write_text(
        json.dumps(
            {
                "status": "passed",
                "hero_demo_score": 100.0,
                "metrics": {
                    "output_duration_s": 90.0,
                    "visible_generated_object_count": 4,
                    "risk_event_count": 6,
                    "reasoning_event_count": 4,
                    "rag_event_count": 4,
                    "alpamayo_prediction_count": 1
                },
                "claim_boundaries": [
                    "time_warped_offline_demo=true",
                    "sampled_open_loop_reasoning=true",
                    "real_time_vla_control=false"
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_checks(root: Path) -> Path:
    path = root / "checks_report.json"
    path.write_text(
        json.dumps(
            {
                "checks_passed": True,
                "pre_push_passed": True,
                "review_passed": True,
                "large_file_count": 4,
            }
        ),
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    unittest.main()
