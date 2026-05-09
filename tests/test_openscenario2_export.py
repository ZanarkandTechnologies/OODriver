from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.scenarios.openscenario2 import (
    run_openscenario2,
    validate_openscenario2,
    write_openscenario2_run,
    write_openscenario2_validation,
)


FIXTURE = Path("tests/fixtures/osc2/static_blocker.osc")
SIDECAR = Path("tests/fixtures/osc2/static_blocker_sidecar.json")


class OpenScenario2Tests(unittest.TestCase):
    def test_validate_agent_authored_osc2_fixture(self) -> None:
        validation = validate_openscenario2(FIXTURE, sidecar_path=SIDECAR)

        self.assertEqual(validation.status, "passed")
        self.assertGreaterEqual(validation.coverage_ratio, 0.5)
        self.assertIn("scenario declaration", validation.supported_features)
        self.assertIn("agent_authored_scenario=true", validation.claim_boundaries)

    def test_validation_blocks_wrong_suffix_and_missing_declaration(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.txt"
            path.write_text("ego: actor\n", encoding="utf-8")
            validation = validate_openscenario2(path)

            self.assertEqual(validation.status, "blocked")
            self.assertTrue(any(".osc" in blocker for blocker in validation.blockers))
            self.assertTrue(any("scenario" in blocker for blocker in validation.blockers))

    def test_run_blocks_when_scenario_runner_root_missing(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            result = run_openscenario2(
                FIXTURE,
                scenario_runner_root=Path(tmp) / "missing-scenario-runner",
                output_dir=run_dir,
            )
            paths = write_openscenario2_run(run_dir, result)
            payload = json.loads(Path(paths["json_path"]).read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "blocked")
            self.assertIn("ScenarioRunner", payload["blockers"][0])

    def test_write_validation_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            paths = write_openscenario2_validation(run_dir, validate_openscenario2(FIXTURE))

            self.assertTrue(Path(paths["json_path"]).exists())
            self.assertTrue(Path(paths["report_path"]).exists())


if __name__ == "__main__":
    unittest.main()
