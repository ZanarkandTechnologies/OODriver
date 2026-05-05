import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.remote import (
    extract_runpod_pods,
    format_runpod_shell_exports,
    select_runpod_ssh_target,
)


ROOT = Path(__file__).resolve().parents[1]


class RunPodRemoteTest(unittest.TestCase):
    def test_rest_payload_selects_current_direct_tcp_mapping(self) -> None:
        pods = extract_runpod_pods(_rest_payload())

        target = select_runpod_ssh_target(
            pods,
            key_file=Path("~/.ssh/id_ed25519_runpod"),
        )

        expected_key = str(Path("~/.ssh/id_ed25519_runpod").expanduser())
        self.assertEqual(target.gpu_ssh_host, "root@195.26.233.80")
        self.assertEqual(target.gpu_ssh_opts, f"-p 55050 -i {expected_key}")
        self.assertEqual(target.source, "rest_port_mappings")
        self.assertIn("GPU_SSH_HOST", format_runpod_shell_exports(target))

    def test_graphql_payload_selects_runtime_port_mapping(self) -> None:
        pods = extract_runpod_pods(
            {
                "data": {
                    "myself": {
                        "pods": [
                            {
                                "id": "abc",
                                "name": "gpu",
                                "desiredStatus": "RUNNING",
                                "runtime": {
                                    "ports": [
                                        {
                                            "ip": "38.80.152.148",
                                            "isIpPublic": True,
                                            "privatePort": 22,
                                            "publicPort": 31257,
                                            "type": "tcp",
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            }
        )

        target = select_runpod_ssh_target(pods, key_file=Path("/tmp/key"))

        self.assertEqual(target.gpu_ssh_host, "root@38.80.152.148")
        self.assertEqual(target.gpu_ssh_opts, "-p 31257 -i /tmp/key")
        self.assertEqual(target.source, "runtime_ports")

    def test_missing_ssh_mapping_fails_clearly(self) -> None:
        pods = extract_runpod_pods([{"id": "abc", "desiredStatus": "RUNNING"}])

        with self.assertRaisesRegex(ValueError, "exposes SSH"):
            select_runpod_ssh_target(pods)

    def test_cli_writes_resolution_from_fixture_payload(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pods_json = tmp_path / "pods.json"
            output_root = tmp_path / "runs"
            pods_json.write_text(json.dumps(_rest_payload()), encoding="utf-8")
            env = os.environ.copy()
            env["PYTHONPATH"] = "src"

            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "driverx",
                    "resolve-runpod-ssh",
                    "--pods-json",
                    str(pods_json),
                    "--ssh-key",
                    "/tmp/runpod-key",
                    "--output-root",
                    str(output_root),
                    "--run-id",
                    "resolver",
                ],
                cwd=ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["target"]["gpu_ssh_opts"], "-p 55050 -i /tmp/runpod-key")
            self.assertTrue((output_root / "resolver" / "runpod_ssh_resolution.md").exists())


def _rest_payload() -> list[dict[str, object]]:
    return [
        {
            "id": "zqqmn9ryopmmro",
            "name": "thundering_apricot_locust",
            "desiredStatus": "RUNNING",
            "imageName": "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
            "gpuCount": 1,
            "memoryInGb": 62,
            "vcpuCount": 16,
            "containerDiskInGb": 20,
            "volumeInGb": 200,
            "publicIp": "195.26.233.80",
            "portMappings": {"22": 55050},
        }
    ]


if __name__ == "__main__":
    unittest.main()
