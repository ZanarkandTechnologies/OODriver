import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.pipeline.reasoning_video_pack import (
    ReasoningVideoPackInputs,
    build_reasoning_video_pack,
)


class ReasoningVideoPackTest(unittest.TestCase):
    def test_build_pack_writes_json_markdown_and_html(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)

            result = build_reasoning_video_pack(
                root / "pack",
                ReasoningVideoPackInputs(
                    ood_video_evidence_path=paths["video"],
                    alpamayo_scene_path=paths["scene"],
                    alpamayo_comparison_path=paths["comparison"],
                ),
            )
            html = Path(result["html_path"]).read_text(encoding="utf-8")
            saved = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))
            report = Path(result["report_path"]).read_text(encoding="utf-8")

        self.assertEqual(result["status"], "ready")
        self.assertEqual(saved["html_path"], result["html_path"])
        self.assertEqual(result["scenario_id"], "scene-1")
        self.assertEqual(result["memory_ids"], ["mem-1"])
        self.assertEqual(result["trajectory_delta"]["final_l2_m"], 2.5)
        self.assertIn("DriverX Reasoning Video Pack", html)
        self.assertIn("baseline reasoning", report)

    def test_build_pack_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _write_inputs(root)
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-reasoning-video-pack",
                        "--ood-video-evidence",
                        str(paths["video"]),
                        "--alpamayo-scene",
                        str(paths["scene"]),
                        "--alpamayo-comparison",
                        str(paths["comparison"]),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "pack",
                    ]
                )
            result = json.loads(stream.getvalue())
            html_exists = Path(result["html_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(html_exists)


def _write_inputs(root: Path) -> dict[str, Path]:
    video = root / "video.json"
    video.write_text(
        json.dumps(
            {
                "scenario_id": "scene-1",
                "behavior_id": "motorcycle_filtering",
                "video_path": "scene.mp4",
                "duration_s": 24.0,
                "input_rgb_folder": "rgb",
                "worst_risk": {"tick": 9, "distance_m": 0.4},
            }
        ),
        encoding="utf-8",
    )
    scene = root / "scene.json"
    scene.write_text(
        json.dumps({"scenario_id": "scene-1", "latency_ms": 123.0, "cot_snippet": "scene reasoning"}),
        encoding="utf-8",
    )
    comparison = root / "comparison.json"
    comparison.write_text(
        json.dumps(
            {
                "scenario_id": "scene-1",
                "memory_ids": ["mem-1"],
                "memory_context": [
                    {"entry_id": "mem-1", "recommended_behavior": "slow early"}
                ],
                "trajectory_delta": {"available": True, "final_l2_m": 2.5},
                "reasoning_delta": {"available": True, "changed": True},
                "records": [
                    {"mode": "alpamayo", "cot_snippet": "baseline reasoning", "latency_ms": 1.0},
                    {"mode": "alpamayo+memory", "cot_snippet": "memory reasoning", "latency_ms": 2.0},
                ],
            }
        ),
        encoding="utf-8",
    )
    return {"video": video, "scene": scene, "comparison": comparison}


if __name__ == "__main__":
    unittest.main()
