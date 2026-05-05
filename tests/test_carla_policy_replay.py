import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.simulators import (
    CarlaPolicyReplayConfig,
    replay_policy_decision,
    write_carla_policy_replay,
)


class _FakeActor:
    def __init__(self) -> None:
        self.controls: list[dict[str, float]] = []

    def apply_control(self, control: dict[str, float]) -> None:
        self.controls.append(control)


def _write_decision(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "policy_decision": {
                    "policy_id": "alpamayo-live",
                    "action": {
                        "trajectory": {
                            "points_xy": [(float(i + 1), 0.0) for i in range(20)],
                            "source": "alpamayo_live_open_loop",
                            "score": 0.0,
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )


class CarlaPolicyReplayTest(unittest.TestCase):
    def test_replay_policy_decision_can_apply_to_fake_actor(self) -> None:
        with TemporaryDirectory() as tmp:
            decision = Path(tmp) / "decision.json"
            _write_decision(decision)
            actor = _FakeActor()

            result = replay_policy_decision(
                CarlaPolicyReplayConfig(decision_path=decision, apply_to_actor=True),
                actor=actor,
            )

        self.assertEqual(result.source_policy_id, "alpamayo-live")
        self.assertEqual(result.command_count, 20)
        self.assertEqual(result.applied_count, 20)
        self.assertEqual(len(actor.controls), 20)
        self.assertEqual(result.closed_loop_control, "cached_replay")

    def test_write_replay_outputs_json_and_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            decision = tmp_path / "decision.json"
            _write_decision(decision)
            result = replay_policy_decision(CarlaPolicyReplayConfig(decision_path=decision))
            summary = write_carla_policy_replay(tmp_path / "run", result)
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))
            report_exists = Path(summary["report_path"]).exists()

        self.assertEqual(payload["command_count"], 20)
        self.assertTrue(report_exists)

    def test_replay_policy_decision_cli_writes_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            decision = tmp_path / "decision.json"
            _write_decision(decision)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "replay-policy-decision",
                        "--decision",
                        str(decision),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "replay",
                    ]
                )
            summary = json.loads(stream.getvalue())
            json_exists = Path(summary["json_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["command_count"], 20)
        self.assertTrue(summary["dry_run"])
        self.assertTrue(json_exists)


if __name__ == "__main__":
    unittest.main()
