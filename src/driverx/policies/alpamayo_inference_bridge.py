"""Resumable fake/cached/remote Alpamayo inference bridge for OODrive."""

from __future__ import annotations

import json
import shutil
import os
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from driverx.remote.alpamayo_handoff import (
    build_alpamayo_handoff_manifest,
    package_cache_key,
    write_alpamayo_handoff_manifest,
)
from driverx.scenarios.studio_product_helpers import cot_from_prediction, latency_from_prediction

InferenceMode = Literal["fake", "cached-json", "remote-kasm"]


@dataclass(frozen=True)
class AlpamayoInferenceResult:
    status: str
    mode: str
    package_path: str
    cache_key: str
    prediction_json_path: str | None = None
    handoff_manifest_path: str | None = None
    latency_ms: float | None = None
    vram_peak_mb: float | None = None
    reasoning_snippet: str | None = None
    trajectory_shape: list[Any] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    safe_for_kasm_proxy: bool = True
    claim_boundaries: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mode": self.mode,
            "package_path": self.package_path,
            "cache_key": self.cache_key,
            "prediction_json_path": self.prediction_json_path,
            "handoff_manifest_path": self.handoff_manifest_path,
            "latency_ms": self.latency_ms,
            "vram_peak_mb": self.vram_peak_mb,
            "reasoning_snippet": self.reasoning_snippet,
            "trajectory_shape": list(self.trajectory_shape),
            "blockers": list(self.blockers),
            "safe_for_kasm_proxy": self.safe_for_kasm_proxy,
            "claim_boundaries": list(self.claim_boundaries),
        }


def run_alpamayo_inference_bridge(
    *,
    package_path: Path,
    mode: InferenceMode,
    output_root: Path,
    run_id: str,
    prediction_json: Path | None = None,
    cache_root: Path | None = None,
    remote_output_root: str | None = None,
    alpamayo_python: Path | None = None,
    alpamayo_command: str | None = None,
    timeout_s: float = 180.0,
    retries: int = 0,
) -> AlpamayoInferenceResult:
    expanded = package_path.expanduser().resolve()
    if not expanded.exists():
        return _blocked(mode, expanded, "missing-package", [f"Alpamayo package does not exist: {expanded}"])
    run_dir = (output_root / run_id).expanduser().resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    cache_key = package_cache_key(expanded, mode=mode)
    cached_path = _cached_prediction(cache_root, cache_key)
    if cached_path is not None:
        return _result_from_prediction(
            mode=mode,
            package_path=expanded,
            cache_key=cache_key,
            prediction_path=cached_path,
            status="cached",
        )
    if mode == "fake":
        start = time.perf_counter()
        fake_path = run_dir / "alpamayo_fake_prediction.json"
        fake_payload = _fake_prediction_payload(expanded)
        fake_path.write_text(json.dumps(fake_payload, indent=2), encoding="utf-8")
        _write_cache(cache_root, cache_key, fake_path)
        return _result_from_prediction(
            mode=mode,
            package_path=expanded,
            cache_key=cache_key,
            prediction_path=fake_path,
            status="passed",
            latency_ms=round((time.perf_counter() - start) * 1000.0, 3),
        )
    if mode == "cached-json":
        if prediction_json is None or not prediction_json.expanduser().exists():
            return _blocked(mode, expanded, cache_key, ["cached-json mode requires --prediction-json"])
        copied = run_dir / "alpamayo_cached_prediction.json"
        shutil.copyfile(prediction_json.expanduser(), copied)
        _write_cache(cache_root, cache_key, copied)
        return _result_from_prediction(
            mode=mode,
            package_path=expanded,
            cache_key=cache_key,
            prediction_path=copied,
            status="passed",
        )
    executed = _execute_remote_kasm_inference(
        package_path=expanded,
        run_dir=run_dir,
        cache_key=cache_key,
        cache_root=cache_root,
        alpamayo_python=alpamayo_python,
        alpamayo_command=alpamayo_command,
        timeout_s=timeout_s,
        retries=retries,
    )
    if executed is not None:
        return executed
    manifest = build_alpamayo_handoff_manifest(
        expanded,
        Path(remote_output_root or "/workspace/driverx_remote_artifacts/closed-loop"),
        mode=mode,
    )
    manifest_path = write_alpamayo_handoff_manifest(run_dir, manifest)
    return AlpamayoInferenceResult(
        status="blocked",
        mode=mode,
        package_path=str(expanded),
        cache_key=cache_key,
        handoff_manifest_path=str(manifest_path),
        blockers=[
            "remote-kasm mode requires running the handoff on Kasm with HF auth installed through a safe channel",
            f"timeout_s={timeout_s}",
            f"retries={retries}",
        ],
        claim_boundaries=["real_time_vla_control=false", "alpamayo_remote_inference=blocked"],
    )


def write_alpamayo_inference_result(run_dir: Path, result: AlpamayoInferenceResult) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = result.to_jsonable()
    json_path = run_dir / "alpamayo_inference_result.json"
    report_path = run_dir / "alpamayo_inference_result.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _result_from_prediction(
    *,
    mode: str,
    package_path: Path,
    cache_key: str,
    prediction_path: Path,
    status: str,
    latency_ms: float | None = None,
) -> AlpamayoInferenceResult:
    payload = json.loads(prediction_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        payload = {}
    return AlpamayoInferenceResult(
        status=status,
        mode=mode,
        package_path=str(package_path),
        cache_key=cache_key,
        prediction_json_path=str(prediction_path),
        latency_ms=latency_ms if latency_ms is not None else latency_from_prediction(payload),
        vram_peak_mb=_float_or_none(payload.get("vram_peak_mb") or payload.get("peak_vram_mb")),
        reasoning_snippet=cot_from_prediction(payload),
        trajectory_shape=list(payload.get("pred_xyz_shape") or payload.get("trajectory_shape") or []),
        claim_boundaries=["sampled_open_loop_reasoning=true", "real_time_vla_control=false"],
    )


def _fake_prediction_payload(package_path: Path) -> dict[str, Any]:
    return {
        "policy_id": "alpamayo-fake-closed-loop",
        "cot": f"Fake Alpamayo checkpoint analysis for {package_path.name}: slow down, hold lane, and stop if obstacle remains ahead.",
        "latency_ms": 12.0,
        "pred_xyz_shape": [1, 1, 1, 20, 3],
        "policy_decision": {
            "policy_id": "alpamayo-fake-closed-loop",
            "action": {
                "trajectory": {
                    "points_xy": [[0.2 * index, 0.0] for index in range(20)],
                    "source": "fake_alpamayo",
                    "score": 0.75,
                }
            },
        },
    }


def _cached_prediction(cache_root: Path | None, cache_key: str) -> Path | None:
    if cache_root is None:
        return None
    path = cache_root / cache_key / "prediction.json"
    return path if path.exists() else None


def _write_cache(cache_root: Path | None, cache_key: str, prediction_path: Path) -> None:
    if cache_root is None:
        return
    cache_dir = cache_root / cache_key
    cache_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(prediction_path, cache_dir / "prediction.json")


def _execute_remote_kasm_inference(
    *,
    package_path: Path,
    run_dir: Path,
    cache_key: str,
    cache_root: Path | None,
    alpamayo_python: Path | None,
    alpamayo_command: str | None,
    timeout_s: float,
    retries: int,
) -> AlpamayoInferenceResult | None:
    """Execute a local RunPod-side Alpamayo command when one is configured.

    The bridge intentionally does not bake tokens or SSH commands into artifacts.
    A Kasm pod can expose the actual model runner through
    ``DRIVERX_ALPAMAYO_REMOTE_COMMAND`` using ``{package}``, ``{output}``, and
    ``{python}`` placeholders. If no command is configured we keep the previous
    safe handoff behavior.
    """

    command_template = alpamayo_command or os.environ.get("DRIVERX_ALPAMAYO_REMOTE_COMMAND")
    if not command_template:
        return None
    python_path = str(alpamayo_python.expanduser()) if alpamayo_python is not None else "python3"
    output_path = run_dir / "alpamayo_live_prediction.json"
    replacements = {
        "{package}": str(package_path),
        "{output}": str(output_path),
        "{output_dir}": str(run_dir),
        "{python}": python_path,
    }
    rendered = command_template
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    command = shlex.split(rendered)
    if not command:
        return None
    started = time.perf_counter()
    attempts = max(1, retries + 1)
    last_error = ""
    for attempt in range(attempts):
        try:
            completed = subprocess.run(
                command,
                cwd=run_dir,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            (run_dir / f"alpamayo_remote_command_attempt_{attempt}.log").write_text(
                _redact_command_log(command, completed.stdout, completed.stderr),
                encoding="utf-8",
            )
            if completed.returncode == 0 and output_path.exists():
                _write_cache(cache_root, cache_key, output_path)
                return _result_from_prediction(
                    mode="remote-kasm",
                    package_path=package_path,
                    cache_key=cache_key,
                    prediction_path=output_path,
                    status="passed",
                    latency_ms=round((time.perf_counter() - started) * 1000.0, 3),
                )
            last_error = f"attempt {attempt}: exit={completed.returncode}; output_exists={output_path.exists()}"
        except Exception as exc:
            last_error = f"attempt {attempt}: {type(exc).__name__}: {exc}"
            (run_dir / f"alpamayo_remote_command_attempt_{attempt}.log").write_text(last_error, encoding="utf-8")
    return AlpamayoInferenceResult(
        status="blocked",
        mode="remote-kasm",
        package_path=str(package_path),
        cache_key=cache_key,
        blockers=[f"remote-kasm command did not produce prediction JSON: {last_error}"],
        latency_ms=round((time.perf_counter() - started) * 1000.0, 3),
        claim_boundaries=["real_time_vla_control=false", "alpamayo_remote_inference=command_failed"],
    )


def _redact_command_log(command: list[str], stdout: str, stderr: str) -> str:
    redacted_command = ["<redacted>" if "token" in part.lower() else part for part in command]
    return "\n".join(
        [
            "command: " + json.dumps(redacted_command),
            "",
            "stdout:",
            stdout,
            "",
            "stderr:",
            stderr,
        ]
    )


def _blocked(mode: str, package_path: Path, cache_key: str, blockers: list[str]) -> AlpamayoInferenceResult:
    return AlpamayoInferenceResult(
        status="blocked",
        mode=mode,
        package_path=str(package_path),
        cache_key=cache_key,
        blockers=blockers,
        claim_boundaries=["real_time_vla_control=false"],
    )


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Alpamayo Inference Result",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Mode: `{payload.get('mode')}`",
        f"- Cache key: `{payload.get('cache_key')}`",
        f"- Prediction: `{payload.get('prediction_json_path')}`",
    ]
    blockers = list(payload.get("blockers", []))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in blockers)
    lines.append("")
    return "\n".join(lines)


def _float_or_none(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


__all__ = [
    "AlpamayoInferenceResult",
    "InferenceMode",
    "run_alpamayo_inference_bridge",
    "write_alpamayo_inference_result",
]
