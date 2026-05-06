import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.simulators.carla_cached_ood_replay import (
    CachedOodReplayConfig,
    run_cached_ood_replay,
    write_cached_ood_replay,
)


def _write_decision(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "policy_decision": {
                    "policy_id": "alpamayo-live",
                    "action": {
                        "trajectory": {
                            "points_xy": [[float(i + 1), 0.1 * i] for i in range(20)],
                            "source": "alpamayo_live_open_loop",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )


class CarlaCachedOodReplayTest(unittest.TestCase):
    def test_cached_replay_writes_control_trace_and_synthetic_tracks(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = root / "decision.json"
            _write_decision(decision)

            result = run_cached_ood_replay(
                CachedOodReplayConfig(decision_path=decision),
                root / "run",
            )
            summary = write_cached_ood_replay(root / "run", result)
            tracks = json.loads(Path(summary["tracks_path"]).read_text(encoding="utf-8"))

        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["source_policy_id"], "alpamayo-live")
        self.assertEqual(summary["command_count"], 20)
        self.assertEqual(summary["applied_count"], 20)
        self.assertEqual(summary["closed_loop_control"], "cached_replay")
        self.assertIn("real_time_vla_control=false", summary["claim_boundaries"])
        self.assertEqual(len(tracks), 20)

    def test_cached_replay_cli_accepts_decision_override(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = root / "decision.json"
            config = root / "config.yaml"
            _write_decision(decision)
            config.write_text(
                "cached_ood_replay:\n"
                "  decision_path: ignored.json\n"
                "  live: false\n",
                encoding="utf-8",
            )
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "run-cached-ood-replay",
                        "--config",
                        str(config),
                        "--decision",
                        str(decision),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "cached",
                    ]
            )
            summary = json.loads(stream.getvalue())
            json_exists = Path(summary["json_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(json_exists)
        self.assertEqual(summary["command_count"], 20)


if __name__ == "__main__":
    unittest.main()
