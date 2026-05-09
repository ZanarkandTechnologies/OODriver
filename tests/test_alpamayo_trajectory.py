import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.policies import (
    alpamayo_prediction_to_trajectory,
    resample_alpamayo_xy,
    resample_alpamayo_yaw,
    select_alpamayo_rot_sample,
    select_alpamayo_xyz_sample,
    write_alpamayo_trajectory_conversion,
)


def _native_points(scale: float = 1.0) -> list[list[float]]:
    return [
        [round((index + 1) / 10.0 * scale, 4), round((index + 1) / 20.0, 4), 0.0]
        for index in range(64)
    ]


def _native_rot(yaw_rad: float = 0.1) -> list[list[list[float]]]:
    import math

    c = math.cos(yaw_rad)
    s = math.sin(yaw_rad)
    return [
        [
            [round(c, 6), round(-s, 6), 0.0],
            [round(s, 6), round(c, 6), 0.0],
            [0.0, 0.0, 1.0],
        ]
        for _ in range(64)
    ]


class AlpamayoTrajectoryTest(unittest.TestCase):
    def test_resample_interpolates_10hz_native_output_to_4hz_driverx_chunk(self) -> None:
        resampled = resample_alpamayo_xy(_native_points())

        self.assertEqual(len(resampled), 20)
        self.assertEqual(resampled[0], (0.25, 0.125))
        self.assertEqual(resampled[1], (0.5, 0.25))
        self.assertEqual(resampled[-1], (5.0, 2.5))

    def test_sample_selection_supports_full_alpamayo_batch_shape(self) -> None:
        sample_a = _native_points(scale=1.0)
        sample_b = _native_points(scale=2.0)
        pred_xyz = [[[
            sample_a,
            sample_b,
        ]]]

        selected = select_alpamayo_xyz_sample(pred_xyz, sample_index=1)

        self.assertEqual(selected[0], (0.2, 0.05, 0.0))
        self.assertEqual(selected[-1], (12.8, 3.2, 0.0))

    def test_rotation_selection_extracts_and_resamples_yaw(self) -> None:
        selected = select_alpamayo_rot_sample([[[ _native_rot(0.25) ]]])
        yaw = resample_alpamayo_yaw(selected)

        self.assertEqual(len(yaw), 20)
        self.assertAlmostEqual(yaw[0], 0.25, places=5)

    def test_prediction_to_trajectory_returns_driverx_candidate(self) -> None:
        candidate = alpamayo_prediction_to_trajectory(
            _native_points(),
            pred_rot=_native_rot(0.2),
            source="alpamayo_fixture",
            score=0.42,
            reasoning="yield to lateral pressure",
        )

        self.assertEqual(candidate.source, "alpamayo_fixture")
        self.assertEqual(candidate.score, 0.42)
        self.assertEqual(len(candidate.points_xy), 20)
        self.assertEqual(candidate.metadata["native_steps"], 64)
        self.assertEqual(candidate.metadata["reasoning"], "yield to lateral pressure")
        self.assertAlmostEqual(candidate.metadata["target_yaw_rad"][0], 0.2, places=5)

    def test_short_native_output_fails_before_silent_truncation(self) -> None:
        with self.assertRaisesRegex(ValueError, "need at least 50"):
            resample_alpamayo_xy(_native_points()[:32])

    def test_report_writer_and_cli_emit_conversion_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pred_path = tmp_path / "pred.json"
            pred_path.write_text(
                json.dumps({"pred_xyz": _native_points(), "pred_rot": _native_rot(0.1)}),
                encoding="utf-8",
            )

            summary = write_alpamayo_trajectory_conversion(
                tmp_path / "direct",
                prediction_json=pred_path,
            )
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "convert-alpamayo-trajectory",
                        "--prediction-json",
                        str(pred_path),
                        "--output-root",
                        str(tmp_path),
                        "--run-id",
                        "cli-convert",
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
        self.assertEqual(len(cli_summary["trajectory"]["points_xy"]), 20)
        self.assertIn("target_yaw_rad", cli_summary["trajectory"]["metadata"])


if __name__ == "__main__":
    unittest.main()
