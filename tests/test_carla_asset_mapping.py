import unittest

from driverx.assets import (
    default_asset_requests,
    generate_assets_dry_run,
    map_asset_to_carla_spawn,
    map_assets_to_carla_spawns,
    validate_carla_asset_mappings,
)


class CarlaAssetMappingTest(unittest.TestCase):
    def test_maps_dry_run_assets_to_stock_carla_spawn_specs(self) -> None:
        manifests = generate_assets_dry_run(default_asset_requests())

        specs = map_assets_to_carla_spawns(manifests)

        self.assertEqual(len(specs), 3)
        self.assertEqual(specs[0].asset_id, "asset-fallen-cargo-sack")
        self.assertEqual(specs[0].blueprint_filter, "static.prop.dirtdebris01")
        self.assertEqual(specs[1].blueprint_filter, "static.prop.foodcart")
        self.assertEqual(specs[2].blueprint_filter, "static.prop.constructioncone")
        self.assertEqual(specs[2].spawn_transform["location"]["x"], 18.0)
        self.assertEqual(specs[2].spawn_transform["location"]["y"], -0.2)

    def test_falls_back_to_tag_mapping_when_metadata_has_no_blueprint(self) -> None:
        manifest = generate_assets_dry_run(default_asset_requests())[0]
        stripped = type(manifest)(
            asset_id=manifest.asset_id,
            provider=manifest.provider,
            status=manifest.status,
            prompt=manifest.prompt,
            semantic_tags=manifest.semantic_tags,
            dimensions_m=manifest.dimensions_m,
            collision_proxy=manifest.collision_proxy,
            intended_placement=manifest.intended_placement,
            license=manifest.license,
            metadata={},
        )

        spec = map_asset_to_carla_spawn(stripped)

        self.assertEqual(spec.blueprint_filter, "static.prop.dirtdebris01")

    def test_validates_blueprint_availability(self) -> None:
        manifests = generate_assets_dry_run(default_asset_requests())

        missing = validate_carla_asset_mappings(manifests, ["static.prop.dirtdebris01"])
        present = validate_carla_asset_mappings(
            manifests,
            [
                "static.prop.dirtdebris01",
                "static.prop.foodcart",
                "static.prop.constructioncone",
            ],
        )

        self.assertIn("asset-roadside-food-cart", missing)
        self.assertIn("asset-reflective-flood-barrier", missing)
        self.assertEqual(present, {})


if __name__ == "__main__":
    unittest.main()
