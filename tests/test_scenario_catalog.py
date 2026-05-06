import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.scenarios import (
    PromotionDecision,
    ScenarioQuery,
    filter_catalog,
    index_scenario_artifacts,
    load_scenario_catalog,
    promote_scenario,
    write_scenario_catalog_outputs,
    write_scenario_selection,
)


class ScenarioCatalogTest(unittest.TestCase):
    def test_indexes_and_merges_campaign_video_with_alpamayo_reasoning(self) -> None:
        with TemporaryDirectory() as tmp:
            root = _write_catalog_fixture(Path(tmp))

            catalog = index_scenario_artifacts([root])
            records = catalog.records

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.scenario_id, "seed-regional-driving-behavior-001")
        self.assertEqual(record.behavior_id, "sudden_brake")
        self.assertTrue(record.quality.has_video)
        self.assertTrue(record.quality.has_model_reasoning)
        self.assertTrue(record.quality.road_aligned)
        self.assertIn("video", record.ood_tags)
        self.assertIn("memory-case-7", record.ood_tags)
        self.assertEqual(record.promotion.status, "candidate")
        self.assertEqual(len(record.source_artifacts), 3)

    def test_filters_promotes_and_writes_selection_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = _write_catalog_fixture(tmp_path / "inputs")
            catalog = index_scenario_artifacts([root])
            updated = promote_scenario(
                catalog,
                "seed-regional-driving-behavior-001",
                PromotionDecision(status="hero", reason="submission hero candidate"),
            )
            output = write_scenario_catalog_outputs(updated, tmp_path / "catalog")
            reloaded = load_scenario_catalog(Path(output["json_path"]))
            filtered = filter_catalog(
                reloaded,
                ScenarioQuery(
                    tag="regional-driving-behavior",
                    promotion_status="hero",
                    requires_video=True,
                    requires_model_reasoning=True,
                    requires_road_aligned=True,
                ),
            )
            selection = write_scenario_selection(filtered, tmp_path / "selection", selection_id="heroes")

            self.assertEqual(len(filtered), 1)
            self.assertTrue(Path(output["report_path"]).exists())
            self.assertEqual(selection["record_count"], 1)
            self.assertTrue(Path(selection["json_path"]).exists())
            self.assertIn("heroes", Path(selection["report_path"]).read_text(encoding="utf-8"))

    def test_catalog_cli_indexes_lists_promotes_and_exports(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = _write_catalog_fixture(tmp_path / "inputs")
            stream = StringIO()
            with redirect_stdout(stream):
                index_exit = main(
                    [
                        "index-scenarios",
                        "--artifact-root",
                        str(root),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "catalog",
                    ]
                )
            indexed = json.loads(stream.getvalue())

            catalog_path = indexed["json_path"]
            list_stream = StringIO()
            with redirect_stdout(list_stream):
                list_exit = main(
                    [
                        "list-scenarios",
                        "--catalog",
                        catalog_path,
                        "--requires-video",
                        "--requires-model-reasoning",
                    ]
                )
            listed = json.loads(list_stream.getvalue())

            promote_stream = StringIO()
            with redirect_stdout(promote_stream):
                promote_exit = main(
                    [
                        "promote-scenario",
                        "--catalog",
                        catalog_path,
                        "--scenario-id",
                        "seed-regional-driving-behavior-001",
                        "--status",
                        "failure_case",
                        "--reason",
                        "best understood failure",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "promoted",
                    ]
                )
            promoted = json.loads(promote_stream.getvalue())

            selection_stream = StringIO()
            with redirect_stdout(selection_stream):
                selection_exit = main(
                    [
                        "export-scenario-selection",
                        "--catalog",
                        promoted["json_path"],
                        "--status",
                        "failure_case",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "selection",
                    ]
                )
            selection = json.loads(selection_stream.getvalue())

        self.assertEqual(index_exit, 0)
        self.assertEqual(indexed["record_count"], 1)
        self.assertEqual(list_exit, 0)
        self.assertEqual(listed["record_count"], 1)
        self.assertEqual(promote_exit, 0)
        self.assertEqual(promoted["promotion_counts"]["failure_case"], 1)
        self.assertEqual(selection_exit, 0)
        self.assertEqual(selection["record_count"], 1)


def _write_catalog_fixture(root: Path) -> Path:
    campaign_dir = root / "campaign"
    case_dir = campaign_dir / "cases" / "case-001" / "carla"
    case_dir.mkdir(parents=True, exist_ok=True)
    road_alignment_path = case_dir / "road_alignment_report.json"
    road_alignment_path.write_text(
        json.dumps({"passes": True, "ego": {"max_abs_lateral_m": 0.2}}),
        encoding="utf-8",
    )
    scenario_report_path = case_dir / "carla_ood_demo.json"
    scenario_report_path.write_text(
        json.dumps(
            {
                "status": "passed",
                "scenario_id": "seed-regional-driving-behavior-001",
                "recipe_id": "seed-regional-driving-behavior-001",
                "behavior_id": "sudden_brake",
                "road_alignment_path": str(road_alignment_path),
            }
        ),
        encoding="utf-8",
    )
    campaign_summary = {
        "campaign_id": "campaign",
        "cases": [
            {
                "case_id": "case-001",
                "recipe_id": "seed-regional-driving-behavior-001",
                "behavior_id": "sudden_brake",
                "status": "passed",
                "live": True,
                "min_distance_m": 2.4,
                "frame_count": 120,
                "duration_s": 24.0,
                "scenario_report_path": str(scenario_report_path),
                "road_alignment_path": str(road_alignment_path),
                "tracks_path": str(case_dir / "entity_tracks.json"),
                "rgb_folder": str(case_dir / "rgb"),
                "video_status": "passed",
                "video_path": str(case_dir / "video.mp4"),
                "blockers": [],
            }
        ],
    }
    (campaign_dir / "scripted_ood_campaign_summary.json").write_text(
        json.dumps(campaign_summary),
        encoding="utf-8",
    )

    alpamayo_dir = root / "alpamayo"
    alpamayo_dir.mkdir(parents=True, exist_ok=True)
    alpamayo_summary = {
        "records": [
            {
                "scenario_id": "seed-regional-driving-behavior-001",
                "case_id": "case-001",
                "status": "passed",
                "memory_decision_path": str(alpamayo_dir / "memory_decision.json"),
                "baseline_decision_path": str(alpamayo_dir / "baseline_decision.json"),
                "comparison_path": str(alpamayo_dir / "comparison.json"),
                "package_path": str(alpamayo_dir / "package.json"),
                "memory_ids": ["memory-case-7"],
                "blockers": [],
            }
        ]
    }
    (alpamayo_dir / "alpamayo_ood_batch_summary.json").write_text(
        json.dumps(alpamayo_summary),
        encoding="utf-8",
    )
    return root


if __name__ == "__main__":
    unittest.main()
