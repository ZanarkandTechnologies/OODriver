"""Batch Alpamayo OOD comparison planning and aggregation."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir


@dataclass(frozen=True)
class AlpamayoRemoteConfig:
    remote: str = "root@195.26.233.80"
    ssh_opts: str = "-p 55050 -i ~/.ssh/id_ed25519_runpod"
    python_bin: str = "/workspace/alpamayo1.5/a1_5_venv/bin/python"
    attn_implementation: str = "eager"
    num_traj_samples: int = 1


@dataclass(frozen=True)
class AlpamayoOodBatchConfig:
    output_root: Path = Path("artifacts/runs")
    run_id: str = "alpamayo-ood-batch"
    campaign_summary_path: Path | None = None
    package_paths: tuple[Path, ...] = ()
    baseline_decision_paths: tuple[Path, ...] = ()
    memory_decision_paths: tuple[Path, ...] = ()
    comparison_paths: tuple[Path, ...] = ()
    limit: int = 3
    execute_remote: bool = False
    reuse_existing: bool = True
    remote: AlpamayoRemoteConfig = field(default_factory=AlpamayoRemoteConfig)


@dataclass(frozen=True)
class AlpamayoRemoteCommand:
    command: tuple[str, ...]
    env: dict[str, str]
    local_output_dir: str
    execute_remote: bool

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "command": list(self.command),
            "env": self.env,
            "local_output_dir": self.local_output_dir,
            "execute_remote": self.execute_remote,
        }


def run_alpamayo_ood_batch(config: AlpamayoOodBatchConfig) -> dict[str, Any]:
    run_dir = prepare_run_dir(config.output_root, config.run_id)
    cases = _select_cases(config)
    records: list[dict[str, Any]] = []
    for index, case in enumerate(cases[: config.limit]):
        records.append(_run_or_plan_case(run_dir, index, case, config))
    payload = summarize_alpamayo_batch(run_dir, records)
    return write_alpamayo_ood_batch(run_dir, payload)


def plan_remote_alpamayo_case(
    package_path: Path,
    *,
    case_id: str,
    run_dir: Path,
    config: AlpamayoOodBatchConfig,
) -> AlpamayoRemoteCommand:
    local_output = run_dir / "remote_outputs" / case_id
    env = {
        "GPU_SSH_OPTS": config.remote.ssh_opts,
        "PYTHON_BIN": config.remote.python_bin,
        "ALPAMAYO_ATTN_IMPLEMENTATION": config.remote.attn_implementation,
        "ALPAMAYO_NUM_TRAJ_SAMPLES": str(config.remote.num_traj_samples),
        "RUN_ID": case_id,
    }
    return AlpamayoRemoteCommand(
        command=(
            "bash",
            "scripts/run_remote_alpamayo_carla_inference.sh",
            str(package_path),
            config.remote.remote,
            str(local_output),
        ),
        env=env,
        local_output_dir=str(local_output),
        execute_remote=config.execute_remote,
    )


def summarize_alpamayo_batch(run_dir: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [record for record in records if record.get("status") == "passed"]
    planned = [record for record in records if record.get("status") == "planned"]
    blocked = [record for record in records if record.get("status") == "blocked"]
    final_deltas = [
        float(record["trajectory_final_l2_m"])
        for record in records
        if record.get("trajectory_final_l2_m") is not None
    ]
    latencies = [
        latency
        for record in records
        for latency in list(record.get("latency_ms", []))
        if latency is not None
    ]
    vram_peaks = [
        vram
        for record in records
        for vram in list(record.get("vram_peak_mb", []))
        if vram is not None
    ]
    return {
        "batch_id": run_dir.name,
        "status": "passed" if passed and not blocked else "planned" if planned and not blocked else "blocked" if blocked else "empty",
        "case_count": len(records),
        "passed_count": len(passed),
        "planned_count": len(planned),
        "blocked_count": len(blocked),
        "mean_trajectory_final_l2_m": _mean(final_deltas),
        "mean_latency_ms": _mean([float(value) for value in latencies]),
        "mean_vram_peak_mb": _mean([float(value) for value in vram_peaks]),
        "max_vram_peak_mb": max([float(value) for value in vram_peaks], default=None),
        "records": records,
        "blockers": [
            f"{record.get('scenario_id')}: {blocker}"
            for record in records
            for blocker in list(record.get("blockers", []))
        ],
        "claim_boundaries": [
            "alpamayo_batch_open_loop_policy_evaluation=true",
            "closed_loop_carla_control=false",
            "real_time_vla_control=false",
            "model_weights_frozen=true",
        ],
    }


def write_alpamayo_ood_batch(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    json_path = run_dir / "alpamayo_ood_batch_summary.json"
    report_path = run_dir / "alpamayo_ood_batch_summary.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _run_or_plan_case(
    run_dir: Path,
    index: int,
    case: dict[str, Any],
    config: AlpamayoOodBatchConfig,
) -> dict[str, Any]:
    case_id = str(case.get("case_id") or f"case-{index:03d}")
    package_path = Path(str(case.get("package_path"))) if case.get("package_path") else None
    baseline = _nth(config.baseline_decision_paths, index)
    memory = _nth(config.memory_decision_paths, index)
    comparison = _nth(config.comparison_paths, index)
    blockers: list[str] = []
    if package_path is None:
        blockers.append("No Alpamayo package path is available for this campaign case.")
    elif not package_path.exists():
        blockers.append(f"Alpamayo package path does not exist: {package_path}")
    command = (
        plan_remote_alpamayo_case(package_path, case_id=case_id, run_dir=run_dir, config=config)
        if package_path is not None
        else None
    )
    execution: dict[str, Any] | None = None
    if command is not None and config.execute_remote and not blockers:
        execution = _execute_command(command)
        if execution.get("exit_code") != 0:
            blockers.append("Remote Alpamayo inference command failed; inspect stdout/stderr in batch record.")
    comparison_payload = _load_json(comparison) if comparison and comparison.exists() else {}
    record = {
        "scenario_id": str(case.get("scenario_id") or case.get("recipe_id") or case_id),
        "case_id": case_id,
        "package_path": str(package_path) if package_path else None,
        "baseline_decision_path": str(baseline) if baseline else None,
        "memory_decision_path": str(memory) if memory else None,
        "comparison_path": str(comparison) if comparison else None,
        "remote_command": command.to_jsonable() if command else None,
        "remote_execution": execution,
        "latency_ms": _latencies_from_comparison(comparison_payload),
        "vram_peak_mb": _vram_peaks_from_comparison(comparison_payload),
        "trajectory_final_l2_m": _trajectory_final_delta(comparison_payload),
        "reasoning_changed": _mapping(comparison_payload.get("reasoning_delta")).get("changed"),
        "memory_ids": list(comparison_payload.get("memory_ids", [])),
        "open_loop_policy_evaluation": True,
        "status": "blocked" if blockers else "passed" if comparison_payload else "planned",
        "blockers": blockers,
    }
    return record


def _select_cases(config: AlpamayoOodBatchConfig) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    if config.campaign_summary_path is not None and config.campaign_summary_path.exists():
        campaign = _load_json(config.campaign_summary_path)
        for case in list(campaign.get("cases", [])):
            if isinstance(case, dict):
                cases.append(dict(case))
    for index, package_path in enumerate(config.package_paths):
        payload = _load_json(package_path) if package_path.exists() else {}
        cases.append(
            {
                "case_id": payload.get("scenario_id") or package_path.stem or f"package-{index:03d}",
                "scenario_id": payload.get("scenario_id") or package_path.stem,
                "package_path": str(package_path),
            }
        )
    if not cases:
        cases.append({"case_id": "no-cases", "blockers": ["No campaign or package paths supplied."]})
    return cases


def _execute_command(command: AlpamayoRemoteCommand) -> dict[str, Any]:
    env = {**os.environ, **command.env}
    try:
        completed = subprocess.run(
            list(command.command),
            cwd=Path.cwd(),
            env=env,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=1800,
        )
        return {
            "exit_code": completed.returncode,
            "stdout_tail": completed.stdout[-4000:],
        }
    except Exception as exc:
        return {"exit_code": 1, "stdout_tail": f"{type(exc).__name__}: {exc}"}


def _latencies_from_comparison(payload: dict[str, Any]) -> list[float]:
    latencies: list[float] = []
    for record in list(payload.get("records", [])):
        if isinstance(record, dict) and record.get("latency_ms") is not None:
            latencies.append(float(record["latency_ms"]))
    return latencies


def _vram_peaks_from_comparison(payload: dict[str, Any]) -> list[float]:
    peaks: list[float] = []
    for record in list(payload.get("records", [])):
        if isinstance(record, dict) and record.get("vram_peak_mb") is not None:
            peaks.append(float(record["vram_peak_mb"]))
    return peaks


def _trajectory_final_delta(payload: dict[str, Any]) -> float | None:
    delta = _mapping(payload.get("trajectory_delta"))
    if delta.get("final_l2_m") is None:
        return None
    return float(delta["final_l2_m"])


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _nth(values: tuple[Path, ...], index: int) -> Path | None:
    return values[index] if index < len(values) else None


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Alpamayo OOD Batch",
        "",
        f"- status: `{payload.get('status')}`",
        f"- case_count: `{payload.get('case_count')}`",
        f"- passed_count: `{payload.get('passed_count')}`",
        f"- planned_count: `{payload.get('planned_count')}`",
        f"- blocked_count: `{payload.get('blocked_count')}`",
        f"- mean_trajectory_final_l2_m: `{payload.get('mean_trajectory_final_l2_m')}`",
        f"- mean_latency_ms: `{payload.get('mean_latency_ms')}`",
        f"- mean_vram_peak_mb: `{payload.get('mean_vram_peak_mb')}`",
        f"- max_vram_peak_mb: `{payload.get('max_vram_peak_mb')}`",
        "",
        "## Records",
        "",
    ]
    for record in list(payload.get("records", [])):
        lines.append(
            f"- `{record.get('scenario_id')}`: status=`{record.get('status')}`, "
            f"final_l2=`{record.get('trajectory_final_l2_m')}`, "
            f"latency_ms=`{record.get('latency_ms')}`, vram_peak_mb=`{record.get('vram_peak_mb')}`, "
            f"reasoning_changed=`{record.get('reasoning_changed')}`"
        )
    blockers = list(payload.get("blockers", []))
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("- none")
    return "\n".join(lines) + "\n"


__all__ = [
    "AlpamayoOodBatchConfig",
    "AlpamayoRemoteCommand",
    "AlpamayoRemoteConfig",
    "plan_remote_alpamayo_case",
    "run_alpamayo_ood_batch",
    "summarize_alpamayo_batch",
    "write_alpamayo_ood_batch",
]
