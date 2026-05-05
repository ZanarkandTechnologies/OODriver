import json
import struct
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.datasets.fixtures import load_fixture_frame
from driverx.policies import (
    build_alpamayo_live_decision,
    run_alpamayo_live_package,
    select_policy_adapter,
)
from driverx.policies.types import PolicyContext, PolicySetupError


class AlpamayoLiveTest(unittest.TestCase):
    def test_live_package_runner_writes_open_loop_policy_decision(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_path = _write_package(root)
            prediction_path = _write_prediction(root / "prediction.json")

            summary = run_alpamayo_live_package(
                package_path=package_path,
                prediction_json=prediction_path,
                output_root=root,
                run_id="live-policy",
            )
            decision = summary["policy_decision"]
            report_exists = Path(summary["report_path"]).exists()

        self.assertEqual(decision["policy_id"], "alpamayo-live")
        self.assertEqual(decision["adapter_kind"], "alpamayo_open_loop")
        self.assertEqual(decision["action"]["mode"], "trajectory_chunk_open_loop")
        self.assertTrue(decision["action"]["control"]["open_loop_policy_evaluation"])
        self.assertFalse(decision["action"]["control"]["closed_loop_control"])
        self.assertEqual(len(decision["action"]["trajectory"]["points_xy"]), 20)
        self.assertIn("yield to the motorcycle", decision["reason_summary"])
        self.assertTrue(report_exists)

    def test_adapter_requires_package_and_prediction_metadata(self) -> None:
        adapter = select_policy_adapter("alpamayo-live")

        with self.assertRaises(PolicySetupError):
            adapter.decide(PolicyContext(frame=load_fixture_frame("construction_merge")))

    def test_adapter_consumes_prediction_metadata(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_path = _write_package(root)
            prediction_path = _write_prediction(root / "prediction.json")
            adapter = select_policy_adapter("alpamayo-live")

            decision = adapter.decide(
                PolicyContext(
                    frame=load_fixture_frame("construction_merge"),
                    metadata={
                        "alpamayo_package_path": package_path,
                        "alpamayo_prediction_json": prediction_path,
                    },
                )
            )

        self.assertEqual(decision.policy_id, "alpamayo-live")
        self.assertEqual(decision.action.trajectory.source, "alpamayo_live_open_loop")
        self.assertEqual(decision.latency_ms, 1234.5)

    def test_cli_runs_live_policy_and_policy_fixture_path(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_path = _write_package(root)
            prediction_path = _write_prediction(root / "prediction.json")
            live_stream = StringIO()
            with redirect_stdout(live_stream):
                live_exit = main(
                    [
                        "run-alpamayo-live",
                        "--package",
                        str(package_path),
                        "--prediction-json",
                        str(prediction_path),
                        "--output-root",
                        str(root),
                        "--run-id",
                        "cli-live",
                    ]
                )
            fixture_stream = StringIO()
            with redirect_stdout(fixture_stream):
                fixture_exit = main(
                    [
                        "run-policy-fixture",
                        "--policy",
                        "alpamayo-live",
                        "--alpamayo-package",
                        str(package_path),
                        "--alpamayo-prediction-json",
                        str(prediction_path),
                        "--output-root",
                        str(root),
                        "--run-id",
                        "fixture-live",
                    ]
                )
            live_summary = json.loads(live_stream.getvalue())
            fixture_summary = json.loads(fixture_stream.getvalue())

        self.assertEqual(live_exit, 0)
        self.assertEqual(fixture_exit, 0)
        self.assertEqual(live_summary["policy_decision"]["policy_id"], "alpamayo-live")
        self.assertEqual(fixture_summary["policy_id"], "alpamayo-live")

    def test_build_decision_rejects_invalid_package(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_path = _write_package(root, write_images=False)
            prediction_path = _write_prediction(root / "prediction.json")

            with self.assertRaisesRegex(ValueError, "not torch-ready"):
                build_alpamayo_live_decision(
                    package_path=package_path,
                    prediction_json=prediction_path,
                )


def _write_prediction(path: Path) -> Path:
    points = [[[
        [round((index + 1) / 10.0, 4), round((index + 1) / 30.0, 4), 0.0]
        for index in range(64)
    ]]]
    path.write_text(
        json.dumps(
            {
                "model_id": "nvidia/Alpamayo-1.5-10B",
                "run_id": "unit-live",
                "latency_ms": 1234.5,
                "vram_peak_mb": 24576.0,
                "output_shapes": {
                    "pred_xyz": [1, 1, 1, 64, 3],
                    "pred_rot": [1, 1, 1, 64, 3, 3],
                    "extra.cot": [1, 1, 1],
                },
                "extra": {"cot": [[["Slow down and yield to the motorcycle before proceeding."]]]},
                "pred_xyz": points,
            }
        ),
        encoding="utf-8",
    )
    return path


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
        windows.append({"camera_index": camera_index, "frames": frames})
    package_path = root / "alpamayo_carla_input_package.json"
    package_path.write_text(
        json.dumps(
            {
                "frame_name": "fixture_carla_live",
                "camera_windows": windows,
                "camera_indices": [0, 1, 2],
                "ego_history_xyz": [[float(index), 0.0, 0.0] for index in range(16)],
                "ego_history_rot": [
                    [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
                    for _ in range(16)
                ],
            }
        ),
        encoding="utf-8",
    )
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
