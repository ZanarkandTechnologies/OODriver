import json
import struct
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline.alpamayo_ood_evaluation import (
    AlpamayoOodEvaluationInputs,
    build_alpamayo_ood_evaluation,
)


class AlpamayoOodEvaluationTest(unittest.TestCase):
    def test_compares_two_open_loop_alpamayo_decisions(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = _write_decision(root / "baseline.json", offset_y=0.0, reason="Proceed.")
            memory = _write_decision(root / "memory.json", offset_y=0.5, reason="Slow and yield.")

            summary = build_alpamayo_ood_evaluation(
                root / "out",
                AlpamayoOodEvaluationInputs(
                    baseline_decision_path=baseline,
                    memory_decision_path=memory,
                ),
            )

        self.assertTrue(summary["open_loop_policy_evaluation"])
        self.assertFalse(summary["closed_loop_control"])
        self.assertTrue(summary["trajectory_delta"]["available"])
        self.assertGreater(summary["trajectory_delta"]["mean_l2_m"], 0.0)
        self.assertTrue(summary["reasoning_delta"]["changed"])
        self.assertTrue(summary["safety_flags"]["memory_augmented_live_run_available"])

    def test_missing_memory_run_writes_augmented_package_and_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = _write_decision(root / "baseline.json", offset_y=0.0, reason="Proceed.")
            package = _write_package(root / "package")
            route_evidence = root / "route_evidence.json"
            route_evidence.write_text(
                json.dumps(
                    {
                        "status": "partial",
                        "video": {"exists": True, "path": "route.mp4"},
                        "metrics": {},
                        "blockers": [],
                    }
                ),
                encoding="utf-8",
            )

            summary = build_alpamayo_ood_evaluation(
                root / "out",
                AlpamayoOodEvaluationInputs(
                    baseline_decision_path=baseline,
                    source_package_path=package,
                    route_evidence_path=route_evidence,
                ),
            )
            memory_package = Path(summary["memory_augmented_package"]["json_path"])
            payload = json.loads(memory_package.read_text(encoding="utf-8"))

        self.assertFalse(summary["trajectory_delta"]["available"])
        self.assertEqual(summary["records"][1]["setup_blocker"], "memory-augmented live Alpamayo decision was not supplied")
        self.assertIn("mem-sample-motorcycle-filtering", summary["memory_ids"])
        self.assertIn("DriverX retrieved safety memory", payload["nav_text"])
        self.assertTrue(summary["memory_augmented_package"]["torch_ready"])
        self.assertTrue(summary["safety_flags"]["route_video_available"])
        self.assertFalse(summary["safety_flags"]["route_score_available"])

    def test_cli_builds_comparison_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = _write_decision(root / "baseline.json", offset_y=0.0, reason="Proceed.")
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-alpamayo-ood-comparison",
                        "--baseline-decision",
                        str(baseline),
                        "--output-root",
                        str(root),
                        "--run-id",
                        "cli",
                    ]
                )
            summary = json.loads(stream.getvalue())
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn("Alpamayo OOD Evaluation", report)
        self.assertEqual(summary["records"][0]["policy_id"], "alpamayo-live")


def _write_decision(path: Path, *, offset_y: float, reason: str) -> Path:
    points = [[round(index * 0.2, 4), round(offset_y, 4)] for index in range(20)]
    payload = {
        "policy_decision": {
            "policy_id": "alpamayo-live",
            "adapter_kind": "alpamayo_open_loop",
            "intent": {
                "scene_type": "alpamayo_carla_capture:fixture",
                "hazards": ["open-loop"],
                "ego_intent": "evaluate",
                "target_behavior": "open_loop_trajectory_eval",
                "speed_profile": "trajectory_chunk",
                "lateral_bias": "center",
                "uncertainty": 0.4,
            },
            "action": {
                "mode": "trajectory_chunk_open_loop",
                "trajectory": {
                    "points_xy": points,
                    "source": "alpamayo_live_open_loop",
                    "score": 0.5,
                    "metadata": {},
                },
                "control": {
                    "closed_loop_control": False,
                    "open_loop_policy_evaluation": True,
                    "vram_peak_mb": 23200.0,
                },
                "safety_notes": [],
            },
            "latency_ms": 1000.0 + offset_y,
            "reason_summary": reason,
            "retrieved_memory_ids": [],
            "setup_blocker": None,
        }
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_package(root: Path) -> Path:
    image_dir = root / "images"
    image_dir.mkdir(parents=True)
    windows = []
    for camera_index in range(3):
        frames = []
        for frame_index in range(4):
            image = image_dir / f"camera_{camera_index}_frame_{frame_index:03d}.png"
            _write_png_header(image, width=8, height=6)
            frames.append(
                {
                    "frame_index": frame_index,
                    "path": f"images/{image.name}",
                    "width": 8,
                    "height": 6,
                }
            )
        windows.append({"camera_index": camera_index, "frames": frames})
    package = {
        "frame_name": "fixture_carla",
        "camera_windows": windows,
        "camera_indices": [0, 1, 2],
        "ego_history_xyz": [[float(index), 0.0, 0.0] for index in range(16)],
        "ego_history_rot": [
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
            for _ in range(16)
        ],
        "nav_text": "continue straight",
    }
    path = root / "alpamayo_carla_input_package.json"
    path.write_text(json.dumps(package), encoding="utf-8")
    return path


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
