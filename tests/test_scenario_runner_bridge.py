from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.scenarios.scenario_runner_bridge import build_scenario_runner_package, run_scenario_runner_package


OSC2_FIXTURE = Path("tests/fixtures/osc2/static_blocker.osc")
SIDECAR_FIXTURE = Path("tests/fixtures/osc2/static_blocker_sidecar.json")


class ScenarioRunnerBridgeTests(unittest.TestCase):
    def test_package_agent_authored_osc2(self) -> None:
        with TemporaryDirectory() as tmp:
            package = build_scenario_runner_package(
                scenario_graph_path=None,
                osc2_path=OSC2_FIXTURE,
                sidecar_path=SIDECAR_FIXTURE,
                output_root=Path(tmp),
                run_id="package",
            )

            payload = json.loads(Path(package.package_manifest_path).read_text(encoding="utf-8"))
            self.assertEqual(package.status, "passed")
            self.assertEqual(payload["scenario_runner_entrypoint"], "osc2")
            self.assertTrue(Path(payload["files"]["osc2"]).exists())
            self.assertTrue(Path(payload["files"]["sidecar"]).exists())

    def test_package_blocks_without_entrypoint(self) -> None:
        with TemporaryDirectory() as tmp:
            package = build_scenario_runner_package(
                scenario_graph_path=None,
                osc2_path=None,
                sidecar_path=None,
                output_root=Path(tmp),
                run_id="package",
            )

            self.assertEqual(package.status, "blocked")
            self.assertTrue(package.blockers)

    def test_run_blocks_when_scenario_runner_missing(self) -> None:
        with TemporaryDirectory() as tmp:
            package = build_scenario_runner_package(
                scenario_graph_path=None,
                osc2_path=OSC2_FIXTURE,
                sidecar_path=None,
                output_root=Path(tmp),
                run_id="package",
            )
            result = run_scenario_runner_package(
                Path(package.package_manifest_path),
                scenario_runner_root=Path(tmp) / "missing",
                output_root=Path(tmp),
                run_id="run",
            )

            self.assertEqual(result.status, "blocked")
            self.assertTrue(any("ScenarioRunner" in blocker for blocker in result.blockers))


if __name__ == "__main__":
    unittest.main()
