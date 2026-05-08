from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from driverx.policies.alpamayo_inference_bridge import run_alpamayo_inference_bridge
from driverx.remote.alpamayo_handoff import build_alpamayo_handoff_manifest, package_cache_key


class AlpamayoHandoffTests(unittest.TestCase):
    def test_cache_key_is_stable_for_same_package(self) -> None:
        with TemporaryDirectory() as tmp:
            package = Path(tmp) / "package.json"
            package.write_text(json.dumps({"frames": [1, 2, 3]}), encoding="utf-8")

            self.assertEqual(package_cache_key(package), package_cache_key(package))

    def test_remote_handoff_manifest_is_secret_safe(self) -> None:
        with TemporaryDirectory() as tmp:
            package = Path(tmp) / "package.json"
            package.write_text("{}", encoding="utf-8")

            manifest = build_alpamayo_handoff_manifest(package, Path("/workspace/out"))

            payload = manifest.to_jsonable()
            self.assertTrue(payload["safe_for_kasm_proxy"])
            self.assertNotIn("token", json.dumps(payload).lower())

    def test_fake_inference_writes_prediction_and_cache(self) -> None:
        with TemporaryDirectory() as tmp:
            package = Path(tmp) / "package.json"
            package.write_text("{}", encoding="utf-8")
            cache_root = Path(tmp) / "cache"

            first = run_alpamayo_inference_bridge(
                package_path=package,
                mode="fake",
                output_root=Path(tmp),
                run_id="infer",
                cache_root=cache_root,
            )
            second = run_alpamayo_inference_bridge(
                package_path=package,
                mode="fake",
                output_root=Path(tmp),
                run_id="infer2",
                cache_root=cache_root,
            )

            self.assertEqual(first.status, "passed")
            self.assertEqual(second.status, "cached")
            self.assertTrue(Path(first.prediction_json_path or "").exists())

    def test_cached_json_mode_copies_prediction(self) -> None:
        with TemporaryDirectory() as tmp:
            package = Path(tmp) / "package.json"
            prediction = Path(tmp) / "prediction.json"
            package.write_text("{}", encoding="utf-8")
            prediction.write_text(json.dumps({"cot": "stop for obstacle", "pred_xyz_shape": [1, 1, 1, 20, 3]}), encoding="utf-8")

            result = run_alpamayo_inference_bridge(
                package_path=package,
                mode="cached-json",
                output_root=Path(tmp),
                run_id="cached",
                prediction_json=prediction,
            )

            self.assertEqual(result.status, "passed")
            self.assertTrue(Path(result.prediction_json_path or "").exists())

    def test_remote_kasm_command_executes_and_caches_prediction(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package.json"
            script = root / "write_prediction.py"
            cache_root = root / "cache"
            package.write_text(json.dumps({"frames": [1]}), encoding="utf-8")
            script.write_text(
                "\n".join(
                    [
                        "import argparse, json",
                        "parser = argparse.ArgumentParser()",
                        "parser.add_argument('--package')",
                        "parser.add_argument('--output')",
                        "args = parser.parse_args()",
                        "payload = {",
                        "  'cot': 'remote Kasm command says slow and stop',",
                        "  'latency_ms': 33.0,",
                        "  'vram_peak_mb': 44.0,",
                        "  'pred_xyz_shape': [1, 1, 1, 20, 3],",
                        "  'policy_decision': {'policy_id': 'alpamayo-remote', 'action': {'trajectory': {'points_xy': [[0.2 * i, 0.0] for i in range(20)], 'source': 'remote-kasm', 'score': 0.9}}}",
                        "}",
                        "open(args.output, 'w', encoding='utf-8').write(json.dumps(payload))",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_alpamayo_inference_bridge(
                package_path=package,
                mode="remote-kasm",
                output_root=root,
                run_id="remote",
                cache_root=cache_root,
                alpamayo_command=f"{sys.executable} {script} --package {{package}} --output {{output}}",
            )
            cached = run_alpamayo_inference_bridge(
                package_path=package,
                mode="remote-kasm",
                output_root=root,
                run_id="remote2",
                cache_root=cache_root,
            )

            self.assertEqual(result.status, "passed")
            self.assertEqual(cached.status, "cached")
            self.assertEqual(result.reasoning_snippet, "remote Kasm command says slow and stop")
            self.assertEqual(result.vram_peak_mb, 44.0)


if __name__ == "__main__":
    unittest.main()
