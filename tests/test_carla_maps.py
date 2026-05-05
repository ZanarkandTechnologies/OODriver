import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

from driverx.simulators.carla_maps import (
    CarlaMapProbeConfig,
    CarlaMapsInstallConfig,
    default_additional_maps_url,
    discover_carla_install_candidates,
    install_carla_additional_maps,
    load_carla_map_probe_config,
    probe_carla_map_inventory,
    write_carla_maps_report,
)


class _FakeMap:
    def __init__(self, name: str) -> None:
        self.name = name


class _FakeWorld:
    def __init__(self, name: str) -> None:
        self._name = name

    def get_map(self) -> _FakeMap:
        return _FakeMap(self._name)


class _FakeClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.timeout_s = 0.0
        self.current_map = "Carla/Maps/Town10HD_Opt"

    def set_timeout(self, timeout_s: float) -> None:
        self.timeout_s = timeout_s

    def get_world(self) -> _FakeWorld:
        return _FakeWorld(self.current_map)

    def get_available_maps(self) -> list[str]:
        return [
            "/Game/Carla/Maps/Town10HD_Opt",
            "/Game/Carla/Maps/Town13",
        ]

    def load_world(self, map_name: str) -> _FakeWorld:
        if map_name != "Town13":
            raise RuntimeError(f"map not found: {map_name}")
        self.current_map = "Carla/Maps/Town13"
        return _FakeWorld(self.current_map)

    def get_server_version(self) -> str:
        return "0.9.16"

    def get_client_version(self) -> str:
        return "0.9.16"


def _write_fake_root(path: Path) -> None:
    path.mkdir(parents=True)
    (path / "CarlaUE4.exe").write_text("fake exe\n", encoding="utf-8")
    (path / "PythonAPI" / "carla").mkdir(parents=True)


def _write_fake_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("CarlaUE4/Content/Carla/Maps/Town13/Town13.umap", "fake map")
        archive.writestr("Import/AdditionalMaps_0.9.16/manifest.txt", "fake import")


class CarlaMapsTest(unittest.TestCase):
    def test_default_url_uses_official_0916_backblaze_asset(self) -> None:
        self.assertEqual(
            default_additional_maps_url("0.9.16", "windows"),
            "https://carla-releases.s3.us-east-005.backblazeb2.com/"
            "Windows/AdditionalMaps_0.9.16.zip",
        )

    def test_discover_carla_install_candidates_finds_fake_windows_root(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "CARLA_0.9.16"
            _write_fake_root(root)

            candidates = discover_carla_install_candidates([root])

        self.assertTrue(candidates)
        self.assertEqual(candidates[0].path, root)
        self.assertEqual(candidates[0].platform, "windows")
        self.assertGreaterEqual(candidates[0].confidence, 50)

    def test_dry_run_install_reports_url_root_and_disk_without_extracting(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "CARLA_0.9.16"
            _write_fake_root(root)
            config = CarlaMapsInstallConfig(
                carla_root=root,
                package_cache_dir=Path(tmp) / "cache",
                dry_run=True,
                required_free_bytes=1,
            )

            result = install_carla_additional_maps(config)

        self.assertEqual(result.status, "dry_run")
        self.assertEqual(result.carla_root, root.resolve())
        self.assertIn("AdditionalMaps_0.9.16.zip", str(result.package_path))
        self.assertEqual(result.extracted_count, 0)

    def test_install_extracts_fake_archive_and_finds_town_marker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "CARLA_0.9.16"
            _write_fake_root(root)
            package_path = Path(tmp) / "AdditionalMaps_0.9.16.zip"
            _write_fake_zip(package_path)
            config = CarlaMapsInstallConfig(
                carla_root=root,
                package_path=package_path,
                dry_run=False,
                required_free_bytes=1,
            )

            result = install_carla_additional_maps(config)

        self.assertEqual(result.status, "installed")
        self.assertEqual(result.extracted_count, 2)
        self.assertTrue(result.map_markers["Town13"])

    def test_probe_carla_map_inventory_loads_desired_map_with_fake_client(self) -> None:
        result = probe_carla_map_inventory(
            CarlaMapProbeConfig(host="host.docker.internal", port=2000),
            client_factory=_FakeClient,
        )

        self.assertTrue(result.connected)
        self.assertEqual(result.current_map, "Carla/Maps/Town10HD_Opt")
        self.assertTrue(result.load_attempts[0].success)
        self.assertEqual(result.load_attempts[0].loaded_map, "Carla/Maps/Town13")

    def test_write_reports_json_and_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            result = probe_carla_map_inventory(
                CarlaMapProbeConfig(host="host.docker.internal", port=2000),
                client_factory=_FakeClient,
            )
            summary = write_carla_maps_report(Path(tmp), result)
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))
            report_exists = Path(summary["report_path"]).exists()

        self.assertTrue(report_exists)
        self.assertEqual(payload["load_attempts"][0]["map_name"], "Town13")

    def test_load_config_parses_comma_separated_maps_and_paths(self) -> None:
        with TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "carla_maps.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "carla_maps:",
                        "  desired_maps: Town13,Town12",
                        "  search_paths: ~/CARLA_0.9.16,/opt/carla",
                        "  host: host.docker.internal",
                        "  port: 2000",
                    ]
                ),
                encoding="utf-8",
            )

            config = load_carla_map_probe_config(config_path)

        self.assertEqual(config.desired_maps, ("Town13", "Town12"))
        self.assertEqual(config.host, "host.docker.internal")


if __name__ == "__main__":
    unittest.main()
