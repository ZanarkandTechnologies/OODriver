import json
import struct
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.policies.alpamayo_materializer import materialize_alpamayo_input
from driverx.policies.alpamayo_ood_package import (
    AlpamayoOodPackageInputs,
    build_alpamayo_package_from_ood_demo,
    write_alpamayo_ood_package,
)


def _write_png_header(path: Path, width: int = 64, height: int = 36) -> None:
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR"
        + struct.pack(">II", width, height)
        + b"\x08\x02\x00\x00\x00"
    )


class AlpamayoOodPackageTest(unittest.TestCase):
    def test_builds_torch_ready_package_from_ood_frames_and_tracks(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            rgb = root / "rgb"
            rgb.mkdir()
            for index in range(8):
                _write_png_header(rgb / f"frame_{index:06d}.png")
            tracks = []
            for tick in range(8):
                tracks.append(
                    {
                        "actor_ref": "ego",
                        "tick": tick,
                        "location": {"x": float(tick), "y": 0.0, "z": 0.2},
                    }
                )
            tracks_path = root / "entity_tracks.json"
            tracks_path.write_text(json.dumps(tracks), encoding="utf-8")
            video_path = root / "ood_video_evidence.json"
            video_path.write_text(
                json.dumps(
                    {
                        "scenario_id": "generated-demo",
                        "behavior_id": "motorcycle_filtering",
                        "worst_risk": {"tick": 5},
                    }
                ),
                encoding="utf-8",
            )

            package = build_alpamayo_package_from_ood_demo(
                AlpamayoOodPackageInputs(
                    rgb_folder=rgb,
                    tracks_path=tracks_path,
                    video_evidence_path=video_path,
                )
            )
            summary = write_alpamayo_ood_package(
                root / "out",
                package,
                source={"rgb_folder": str(rgb), "tracks_path": str(tracks_path)},
            )
            manifest = materialize_alpamayo_input(Path(summary["json_path"]))

        self.assertEqual(package.frame_name, "driverx_ood_generated-demo")
        self.assertEqual(len(package.camera_windows), 3)
        self.assertTrue(all(len(window.frames) == 4 for window in package.camera_windows))
        self.assertEqual(package.ego_history_xyz[-1], [6.0, 0.0, 0.2])
        self.assertTrue(manifest.torch_ready)
        self.assertEqual(manifest.image_frames_shape, [3, 4, 3, 36, 64])

    def test_extracts_package_frames_from_video_when_rgb_folder_is_empty(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            rgb = root / "rgb"
            tracks_path = root / "entity_tracks.json"
            tracks_path.write_text(
                json.dumps(
                    [
                        {
                            "actor_ref": "ego",
                            "tick": tick,
                            "location": {"x": float(tick), "y": 0.0, "z": 0.2},
                        }
                        for tick in range(8)
                    ]
                ),
                encoding="utf-8",
            )
            evidence_path = root / "ood_video_evidence.json"
            evidence_path.write_text(
                json.dumps({"scenario_id": "generated-video", "overlay": {"worst_risk": {"tick": 3}}}),
                encoding="utf-8",
            )
            video_path = root / "hero.mp4"
            video_path.write_bytes(b"fake video")
            fake_ffmpeg = root / "fake_ffmpeg.py"
            fake_ffmpeg.write_text(
                """#!/usr/bin/env python3
from pathlib import Path
import struct
import sys
pattern = sys.argv[-1]
for index in range(1, 5):
    path = Path(pattern.replace("%06d", f"{index:06d}"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\\x89PNG\\r\\n\\x1a\\n"
        + b"\\x00\\x00\\x00\\rIHDR"
        + struct.pack(">II", 64, 36)
        + b"\\x08\\x02\\x00\\x00\\x00"
    )
""",
                encoding="utf-8",
            )
            fake_ffmpeg.chmod(0o755)

            package = build_alpamayo_package_from_ood_demo(
                AlpamayoOodPackageInputs(
                    rgb_folder=rgb,
                    video_path=video_path,
                    tracks_path=tracks_path,
                    video_evidence_path=evidence_path,
                    ffmpeg_bin=str(fake_ffmpeg),
                )
            )

        self.assertEqual(package.frame_name, "driverx_ood_generated-video")
        self.assertEqual(len(package.camera_windows[0].frames), 4)


if __name__ == "__main__":
    unittest.main()
