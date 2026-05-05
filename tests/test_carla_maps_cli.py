import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from driverx.cli import main
from driverx.simulators import (
    CarlaMapInventory,
    CarlaMapLoadAttempt,
    CarlaMapsInstallResult,
)


class CarlaMapsCliTest(unittest.TestCase):
    def test_install_carla_additional_maps_cli_writes_install_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            with patch(
                "driverx.simulators.carla_maps_cli.install_carla_additional_maps",
                return_value=CarlaMapsInstallResult(
                    status="dry_run",
                    dry_run=True,
                    version="0.9.16",
                    platform="windows",
                    carla_root=Path(tmp) / "CARLA_0.9.16",
                    package_url="https://example.test/AdditionalMaps_0.9.16.zip",
                    package_path=Path(tmp) / "AdditionalMaps_0.9.16.zip",
                    package_size_bytes=None,
                    disk_free_bytes=123,
                    required_free_bytes=1,
                    desired_maps=("Town13",),
                    candidates=(),
                    archive_members_sample=(),
                    extracted_count=0,
                    map_markers={"Town13": []},
                    blockers=(),
                ),
            ), redirect_stdout(stream):
                exit_code = main(
                    [
                        "install-carla-additional-maps",
                        "--config",
                        "configs/carla_maps.local.sample.yaml",
                        "--dry-run",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "maps",
                    ]
                )
            result = json.loads(stream.getvalue())
            json_exists = Path(result["json_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "dry_run")
        self.assertTrue(json_exists)

    def test_probe_carla_maps_cli_writes_inventory_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            stream = StringIO()
            with patch(
                "driverx.simulators.carla_maps_cli.probe_carla_map_inventory",
                return_value=CarlaMapInventory(
                    connected=True,
                    host="host.docker.internal",
                    port=2000,
                    server_version="0.9.16",
                    client_version="0.9.16",
                    current_map="Carla/Maps/Town10HD_Opt",
                    available_maps=("/Game/Carla/Maps/Town13",),
                    load_attempts=(
                        CarlaMapLoadAttempt(
                            map_name="Town13",
                            success=True,
                            loaded_map="Carla/Maps/Town13",
                        ),
                    ),
                ),
            ), redirect_stdout(stream):
                exit_code = main(
                    [
                        "probe-carla-maps",
                        "--config",
                        "configs/carla_maps.local.sample.yaml",
                        "--host",
                        "host.docker.internal",
                        "--port",
                        "2000",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "maps-probe",
                    ]
                )
            result = json.loads(stream.getvalue())
            report_exists = Path(result["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["connected"])
        self.assertTrue(result["load_attempts"][0]["success"])
        self.assertTrue(report_exists)


if __name__ == "__main__":
    unittest.main()
