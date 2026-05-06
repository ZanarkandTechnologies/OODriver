"""Live evidence helpers for submission demo packs."""

from __future__ import annotations

from typing import Any


def live_evidence(
    route_evidence: dict[str, Any],
    alpamayo_comparison: dict[str, Any],
    cached_replay: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "route": {
            "status": route_evidence.get("status"),
            "video": _mapping(route_evidence.get("video")),
            "metrics": _mapping(route_evidence.get("metrics")),
        },
        "alpamayo_comparison": {
            "open_loop_policy_evaluation": alpamayo_comparison.get("open_loop_policy_evaluation"),
            "closed_loop_control": alpamayo_comparison.get("closed_loop_control"),
            "trajectory_delta": _mapping(alpamayo_comparison.get("trajectory_delta")),
            "reasoning_delta": _mapping(alpamayo_comparison.get("reasoning_delta")),
            "safety_flags": _mapping(alpamayo_comparison.get("safety_flags")),
            "evidence_warnings": list(alpamayo_comparison.get("evidence_warnings", []))
            if isinstance(alpamayo_comparison.get("evidence_warnings"), list)
            else [],
        },
        "cached_replay": _cached_replay_summary(cached_replay or {}),
    }


def preferred_blocker(blockers: list[str]) -> str:
    if not blockers:
        return "No open blocker in the provided blocker ledger."
    for keyword in (
        "TASK-072",
        "run-carla-ood-demo",
        "host.docker.internal:2000",
        "scripted OOD",
        "Town13",
        "fail2drive,carla,map",
        "CARLA package containing Town13",
    ):
        for blocker in blockers:
            if keyword.lower() in blocker.lower():
                return blocker
    return blockers[0]


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _cached_replay_summary(payload: dict[str, Any]) -> dict[str, Any]:
    trace = _mapping(payload.get("trace"))
    return {
        "available": bool(payload),
        "closed_loop_control": payload.get("closed_loop_control"),
        "trajectory_frame": trace.get("trajectory_frame"),
        "command_count": payload.get("command_count"),
        "applied_count": payload.get("applied_count"),
        "dry_run": payload.get("dry_run"),
        "safety_clamp_count": len(list(payload.get("safety_clamps", [])))
        if isinstance(payload.get("safety_clamps"), list)
        else 0,
    }


__all__ = ["live_evidence", "preferred_blocker"]
