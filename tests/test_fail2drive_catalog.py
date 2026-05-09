from __future__ import annotations

from pathlib import Path
import unittest

from driverx.fail2drive.catalog import load_fail2drive_catalog


class Fail2DriveCatalogTest(unittest.TestCase):
    def test_loads_upstream_toolbox_scenario_metadata(self) -> None:
        catalog = load_fail2drive_catalog(Path("third_party/fail2drive"))
        by_name = catalog.by_name()

        self.assertIn("RoadBlocked", by_name)
        self.assertIn("DynamicObjectCrossing", by_name)
        self.assertIn("Accident", by_name)
        self.assertTrue(by_name["RoadBlocked"].graphical_editor)
        self.assertEqual(by_name["DynamicObjectCrossing"].group, "Crossing Actors")
        self.assertIn("distance", {param.name for param in by_name["RoadBlocked"].params})
        self.assertGreater(len(catalog.towns_with_toolbox_data), 0)


if __name__ == "__main__":
    unittest.main()
