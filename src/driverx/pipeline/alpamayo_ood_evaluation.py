"""Open-loop Alpamayo OOD comparison harness."""

from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driverx.memory import MemoryEntry
from driverx.policies.alpamayo_materializer import materialize_alpamayo_input
from driverx.policies.runner import memory_entries_from_json, sample_memory_entries


@dataclass(frozen=True)
class AlpamayoOodEvaluationInputs:
    baseline_decision_path: Path
    memory_decision_path: Path | None = None
    source_package_path: Path | None = None
    route_evidence_path: Path | None = None
    memory_entries_path: Path | None = None


def build_alpamayo_ood_evaluation(
    run_dir: Path,
    inputs: AlpamayoOodEvaluationInputs,
) -> dict[str, Any]:
    """Build a comparison report for Alpamayo with and without memory context."""

    run_dir.mkdir(parents=True, exist_ok=True)
    memories = _load_memories(inputs.memory_entries_path)
    baseline_payload = _load_json(inputs.baseline_decision_path)
    baseline = _decision_record(
        mode="alpamayo",
        path=inputs.baseline_decision_path,
        payload=baseline_payload,
        memories=[],
    )

    memory_package = None
    if inputs.source_package_path is not None:
        memory_package = _write_memory_augmented_package(
            source_package_path=inputs.source_package_path,
            run_dir=run_dir,
            memories=memories,
        )

    memory_record: dict[str, Any]
    memory_payload: dict[str, Any] | None = None
    if inputs.memory_decision_path is not None:
        memory_payload = _load_json(inputs.memory_decision_path)
        memory_record = _decision_record(
            mode="alpamayo+memory",
            path=inputs.memory_decision_path,
            payload=memory_payload,
            memories=memories,
        )
    else:
        memory_record = _missing_memory_record(memories, memory_package)

    route_evidence = _load_json(inputs.route_evidence_path) if inputs.route_evidence_path else None
    comparison = {
        "open_loop_policy_evaluation": True,
        "closed_loop_control": False,
        "scenario_id": _scenario_id(baseline, route_evidence),
        "records": [baseline, memory_record],
        "memory_ids": [memory.entry_id for memory in memories],
        "memory_context": [_memory_summary(memory) for memory in memories],
        "trajectory_delta": _trajectory_delta(
            baseline.get("trajectory_points_xy"),
            memory_record.get("trajectory_points_xy"),
        ),
        "reasoning_delta": _reasoning_delta(baseline, memory_record),
        "latency_delta_ms": _latency_delta(baseline, memory_record),
        "route_evidence": _compact_route_evidence(route_evidence, inputs.route_evidence_path),
        "memory_augmented_package": memory_package,
        "safety_flags": _safety_flags(baseline, memory_record, route_evidence),
        "inputs": {
            "baseline_decision_path": str(inputs.baseline_decision_path),
            "memory_decision_path": str(inputs.memory_decision_path)
            if inputs.memory_decision_path is not None
            else None,
            "source_package_path": str(inputs.source_package_path)
            if inputs.source_package_path is not None
            else None,
            "route_evidence_path": str(inputs.route_evidence_path)
            if inputs.route_evidence_path is not None
            else None,
            "memory_entries_path": str(inputs.memory_entries_path)
            if inputs.memory_entries_path is not None
            else None,
        },
    }
    return write_alpamayo_ood_evaluation(run_dir, comparison)


def write_alpamayo_ood_evaluation(run_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "alpamayo_ood_comparison.json"
    report_path = run_dir / "alpamayo_ood_comparison.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _load_memories(path: Path | None) -> list[MemoryEntry]:
    if path is None:
        return sample_memory_entries()
    return memory_entries_from_json(path)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {"value": payload}


def _decision_record(
    *,
    mode: str,
    path: Path,
    payload: dict[str, Any],
    memories: list[MemoryEntry],
) -> dict[str, Any]:
    decision = _extract_decision(payload)
    trajectory = _trajectory_points(decision)
    control = _mapping(_mapping(decision.get("action")).get("control"))
    return {
        "mode": mode,
        "path": str(path),
        "policy_id": decision.get("policy_id"),
        "adapter_kind": decision.get("adapter_kind"),
        "open_loop_policy_evaluation": bool(
            control.get("open_loop_policy_evaluation", payload.get("open_loop_policy_evaluation", True))
        ),
        "closed_loop_control": bool(control.get("closed_loop_control", False)),
        "latency_ms": _number(decision.get("latency_ms")),
        "vram_peak_mb": _number(control.get("vram_peak_mb"))
        or _number(_mapping(payload.get("prediction_summary")).get("vram_peak_mb")),
        "retrieved_memory_ids": list(decision.get("retrieved_memory_ids", []))
        or [memory.entry_id for memory in memories],
        "cot_snippet": _cot_snippet(decision, payload),
        "target_behavior": _mapping(decision.get("intent")).get("target_behavior"),
        "speed_profile": _mapping(decision.get("intent")).get("speed_profile"),
        "trajectory_points_xy": trajectory,
        "trajectory_summary": _trajectory_summary(trajectory),
        "setup_blocker": decision.get("setup_blocker"),
    }


def _missing_memory_record(
    memories: list[MemoryEntry],
    memory_package: dict[str, Any] | None,
) -> dict[str, Any]:
    package_path = None
    if memory_package is not None:
        package_path = memory_package.get("json_path")
    next_step = (
        "Run scripts/run_remote_alpamayo_carla_inference.sh against the memory-augmented "
        "package, then rerun build-alpamayo-ood-comparison with --memory-decision."
    )
    if package_path:
        next_step = (
            "Run scripts/run_remote_alpamayo_carla_inference.sh "
            f"{package_path} <gpu-ssh-target> <local-output>, then rerun "
            "build-alpamayo-ood-comparison with --memory-decision."
        )
    return {
        "mode": "alpamayo+memory",
        "path": None,
        "policy_id": "alpamayo-live",
        "adapter_kind": "alpamayo_open_loop",
        "open_loop_policy_evaluation": True,
        "closed_loop_control": False,
        "latency_ms": None,
        "vram_peak_mb": None,
        "retrieved_memory_ids": [memory.entry_id for memory in memories],
        "cot_snippet": None,
        "target_behavior": None,
        "speed_profile": None,
        "trajectory_points_xy": None,
        "trajectory_summary": None,
        "setup_blocker": "memory-augmented live Alpamayo decision was not supplied",
        "next_step": next_step,
    }


def _write_memory_augmented_package(
    *,
    source_package_path: Path,
    run_dir: Path,
    memories: list[MemoryEntry],
) -> dict[str, Any]:
    source = source_package_path.expanduser()
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Alpamayo package must be a JSON object: {source}")

    payload["memory_context"] = [_memory_payload(memory) for memory in memories]
    payload["nav_text"] = _augment_nav_text(payload.get("nav_text"), memories)
    target = run_dir / "memory_augmented_alpamayo_carla_input_package.json"
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Keep the package self-contained when the source used relative image paths.
    source_images = source.parent / "images"
    target_images = run_dir / "images"
    if source_images.exists() and not target_images.exists():
        shutil.copytree(source_images, target_images)

    manifest = materialize_alpamayo_input(target)
    report_path = run_dir / "memory_augmented_alpamayo_carla_input_package.md"
    report_path.write_text(_memory_package_markdown(target, manifest.to_jsonable()), encoding="utf-8")
    return {
        "json_path": str(target),
        "report_path": str(report_path),
        "torch_ready": manifest.torch_ready,
        "validation_errors": manifest.validation_errors,
        "memory_context_count": manifest.memory_context_count,
        "nav_text_excerpt": str(payload.get("nav_text", ""))[:500],
    }


def _augment_nav_text(value: Any, memories: list[MemoryEntry]) -> str:
    base = str(value).strip() if isinstance(value, str) and value.strip() else "follow the route safely"
    if not memories:
        return base
    memory_lines = [
        f"{memory.entry_id}: {memory.principle} Recommended behavior: {memory.recommended_behavior}"
        for memory in memories[:3]
    ]
    return "\n".join(
        [
            base,
            "DriverX retrieved safety memory, prompt-side only:",
            *memory_lines,
        ]
    )


def _memory_payload(memory: MemoryEntry) -> dict[str, Any]:
    return {
        "entry_id": memory.entry_id,
        "situation": memory.situation,
        "observed_failure": memory.observed_failure,
        "principle": memory.principle,
        "recommended_behavior": memory.recommended_behavior,
        "source_scenario": memory.source_scenario,
        "confidence": memory.confidence,
        "tags": memory.tags,
    }


def _memory_summary(memory: MemoryEntry) -> dict[str, Any]:
    return {
        "entry_id": memory.entry_id,
        "principle": memory.principle,
        "recommended_behavior": memory.recommended_behavior,
        "confidence": memory.confidence,
        "tags": memory.tags,
    }


def _extract_decision(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("policy_decision"), dict):
        return dict(payload["policy_decision"])
    if isinstance(payload.get("decision"), dict):
        return dict(payload["decision"])
    if payload.get("policy_id") is not None:
        return payload
    raise ValueError("Policy decision payload must contain policy_decision or policy_id.")


def _trajectory_points(decision: dict[str, Any]) -> list[list[float]] | None:
    trajectory = _mapping(_mapping(decision.get("action")).get("trajectory"))
    points = trajectory.get("points_xy")
    if not isinstance(points, list):
        return None
    parsed: list[list[float]] = []
    for point in points:
        if isinstance(point, (list, tuple)) and len(point) >= 2:
            parsed.append([float(point[0]), float(point[1])])
    return parsed or None


def _trajectory_summary(points: list[list[float]] | None) -> dict[str, Any] | None:
    if not points:
        return None
    distances = [_l2(points[index - 1], points[index]) for index in range(1, len(points))]
    return {
        "point_count": len(points),
        "start_xy": points[0],
        "end_xy": points[-1],
        "path_length_m": round(sum(distances), 4),
    }


def _trajectory_delta(
    baseline: list[list[float]] | None,
    memory: list[list[float]] | None,
) -> dict[str, Any]:
    if not baseline or not memory:
        return {
            "available": False,
            "reason": "both baseline and memory trajectory points are required",
        }
    count = min(len(baseline), len(memory))
    distances = [_l2(baseline[index], memory[index]) for index in range(count)]
    return {
        "available": True,
        "point_count": count,
        "mean_l2_m": round(sum(distances) / max(count, 1), 4),
        "max_l2_m": round(max(distances) if distances else 0.0, 4),
        "final_l2_m": round(distances[-1] if distances else 0.0, 4),
    }


def _reasoning_delta(baseline: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    baseline_text = str(baseline.get("cot_snippet") or "")
    memory_text = str(memory.get("cot_snippet") or "")
    return {
        "baseline_chars": len(baseline_text),
        "memory_chars": len(memory_text),
        "changed": bool(baseline_text and memory_text and baseline_text != memory_text),
        "available": bool(baseline_text and memory_text),
    }


def _latency_delta(baseline: dict[str, Any], memory: dict[str, Any]) -> float | None:
    baseline_latency = _number(baseline.get("latency_ms"))
    memory_latency = _number(memory.get("latency_ms"))
    if baseline_latency is None or memory_latency is None:
        return None
    return round(memory_latency - baseline_latency, 4)


def _cot_snippet(decision: dict[str, Any], payload: dict[str, Any]) -> str | None:
    for value in (
        decision.get("reason_summary"),
        _mapping(payload.get("prediction_summary")).get("cot_summary"),
        payload.get("cot_summary"),
    ):
        if isinstance(value, str) and value.strip():
            return value.strip()[:500]
    return None


def _compact_route_evidence(
    payload: dict[str, Any] | None,
    path: Path | None,
) -> dict[str, Any] | None:
    if payload is None:
        return None
    return {
        "path": str(path) if path is not None else None,
        "status": payload.get("status"),
        "video": _mapping(payload.get("video")),
        "metrics": _mapping(payload.get("metrics")),
        "blockers": list(payload.get("blockers", [])) if isinstance(payload.get("blockers"), list) else [],
    }


def _scenario_id(
    baseline: dict[str, Any],
    route_evidence: dict[str, Any] | None,
) -> str:
    route_id = _mapping(route_evidence or {}).get("route_id")
    if route_id:
        return str(route_id)
    return f"alpamayo-open-loop::{baseline.get('policy_id') or 'unknown'}"


def _safety_flags(
    baseline: dict[str, Any],
    memory: dict[str, Any],
    route_evidence: dict[str, Any] | None,
) -> dict[str, Any]:
    route_metrics = _mapping(_mapping(route_evidence or {}).get("metrics"))
    return {
        "open_loop_only": True,
        "closed_loop_control_claimed": bool(
            baseline.get("closed_loop_control") or memory.get("closed_loop_control")
        ),
        "memory_augmented_live_run_available": memory.get("setup_blocker") is None,
        "route_video_available": bool(_mapping(_mapping(route_evidence or {}).get("video")).get("exists")),
        "route_score_available": any(
            route_metrics.get(key) is not None
            for key in ("driving_score", "route_completion", "infraction_penalty")
        ),
    }


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _l2(a: list[float], b: list[float]) -> float:
    return math.sqrt((float(a[0]) - float(b[0])) ** 2 + (float(a[1]) - float(b[1])) ** 2)


def _memory_package_markdown(path: Path, manifest: dict[str, Any]) -> str:
    lines = [
        "# Memory-Augmented Alpamayo Package",
        "",
        f"- json_path: `{path}`",
        f"- torch_ready: `{manifest.get('torch_ready')}`",
        f"- memory_context_count: `{manifest.get('memory_context_count')}`",
        f"- image_frames_shape: `{manifest.get('image_frames_shape')}`",
        "",
        "## Validation Errors",
        "",
    ]
    lines.extend([f"- {error}" for error in list(manifest.get("validation_errors", []))] or ["- none"])
    return "\n".join(lines) + "\n"


def _markdown(payload: dict[str, Any]) -> str:
    flags = _mapping(payload.get("safety_flags"))
    delta = _mapping(payload.get("trajectory_delta"))
    lines = [
        "# Alpamayo OOD Evaluation",
        "",
        f"- scenario_id: `{payload.get('scenario_id')}`",
        f"- open_loop_policy_evaluation: `{payload.get('open_loop_policy_evaluation')}`",
        f"- closed_loop_control: `{payload.get('closed_loop_control')}`",
        f"- memory_augmented_live_run_available: `{flags.get('memory_augmented_live_run_available')}`",
        f"- route_video_available: `{flags.get('route_video_available')}`",
        "",
        "## Trajectory Delta",
        "",
    ]
    for key, value in delta.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Memory", ""])
    for memory in list(payload.get("memory_context", [])):
        lines.append(
            f"- `{memory['entry_id']}`: {memory['recommended_behavior']} "
            f"(confidence `{memory['confidence']}`)"
        )
    lines.extend(["", "## Records", ""])
    for record in list(payload.get("records", [])):
        lines.extend(
            [
                f"### {record.get('mode')}",
                "",
                f"- policy_id: `{record.get('policy_id')}`",
                f"- latency_ms: `{record.get('latency_ms')}`",
                f"- vram_peak_mb: `{record.get('vram_peak_mb')}`",
                f"- closed_loop_control: `{record.get('closed_loop_control')}`",
                f"- retrieved_memory_ids: `{', '.join(record.get('retrieved_memory_ids') or [])}`",
                f"- target_behavior: `{record.get('target_behavior')}`",
                f"- speed_profile: `{record.get('speed_profile')}`",
                "",
            ]
        )
        if record.get("cot_snippet"):
            lines.extend(["CoC snippet:", "", f"> {record['cot_snippet']}", ""])
        if record.get("setup_blocker"):
            lines.append(f"- setup_blocker: {record['setup_blocker']}")
        if record.get("next_step"):
            lines.append(f"- next_step: {record['next_step']}")
        lines.append("")
    package = _mapping(payload.get("memory_augmented_package"))
    if package:
        lines.extend(
            [
                "## Memory-Augmented Package",
                "",
                f"- json_path: `{package.get('json_path')}`",
                f"- torch_ready: `{package.get('torch_ready')}`",
                f"- memory_context_count: `{package.get('memory_context_count')}`",
                "",
            ]
        )
    return "\n".join(lines)


__all__ = [
    "AlpamayoOodEvaluationInputs",
    "build_alpamayo_ood_evaluation",
    "write_alpamayo_ood_evaluation",
]
