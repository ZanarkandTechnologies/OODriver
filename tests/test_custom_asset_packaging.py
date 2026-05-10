from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.assets.carla_packaging import (
    build_asset_package_plan,
    build_asset_cook_plan,
    probe_asset_blueprint,
    spawn_custom_asset,
    spawn_runtime_mesh_path,
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
            self.assertEqual(payload["prop_name"], "fallen_crane_arm")
            self.assertEqual(payload["package_json_name"], f"{payload['import_package_name']}.json")
            self.assertTrue(Path(payload["package_json_path"]).exists())
            self.assertTrue(Path(payload["copied_fbx_path"]).exists())
            self.assertIn("static.prop.fallen_crane_arm", "\n".join(payload["commands"]))
            self.assertIn("arbitrary_mesh_spawn=false_until_blueprint_probe_and_spawn_pass", payload["claim_boundaries"])

    def test_package_plan_detects_packaged_carla_root_without_cook_tooling(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "carla"
            root.mkdir()
            (root / "Import").mkdir()
            (root / "ImportAssets.sh").write_text("#!/bin/bash\n", encoding="utf-8")
            plan = build_asset_package_plan(ASSET, carla_root=root)

            self.assertEqual(plan.status, "passed")
            self.assertTrue(plan.carla_root_capabilities["has_package_import_assets"])
            self.assertFalse(plan.carla_root_capabilities["has_source_make_import"])
            self.assertTrue(any("cannot cook a raw FBX" in warning for warning in plan.warnings))

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

    def test_runtime_mesh_spawn_blocks_without_carla_package(self) -> None:
        proof = spawn_runtime_mesh_path("/tmp/generated-crane.fbx", scale=4.0)

        self.assertEqual(proof.status, "blocked")
        self.assertEqual(proof.mesh_path, "/tmp/generated-crane.fbx")
        self.assertEqual(proof.scale, 4.0)
        self.assertIn("runtime_mesh_actor_spawned=false", proof.claim_boundaries)

    def test_cook_plan_blocks_without_source_docker_or_cooked_package(self) -> None:
        with TemporaryDirectory() as tmp:
            package = write_asset_package_plan(Path(tmp), build_asset_package_plan(ASSET))
            plan = build_asset_cook_plan(Path(package["json_path"]))

            self.assertEqual(plan.status, "blocked")
            self.assertEqual(plan.mode, "blocked")
            self.assertTrue(any("No programmatic cook/import lane" in blocker for blocker in plan.blockers))
            self.assertIn("raw_fbx_runtime_import=false", plan.claim_boundaries)

    def test_cook_plan_supports_source_make_lane(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "carla-source"
            root.mkdir()
            (root / "Makefile").write_text("import:\n\ttrue\n", encoding="utf-8")
            package = write_asset_package_plan(Path(tmp) / "pkg", build_asset_package_plan(ASSET))

            plan = build_asset_cook_plan(Path(package["json_path"]), carla_source_root=root)

            self.assertEqual(plan.status, "passed")
            self.assertEqual(plan.mode, "source")
            self.assertIn("programmatic_asset_cook_available=true", plan.claim_boundaries)
            self.assertTrue(any("make import" in command for command in plan.commands))

    def test_cook_plan_supports_packaged_cooked_tar_import_lane(self) -> None:
        with TemporaryDirectory() as tmp:
            package_root = Path(tmp) / "carla-package"
            package_root.mkdir()
            (package_root / "ImportAssets.sh").write_text("#!/bin/bash\n", encoding="utf-8")
            cooked = Path(tmp) / "OODrive_fallen_crane_arm.tar.gz"
            cooked.write_bytes(b"placeholder")
            package = write_asset_package_plan(Path(tmp) / "pkg", build_asset_package_plan(ASSET))

            plan = build_asset_cook_plan(
                Path(package["json_path"]),
                carla_package_root=package_root,
                cooked_package_path=cooked,
            )

            self.assertEqual(plan.status, "passed")
            self.assertEqual(plan.mode, "import_cooked")
            self.assertIn("cooked_package_import_available=true", plan.claim_boundaries)
            self.assertTrue(any("ImportAssets.sh" in command for command in plan.commands))


if __name__ == "__main__":
    unittest.main()
