from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.simulators.carla_custom_map import (
    prepare_custom_map_import,
    probe_carla_map,
    validate_custom_map_import,
    write_custom_map_import,
)


FBX = Path("tests/fixtures/custom_map/OODriveTiny.fbx")
XODR = Path("tests/fixtures/custom_map/OODriveTiny.xodr")


class CustomMapImportTests(unittest.TestCase):
    def test_prepare_and_validate_custom_map_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            manifest = prepare_custom_map_import(fbx_path=FBX, xodr_path=XODR, map_name="OODriveTiny")
            paths = write_custom_map_import(run_dir, manifest)
            validation = validate_custom_map_import(Path(paths["json_path"]))

            self.assertEqual(manifest.status, "passed")
            self.assertEqual(validation.status, "passed")
            payload = json.loads(Path(paths["json_path"]).read_text(encoding="utf-8"))
            self.assertIn("custom_unreal_map_import=false_until_carla_map_probe_passes", payload["claim_boundaries"])

    def test_validate_blocks_missing_files(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            manifest = prepare_custom_map_import(
                fbx_path=Path(tmp) / "missing.fbx",
                xodr_path=Path(tmp) / "missing.xodr",
                map_name="MissingMap",
            )
            paths = write_custom_map_import(run_dir, manifest)
            validation = validate_custom_map_import(Path(paths["json_path"]))

            self.assertEqual(validation.status, "blocked")
            self.assertGreaterEqual(len(validation.blockers), 2)

    def test_probe_blocks_without_carla_package(self) -> None:
        probe = probe_carla_map(map_name="OODriveTiny")

        self.assertEqual(probe.status, "blocked")
        self.assertIn("custom_unreal_map_import=false", probe.claim_boundaries)


if __name__ == "__main__":
    unittest.main()
