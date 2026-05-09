from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.fail2drive.catalog import load_fail2drive_catalog
from driverx.fail2drive.route_authoring import load_fail2drive_route_spec, write_fail2drive_route_xml


class Fail2DriveRouteAuthoringTest(unittest.TestCase):
    def test_writes_route_xml_that_validates(self) -> None:
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "route.xml"
            catalog = load_fail2drive_catalog(Path("third_party/fail2drive"))
            result = write_fail2drive_route_xml(
                load_fail2drive_route_spec(Path("tests/fixtures/fail2drive_route_specs/roadblocked.json")),
                output,
                catalog=catalog,
                validate=True,
            )

            self.assertTrue(output.exists())
            self.assertTrue(result.validation)
            self.assertTrue(result.validation["ok"])
            self.assertIn("RoadBlocked", output.read_text(encoding="utf-8"))

    def test_edge_case_specs_compile_and_validate(self) -> None:
        catalog = load_fail2drive_catalog(Path("third_party/fail2drive"))
        with TemporaryDirectory() as tmp:
            for name in ("roadblocked", "dynamic_crossing", "accident", "custom_obstacle"):
                output = Path(tmp) / f"{name}.xml"
                result = write_fail2drive_route_xml(
                    load_fail2drive_route_spec(Path("tests/fixtures/fail2drive_route_specs") / f"{name}.json"),
                    output,
                    catalog=catalog,
                    validate=True,
                )
                self.assertTrue(result.validation, name)
                self.assertTrue(result.validation["ok"], name)


if __name__ == "__main__":
    unittest.main()
