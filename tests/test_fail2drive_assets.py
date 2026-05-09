from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.fail2drive.assets import (
    extract_route_blueprints,
    load_fail2drive_asset_catalog,
    qa_fail2drive_route_assets,
    write_fail2drive_asset_catalog_report,
    write_fail2drive_asset_qa,
)
from driverx.scenarios.studio_product_production_runtime import run_studio_generate_assets


F2D_ROOT = Path("third_party/fail2drive")


class Fail2DriveAssetsTest(unittest.TestCase):
    def test_catalog_exposes_stock_props_and_animal_blueprints(self) -> None:
        catalog = load_fail2drive_asset_catalog(F2D_ROOT)
        by_blueprint = catalog.by_blueprint()

        self.assertIn("static.prop.haybale", by_blueprint)
        self.assertTrue(any(asset.kind == "animal_walker" for asset in catalog.assets))
        self.assertTrue(catalog.content_hints["animal_content_families"])

    def test_route_blueprint_extraction_reads_upstream_animals(self) -> None:
        blueprints = extract_route_blueprints(F2D_ROOT / "fail2drive_split" / "Generalization_Animals_1079.xml")

        self.assertIn("walker.animal.1010", blueprints)

    def test_asset_qa_passes_when_prompt_route_catalog_and_frame_align(self) -> None:
        with TemporaryDirectory() as tmp:
            frame = Path(tmp) / "frame.jpg"
            frame.write_bytes(b"fake-frame")
            catalog = load_fail2drive_asset_catalog(F2D_ROOT)
            qa = qa_fail2drive_route_assets(
                F2D_ROOT / "fail2drive_split" / "Generalization_Animals_1079.xml",
                prompt="a deer crosses a rural road",
                catalog=catalog,
                evidence_frames=(frame,),
            )
            paths = write_fail2drive_asset_qa(Path(tmp), qa)

            self.assertEqual(qa.status, "passed")
            self.assertIn("animal", qa.matched_requirements)
            self.assertTrue(Path(paths["json_path"]).exists())

    def test_asset_qa_blocks_prompt_route_mismatch(self) -> None:
        with TemporaryDirectory() as tmp:
            frame = Path(tmp) / "frame.jpg"
            frame.write_bytes(b"fake-frame")
            catalog = load_fail2drive_asset_catalog(F2D_ROOT)
            qa = qa_fail2drive_route_assets(
                F2D_ROOT / "fail2drive_split" / "Generalization_Animals_1079.xml",
                prompt="a haybale blocks the lane",
                catalog=catalog,
                evidence_frames=(frame,),
            )

            self.assertEqual(qa.status, "blocked")
            self.assertIn("haybale", qa.missing_requirements)

    def test_writes_asset_catalog_report(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = write_fail2drive_asset_catalog_report(Path(tmp), load_fail2drive_asset_catalog(F2D_ROOT), fmt="both")

            self.assertGreater(summary["asset_count"], 20)
            self.assertTrue(Path(summary["json_path"]).exists())
            self.assertTrue(Path(summary["report_path"]).exists())

    def test_generate_assets_accepts_external_manifest_provider(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            mesh = root / "custom_crane.obj"
            mesh.write_text("o crane\nv 0 0 0\n", encoding="utf-8")
            pack = _scenario_pack(root)
            external = root / "external_assets.json"
            external.write_text(
                json.dumps(
                    {
                        "asset_id": "custom_crane",
                        "provider": "external_manifest",
                        "status": "generated",
                        "prompt": "external generated crane arm",
                        "semantic_tags": ["construction", "crane", "route_blockage"],
                        "dimensions_m": {"length": 6.0, "width": 1.0, "height": 1.0},
                        "collision_proxy": {"kind": "box", "length": 6.0, "width": 1.0, "height": 1.0},
                        "intended_placement": {"surface": "road", "relative_to": "lane_center", "x_m": 20.0},
                        "license": "external-generator-test",
                        "local_path": str(mesh),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            result = run_studio_generate_assets(
                scenario_pack_path=pack,
                provider="external-manifest",
                external_manifest_path=external,
                output_root=root,
                run_id="external-assets",
            )

            self.assertEqual(result.status, "passed")
            patched_pack = json.loads(Path(result.artifacts["scenario_pack_path"]).read_text(encoding="utf-8"))
            self.assertEqual(patched_pack["asset_manifests"][0]["provider"], "external_manifest")


def _scenario_pack(root: Path) -> Path:
    pack_path = root / "scenario_pack.json"
    request = {
        "asset_id": "placeholder_crane",
        "prompt": "placeholder crane",
        "semantic_tags": ["construction"],
        "dimensions_m": {"length": 6.0, "width": 1.0, "height": 1.0},
        "collision_proxy": {"kind": "box", "length": 6.0, "width": 1.0, "height": 1.0},
        "intended_placement": {"surface": "road", "relative_to": "lane_center"},
        "license": "test",
    }
    pack_path.write_text(
        json.dumps(
            {
                "schema_version": "oodrive.production_scenario_pack.v1",
                "scenario_id": "test-pack",
                "source_prompt": "test pack",
                "behavior_timelines": [{"actor_ref": "ego"}],
                "asset_requests": [request],
                "asset_readiness": {"stock_proxy": True},
                "claim_boundaries": ["custom_asset_imported_in_carla=false_until_registry_probe_passes"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return pack_path


if __name__ == "__main__":
    unittest.main()
