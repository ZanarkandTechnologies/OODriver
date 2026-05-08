from pathlib import Path
import os
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CarlaDockerScriptsTest(unittest.TestCase):
    def test_carla_client_dockerfile_pins_carla_0916_default(self) -> None:
        dockerfile = (ROOT / "docker" / "carla-client.Dockerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("ARG CARLA_PYTHON_VERSION=0.9.16", dockerfile)
        self.assertIn('"carla==${CARLA_PYTHON_VERSION}"', dockerfile)

    def test_runner_prefers_built_image_and_supports_explicit_env_file(self) -> None:
        script = (ROOT / "scripts" / "run_carla_client_docker.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("driverx-carla-client:${CARLA_PYTHON_VERSION}", script)
        self.assertIn("DRIVERX_DOCKER_ENV_FILE", script)
        self.assertIn("python:3.10-bullseye", script)
        self.assertIn("carla==${CARLA_PYTHON_VERSION}", script)

    def test_proof_script_defaults_match_documented_artifact_contract(self) -> None:
        script = (ROOT / "scripts" / "prove_carla_0916_docker.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn('CARLA_TIMEOUT_S="${CARLA_TIMEOUT_S:-1.0}"', script)
        self.assertIn('RUN_ID="${1:-task16-proof}"', script)
        self.assertIn("git rev-parse --show-toplevel 2>/dev/null || pwd", script)

    def test_proof_script_exercises_probe_and_ego_smoke(self) -> None:
        script = (ROOT / "scripts" / "prove_carla_0916_docker.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("build_carla_client_docker.sh", script)
        self.assertIn("probe-carla", script)
        self.assertIn("spawn-ego-smoke", script)

    def test_proof_script_emits_expected_docker_contract_with_fake_docker(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "docker.log"
            fake_docker = tmp_path / "docker"
            fake_docker.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        'printf "%s\\n" "$*" >> "${FAKE_DOCKER_LOG}"',
                        'if [ "${1:-}" = "image" ] && [ "${2:-}" = "inspect" ]; then exit 0; fi',
                        'if [ "${1:-}" = "build" ] || [ "${1:-}" = "run" ]; then exit 0; fi',
                        "exit 0",
                    ]
                ),
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp_path}:{env['PATH']}"
            env["FAKE_DOCKER_LOG"] = str(log_path)
            env.pop("CARLA_CLIENT_DOCKER_IMAGE", None)
            env.pop("CARLA_TIMEOUT_S", None)
            env.pop("CARLA_TICK_COUNT", None)
            env.pop("DRIVERX_DOCKER_ENV_FILE", None)

            result = subprocess.run(
                ["bash", "scripts/prove_carla_0916_docker.sh"],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            log = log_path.read_text(encoding="utf-8")

        self.assertIn(
            "build --platform linux/amd64 --build-arg CARLA_PYTHON_VERSION=0.9.16",
            log,
        )
        self.assertIn("image inspect driverx-carla-client:0.9.16", log)
        self.assertIn("--run-id task16-proof-probe", log)
        self.assertIn("--run-id task16-proof-ego", log)
        self.assertIn("--timeout-s 1.0", log)
        self.assertIn("--tick-count 5", log)
        self.assertNotIn("--env-file", log)

    def test_remote_gpu_sync_excludes_secrets_and_heavy_assets(self) -> None:
        script = (ROOT / "scripts" / "sync_remote_gpu.sh").read_text(encoding="utf-8")

        self.assertIn("git rev-parse --show-toplevel 2>/dev/null || pwd", script)
        self.assertIn("--include='.env.example'", script)
        self.assertIn("--exclude='.env'", script)
        self.assertIn("--exclude='data/'", script)
        self.assertIn("--exclude='artifacts/'", script)
        self.assertIn("/usr/bin/python3 -m unittest discover -s tests", script)
        self.assertLess(
            script.index("--include='.env.example'"),
            script.index("--exclude='.env.*'"),
        )

    def test_remote_simlingo_bootstrap_handles_packaged_carla_layout(self) -> None:
        script = (
            ROOT / "scripts" / "archive" / "simlingo" / "remote_simlingo_bootstrap.sh"
        ).read_text(encoding="utf-8")

        self.assertIn("ensure_carla_compat_layout", script)
        self.assertIn("Binaries/Linux/CarlaUE4-Linux-Shipping", script)
        self.assertIn("LD_LIBRARY_PATH", script)
        self.assertIn("CarlaUE4 \"$@\"", script)
        self.assertIn("prepare_runtime_user", script)
        self.assertIn("run_one_route_as_user.sh", script)
        self.assertIn("start_carla_server.sh", script)
        self.assertIn("run_one_route_with_carla_as_user.sh", script)
        self.assertIn("-RenderOffScreen", script)
        self.assertIn("-carla-rpc-port=20000", script)
        self.assertIn("CARLA port 20000 is reachable", script)
        self.assertIn('export PYTHONPATH="${SIMLINGO_ROOT}:', script)
        self.assertIn('HOME="/home/${RUNTIME_USER}"', script)
        self.assertIn("safe.directory", script)
        self.assertIn("PythonAPI/carla", script)
        self.assertIn("Engine/Content", script)
        self.assertIn("tar --no-same-owner -xzf", script)
        self.assertIn("tar --no-same-owner --keep-newer-files", script)
        self.assertNotIn("--strip-components=1", script)
        self.assertIn("carla-0.9.15*py3*linux-x86_64.egg", script)
        self.assertIn("CHECKPOINT_RELATIVE_PATH", script)
        self.assertIn("simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt", script)
        self.assertIn("HF_REVISION", script)
        self.assertIn("26c7c89e797d4e25bbf640013317af8da26a5454", script)
        self.assertIn("model_revision.txt", script)
        self.assertIn("checkpoint.sha256", script)
        self.assertIn("torch_cuda_compatibility.json", script)
        self.assertIn("torch.cuda.get_arch_list()", script)
        self.assertIn('token=os.environ.get("HF_TOKEN") or None', script)
        self.assertIn('DRIVERX_PYTHON="${DRIVERX_PYTHON:-/usr/bin/python3}"', script)
        self.assertNotIn("huggingface/token", script)

    def test_remote_simlingo_launcher_uses_temporary_token_file(self) -> None:
        script = (
            ROOT
            / "scripts"
            / "archive"
            / "simlingo"
            / "run_remote_simlingo_bootstrap.sh"
        ).read_text(encoding="utf-8")

        self.assertIn("load_env_value HF_TOKEN", script)
        self.assertIn("REMOTE_TOKEN_FILE", script)
        self.assertIn("cleanup_remote_token_file", script)
        self.assertIn("trap cleanup_remote_token_file EXIT", script)
        self.assertIn("rm -f '${REMOTE_TOKEN_FILE}'", script)
        self.assertIn("tmux new-session", script)
        self.assertIn("remote_simlingo_bootstrap.sh", script)
        self.assertNotIn("/root/.cache/huggingface/token", script)

    def test_remote_simlingo_route_runner_logs_and_pulls_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "calls.log"
            fake_ssh = tmp_path / "ssh"
            fake_ssh.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        'printf "SSH:%s\\n" "$*" >> "${CALL_LOG}"',
                        "exit 23",
                    ]
                ),
                encoding="utf-8",
            )
            fake_ssh.chmod(0o755)
            fake_pull = tmp_path / "pull.sh"
            fake_pull.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        'printf "PULL:%s:%s:%s\\n" "${REMOTE_RUN_ID}" "${REMOTE_ARTIFACT_DIR}" "${LOCAL_ARTIFACT_DIR}" >> "${CALL_LOG}"',
                    ]
                ),
                encoding="utf-8",
            )
            fake_pull.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp_path}:{env['PATH']}"
            env["CALL_LOG"] = str(log_path)
            env["GPU_SSH_OPTS"] = "-p 31257 -i /tmp/fake-key"
            env["REMOTE_RUN_ID"] = "task20"
            env["PULL_REMOTE_ARTIFACTS_SCRIPT"] = str(fake_pull)

            result = subprocess.run(
                ["bash", "scripts/run_remote_simlingo_route.sh", "root@example"],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 23)
            log = log_path.read_text(encoding="utf-8")

        self.assertIn("SSH:-p 31257 -i /tmp/fake-key", log)
        self.assertIn("run_one_route_with_carla_as_user.sh", log)
        self.assertIn("run_one_route_with_carla.log", log)
        self.assertIn("tee", log)
        self.assertIn("PULL:task20:/workspace/artifacts/task20:", log)

    def test_remote_simlingo_route_runner_preserves_route_status_when_pull_fails(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_ssh = tmp_path / "ssh"
            fake_ssh.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "exit 23",
                    ]
                ),
                encoding="utf-8",
            )
            fake_ssh.chmod(0o755)
            fake_pull = tmp_path / "pull.sh"
            fake_pull.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "exit 7",
                    ]
                ),
                encoding="utf-8",
            )
            fake_pull.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp_path}:{env['PATH']}"
            env["PULL_REMOTE_ARTIFACTS_SCRIPT"] = str(fake_pull)

            result = subprocess.run(
                ["bash", "scripts/run_remote_simlingo_route.sh", "root@example"],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(result.returncode, 23)
        self.assertIn("Artifact pullback failed with status 7", result.stderr)
        self.assertIn("preserving route status 23", result.stderr)

    def test_remote_simlingo_artifact_pull_keeps_only_compact_evidence(self) -> None:
        script = (
            ROOT
            / "scripts"
            / "archive"
            / "simlingo"
            / "pull_remote_simlingo_artifacts.sh"
        ).read_text(encoding="utf-8")

        self.assertIn("REMOTE_ARTIFACT_DIR", script)
        self.assertIn("LOCAL_ARTIFACT_DIR", script)
        self.assertIn("GPU_SSH_OPTS", script)
        self.assertIn("--prune-empty-dirs", script)
        self.assertIn("--no-owner", script)
        self.assertIn("--no-group", script)
        for included in [
            "bootstrap.log",
            "torch_cuda_compatibility.json",
            "model_revision.txt",
            "checkpoint.sha256",
            "*.json",
            "*.md",
            "*.log",
            "*.sh",
        ]:
            self.assertIn(f"--include='{included}'", script)
        for excluded in [
            "*.pt",
            "*.ckpt",
            "*.safetensors",
            "*.mp4",
            "*.png",
            "viz/***",
            "models/***",
            "software/***",
            ".cache/***",
        ]:
            self.assertIn(f"--exclude='{excluded}'", script)

    def test_remote_gpu_probe_collects_compact_host_suitability_inputs(self) -> None:
        script = (ROOT / "scripts" / "run_remote_gpu_probe.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("REMOTE_PROBE_DIR", script)
        self.assertIn("gpu_snapshot.txt", script)
        self.assertIn("torch_cuda_compatibility.json", script)
        self.assertIn("carla_runtime_diagnostics.md", script)
        self.assertIn("torch.cuda.get_arch_list()", script)
        self.assertIn("torch.cuda.get_device_capability(0)", script)
        self.assertIn("vulkaninfo --summary", script)
        self.assertIn("VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json", script)
        self.assertIn("--include='gpu_snapshot.txt'", script)
        self.assertIn("--include='torch_cuda_compatibility.json'", script)
        self.assertIn("--include='carla_runtime_diagnostics.md'", script)
        self.assertIn("--exclude='*.pt'", script)
        self.assertIn("--exclude='*.safetensors'", script)
        self.assertIn("--exclude='*.mp4'", script)

    def test_remote_simlingo_artifact_pull_executes_compact_filter_contract(self) -> None:
        if shutil.which("rsync") is None:
            self.skipTest("rsync is required to exercise the pullback helper")

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "remote"
            destination = tmp_path / "local"
            for path in [
                "bootstrap.log",
                "torch_cuda_compatibility.json",
                "model_revision.txt",
                "checkpoint.sha256",
                "run_one_route_with_carla.sh",
                "res/seed_1_res.json",
                "readiness/simlingo_readiness.md",
                "plan/simlingo_command_plan.json",
                "carla/carla.log",
                "models/manifest.json",
                "software/readme.md",
                "viz/frame.json",
                "nested/viz/frame.json",
                ".cache/huggingface/token",
                "checkpoint.pt",
                "weights/model.safetensors",
                "camera.png",
                "notes.txt",
            ]:
                file_path = source / path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(path, encoding="utf-8")

            env = os.environ.copy()
            env["LOCAL_SIMLINGO_ARTIFACT_SOURCE"] = str(source)
            result = subprocess.run(
                [
                    "bash",
                    "scripts/pull_remote_simlingo_artifacts.sh",
                    "unused-host",
                    "/unused/remote",
                    str(destination),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            copied = {
                str(path.relative_to(destination))
                for path in destination.rglob("*")
                if path.is_file()
            }

        self.assertEqual(
            copied,
            {
                "bootstrap.log",
                "torch_cuda_compatibility.json",
                "model_revision.txt",
                "checkpoint.sha256",
                "run_one_route_with_carla.sh",
                "res/seed_1_res.json",
                "readiness/simlingo_readiness.md",
                "plan/simlingo_command_plan.json",
            },
        )

    def test_remote_simlingo_launcher_cleans_token_when_launch_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "ssh.log"
            count_path = tmp_path / "ssh.count"
            fake_ssh = tmp_path / "ssh"
            fake_ssh.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        'count_file="${FAKE_SSH_COUNT}"',
                        'count=0',
                        'if [ -f "${count_file}" ]; then count="$(cat "${count_file}")"; fi',
                        'count=$((count + 1))',
                        'printf "%s" "${count}" > "${count_file}"',
                        'printf "CALL:%s:%s\\n" "${count}" "$*" >> "${FAKE_SSH_LOG}"',
                        'if [ "${count}" = "1" ]; then cat >/dev/null; exit 0; fi',
                        'if [ "${count}" = "2" ]; then exit 42; fi',
                        'exit 0',
                    ]
                ),
                encoding="utf-8",
            )
            fake_ssh.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp_path}:{env['PATH']}"
            env["HF_TOKEN"] = "fake-token"
            env["FAKE_SSH_LOG"] = str(log_path)
            env["FAKE_SSH_COUNT"] = str(count_path)
            result = subprocess.run(
                [
                    "bash",
                    "scripts/run_remote_simlingo_bootstrap.sh",
                    "fake-host",
                    "/workspace/0xDriver",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 42)
            log = log_path.read_text(encoding="utf-8")

        self.assertIn("CALL:1:", log)
        self.assertIn("CALL:2:", log)
        self.assertIn("CALL:3:", log)
        self.assertIn("cat > '/tmp/driverx_hf_token_task20_", log)
        self.assertIn("tmux new-session", log)
        self.assertIn("rm -f '/tmp/driverx_hf_token_task20_", log)


if __name__ == "__main__":
    unittest.main()
