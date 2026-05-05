from pathlib import Path
import subprocess
import unittest


class AlpamayoRemoteBootstrapScriptTest(unittest.TestCase):
    def test_script_is_secret_safe_and_configurable(self) -> None:
        script = Path("scripts/bootstrap_remote_alpamayo_release.sh").read_text(encoding="utf-8")

        self.assertIn("GPU_SSH_OPTS", script)
        self.assertIn("DRIVERX_ENV_FILE", script)
        self.assertIn("ALPAMAYO_REMOTE_ROOT", script)
        self.assertIn("ALPAMAYO_SYNC_MODE", script)
        self.assertIn("ALPAMAYO_RUN_TEST", script)
        self.assertIn("--no-install-package flash-attn", script)
        self.assertIn("nvcc is required", script)
        self.assertIn("/tmp/driverx_hf_token", script)
        self.assertIn("REMOTE_CACHE_ROOT", script)
        self.assertIn("uv python install", script)
        self.assertNotIn("set -x", script)
        self.assertNotIn("echo \"$HF_TOKEN", script)

    def test_script_has_valid_bash_syntax(self) -> None:
        completed = subprocess.run(
            ["bash", "-n", "scripts/bootstrap_remote_alpamayo_release.sh"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_probe_script_has_valid_bash_syntax_and_tar_fallback(self) -> None:
        script = Path("scripts/run_remote_alpamayo_probe.sh").read_text(encoding="utf-8")

        self.assertIn("REMOTE_CACHE_ROOT", script)
        self.assertIn("falling back to ssh tar stream", script)
        self.assertIn("HF_HUB_CACHE", script)
        self.assertIn("rsync", script)
        self.assertIn("ALPAMAYO_ATTN_IMPLEMENTATION", script)
        self.assertIn("attn_implementation", script)
        completed = subprocess.run(
            ["bash", "-n", "scripts/run_remote_alpamayo_probe.sh"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
