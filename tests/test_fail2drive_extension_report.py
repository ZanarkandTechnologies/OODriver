import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline.fail2drive_extension_report import build_fail2drive_extension_report


class Fail2DriveExtensionReportTest(unittest.TestCase):
    def test_studio_batch_links_generated_case_to_fixture_reference_and_memory(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "studio.json"
            source.write_text(
                json.dumps(
                    {
                        "candidates": [
                            {
                                "candidate_id": "studio-pedestrian-001",
                                "compiled_recipe": {
                                    "recipe_id": "studio-pedestrian-001",
                                    "memory_query": ["school_zone", "occlusion", "pedestrian"],
                                    "environment": {
                                        "ood_tags": ["school_zone", "pedestrian_occlusion"],
                                        "asset_tags": ["parked_van"],
                                    },
                                    "route_path": "fail2drive_split/Generalization_PedestriansOnRoad_1088.xml",
                                },
                                "environment_recipe": {
                                    "family": "pedestrian_occlusion",
                                    "tags": ["school_zone", "pedestrian_occlusion"],
                                },
                                "behavior_plan": {
                                    "behavior_id": "informal_right_of_way_push",
                                    "tags": ["creep", "right_of_way"],
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            summary = build_fail2drive_extension_report(
                generated_source_paths=[source],
                output_dir=Path(tmp) / "out",
            )
            self.assertEqual(summary["generated_case_count"], 1)
            record = summary["extension_records"][0]
            self.assertEqual(record["claim"], "generated_extension")
            self.assertEqual(record["fail2drive_seed_family"], "PedestriansOnRoad")
            self.assertIn("Generalization_PedestriansOnRoad_1088", record["matched_reference_ids"])
            self.assertTrue(record["memory_entry_ids"])
            self.assertEqual(record["official_score_claim"], "reference_only_no_official_fail2drive_score")
            self.assertTrue(Path(summary["json_path"]).exists())
            self.assertTrue(Path(summary["report_path"]).exists())

    def test_missing_external_checkout_uses_fixture_fallback(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "matrix.json"
            source.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "scenario_id": "generated-visual-noise-001",
                                "scenario_family": "construction",
                                "behavior_id": "no_signal_cut_in",
                                "environment_tags": ["visual_noise", "debris"],
                                "ood_tags": ["unknown_object", "visual_noise"],
                                "blockers": [],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            summary = build_fail2drive_extension_report(
                generated_source_paths=[source],
                output_dir=Path(tmp) / "out",
                fail2drive_root=Path(tmp) / "does-not-exist",
            )

        self.assertGreaterEqual(summary["reference_count"], 3)
        record = summary["extension_records"][0]
        self.assertIn(record["claim"], {"generated_extension", "unlinked_generated_case"})
        self.assertFalse(summary["fail2drive_root"] is None)
        self.assertIn("official_fail2drive_score_claim=false", summary["claim_boundaries"])

    def test_cli_writes_report(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "catalog.json"
            source.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "scenario_id": "generated-animal-001",
                                "recipe_id": "recipe",
                                "case_id": None,
                                "family": "animals",
                                "behavior_id": "sudden_brake",
                                "environment_tags": ["animals", "unknown_obstacle"],
                                "ood_tags": ["occupied_space"],
                                "quality": {"status": "passed", "has_video": True},
                                "artifacts": {},
                                "promotion": {"status": "candidate", "reason": None},
                                "source_artifacts": [],
                                "blockers": [],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-fail2drive-extension-report",
                        "--source",
                        str(source),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "report",
                    ]
                )
            summary = json.loads(stream.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(summary["generated_case_count"], 1)
            self.assertTrue(Path(summary["report_path"]).exists())


if __name__ == "__main__":
    unittest.main()
