import json
import os
import re
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline.submission_scenario_browser import (
    SubmissionBrowserInputs,
    build_submission_scenario_browser,
)
from driverx.scenarios import (
    PromotionDecision,
    ScenarioArtifacts,
    ScenarioCatalog,
    ScenarioCatalogRecord,
    ScenarioQuality,
    write_scenario_catalog_outputs,
)


class SubmissionScenarioBrowserTest(unittest.TestCase):
    def test_browser_builder_writes_html_dossier_and_script(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            catalog_path = _write_browser_catalog(tmp_path)
            policy_path = _write_policy(tmp_path)
            outputs = build_submission_scenario_browser(
                SubmissionBrowserInputs(
                    catalog_path=catalog_path,
                    policy_evaluation_path=policy_path,
                ),
                tmp_path / "browser",
            )
            browser = Path(outputs.browser_html).read_text(encoding="utf-8")
            dossier = Path(outputs.dossier_md).read_text(encoding="utf-8")
            summary = json.loads(Path(outputs.summary_json).read_text(encoding="utf-8"))

            self.assertIn("0xDriver Scenario Browser", browser)
            self.assertIn("generated-hero", browser)
            self.assertIn("quality_status=passed", browser)
            self.assertIn("promotion=hero", browser)
            self.assertIn("passed policy evals", browser)
            self.assertIn("Submission Dossier V6", dossier)
            self.assertIn("policy evaluations by status", dossier)
            self.assertEqual(outputs.hero_scenarios, ["generated-hero"])
            self.assertEqual(outputs.failure_scenarios, [])
            self.assertEqual(summary["policy_passed_count"], 1)
            self.assertEqual(summary["policy_planned_count"], 1)
            self.assertEqual(summary["policy_blocked_count"], 0)

    def test_browser_artifact_links_resolve_from_output_directory(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            evidence_dir = tmp_path / "evidence"
            evidence_dir.mkdir()
            for name in [
                "hero.mp4",
                "tracks.json",
                "reasoning.json",
                "package.json",
                "road_alignment_report.json",
            ]:
                (evidence_dir / name).write_text("ok", encoding="utf-8")
            original_cwd = Path.cwd()
            try:
                os.chdir(tmp_path)
                catalog_path = _write_browser_catalog(Path("."), artifact_prefix="evidence")
                outputs = build_submission_scenario_browser(
                    SubmissionBrowserInputs(catalog_path=catalog_path),
                    Path("browser"),
                )
                browser_path = Path(outputs.browser_html)
                browser = browser_path.read_text(encoding="utf-8")
                hrefs = re.findall(r"href='([^']+)'", browser)
                resolved = [(browser_path.parent / href).resolve() for href in hrefs]
            finally:
                os.chdir(original_cwd)

            self.assertGreaterEqual(len(resolved), 5)
            self.assertTrue(all(path.exists() for path in resolved))

    def test_browser_cli_writes_summary(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            catalog_path = _write_browser_catalog(tmp_path)
            policy_path = _write_policy(tmp_path)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-submission-scenario-browser",
                        "--catalog",
                        str(catalog_path),
                        "--policy-evaluation",
                        str(policy_path),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "browser-cli",
                    ]
            )
            summary = json.loads(stream.getvalue())

            self.assertEqual(exit_code, 0)
            self.assertTrue(Path(summary["browser_html"]).exists())
            self.assertTrue(Path(summary["dossier_md"]).exists())
            self.assertTrue(Path(summary["video_script_md"]).exists())

    def test_failure_case_is_not_selected_as_hero(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            catalog_path = _write_browser_catalog(tmp_path, promotion_status="failure_case")
            policy_path = _write_policy(tmp_path)
            outputs = build_submission_scenario_browser(
                SubmissionBrowserInputs(
                    catalog_path=catalog_path,
                    policy_evaluation_path=policy_path,
                ),
                tmp_path / "browser",
            )
            script = Path(outputs.video_script_md).read_text(encoding="utf-8")

            self.assertEqual(outputs.hero_scenarios, [])
            self.assertEqual(outputs.failure_scenarios, ["generated-hero"])
            self.assertIn("no submission-grade hero", script)
            self.assertIn("Show failure case `generated-hero`", script)

    def test_blocked_policy_packet_is_not_reported_as_completed(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            catalog_path = _write_browser_catalog(tmp_path)
            policy_path = tmp_path / "blocked-policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "evaluation_count": 27,
                        "status_counts": {"blocked": 18, "planned": 9},
                        "decision_artifact_count": 0,
                        "evaluations": [],
                    }
                ),
                encoding="utf-8",
            )
            outputs = build_submission_scenario_browser(
                SubmissionBrowserInputs(
                    catalog_path=catalog_path,
                    policy_evaluation_path=policy_path,
                ),
                tmp_path / "browser",
            )
            summary = json.loads(Path(outputs.summary_json).read_text(encoding="utf-8"))
            dossier = Path(outputs.dossier_md).read_text(encoding="utf-8")

            self.assertNotIn("policy_evaluation_count", summary)
            self.assertEqual(summary["policy_evaluation_row_count"], 27)
            self.assertEqual(summary["policy_passed_count"], 0)
            self.assertEqual(summary["policy_planned_count"], 9)
            self.assertEqual(summary["policy_blocked_count"], 18)
            self.assertEqual(summary["policy_decision_artifact_count"], 0)
            self.assertIn("policy evaluations by status: passed `0`, planned `9`, blocked `18`", dossier)


def _write_browser_catalog(
    root: Path,
    *,
    promotion_status: str = "hero",
    artifact_prefix: str = "",
) -> Path:
    def artifact(name: str) -> str:
        return str(Path(artifact_prefix) / name) if artifact_prefix else name

    record = ScenarioCatalogRecord(
        scenario_id="generated-hero",
        recipe_id="generated-hero",
        case_id="case-hero",
        family="regional",
        behavior_id="motorcycle_filtering",
        environment_tags=["malaysian_driving", "construction"],
        ood_tags=["video", "motorcycle_filtering"],
        quality=ScenarioQuality(
            road_aligned=True,
            has_conflict=True,
            has_video=True,
            has_model_reasoning=True,
            status="passed",
        ),
        artifacts=ScenarioArtifacts(
            video=artifact("hero.mp4"),
            tracks=artifact("tracks.json"),
            reasoning=artifact("reasoning.json"),
            package=artifact("package.json"),
            quality_report=artifact("road_alignment_report.json"),
        ),
        promotion=PromotionDecision(status=promotion_status),
        source_artifacts=["fixture.json"],
    )
    summary = write_scenario_catalog_outputs(ScenarioCatalog(records=[record]), root / "catalog")
    return Path(summary["json_path"])


def _write_policy(root: Path) -> Path:
    path = root / "policy.json"
    path.write_text(
        json.dumps(
            {
                "evaluation_count": 2,
                "status_counts": {"passed": 1, "planned": 1},
                "decision_artifact_count": 0,
                "evaluations": [
                    {
                        "scenario_id": "generated-hero",
                        "policy_mode": "alpamayo-open-loop",
                        "status": "passed",
                        "blockers": [],
                    },
                    {
                        "scenario_id": "generated-hero",
                        "policy_mode": "live-alpamayo",
                        "status": "planned",
                        "blockers": ["remote adapter not attached in fixture"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    unittest.main()
