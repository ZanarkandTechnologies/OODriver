import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline.policy_evaluation_campaign import (
    PolicyEvaluationCampaignConfig,
    evaluate_policy_on_scenario,
    run_policy_evaluation_campaign,
)
from driverx.scenarios import (
    PromotionDecision,
    ScenarioArtifacts,
    ScenarioCatalog,
    ScenarioCatalogRecord,
    ScenarioQuality,
    write_scenario_catalog_outputs,
)


class PolicyEvaluationCampaignTest(unittest.TestCase):
    def test_evaluates_catalog_record_modes(self) -> None:
        with TemporaryDirectory() as tmp:
            record = _catalog_record(has_reasoning=True, root=Path(tmp))
            evaluations = evaluate_policy_on_scenario(
                record,
                ["deterministic-baseline", "memory-guided", "alpamayo-open-loop", "live-alpamayo"],
                output_dir=Path(tmp) / "evals",
            )
            by_mode = {evaluation.policy_mode: evaluation for evaluation in evaluations}
            decision_path = by_mode["deterministic-baseline"].artifacts["policy_decision"]
            self.assertTrue(Path(str(decision_path)).exists())

        self.assertEqual(by_mode["deterministic-baseline"].status, "passed")
        self.assertEqual(by_mode["memory-guided"].status, "passed")
        self.assertEqual(by_mode["alpamayo-open-loop"].status, "passed")
        self.assertEqual(by_mode["live-alpamayo"].status, "planned")

    def test_policy_campaign_writes_summary(self) -> None:
        with TemporaryDirectory() as tmp:
            catalog_path = _write_catalog(Path(tmp), has_reasoning=True)
            summary = run_policy_evaluation_campaign(
                PolicyEvaluationCampaignConfig(
                    catalog_path=catalog_path,
                    output_root=Path(tmp),
                    run_id="policy",
                    policy_modes=("deterministic-baseline", "alpamayo-open-loop"),
                )
            )

            self.assertEqual(summary["scenario_count"], 1)
            self.assertEqual(summary["evaluation_count"], 2)
            self.assertEqual(summary["passed_evaluation_count"], 2)
            self.assertEqual(summary["planned_evaluation_count"], 0)
            self.assertEqual(summary["blocked_evaluation_count"], 0)
            self.assertEqual(summary["status_counts"]["passed"], 2)
            self.assertEqual(summary["decision_artifact_count"], 1)
            decision = summary["evaluations"][0]["artifacts"]["policy_decision"]
            self.assertTrue(Path(decision).exists())
            self.assertTrue(Path(summary["json_path"]).exists())
            self.assertTrue(Path(summary["report_path"]).exists())

    def test_policy_campaign_cli_accepts_selection_and_modes(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            catalog_path = _write_catalog(tmp_path, has_reasoning=False)
            catalog_payload = json.loads(catalog_path.read_text(encoding="utf-8"))
            selection_path = tmp_path / "selection.json"
            selection_path.write_text(
                json.dumps({"records": catalog_payload["records"]}),
                encoding="utf-8",
            )
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "run-policy-evaluation-campaign",
                        "--catalog",
                        str(catalog_path),
                        "--selection",
                        str(selection_path),
                        "--policy-mode",
                        "memory-guided",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "policy-cli",
                    ]
                )
            summary = json.loads(stream.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["evaluation_count"], 1)
        self.assertEqual(summary["status_counts"]["passed"], 1)
        self.assertEqual(summary["blockers"], [])


def _write_catalog(root: Path, *, has_reasoning: bool) -> Path:
    catalog = ScenarioCatalog(records=[_catalog_record(has_reasoning=has_reasoning, root=root)])
    summary = write_scenario_catalog_outputs(catalog, root / "catalog")
    return Path(summary["json_path"])


def _catalog_record(*, has_reasoning: bool, root: Path) -> ScenarioCatalogRecord:
    tracks_path = root / "entity_tracks.json"
    tracks_path.write_text(
        json.dumps(
            [
                {"actor_ref": "ego", "tick": 0, "location": {"x": 0.0, "y": 0.0}},
                {"actor_ref": "ood_actor_0", "tick": 0, "location": {"x": 4.0, "y": 0.0}},
                {"actor_ref": "ego", "tick": 1, "location": {"x": 1.0, "y": 0.0}},
                {"actor_ref": "ood_actor_0", "tick": 1, "location": {"x": 3.0, "y": 0.0}},
            ]
        ),
        encoding="utf-8",
    )
    return ScenarioCatalogRecord(
        scenario_id="generated-test",
        recipe_id="generated-test",
        case_id="case-1",
        family="regional",
        behavior_id="motorcycle_filtering",
        environment_tags=["malaysian_driving"],
        ood_tags=["motorcycle_filtering"],
        quality=ScenarioQuality(
            road_aligned=True,
            has_conflict=True,
            has_video=True,
            has_model_reasoning=has_reasoning,
            status="passed",
        ),
        artifacts=ScenarioArtifacts(
            video="case.mp4",
            tracks=str(tracks_path),
            reasoning="alpamayo_policy_decision.json" if has_reasoning else None,
            package="alpamayo_carla_input_package.json" if has_reasoning else None,
            comparison="alpamayo_ood_comparison.json" if has_reasoning else None,
        ),
        promotion=PromotionDecision(status="candidate"),
        source_artifacts=["scenario_catalog_fixture.json"],
    )


if __name__ == "__main__":
    unittest.main()
