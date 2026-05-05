"""RunPod metadata helpers for volatile direct TCP SSH mappings."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_RUNPOD_REST_API = "https://rest.runpod.io/v1/pods"


@dataclass(frozen=True)
class RunPodPort:
    ip: str
    private_port: int
    public_port: int
    port_type: str
    is_ip_public: bool

    @classmethod
    def from_jsonable(cls, payload: dict[str, Any]) -> "RunPodPort":
        return cls(
            ip=str(payload.get("ip", "")),
            private_port=int(payload.get("privatePort", payload.get("private_port", 0))),
            public_port=int(payload.get("publicPort", payload.get("public_port", 0))),
            port_type=str(payload.get("type", payload.get("port_type", ""))),
            is_ip_public=bool(payload.get("isIpPublic", payload.get("is_ip_public", False))),
        )

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "ip": self.ip,
            "private_port": self.private_port,
            "public_port": self.public_port,
            "type": self.port_type,
            "is_ip_public": self.is_ip_public,
        }


@dataclass(frozen=True)
class RunPodPod:
    pod_id: str
    name: str
    desired_status: str
    public_ip: str | None
    port_mappings: dict[str, int]
    runtime_ports: tuple[RunPodPort, ...]
    image_name: str | None = None
    gpu_count: int | None = None
    memory_in_gb: int | None = None
    vcpu_count: int | None = None
    container_disk_in_gb: int | None = None
    volume_in_gb: int | None = None

    @classmethod
    def from_rest_jsonable(cls, payload: dict[str, Any]) -> "RunPodPod":
        raw_mappings = payload.get("portMappings", payload.get("port_mappings", {})) or {}
        port_mappings: dict[str, int] = {}
        if isinstance(raw_mappings, dict):
            for key, value in raw_mappings.items():
                try:
                    port_mappings[str(key)] = int(value)
                except (TypeError, ValueError):
                    continue
        return cls(
            pod_id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            desired_status=str(payload.get("desiredStatus", payload.get("desired_status", ""))),
            public_ip=_optional_str(payload.get("publicIp", payload.get("public_ip"))),
            port_mappings=port_mappings,
            runtime_ports=tuple(
                RunPodPort.from_jsonable(dict(port))
                for port in list(payload.get("runtimePorts", payload.get("runtime_ports", [])) or [])
            ),
            image_name=_optional_str(payload.get("imageName", payload.get("image_name"))),
            gpu_count=_optional_int(payload.get("gpuCount", payload.get("gpu_count"))),
            memory_in_gb=_optional_int(payload.get("memoryInGb", payload.get("memory_in_gb"))),
            vcpu_count=_optional_int(payload.get("vcpuCount", payload.get("vcpu_count"))),
            container_disk_in_gb=_optional_int(
                payload.get("containerDiskInGb", payload.get("container_disk_in_gb"))
            ),
            volume_in_gb=_optional_int(payload.get("volumeInGb", payload.get("volume_in_gb"))),
        )

    @classmethod
    def from_graphql_jsonable(cls, payload: dict[str, Any]) -> "RunPodPod":
        runtime = dict(payload.get("runtime") or {})
        return cls(
            pod_id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            desired_status=str(payload.get("desiredStatus", payload.get("desired_status", ""))),
            public_ip=None,
            port_mappings={},
            runtime_ports=tuple(
                RunPodPort.from_jsonable(dict(port))
                for port in list(runtime.get("ports") or [])
            ),
            image_name=_optional_str(payload.get("imageName", payload.get("image_name"))),
            gpu_count=_optional_int(payload.get("gpuCount", payload.get("gpu_count"))),
            memory_in_gb=_optional_int(payload.get("memoryInGb", payload.get("memory_in_gb"))),
            vcpu_count=_optional_int(payload.get("vcpuCount", payload.get("vcpu_count"))),
            container_disk_in_gb=_optional_int(
                payload.get("containerDiskInGb", payload.get("container_disk_in_gb"))
            ),
            volume_in_gb=_optional_int(payload.get("volumeInGb", payload.get("volume_in_gb"))),
        )

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "id": self.pod_id,
            "name": self.name,
            "desired_status": self.desired_status,
            "public_ip": self.public_ip,
            "port_mappings": self.port_mappings,
            "runtime_ports": [port.to_jsonable() for port in self.runtime_ports],
            "image_name": self.image_name,
            "gpu_count": self.gpu_count,
            "memory_in_gb": self.memory_in_gb,
            "vcpu_count": self.vcpu_count,
            "container_disk_in_gb": self.container_disk_in_gb,
            "volume_in_gb": self.volume_in_gb,
        }


@dataclass(frozen=True)
class RunPodSshTarget:
    pod_id: str
    pod_name: str
    host: str
    port: int
    user: str
    key_file: Path
    source: str
    warnings: tuple[str, ...] = ()

    @property
    def gpu_ssh_host(self) -> str:
        return f"{self.user}@{self.host}"

    @property
    def gpu_ssh_opts(self) -> str:
        return f"-p {self.port} -i {self.key_file}"

    @property
    def ssh_command(self) -> str:
        return f"ssh {self.gpu_ssh_opts} {self.gpu_ssh_host}"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "pod_id": self.pod_id,
            "pod_name": self.pod_name,
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "key_file": str(self.key_file),
            "source": self.source,
            "gpu_ssh_host": self.gpu_ssh_host,
            "gpu_ssh_opts": self.gpu_ssh_opts,
            "ssh_command": self.ssh_command,
            "warnings": list(self.warnings),
        }


def load_env_values(path: Path) -> dict[str, str]:
    """Load simple KEY=VALUE lines from an env file without exporting them."""
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def fetch_runpod_pods(
    api_key: str,
    *,
    api_url: str = DEFAULT_RUNPOD_REST_API,
    timeout_s: float = 30.0,
) -> list[dict[str, Any]]:
    """Fetch pod metadata from RunPod's REST API."""
    request = urllib.request.Request(api_url, headers={"Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("RunPod REST response must be a list of pods.")
    return [dict(item) for item in payload]


def extract_runpod_pods(payload: Any) -> list[RunPodPod]:
    """Extract pods from REST, GraphQL, or already-normalized payloads."""
    if isinstance(payload, list):
        return [RunPodPod.from_rest_jsonable(dict(item)) for item in payload]
    if not isinstance(payload, dict):
        raise ValueError("RunPod payload must be a list or object.")
    if "data" in payload:
        pods = payload.get("data", {}).get("myself", {}).get("pods", [])
        return [RunPodPod.from_graphql_jsonable(dict(item)) for item in list(pods or [])]
    if "pods" in payload:
        return [RunPodPod.from_rest_jsonable(dict(item)) for item in list(payload.get("pods") or [])]
    return [RunPodPod.from_rest_jsonable(payload)]


def select_runpod_ssh_target(
    pods: list[RunPodPod],
    *,
    pod_id: str | None = None,
    pod_name: str | None = None,
    user: str = "root",
    key_file: Path = Path("~/.ssh/id_ed25519_runpod"),
) -> RunPodSshTarget:
    candidates = _filter_pods(pods, pod_id=pod_id, pod_name=pod_name)
    if not candidates:
        raise ValueError("No RunPod pods matched the requested filters.")
    running = [
        pod for pod in candidates if pod.desired_status.upper() in {"RUNNING", "STARTED"}
    ]
    candidates = running or candidates
    warnings: list[str] = []
    if len(candidates) > 1 and pod_id is None and pod_name is None:
        warnings.append(
            f"Multiple RunPod pods matched; selected first candidate {candidates[0].pod_id}."
        )
    for pod in candidates:
        target = _target_from_pod(pod, user=user, key_file=key_file, warnings=warnings)
        if target is not None:
            return target
    raise ValueError("No matched RunPod pod exposes SSH on private port 22.")


def format_runpod_shell_exports(target: RunPodSshTarget) -> str:
    return "\n".join(
        [
            f"export GPU_SSH_HOST='{target.gpu_ssh_host}'",
            f"export GPU_SSH_OPTS='{target.gpu_ssh_opts}'",
        ]
    )


def write_runpod_ssh_resolution(
    run_dir: Path,
    target: RunPodSshTarget,
    pods: list[RunPodPod],
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "target": target.to_jsonable(),
        "shell_exports": format_runpod_shell_exports(target),
        "pods": [pod.to_jsonable() for pod in pods],
    }
    json_path = run_dir / "runpod_ssh_resolution.json"
    markdown_path = run_dir / "runpod_ssh_resolution.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
    return {
        "target": target.to_jsonable(),
        "shell_exports": payload["shell_exports"],
        "resolution_path": str(json_path),
        "report_path": str(markdown_path),
    }


def _filter_pods(
    pods: list[RunPodPod],
    *,
    pod_id: str | None,
    pod_name: str | None,
) -> list[RunPodPod]:
    selected = pods
    if pod_id is not None:
        selected = [pod for pod in selected if pod.pod_id == pod_id]
    if pod_name is not None:
        selected = [pod for pod in selected if pod.name == pod_name]
    return selected


def _target_from_pod(
    pod: RunPodPod,
    *,
    user: str,
    key_file: Path,
    warnings: list[str],
) -> RunPodSshTarget | None:
    if pod.public_ip and "22" in pod.port_mappings:
        return RunPodSshTarget(
            pod_id=pod.pod_id,
            pod_name=pod.name,
            host=pod.public_ip,
            port=pod.port_mappings["22"],
            user=user,
            key_file=key_file.expanduser(),
            source="rest_port_mappings",
            warnings=tuple(warnings),
        )
    for port in pod.runtime_ports:
        if port.private_port == 22 and port.public_port > 0 and port.ip:
            return RunPodSshTarget(
                pod_id=pod.pod_id,
                pod_name=pod.name,
                host=port.ip,
                port=port.public_port,
                user=user,
                key_file=key_file.expanduser(),
                source="runtime_ports",
                warnings=tuple(warnings),
            )
    return None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _render_markdown(payload: dict[str, Any]) -> str:
    target = dict(payload["target"])
    lines = [
        "# RunPod SSH Resolution",
        "",
        f"- Pod: `{target['pod_name']}` (`{target['pod_id']}`)",
        f"- SSH host: `{target['gpu_ssh_host']}`",
        f"- SSH options: `{target['gpu_ssh_opts']}`",
        f"- Source: `{target['source']}`",
        "",
        "## Shell",
        "",
        "```bash",
        str(payload["shell_exports"]),
        "```",
        "",
        "## Probe",
        "",
        "```bash",
        f"{target['ssh_command']} 'nvidia-smi && df -h /workspace /'",
        "```",
    ]
    warnings = list(target.get("warnings") or [])
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines) + "\n"
