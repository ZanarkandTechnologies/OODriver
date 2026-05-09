from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest import mock
import unittest


SCRIPT = Path("skills/meshy-to-oodrive-asset/scripts/meshy_to_oodrive_asset.py")
SCENARIOS = Path("skills/meshy-to-oodrive-asset/references/high_value_fail2drive_scenarios.json")


def _load_script_module():
    spec = importlib.util.spec_from_file_location("meshy_to_oodrive_asset", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MeshyAssetSkillTests(unittest.TestCase):
    def test_default_formats_are_not_duplicated(self) -> None:
        module = _load_script_module()

        with mock.patch(
            "sys.argv",
            [
                "meshy_to_oodrive_asset.py",
                "--asset-id",
                "x",
                "--prompt",
                "test object",
            ],
        ):
            args = module._parse_args()

        self.assertEqual(args.format, ["glb", "fbx", "obj"])

    def test_explicit_format_overrides_default_formats(self) -> None:
        module = _load_script_module()

        with mock.patch(
            "sys.argv",
            [
                "meshy_to_oodrive_asset.py",
                "--asset-id",
                "x",
                "--prompt",
                "test object",
                "--format",
                "glb",
            ],
        ):
            args = module._parse_args()

        self.assertEqual(args.format, ["glb"])

    def test_high_value_scenario_object_keys_are_distinct(self) -> None:
        payload = json.loads(SCENARIOS.read_text(encoding="utf-8"))

        sinkhole = next(item for item in payload if item["scenario_id"] == "vault-sinkhole-swerve-recover")
        objects = sinkhole["route_spec"]["scenarios"][0]["params"]["objects"]

        self.assertIn("static.prop.constructioncone", objects)
        self.assertIn("static.prop.trafficcone02", objects)


if __name__ == "__main__":
    unittest.main()
