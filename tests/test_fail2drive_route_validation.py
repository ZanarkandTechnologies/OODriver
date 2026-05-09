from __future__ import annotations

from pathlib import Path
import unittest

from driverx.fail2drive.catalog import load_fail2drive_catalog
from driverx.fail2drive.route_validation import validate_fail2drive_route


class Fail2DriveRouteValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_fail2drive_catalog(Path("third_party/fail2drive"))

    def test_valid_route_passes(self) -> None:
        validation = validate_fail2drive_route(Path("tests/fixtures/fail2drive_routes/valid_roadblocked.xml"), self.catalog)

        self.assertTrue(validation.ok)
        self.assertEqual(validation.scenario_counts, {"RoadBlocked": 1})
        self.assertEqual(validation.town_names, ("Town05",))

    def test_unknown_scenario_fails_with_actionable_issue(self) -> None:
        validation = validate_fail2drive_route(Path("tests/fixtures/fail2drive_routes/invalid_unknown.xml"), self.catalog)

        self.assertFalse(validation.ok)
        self.assertIn("unknown_scenario_type", {issue.code for issue in validation.issues})


if __name__ == "__main__":
    unittest.main()
