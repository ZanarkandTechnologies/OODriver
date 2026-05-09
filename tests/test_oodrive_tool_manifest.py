from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.tools.artifact_index import build_artifact_index
from driverx.tools.oodrive_manifest import build_oodrive_tools_manifest, write_oodrive_tools_manifest


class OODriveToolManifestTests(unittest.TestCase):
    def test_tool_manifest_exposes_validation_not_prompt_resolution(self) -> None:
        manifest = build_oodrive_tools_manifest()
        names = {tool["name"] for tool in manifest["tools"]}

        self.assertIn("validate-osc2", names)
        self.assertIn("run-osc2", names)
        self.assertIn("tools-manifest", names)
        self.assertNotIn("resolve-prompt", names)
        self.assertIn("oodrive_internal_prompt_resolver=false", manifest["claim_boundaries"])

    def test_write_tool_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            paths = write_oodrive_tools_manifest(Path(tmp), build_oodrive_tools_manifest())

            self.assertTrue(Path(paths["json_path"]).exists())
            self.assertTrue(Path(paths["report_path"]).exists())

    def test_artifact_index_lists_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.json").write_text("{}", encoding="utf-8")
            index = build_artifact_index(root)

            self.assertEqual(index["artifact_count"], 1)
            self.assertEqual(index["artifacts"][0]["kind"], "json")


if __name__ == "__main__":
    unittest.main()
