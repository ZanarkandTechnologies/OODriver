from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.pipeline.scenario_ancestry_cards import build_scenario_ancestry_cards


class ScenarioAncestryCardsTests(unittest.TestCase):
    def test_builds_reference_grounded_cards(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "db.json"
            db.write_text(
                json.dumps(
                    {
                        "candidates": [
                            {
                                "candidate_id": f"scenario-{index}",
                                "ood_tags": ["obstacle"],
                                "compiled_recipe": {
                                    "recipe_id": f"scenario-{index}",
                                    "parent_seed_id": "Base_Animals_0076",
                                    "mutation": "obstacle_substitution",
                                    "environment": {"environment_template_id": "blocked_lane", "behavior_id": "stop"},
                                    "expected_failure_mode": "blocked lane",
                                },
                            }
                            for index in range(4)
                        ]
                    }
                ),
                encoding="utf-8",
            )
            fail2drive = root / "fail2drive.json"
            fail2drive.write_text(
                json.dumps(
                    {
                        "extension_records": [
                            {
                                "generated_scenario_id": "scenario-0",
                                "matched_reference_ids": ["Base_Animals_0076"],
                                "fail2drive_route_refs": ["fail2drive_split/Base_Animals_0076.xml"],
                                "mutation_summary": "extends Animals with obstacle_substitution",
                                "memory_entry_ids": ["mem-animals"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = build_scenario_ancestry_cards(
                db_path=db,
                fail2drive_report_path=fail2drive,
                output_root=root,
                run_id="cards",
            )

            self.assertEqual(report["card_count"], 4)
            self.assertEqual(report["cards"][0]["fail2drive_refs"], ["Base_Animals_0076"])
            self.assertIn("source_citations=true", report["claim_boundaries"])
            self.assertTrue(Path(report["html_path"]).exists())


if __name__ == "__main__":
    unittest.main()
