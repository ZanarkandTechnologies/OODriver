import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline.submission_eval_matrix import build_submission_eval_matrix
from driverx.scenarios import (
    PromotionDecision,
    ScenarioArtifacts,
    ScenarioCatalog,
    ScenarioCatalogRecord,
    ScenarioQuality,
    write_scenario_catalog_outputs,
)


class SubmissionEvalMatrixTest(unittest.TestCase):
    def test_build_matrix_selects_hero_and_needed_next(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_path = _write_catalog(root)
            evidence_path = _write_alpamayo_evidence(root)

            summary = build_submission_eval_matrix(
                [catalog_path],
                [evidence_path],
                root / "matrix",
                limit=6,
            )

            self.assertEqual(summary["case_count"], 6)
            self.assertEqual(summary["hero_count"], 1)
            hero = summary["cases"][0]
            self.assertEqual(hero["role"], "hero")
            self.assertEqual(hero["evidence"]["alpamayo_memory"], str(evidence_path))
            self.assertIn("TASK-104_alpamayo_baseline", hero["needed_next"])
            self.assertTrue(Path(summary["json_path"]).exists())
            self.assertTrue(Path(summary["report_path"]).exists())

    def test_cli_writes_matrix(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_path = _write_catalog(root)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-submission-eval-matrix",
                        "--catalog",
                        str(catalog_path),
                        "--output-root",
                        str(root),
                        "--run-id",
                        "matrix-cli",
                        "--limit",
                        "6",
                    ]
                )
            summary = json.loads(stream.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["case_count"], 6)
        self.assertEqual(summary["hero_count"], 1)


def _write_catalog(root: Path) -> Path:
    records = [
        ScenarioCatalogRecord(
            scenario_id="generated-hero",
            recipe_id="generated-hero",
            case_id="case-hero",
            family="regional",
            behavior_id="motorcycle_filtering",
            environment_tags=["malaysian_driving", "dense_traffic"],
            ood_tags=["visual_noise", "motorcycle"],
            quality=ScenarioQuality(
                road_aligned=True,
                has_conflict=True,
                has_video=True,
                has_model_reasoning=False,
                status="passed",
            ),
            artifacts=ScenarioArtifacts(video="hero.mp4", tracks="tracks.json"),
            promotion=PromotionDecision(status="hero", reason="fixture hero"),
        )
    ]
    for index in range(5):
        records.append(
            ScenarioCatalogRecord(
                scenario_id=f"generated-support-{index}",
                recipe_id=f"generated-support-{index}",
                case_id=f"case-{index}",
                family=f"family-{index}",
                behavior_id="sudden_brake" if index % 2 else None,
                environment_tags=["construction", f"tag-{index}"],
                ood_tags=["blocked_lane"],
                quality=ScenarioQuality(
                    road_aligned=None,
                    has_conflict=bool(index % 2),
                    has_video=False,
                    has_model_reasoning=False,
                    status="blocked",
                ),
                artifacts=ScenarioArtifacts(),
                blockers=["needs video"],
            )
        )
    output = write_scenario_catalog_outputs(ScenarioCatalog(records=records), root / "catalog")
    return Path(output["json_path"])


def _write_alpamayo_evidence(root: Path) -> Path:
    path = root / "alpamayo_policy_decision.json"
    path.write_text(
        json.dumps(
            {
                "policy_decision": {
                    "intent": {
                        "scene_type": "alpamayo_carla_capture:driverx_ood_generated-hero",
                        "hazards": ["1 retrieved DriverX memory entries were provided prompt-side"],
                    },
                    "retrieved_memory_ids": ["mem-1"],
                }
            }
        ),
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    unittest.main()
