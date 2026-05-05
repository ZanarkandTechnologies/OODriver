import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.policies import inspect_alpamayo_release, write_alpamayo_release_contract


def _write_release_fixture(root: Path) -> None:
    (root / "src" / "alpamayo1_5" / "models").mkdir(parents=True)
    (root / "README.md").write_text(
        "\n".join(
            [
                "Python 3.12",
                "CUDA Toolkit 12.x",
                "Single-sample inference (`num_traj_samples=1`)          | ~24 GB",
                "Multi-sample inference (`num_traj_samples=16`)          | ~40 GB",
                "Multi-sample inference with CFG (`num_traj_samples=16`) | ~60 GB",
                "Measured on an NVIDIA H100 80GB GPU.",
                "uv sync --active --no-install-package flash-attn",
                "Navigation conditioning",
            ]
        ),
        encoding="utf-8",
    )
    (root / "src" / "alpamayo1_5" / "load_physical_aiavdataset.py").write_text(
        "\n".join(
            [
                "def load_physical_aiavdataset(",
                "    num_history_steps: int = 16,",
                "    num_future_steps: int = 64,",
                "    time_step: float = 0.1,",
                "    num_frames: int = 4,",
                "):",
                "    camera_features = [",
                "        avdi.features.CAMERA.CAMERA_CROSS_LEFT_120FOV,",
                "        avdi.features.CAMERA.CAMERA_FRONT_WIDE_120FOV,",
                "        avdi.features.CAMERA.CAMERA_CROSS_RIGHT_120FOV,",
                "        avdi.features.CAMERA.CAMERA_FRONT_TELE_30FOV,",
                "    ]",
            ]
        ),
        encoding="utf-8",
    )
    (root / "src" / "alpamayo1_5" / "helper.py").write_text(
        "\n".join(
            [
                "CAMERA_DISPLAY_NAMES = {",
                "0: 'Front left camera',",
                "1: 'Front camera',",
                "2: 'Front right camera',",
                "6: 'Front telephoto camera',",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    (root / "src" / "alpamayo1_5" / "models" / "alpamayo1_5.py").write_text(
        "\n".join(
            [
                "def sample_trajectories_from_data_with_vlm_rollout(self): pass",
                "def sample_trajectories_from_data_with_vlm_rollout_cfg_nav(self): pass",
            ]
        ),
        encoding="utf-8",
    )
    (root / "src" / "alpamayo1_5" / "models" / "base_model.py").write_text(
        "def generate_text(self): pass",
        encoding="utf-8",
    )
    (root / "src" / "alpamayo1_5" / "test_inference.py").write_text(
        "print(extra[\"cot\"])",
        encoding="utf-8",
    )


class AlpamayoReleaseTest(unittest.TestCase):
    def test_inspector_extracts_release_contract_without_importing_model(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_release_fixture(root)

            contract = inspect_alpamayo_release(root)
            payload = contract.to_jsonable()

        self.assertTrue(payload["source_available"])
        self.assertEqual(payload["environment"]["python"], "3.12")
        self.assertEqual(payload["environment"]["cuda_toolkit"], "12.x")
        self.assertEqual(payload["hardware_requirements"][0]["vram_gb"], 24)
        self.assertEqual(payload["camera_contract"]["default_camera_indices"], [0, 1, 2, 6])
        self.assertEqual(payload["camera_contract"]["num_frames_per_camera"], 4)
        self.assertEqual(payload["input_contract"]["ego_history_xyz"]["shape"], "1 x 1 x 16 x 3")
        self.assertEqual(payload["output_contract"]["native_pred_xyz"]["shape"], "B x num_traj_sets x num_traj_samples x 64 x 3")
        self.assertEqual(payload["output_contract"]["driverx_policy_target"]["shape"], "20 x 2")
        self.assertTrue(payload["inference_methods"][0]["supports_navigation"])

    def test_missing_checkout_is_safe_and_actionable(self) -> None:
        with TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            payload = inspect_alpamayo_release(missing).to_jsonable()

        self.assertFalse(payload["source_available"])
        self.assertIn("Missing Alpamayo release checkout", payload["blockers"][0])

    def test_report_writer_and_cli_emit_contract_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "alpamayo"
            repo.mkdir()
            _write_release_fixture(repo)

            summary = write_alpamayo_release_contract(tmp_path / "direct", release_root=repo)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "inspect-alpamayo-release",
                        "--repo",
                        str(repo),
                        "--output-root",
                        str(tmp_path),
                        "--run-id",
                        "cli-contract",
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
        self.assertEqual(cli_summary["output_contract"]["driverx_policy_target"]["rate_hz"], 4)


if __name__ == "__main__":
    unittest.main()
