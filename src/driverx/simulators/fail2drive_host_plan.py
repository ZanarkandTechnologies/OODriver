"""Plan a graphics-capable host handoff for stock Fail2Drive scoring."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Fail2DriveHostPlanConfig:
    target_route: str = "Generalization_PedestriansOnRoad_1088"
    remote: str | None = None
    ssh_opts: str | None = None
    output_root_remote: str = "/workspace/0xdriver-artifacts/fail2drive-score"
    carla_version: str = "0.9.16"


@dataclass(frozen=True)
class HostSuitability:
    state: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    graphics_ready: bool
    cuda_ready: bool

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "graphics_ready": self.graphics_ready,
            "cuda_ready": self.cuda_ready,
        }


@dataclass(frozen=True)
class Fail2DriveHostPlan:
    target_route: str
    suitability: HostSuitability
    required: tuple[str, ...]
    recommended_gpus: tuple[str, ...]
    not_sufficient_alone: tuple[str, ...]
    commands: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    pullback_policy: dict[str, list[str]]
    claim_boundaries: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "target_route": self.target_route,
            "suitability": self.suitability.to_jsonable(),
            "required": list(self.required),
            "recommended_gpus": list(self.recommended_gpus),
            "not_sufficient_alone": list(self.not_sufficient_alone),
            "commands": list(self.commands),
            "expected_outputs": list(self.expected_outputs),
            "pullback_policy": self.pullback_policy,
            "claim_boundaries": list(self.claim_boundaries),
        }


def classify_graphics_host_diagnostics(payload: dict[str, Any]) -> HostSuitability:
    text = json.dumps(payload).lower()
    blockers: list[str] = []
    warnings: list[str] = []
    cuda_ready = any(term in text for term in ("cuda", "nvidia-smi", "sm_86", "sm_89", "sm_90", "rtx", "a6000", "l40s", "a40"))
    graphics_ready = any(term in text for term in ("vulkan ready", "opengl ready", "carla port open", "carla_server_ready", "graphics_ready"))
    if "llvmpipe" in text or "error_incompatible_driver" in text or "did not open port" in text:
        graphics_ready = False
        blockers.append("CARLA graphics runtime is not ready; diagnostics show software rendering, Vulkan driver failure, or no CARLA port.")
    if "sm_120" in text and "compiled_arches" in text and "sm_120" not in str(payload.get("compiled_arches", "")).lower():
        warnings.append("CUDA inference stack may need a Blackwell rebuild; this is separate from CARLA graphics readiness.")
    if not graphics_ready:
        blockers.append("Need a host where CARLA 0.9.16 can render and tick, not just a CUDA-visible inference pod.")
    state = "ready" if graphics_ready else "blocked"
    return HostSuitability(
        state=state,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        graphics_ready=graphics_ready,
        cuda_ready=cuda_ready,
    )


def build_fail2drive_host_plan(
    config: Fail2DriveHostPlanConfig,
    *,
    diagnostics_payload: dict[str, Any] | None = None,
) -> Fail2DriveHostPlan:
    suitability = classify_graphics_host_diagnostics(diagnostics_payload or {})
    remote = config.remote or "<graphics-host>"
    ssh_prefix = f"ssh {config.ssh_opts or '<ssh-opts>'} {remote}".strip()
    return Fail2DriveHostPlan(
        target_route=config.target_route,
        suitability=suitability,
        required=(
            "NVIDIA GPU with working Vulkan/OpenGL graphics exposure",
            f"CARLA {config.carla_version} server can load Town13 and open the client port",
            "Python client environment can import carla and numpy",
            "Enough disk for CARLA, Fail2Drive checkout, logs, and route frames",
        ),
        recommended_gpus=("RTX A6000", "RTX 3090", "RTX 4090", "L40S", "A40"),
        not_sufficient_alone=(
            "CUDA visible through nvidia-smi",
            "An inference-only RunPod pod without Vulkan/OpenGL ICD exposure",
            "A local Wine/Kegworks CARLA run that cannot sustain full route cadence",
        ),
        commands=(
            f"{ssh_prefix} 'nvidia-smi && vulkaninfo --summary || true'",
            f"{ssh_prefix} 'python3 - <<PY\\nimport carla, numpy\\nprint(\"carla client ok\")\\nPY'",
            (
                "bash scripts/sync_remote_gpu.sh "
                f"{remote} {config.output_root_remote} "
                "# then run stock Fail2Drive route on the graphics host"
            ),
            (
                "PYTHONPATH=src python -m driverx run-fail2drive-route "
                f"--route-id {config.target_route} --run-id full-score-town13"
            ),
        ),
        expected_outputs=(
            "route_results.json or Fail2Drive evaluator JSON",
            "run_evidence.md",
            "stdout/stderr log tail",
            "short RGB/MP4 evidence only when explicitly pulled back",
        ),
        pullback_policy={
            "include": ["json", "md", "txt", "log"],
            "exclude": ["model weights", "datasets", "full RGB folders", "videos unless explicitly requested"],
        },
        claim_boundaries=(
            "stock_fail2drive_score_pending=true",
            "no_external_spend_or_execution_in_this_ticket=true",
            "graphics_host_required_for_full_score=true",
        ),
    )


def write_fail2drive_host_plan(run_dir: Path, plan: Fail2DriveHostPlan) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = plan.to_jsonable()
    json_path = run_dir / "fail2drive_host_plan.json"
    report_path = run_dir / "fail2drive_host_plan.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _markdown(payload: dict[str, Any]) -> str:
    suitability = dict(payload.get("suitability", {}))
    lines = [
        "# Stock Fail2Drive Full-Score Host Plan",
        "",
        f"- target_route: `{payload.get('target_route')}`",
        f"- suitability: `{suitability.get('state')}`",
        f"- graphics_ready: `{suitability.get('graphics_ready')}`",
        f"- cuda_ready: `{suitability.get('cuda_ready')}`",
        "",
        "## Required",
        "",
    ]
    lines.extend(f"- {item}" for item in list(payload.get("required", [])))
    lines.extend(["", "## Commands", ""])
    lines.extend(f"```bash\n{command}\n```" for command in list(payload.get("commands", [])))
    lines.extend(["", "## Blockers", ""])
    blockers = list(suitability.get("blockers", []))
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- none")
    lines.extend(["", "## Pullback Policy", ""])
    policy = dict(payload.get("pullback_policy", {}))
    lines.append(f"- include: `{', '.join(policy.get('include', []))}`")
    lines.append(f"- exclude: `{', '.join(policy.get('exclude', []))}`")
    return "\n".join(lines) + "\n"


__all__ = [
    "Fail2DriveHostPlan",
    "Fail2DriveHostPlanConfig",
    "HostSuitability",
    "build_fail2drive_host_plan",
    "classify_graphics_host_diagnostics",
    "write_fail2drive_host_plan",
]
