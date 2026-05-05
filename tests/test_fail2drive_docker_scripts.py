from pathlib import Path
import unittest

from driverx.core.config import read_config_mapping


class Fail2DriveDockerScriptsTest(unittest.TestCase):
    def test_docker_config_targets_container_mounts_and_host_carla(self) -> None:
        config = read_config_mapping(Path("configs/fail2drive_docker.local.yaml"))

        self.assertEqual(config["carla"]["host"], "host.docker.internal")
        self.assertEqual(config["fail2drive"]["root"], "/workspace/fail2drive")
        self.assertIn("viz_path_agent.py", config["fail2drive"]["agent_path"])
        self.assertIn("/workspace/0xDriver", config["fail2drive"]["output_dir"])

    def test_run_script_mounts_repo_and_external_fail2drive(self) -> None:
        script = Path("scripts/run_fail2drive_client_docker.sh").read_text(encoding="utf-8")

        self.assertIn("/workspace/0xDriver", script)
        self.assertIn("/workspace/fail2drive", script)
        self.assertIn("FAIL2DRIVE_ROOT", script)
        self.assertIn("host.docker.internal", Path("configs/fail2drive_docker.local.yaml").read_text(encoding="utf-8"))

    def test_dockerfile_keeps_torch_optional(self) -> None:
        dockerfile = Path("docker/fail2drive-client.Dockerfile").read_text(encoding="utf-8")

        self.assertIn("ARG INSTALL_TORCH=0", dockerfile)
        self.assertIn("carla==${CARLA_PYTHON_VERSION}", dockerfile)
        self.assertIn("torch==2.5.0", dockerfile)


if __name__ == "__main__":
    unittest.main()
