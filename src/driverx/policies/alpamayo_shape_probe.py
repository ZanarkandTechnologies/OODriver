"""Alpamayo live inference shape probe artifact parsing."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from driverx.policies.alpamayo_probe import DEFAULT_ALPAMAYO_MODEL_ID

_KNOWN_ARTIFACTS = (
    "alpamayo_shape_probe.json",
    "entrypoint_inventory.json",
    "gpu_snapshot.txt",
    "package_versions.json",
    "memory_usage.json",
    "shape_probe.log",
)

_SECRET_PATTERNS = (
    re.compile(r"hf_[A-Za-z0-9_=-]{8,}"),
    re.compile(r"(HF_TOKEN\s*=\s*)[^\s]+", re.IGNORECASE),
    re.compile(r"(Authorization:\s*Bearer\s+)[^\s]+", re.IGNORECASE),
)

_AUTH_ERROR_PATTERNS = (
    re.compile(r"\b401\b"),
    re.compile(r"\b403\b"),
    re.compile(r"unauthorized", re.IGNORECASE),
    re.compile(r"forbidden", re.IGNORECASE),
    re.compile(r"gated repo", re.IGNORECASE),
    re.compile(r"invalid token", re.IGNORECASE),
)


def classify_alpamayo_shape_probe_artifacts(
    artifact_root: Path,
    *,
    model_id: str = DEFAULT_ALPAMAYO_MODEL_ID,
) -> dict[str, Any]:
    """Classify pulled live Alpamayo inference shape artifacts."""

    root = artifact_root.expanduser()
    artifacts = _artifact_presence(root)
    probe_payload = _read_json(root / "alpamayo_shape_probe.json")
    memory_payload = _read_json(root / "memory_usage.json")
    inventory_payload = _read_json(root / "entrypoint_inventory.json")
    package_payload = _read_json(root / "package_versions.json")
    combined_text = _combined_text(root, probe_payload, memory_payload, inventory_payload, package_payload)
    status, blockers = _classify(combined_text, probe_payload, artifacts)
    payload = {
        "model_id": model_id,
        "artifact_root": str(root),
        "status": status,
        "blocked": bool(blockers),
        "blockers": blockers,
        "artifacts": artifacts,
        "inference_state": _inference_state(probe_payload),
        "input_shapes": _mapping_or_empty(probe_payload, "input_shapes"),
        "output_shapes": _mapping_or_empty(probe_payload, "output_shapes"),
        "output_types": _mapping_or_empty(probe_payload, "output_types"),
        "latency_ms": _maybe_number(_get(probe_payload, "latency_ms")),
        "vram_peak_mb": _maybe_number(_nested_get(memory_payload, "vram_peak_mb")),
        "entrypoint_inventory": inventory_payload if isinstance(inventory_payload, dict) else {},
        "redacted_excerpt": _redact_secrets(combined_text)[:2400],
    }
    return payload


def write_alpamayo_shape_probe_report(
    run_dir: Path,
    *,
    artifact_root: Path | None = None,
    model_id: str = DEFAULT_ALPAMAYO_MODEL_ID,
) -> dict[str, Any]:
    """Write JSON and Markdown summaries for live Alpamayo shape evidence."""

    run_dir.mkdir(parents=True, exist_ok=True)
    root = artifact_root if artifact_root is not None else run_dir
    payload = classify_alpamayo_shape_probe_artifacts(root, model_id=model_id)
    json_path = run_dir / "alpamayo_shape_probe_report.json"
    report_path = run_dir / "alpamayo_shape_probe_report.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def _artifact_presence(root: Path) -> dict[str, dict[str, Any]]:
    return {
        name: {
            "path": str(root / name),
            "present": (root / name).exists(),
            "bytes": (root / name).stat().st_size if (root / name).exists() else 0,
        }
        for name in _KNOWN_ARTIFACTS
    }


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"parse_error": str(exc)}


def _combined_text(root: Path, *payloads: Any) -> str:
    chunks: list[str] = []
    for name in ("shape_probe.log", "gpu_snapshot.txt"):
        path = root / name
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    for payload in payloads:
        if payload is not None:
            chunks.append(json.dumps(payload, sort_keys=True))
    return "\n".join(chunks)


def _classify(
    text: str,
    payload: Any,
    artifacts: dict[str, dict[str, Any]],
) -> tuple[str, list[str]]:
    present_count = sum(1 for meta in artifacts.values() if meta["present"])
    lower = text.lower()
    if present_count == 0:
        return "not_run", ["No Alpamayo shape probe artifacts found."]
    state = _inference_state(payload)
    if state in {"shape_observed", "completed", "success"}:
        if _has_required_shapes(payload):
            return "shape_observed", []
        return "shape_blocked", ["Inference completed but required output shapes were missing."]
    if any(pattern.search(text) for pattern in _AUTH_ERROR_PATTERNS):
        return "dataset_gate_blocked", ["Hugging Face model or dataset access was rejected."]
    if "out of memory" in lower or "cuda oom" in lower or "cublas_status_alloc_failed" in lower:
        return "oom_blocked", ["Probe exhausted GPU memory before producing shape evidence."]
    if "cuda is not available" in lower or "no cuda" in lower or "no nvidia" in lower:
        return "cuda_blocked", ["CUDA or NVIDIA GPU runtime was unavailable."]
    if state in {"failed", "blocked", "error"}:
        return "runtime_blocked", [_runtime_blocker(payload) or "Live inference failed."]
    if artifacts["alpamayo_shape_probe.json"]["present"]:
        return "shape_blocked", ["Shape probe JSON exists, but no successful inference state was recorded."]
    return "missing_artifacts", ["Probe logs exist, but core alpamayo_shape_probe.json is missing."]


def _has_required_shapes(payload: Any) -> bool:
    output_shapes = _mapping_or_empty(payload, "output_shapes")
    return bool(output_shapes.get("pred_xyz") and output_shapes.get("pred_rot"))


def _inference_state(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get("inference_state") or payload.get("status")
    return value.lower() if isinstance(value, str) else None


def _runtime_blocker(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ("error", "blocker", "exception"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return _redact_secrets(value.strip())
    return None


def _mapping_or_empty(payload: Any, key: str) -> dict[str, Any]:
    value = _get(payload, key)
    return value if isinstance(value, dict) else {}


def _get(payload: Any, key: str) -> Any:
    return payload.get(key) if isinstance(payload, dict) else None


def _nested_get(payload: Any, key: str) -> Any:
    if not isinstance(payload, dict):
        return None
    stack: list[Any] = [payload]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            if key in current:
                return current[key]
            stack.extend(current.values())
    return None


def _maybe_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _redact_secrets(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]" if match.groups() else "[REDACTED]", redacted)
    return redacted


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Alpamayo Shape Probe Report",
        "",
        f"- model_id: `{payload['model_id']}`",
        f"- status: `{payload['status']}`",
        f"- blocked: `{payload['blocked']}`",
        f"- inference_state: `{payload.get('inference_state')}`",
        f"- latency_ms: `{payload.get('latency_ms')}`",
        f"- vram_peak_mb: `{payload.get('vram_peak_mb')}`",
        "",
        "## Input Shapes",
        "",
    ]
    input_shapes = dict(payload.get("input_shapes", {}))
    lines.extend(f"- `{key}`: `{value}`" for key, value in sorted(input_shapes.items())) if input_shapes else lines.append("- none")
    lines.extend(["", "## Output Shapes", ""])
    output_shapes = dict(payload.get("output_shapes", {}))
    lines.extend(f"- `{key}`: `{value}`" for key, value in sorted(output_shapes.items())) if output_shapes else lines.append("- none")
    lines.extend(["", "## Blockers", ""])
    blockers = list(payload.get("blockers", []))
    lines.extend(f"- {blocker}" for blocker in blockers) if blockers else lines.append("- none")
    lines.extend(["", "## Redacted Excerpt", "", "```text", str(payload.get("redacted_excerpt", "")), "```"])
    return "\n".join(lines)


__all__ = [
    "classify_alpamayo_shape_probe_artifacts",
    "write_alpamayo_shape_probe_report",
]
