from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.assets.carla_packaging import (
    build_asset_package_plan,
    probe_asset_blueprint,
    spawn_custom_asset,
    write_asset_package_plan,
)


ASSET = Path("tests/fixtures/assets/crane_asset_manifest.json")


class CustomAssetPackagingTests(unittest.TestCase):
    def test_package_plan_for_asset_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            plan = build_asset_package_plan(ASSET)
            paths = write_asset_package_plan(Path(tmp), plan)
            payload = json.loads(Path(paths["json_path"]).read_text(encoding="utf-8"))

            self.assertEqual(plan.status, "passed")
            self.assertEqual(payload["asset_id"], "fallen_crane_arm")
            self.assertIn("arbitrary_mesh_spawn=false_until_blueprint_probe_and_spawn_pass", payload["claim_boundaries"])

    def test_package_blocks_missing_manifest(self) -> None:
        plan = build_asset_package_plan(Path("missing_asset_manifest.json"))

        self.assertEqual(plan.status, "blocked")
        self.assertTrue(plan.blockers)

    def test_probe_blocks_without_carla_package(self) -> None:
        result = probe_asset_blueprint("driverx.generated.fallen_crane_arm")

        self.assertEqual(result.status, "blocked")
        self.assertIn("arbitrary_mesh_spawn=false", result.claim_boundaries)

    def test_spawn_blocks_without_blueprint_probe(self) -> None:
        proof = spawn_custom_asset("driverx.generated.fallen_crane_arm")

        self.assertEqual(proof.status, "blocked")
        self.assertIn("arbitrary_mesh_spawn=false", proof.claim_boundaries)


if __name__ == "__main__":
    unittest.main()
