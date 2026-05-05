"""Alpamayo offline probe artifact parsing and schema notes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DEFAULT_ALPAMAYO_MODEL_ID = "nvidia/Alpamayo-1.5-10B"

_KNOWN_ARTIFACTS = (
    "alpamayo_probe.json",
    "gpu_snapshot.txt",
    "package_versions.json",
    "package_versions.txt",
    "memory_usage.json",
    "probe.log",
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


def expected_alpamayo_schema(
    model_id: str = DEFAULT_ALPAMAYO_MODEL_ID,
) -> dict[str, Any]:
    """Return the adapter-side schema we expect before live model probing.

    Alpamayo is still a setup-gated adapter in 0xDriver. This schema is a
    conservative contract for TASK-039 and must be replaced by observed tensor
    metadata when the remote probe succeeds.
    """

    return {
        "status": "unverified_adapter_stub",
        "model_id": model_id,
        "coordinate_frame": {
            "name": "ego_vehicle_local",
            "x_axis": "forward",
            "y_axis": "left_positive_before_carla_conversion",
            "z_axis": "up",
            "note": "TASK-039 must validate signs and units against real Alpamayo outputs.",
        },
        "inputs": [
            {
                "name": "camera_views",
                "source": "CARLA RGB sensors or Waymo front cameras",
                "shape": "batch x time x views x height x width x 3",
                "dtype": "uint8 or normalized float tensor, backend-dependent",
                "required": True,
                "notes": "At minimum front, front-left, and front-right views should be supported.",
            },
            {
                "name": "ego_state",
                "source": "vehicle transform, velocity, acceleration, and recent pose history",
                "shape": "structured scalar/vector fields",
                "dtype": "float32",
                "required": True,
                "notes": "Used for speed profile, local frame normalization, and latency-aligned replay.",
            },
            {
                "name": "route_context",
                "source": "route waypoints, high-level command, or Bench2Drive route id",
                "shape": "optional route polyline plus command string",
                "dtype": "float32 plus text",
                "required": False,
                "notes": "Keep optional so image-only and route-aware probes can both be tested.",
            },
            {
                "name": "memory_context",
                "source": "retrieved OOD failure memory",
                "shape": "short structured text snippets",
                "dtype": "text/json",
                "required": False,
                "notes": "DriverX-specific minimal-shot RAG guidance, not part of the base model.",
            },
        ],
        "outputs": [
            {
                "name": "reasoning",
                "shape": "short text or JSON trace",
                "dtype": "text/json",
                "required": False,
                "notes": "Should be compact and redacted before report artifacts.",
            },
            {
                "name": "trajectory",
                "shape": "backend-native 64 x 3 waypoints at 10 Hz, convertible to 20 x 2 waypoints for 5 seconds at 4 Hz",
                "dtype": "float32",
                "required": True,
                "notes": "Primary handoff to CARLA control intent and Waymo-style offline scoring.",
            },
            {
                "name": "control",
                "shape": "optional throttle/steer/brake or speed target",
                "dtype": "float32/bool",
                "required": False,
                "notes": "Only trusted after TASK-039 validates closed-loop conversion.",
            },
            {
                "name": "runtime",
                "shape": "latency_ms, vram_peak_mb, model_load_state",
                "dtype": "json",
                "required": True,
                "notes": "Needed to compare realistic compute constraints.",
            },
        ],
    }


def classify_alpamayo_probe_artifacts(
    artifact_root: Path,
    *,
    model_id: str = DEFAULT_ALPAMAYO_MODEL_ID,
) -> dict[str, Any]:
    """Classify a remote Alpamayo probe directory without leaking secrets."""

    root = artifact_root.expanduser()
    artifacts = _artifact_presence(root)
    probe_payload = _read_json(root / "alpamayo_probe.json")
    memory_payload = _read_json(root / "memory_usage.json")
    package_payload = _read_json(root / "package_versions.json")
    combined_text = _combined_probe_text(root, probe_payload, memory_payload, package_payload)
    status, blockers = _classify_text_and_payload(combined_text, probe_payload, artifacts)
    observed_shape = _observed_shape(probe_payload)
    if observed_shape and status == "model_loaded":
        status = "shape_observed"
    payload = {
        "model_id": model_id,
        "artifact_root": str(root),
        "status": status,
        "blocked": bool(blockers),
        "blockers": blockers,
        "artifacts": artifacts,
        "model_load_state": _model_load_state(probe_payload),
        "latency_ms": _maybe_number(probe_payload.get("latency_ms") if isinstance(probe_payload, dict) else None),
        "vram_peak_mb": _maybe_number(_nested_get(memory_payload, "vram_peak_mb")),
        "observed_shape": observed_shape,
        "package_versions": package_payload if isinstance(package_payload, dict) else {},
        "redacted_excerpt": _redact_secrets(combined_text)[:2400],
        "expected_schema": expected_alpamayo_schema(model_id),
    }
    return payload


def write_alpamayo_probe_report(
    run_dir: Path,
    *,
    artifact_root: Path | None = None,
    model_id: str = DEFAULT_ALPAMAYO_MODEL_ID,
) -> dict[str, Any]:
    """Write JSON and Markdown summaries for Alpamayo probe evidence."""

    run_dir.mkdir(parents=True, exist_ok=True)
    root = artifact_root if artifact_root is not None else run_dir
    payload = classify_alpamayo_probe_artifacts(root, model_id=model_id)
    json_path = run_dir / "alpamayo_probe_report.json"
    report_path = run_dir / "alpamayo_probe_report.md"
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


def _combined_probe_text(root: Path, *payloads: Any) -> str:
    chunks: list[str] = []
    for name in ("probe.log", "gpu_snapshot.txt", "package_versions.txt"):
        path = root / name
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    for payload in payloads:
        if payload is not None:
            chunks.append(json.dumps(payload, sort_keys=True))
    return "\n".join(chunks)


def _classify_text_and_payload(
    text: str,
    payload: Any,
    artifacts: dict[str, dict[str, Any]],
) -> tuple[str, list[str]]:
    present_count = sum(1 for meta in artifacts.values() if meta["present"])
    lower = text.lower()
    if present_count == 0:
        return "not_run", ["No Alpamayo probe artifacts found."]
    if any(pattern.search(text) for pattern in _AUTH_ERROR_PATTERNS):
        return "auth_blocked", ["Hugging Face or model access was rejected."]
    if "out of memory" in lower or "cuda oom" in lower or "cublas_status_alloc_failed" in lower:
        return "oom", ["Probe exhausted GPU memory before producing a usable output."]
    if "cuda is not available" in lower or "no cuda" in lower or "no nvidia" in lower:
        return "cuda_blocked", ["CUDA or NVIDIA GPU runtime was unavailable."]
    load_state = _model_load_state(payload)
    if load_state in {"loaded", "success", "ok"}:
        return "model_loaded", []
    if (
        load_state == "not_requested"
        and isinstance(payload, dict)
        and isinstance(payload.get("model_info"), dict)
    ):
        return "metadata_observed", []
    if load_state in {"failed", "error", "blocked"}:
        return "runtime_blocked", [_runtime_blocker(payload) or "Model load failed."]
    if artifacts["alpamayo_probe.json"]["present"]:
        return "runtime_blocked", ["Probe JSON exists, but no successful model load state was recorded."]
    return "missing_artifacts", ["Probe logs exist, but core alpamayo_probe.json is missing."]


def _model_load_state(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ("model_load_state", "load_state", "status"):
        value = payload.get(key)
        if isinstance(value, str):
            return value.lower()
    if payload.get("loaded") is True:
        return "loaded"
    return None


def _runtime_blocker(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ("error", "blocker", "exception"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return _redact_secrets(value.strip())
    return None


def _observed_shape(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    for key in ("observed_shape", "output_shape", "trajectory_shape", "schema_observed"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
        if isinstance(value, list):
            return {key: value}
        if isinstance(value, str):
            return {key: value}
    return None


def _nested_get(payload: Any, key: str) -> Any:
    if not isinstance(payload, dict):
        return None
    if key in payload:
        return payload[key]
    for value in payload.values():
        found = _nested_get(value, key)
        if found is not None:
            return found
    return None


def _maybe_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _redact_secrets(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]" if match.lastindex else "[REDACTED]", redacted)
    return redacted


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Alpamayo Probe Report",
        "",
        f"- model_id: `{payload['model_id']}`",
        f"- status: `{payload['status']}`",
        f"- blocked: `{payload['blocked']}`",
        f"- model_load_state: `{payload.get('model_load_state')}`",
        f"- latency_ms: `{payload.get('latency_ms')}`",
        f"- vram_peak_mb: `{payload.get('vram_peak_mb')}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = list(payload.get("blockers", []))
    if blockers:
        lines.extend(f"- {blocker}" for blocker in blockers)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "| artifact | present | bytes |",
            "|---|---:|---:|",
        ]
    )
    for name, meta in dict(payload.get("artifacts", {})).items():
        lines.append(f"| `{name}` | `{meta.get('present')}` | `{meta.get('bytes')}` |")
    lines.extend(
        [
            "",
            "## Expected Adapter Schema",
            "",
            "- status: `unverified_adapter_stub`",
            "- trajectory target: `20 x 2` waypoints for 5 seconds at 4 Hz when available",
            "- TASK-039 must replace this with observed input/output shape evidence before live CARLA control.",
            "",
            "## Redacted Excerpt",
            "",
            "```text",
            str(payload.get("redacted_excerpt", "")),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


__all__ = [
    "DEFAULT_ALPAMAYO_MODEL_ID",
    "classify_alpamayo_probe_artifacts",
    "expected_alpamayo_schema",
    "write_alpamayo_probe_report",
]
