import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.datasets.fixtures import load_fixture_frame
from driverx.policies import (
    build_alpamayo_input_package,
    sample_memory_entries,
    write_alpamayo_input_package,
)


class AlpamayoInputTest(unittest.TestCase):
    def test_build_package_uses_default_front_camera_contract(self) -> None:
        frame = load_fixture_frame("construction_merge")

        package = build_alpamayo_input_package(frame)
        payload = package.to_jsonable()

        self.assertEqual(payload["frame_name"], "fixture_construction_merge_001")
        self.assertEqual(payload["camera_indices"], [0, 1, 2])
        self.assertEqual(
            [window["camera_name"] for window in payload["camera_windows"]],
            ["Front left camera", "Front camera", "Front right camera"],
        )
        self.assertTrue(all(len(window["frames"]) == 4 for window in payload["camera_windows"]))
        self.assertEqual(payload["tensor_shapes"]["image_frames"], "3 x 4 x 3 x H x W")

    def test_build_package_resamples_history_and_identity_rotations(self) -> None:
        frame = load_fixture_frame("straight_clear")

        package = build_alpamayo_input_package(frame)

        self.assertEqual(len(package.ego_history_xyz), 16)
        self.assertEqual(package.ego_history_xyz[-1], [0.0, 0.0, 0.0])
        self.assertEqual(package.ego_history_xyz[0], [-6.0, 0.0, 0.0])
        self.assertEqual(len(package.ego_history_rot), 16)
        self.assertEqual(package.ego_history_rot[0][0], [1.0, 0.0, 0.0])

    def test_build_package_includes_nav_text_and_memory_context(self) -> None:
        frame = load_fixture_frame("construction_merge")

        package = build_alpamayo_input_package(
            frame,
            nav_text="Turn left in 11m",
            memory_entries=sample_memory_entries(),
        )

        self.assertEqual(package.nav_text, "Turn left in 11m")
        self.assertEqual(len(package.memory_context), 1)
        self.assertEqual(package.memory_context[0]["entry_id"], "mem-sample-motorcycle-filtering")

    def test_report_writer_and_cli_emit_input_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            package = build_alpamayo_input_package(
                load_fixture_frame("construction_merge"),
                memory_entries=sample_memory_entries(),
            )
            summary = write_alpamayo_input_package(tmp_path / "direct", package)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-alpamayo-input",
                        "--fixture",
                        "construction_merge",
                        "--with-memory",
                        "--output-root",
                        str(tmp_path),
                        "--run-id",
                        "cli-input",
                    ]
                )
            cli_summary = json.loads(stream.getvalue())
            direct_json_exists = Path(summary["json_path"]).exists()
            direct_md_exists = Path(summary["report_path"]).exists()
            cli_json_exists = Path(cli_summary["json_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(direct_json_exists)
        self.assertTrue(direct_md_exists)
        self.assertTrue(cli_json_exists)
        self.assertEqual(len(cli_summary["memory_context"]), 1)


if __name__ == "__main__":
    unittest.main()
