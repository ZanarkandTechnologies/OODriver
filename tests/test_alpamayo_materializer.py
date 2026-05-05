import json
import struct
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.policies import (
    load_alpamayo_torch_tensors,
    materialize_alpamayo_input,
    write_alpamayo_tensor_materialization,
)


class AlpamayoMaterializerTest(unittest.TestCase):
    def test_materializes_fixture_png_package_without_torch(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_path = _write_package(root)

            manifest = materialize_alpamayo_input(package_path)

        self.assertTrue(manifest.torch_ready)
        self.assertEqual(manifest.image_frames_shape, [3, 4, 3, 6, 8])
        self.assertEqual(manifest.camera_indices_shape, [3])
        self.assertEqual(manifest.ego_history_xyz_shape, [1, 1, 16, 3])
        self.assertEqual(manifest.ego_history_rot_shape, [1, 1, 16, 3, 3])
        self.assertEqual(len(manifest.materialized_frames), 12)
        self.assertEqual(manifest.materialized_frames[0].file_width, 8)

    def test_records_validation_errors_for_missing_images_and_bad_history(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_path = _write_package(root, write_images=False)
            payload = json.loads(package_path.read_text(encoding="utf-8"))
            payload["ego_history_xyz"] = [[0.0, 0.0, 0.0]]
            payload["camera_indices"] = [2, 1, 0]
            package_path.write_text(json.dumps(payload), encoding="utf-8")

            manifest = materialize_alpamayo_input(package_path)

        self.assertFalse(manifest.torch_ready)
        self.assertTrue(any("Image path does not exist" in error for error in manifest.validation_errors))
        self.assertTrue(any("ego_history_xyz shape" in error for error in manifest.validation_errors))
        self.assertTrue(any("does not match camera_indices" in error for error in manifest.validation_errors))

    def test_writer_and_cli_emit_materialization_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_path = _write_package(root)
            manifest = materialize_alpamayo_input(package_path)
            direct = write_alpamayo_tensor_materialization(root / "direct", manifest)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "materialize-alpamayo-input",
                        "--package",
                        str(package_path),
                        "--output-root",
                        str(root),
                        "--run-id",
                        "cli-materialized",
                    ]
                )
            cli_summary = json.loads(stream.getvalue())
            direct_json_exists = Path(direct["json_path"]).exists()
            direct_report_exists = Path(direct["report_path"]).exists()
            cli_json_exists = Path(cli_summary["json_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(direct_json_exists)
        self.assertTrue(direct_report_exists)
        self.assertTrue(cli_json_exists)
        self.assertEqual(cli_summary["image_frames_shape"], [3, 4, 3, 6, 8])
        self.assertEqual(cli_summary["torch_loader_contract"]["camera_indices"]["values"], [0, 1, 2])

    def test_torch_loader_is_lazy_and_actionable_when_torch_missing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_path = _write_package(root)

            try:
                load_alpamayo_torch_tensors(package_path)
            except ImportError as exc:
                message = str(exc)
            else:
                message = "torch installed locally"

        self.assertTrue(
            "remote Alpamayo environment" in message or message == "torch installed locally"
        )


def _write_package(root: Path, *, write_images: bool = True) -> Path:
    image_dir = root / "images"
    image_dir.mkdir()
    windows = []
    for camera_index in range(3):
        frames = []
        for frame_index in range(4):
            path = image_dir / f"camera_{camera_index}_frame_{frame_index:03d}.png"
            if write_images:
                _write_png_header(path, width=8, height=6)
            frames.append(
                {
                    "frame_index": frame_index,
                    "path": str(path),
                    "width": 8,
                    "height": 6,
                }
            )
        windows.append(
            {
                "camera_index": camera_index,
                "camera_name": f"Camera {camera_index}",
                "frames": frames,
            }
        )
    package = {
        "frame_name": "fixture_carla_materialized",
        "camera_windows": windows,
        "camera_indices": [0, 1, 2],
        "ego_history_xyz": [[float(index), 0.0, 0.0] for index in range(16)],
        "ego_history_rot": [
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
            for _ in range(16)
        ],
        "nav_text": "continue straight",
        "memory_context": [{"entry_id": "mem-1"}],
    }
    package_path = root / "alpamayo_carla_input_package.json"
    package_path.write_text(json.dumps(package), encoding="utf-8")
    return package_path


def _write_png_header(path: Path, *, width: int, height: int) -> None:
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
        + b"\x08\x02\x00\x00\x00"
        + b"\x00\x00\x00\x00"
    )


if __name__ == "__main__":
    unittest.main()
