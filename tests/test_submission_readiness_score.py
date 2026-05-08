from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from oodrive.cli import main as oodrive_main


class SubmissionReadinessScoreTest(unittest.TestCase):
    def test_weak_fixture_blocks_target_fixture_passes_and_overclaim_blocks(self) -> None:
        weak = _run_score_fixture("weak_submission.json")
        target = _run_score_fixture("target_submission.json")
        overclaim = _run_score_fixture("overclaim_submission.json")

        self.assertEqual(weak["status"], "blocked")
        self.assertLess(weak["summary"]["submission_readiness_score"], weak["summary"]["threshold"])
        self.assertIn("submission pack", " ".join(weak["blockers"]))
        self.assertEqual(target["status"], "passed")
        self.assertEqual(target["summary"]["submission_readiness_score"], 100.0)
        self.assertEqual(overclaim["status"], "blocked")
        self.assertIn("forbidden closed-loop", " ".join(overclaim["blockers"]))

    def test_metric_only_emits_primary_and_component_metrics(self) -> None:
        stream = StringIO()
        with redirect_stdout(stream):
            exit_code = oodrive_main(
                [
                    "score-submission",
                    "--score-input",
                    "qa/fixtures/submission_readiness_score/target_submission.json",
                    "--metric-only",
                ]
            )

        self.assertEqual(exit_code, 0)
        output = stream.getvalue().strip().splitlines()
        self.assertIn("METRIC submission_readiness_score=100.0000", output)
        self.assertIn("METRIC hero_demo_score=100.0000", output)
        self.assertTrue(any(line.startswith("METRIC judge_comprehension_pack=") for line in output))

    def test_product_artifacts_score_commission_readiness_baseline(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = _write_db(root)
            run_path = _write_run(root)
            evaluation_path = _write_evaluation(root)
            hero_score_path = _write_hero_score(root)
            overlay_path = _write_overlay(root)

            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = oodrive_main(
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
                        "--overlay-report",
                        str(overlay_path),
                        "--output-root",
                        str(root / "scores"),
                        "--run-id",
                        "readiness",
                    ]
                )
            result = json.loads(stream.getvalue())
            score_json = Path(result["artifacts"]["json_path"])
            db_payload = json.loads(db_path.read_text(encoding="utf-8"))

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["command"], "oodrive score-submission")
            self.assertEqual(result["status"], "blocked")
            self.assertTrue(score_json.exists())
            self.assertIn("judge-facing submission pack manifest is missing", result["blockers"])
            self.assertTrue(any(entry["command"] == "oodrive score-submission" for entry in db_payload["command_log"]))

    def test_product_score_submission_help_is_registered(self) -> None:
        stream = StringIO()
        with self.assertRaises(SystemExit) as raised, redirect_stdout(stream):
            oodrive_main(["score-submission", "--help"])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn("score-submission", stream.getvalue())


def _run_score_fixture(name: str) -> dict[str, object]:
    stream = StringIO()
    with redirect_stdout(stream):
        exit_code = oodrive_main(
            [
                "score-submission",
                "--score-input",
                f"qa/fixtures/submission_readiness_score/{name}",
                "--output-root",
                "artifacts/runs",
                "--run-id",
                f"test-{Path(name).stem}",
            ]
        )
    result = json.loads(stream.getvalue())
    assert exit_code == 0
    return result


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
                "artifacts": {
                    "placement_plan_path": str(root / "placement.json"),
                    "carla_ood_demo_json": str(root / "carla.json"),
                },
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
                "cot_summary": "Yield to the filtering rider, slow, and keep a margin near roadwork.",
                "memory_ids": ["tag:roadwork", "tag:motorcycle", "tag:wet"],
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
                    "output_duration_s": 42.0,
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


def _write_overlay(root: Path) -> Path:
    path = root / "hero_demo_video.json"
    path.write_text(
        json.dumps(
            {
                "output_duration_s": 42.0,
                "events": [
                    {"vla_reasoning": "slow", "memory_id": "tag:roadwork"},
                    {"vla_reasoning": "yield", "memory_id": "tag:motorcycle"},
                    {"vla_reasoning": "hold margin", "memory_id": "tag:wet"},
                    {"vla_reasoning": "watch occlusion", "memory_id": "tag:occlusion"}
                ],
                "claim_boundaries": ["time_warped_offline_demo=true"],
            }
        ),
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    unittest.main()
