import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from driverx.cli import main
from driverx.simulators.carla_control import CarlaControlResult


class CarlaControlCliTest(unittest.TestCase):
    def test_driverx_control_carla_writes_report(self) -> None:
        with TemporaryDirectory() as tmp:
            screenshot = Path(tmp) / "proof.png"
            screenshot.write_bytes(b"fake")
            fake_result = CarlaControlResult(
                connected=True,
                host="127.0.0.1",
                port=2000,
                status="passed",
                requested_map="Town03_Opt",
                map_before="Carla/Maps/Town10HD_Opt",
                map_after="Carla/Maps/Town03_Opt",
                available_maps=["/Game/Carla/Maps/Town03_Opt"],
                weather_preset_name="night_rain_fog",
                screenshot_path=str(screenshot),
                spawned_actor_ids=[1],
                destroyed_actor_ids=[1],
            )
            stream = StringIO()
            with patch(
                "driverx.simulators.carla_control_cli.control_carla_world",
                return_value=fake_result,
            ), redirect_stdout(stream):
                exit_code = main(
                    [
                        "control-carla",
                        "--town",
                        "Town03",
                        "--load-map",
                        "--weather-preset",
                        "night_rain_fog",
                        "--capture",
                        "--spawn-index",
                        "7",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "control",
                    ]
                )
            result = json.loads(stream.getvalue())
            json_exists = Path(result["json_path"]).exists()
            report_exists = Path(result["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["requested_map"], "Town03_Opt")
        self.assertEqual(result["map_after"], "Carla/Maps/Town03_Opt")
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)


if __name__ == "__main__":
    unittest.main()
