import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.pipeline import OodVideoEvidenceInputs, build_ood_video_evidence
from driverx.simulators import OodVideoOverlayConfig, render_ood_video_overlay


def _write_frames(folder: Path, count: int = 3) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise unittest.SkipTest(f"Pillow unavailable for PNG fixture generation: {exc}")

    folder.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        image = Image.new("RGB", (320, 180), (30 + index * 20, 40, 60))
        image.save(folder / f"frame_{index:06d}.png")


def _write_tracks(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "actor_ref": "ego",
                    "tick": 0,
                    "location": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "rotation": {},
                    "velocity": {},
                },
                {
                    "actor_ref": "ood_actor_0",
                    "tick": 0,
                    "location": {"x": 3.0, "y": 4.0, "z": 0.0},
                    "rotation": {},
                    "velocity": {},
                },
                {
                    "actor_ref": "ego",
                    "tick": 1,
                    "location": {"x": 1.0, "y": 0.0, "z": 0.0},
                    "rotation": {},
                    "velocity": {},
                },
                {
                    "actor_ref": "ood_actor_0",
                    "tick": 1,
                    "location": {"x": 2.0, "y": 0.0, "z": 0.0},
                    "rotation": {},
                    "velocity": {},
                },
            ]
        ),
        encoding="utf-8",
    )


class OodVideoEvidenceTest(unittest.TestCase):
    def test_render_overlay_writes_frames_and_worst_risk(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            rgb = root / "rgb"
            tracks = root / "tracks.json"
            _write_frames(rgb, count=2)
            _write_tracks(tracks)

            result = render_ood_video_overlay(
                OodVideoOverlayConfig(
                    rgb_folder=rgb,
                    output_frame_dir=root / "overlay",
                    scenario_id="scenario-001",
                    behavior_id="motorcycle_filtering",
                    ood_tags=["motorcycle", "filtering"],
                    tracks_path=tracks,
                )
            )

            self.assertEqual(result.status, "passed")
            self.assertEqual(result.input_frame_count, 2)
            self.assertEqual(result.overlay_frame_count, 2)
            self.assertEqual(result.worst_risk, {"tick": 1, "actor_ref": "ood_actor_0", "distance_m": 1.0})
            self.assertEqual(len(list((root / "overlay").glob("*.png"))), 2)

    def test_build_ood_video_evidence_assembles_mp4(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            rgb = root / "rgb"
            tracks = root / "tracks.json"
            _write_frames(rgb, count=3)
            _write_tracks(tracks)

            result = build_ood_video_evidence(
                root / "run",
                OodVideoEvidenceInputs(
                    rgb_folder=rgb,
                    tracks_path=tracks,
                    scenario_id="scenario-001",
                    behavior_id="motorcycle_filtering",
                    ood_tags=["motorcycle"],
                    fps=3,
                ),
            )

            self.assertIn(result["status"], {"passed", "partial"})
            self.assertEqual(result["duration_s"], 1.0)
            self.assertEqual(result["worst_risk"]["distance_m"], 1.0)
            self.assertTrue(Path(result["json_path"]).exists())
            self.assertTrue(Path(result["report_path"]).exists())
            if result["status"] == "passed":
                self.assertTrue(Path(result["video_path"]).exists())

    def test_missing_frames_reports_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = render_ood_video_overlay(
                OodVideoOverlayConfig(
                    rgb_folder=root / "missing",
                    output_frame_dir=root / "overlay",
                    scenario_id="scenario-001",
                    behavior_id="motorcycle_filtering",
                )
            )

            self.assertEqual(result.status, "blocked")
            self.assertIn("No RGB frames", result.blockers[0])


if __name__ == "__main__":
    unittest.main()
