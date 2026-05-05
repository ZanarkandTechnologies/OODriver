"""Live evidence helpers for submission demo packs."""

from __future__ import annotations

from typing import Any


def live_evidence(route_evidence: dict[str, Any], alpamayo_comparison: dict[str, Any]) -> dict[str, Any]:
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
        },
    }


def preferred_blocker(blockers: list[str]) -> str:
    if not blockers:
        return "No open blocker in the provided blocker ledger."
    for keyword in ("Town13", "fail2drive,carla,map", "CARLA package containing Town13"):
        for blocker in blockers:
            if keyword.lower() in blocker.lower():
                return blocker
    return blockers[0]


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


__all__ = ["live_evidence", "preferred_blocker"]
