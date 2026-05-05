"""Offline Alpamayo adapter rehearsal using saved prediction JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir
from driverx.core.types import DrivingIntent
from driverx.datasets.fixtures import load_fixture_frame
from driverx.memory import MemoryEntry
from driverx.policies.alpamayo_input import (
    build_alpamayo_input_package,
    write_alpamayo_input_package,
)
from driverx.policies.alpamayo_trajectory import (
    alpamayo_prediction_to_trajectory,
    load_prediction_json,
    write_alpamayo_trajectory_conversion,
)
from driverx.policies.runner import write_policy_decision
from driverx.policies.types import PolicyAction, PolicyDecision


def run_alpamayo_offline_fixture(
    *,
    fixture: str,
    prediction_json: Path,
    output_root: Path,
    run_id: str,
    nav_text: str | None = None,
    memory_entries: list[MemoryEntry] | None = None,
    sample_index: int = 0,
) -> dict[str, Any]:
    """Rehearse the Alpamayo policy path without loading the model."""

    frame = load_fixture_frame(fixture)
    run_dir = prepare_run_dir(output_root, run_id)
    input_package = build_alpamayo_input_package(
        frame,
        nav_text=nav_text,
        memory_entries=memory_entries,
    )
    input_summary = write_alpamayo_input_package(run_dir / "input", input_package)
    trajectory_summary = write_alpamayo_trajectory_conversion(
        run_dir / "trajectory",
        prediction_json=prediction_json,
        sample_index=sample_index,
    )
    native_prediction = load_prediction_json(prediction_json)
    trajectory = alpamayo_prediction_to_trajectory(
        native_prediction,
        sample_index=sample_index,
        source="alpamayo_offline_saved_prediction",
        reasoning=_reasoning_from_input(input_package),
    )
    decision = _policy_decision(
        input_package=input_package,
        trajectory=trajectory,
        memory_entries=memory_entries or [],
    )
    decision_summary = write_policy_decision(run_dir / "decision", decision)
    summary: dict[str, Any] = {
        "policy_id": decision.policy_id,
        "adapter_kind": decision.adapter_kind,
        "fixture": fixture,
        "prediction_json": str(prediction_json),
        "run_dir": str(run_dir),
        "input_package_path": input_summary["json_path"],
        "trajectory_path": trajectory_summary["json_path"],
        "decision_path": decision_summary["json_path"],
        "report_path": str(run_dir / "alpamayo_offline_policy.md"),
        "memory_ids": decision.retrieved_memory_ids,
        "nav_text": input_package.nav_text,
        "target_points": len(trajectory.points_xy),
    }
    Path(summary["report_path"]).write_text(_markdown(summary), encoding="utf-8")
    (run_dir / "alpamayo_offline_policy.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    summary["json_path"] = str(run_dir / "alpamayo_offline_policy.json")
    return summary


def _policy_decision(
    *,
    input_package: Any,
    trajectory: Any,
    memory_entries: list[MemoryEntry],
) -> PolicyDecision:
    has_memory = bool(memory_entries)
    intent = DrivingIntent(
        scene_type="alpamayo_offline_fixture",
        hazards=[
            memory.situation
            for memory in memory_entries[:3]
        ] or ["saved Alpamayo prediction replay"],
        ego_intent="execute saved Alpamayo trajectory through DriverX safety seam",
        target_behavior="memory_guided_replay" if has_memory else "saved_prediction_replay",
        speed_profile="trajectory_chunk",
        lateral_bias="center",
        uncertainty=0.35 if has_memory else 0.55,
    )
    action = PolicyAction(
        mode="trajectory_chunk",
        trajectory=trajectory,
        control={
            "target_speed_mps": _estimate_initial_speed(trajectory.points_xy),
            "yield": has_memory,
            "memory_guided": has_memory,
            "offline_replay": True,
        },
        safety_notes=[
            "Offline Alpamayo rehearsal used saved pred_xyz; no live model claim is made.",
            *(memory.recommended_behavior for memory in memory_entries[:2]),
        ],
    )
    return PolicyDecision(
        policy_id="alpamayo-offline",
        adapter_kind="alpamayo_saved_prediction",
        intent=intent,
        action=action,
        latency_ms=0.0,
        reason_summary=_reasoning_from_input(input_package),
        retrieved_memory_ids=[memory.entry_id for memory in memory_entries],
    )


def _estimate_initial_speed(points_xy: list[tuple[float, float]]) -> float:
    if len(points_xy) < 2:
        return 0.0
    dx = points_xy[1][0] - points_xy[0][0]
    dy = points_xy[1][1] - points_xy[0][1]
    return round((dx * dx + dy * dy) ** 0.5 * 4.0, 4)


def _reasoning_from_input(input_package: Any) -> str:
    pieces = ["Saved Alpamayo pred_xyz converted through DriverX trajectory contract."]
    if input_package.nav_text:
        pieces.append(f"Navigation context: {input_package.nav_text}.")
    if input_package.memory_context:
        pieces.append(f"Retrieved {len(input_package.memory_context)} memory entries.")
    return " ".join(pieces)


def _markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Alpamayo Offline Policy",
            "",
            f"- policy_id: `{summary['policy_id']}`",
            f"- adapter_kind: `{summary['adapter_kind']}`",
            f"- fixture: `{summary['fixture']}`",
            f"- prediction_json: `{summary['prediction_json']}`",
            f"- target_points: `{summary['target_points']}`",
            f"- memory_ids: `{summary['memory_ids']}`",
            f"- nav_text: `{summary['nav_text']}`",
            f"- input_package_path: `{summary['input_package_path']}`",
            f"- trajectory_path: `{summary['trajectory_path']}`",
            f"- decision_path: `{summary['decision_path']}`",
            "",
        ]
    )


__all__ = [
    "run_alpamayo_offline_fixture",
]
