"""Policy adapter implementations and setup-checked stubs."""

from __future__ import annotations

from time import perf_counter

from driverx.core.types import DrivingIntent, TrajectoryCandidate
from driverx.planning.hybrid import generate_hybrid_candidates
from driverx.planning.ranking import rank_candidates
from driverx.reasoning.mock import MockReasoner
from driverx.policies.alpamayo_live import AlpamayoLiveAdapter
from driverx.policies.types import (
    PolicyAction,
    PolicyAdapter,
    PolicyContext,
    PolicyDecision,
    PolicySetupError,
)


class MockPolicyAdapter:
    policy_id = "mock"

    def __init__(self, *, memory_aware: bool = False) -> None:
        self.memory_aware = memory_aware

    def decide(self, context: PolicyContext) -> PolicyDecision:
        started = perf_counter()
        hazards = [str(item) for item in context.frame.metadata.get("hazards", [])]
        if context.recipe is not None:
            hazards.extend(context.recipe.memory_query)
        has_memory = self.memory_aware and bool(context.memories)
        intent = DrivingIntent(
            scene_type=str(context.frame.metadata.get("scenario", "generated OOD scene")),
            hazards=hazards,
            ego_intent="preserve controllability before progress" if has_memory else "continue unless direct conflict is obvious",
            target_behavior="yield_then_proceed" if has_memory else "probe_then_continue",
            speed_profile="decelerate_then_creep" if has_memory else "steady",
            lateral_bias=_memory_lateral_bias(context) if has_memory else "center",
            uncertainty=0.24 if has_memory else 0.62,
        )
        trajectory = _simple_trajectory(context, intent)
        action = PolicyAction(
            mode="trajectory_chunk",
            trajectory=trajectory,
            control={
                "target_speed_mps": 3.0 if has_memory else 7.5,
                "yield": has_memory,
                "memory_guided": has_memory,
            },
            safety_notes=[
                memory.recommended_behavior
                for memory in context.memories[:2]
            ] if has_memory else ["No retrieved memory supplied; using generic caution."],
        )
        reason = (
            "Retrieved memory changed the decision toward slower yielding behavior."
            if has_memory
            else "No memory supplied, so mock policy uses a generic steady probe."
        )
        return PolicyDecision(
            policy_id=self.policy_id,
            adapter_kind="mock_memory" if has_memory else "mock",
            intent=intent,
            action=action,
            latency_ms=round((perf_counter() - started) * 1000.0, 4),
            reason_summary=reason,
            retrieved_memory_ids=context.memory_ids if has_memory else [],
        )


class HybridPlannerPolicyAdapter:
    policy_id = "hybrid"

    def decide(self, context: PolicyContext) -> PolicyDecision:
        started = perf_counter()
        intent = MockReasoner().infer_intent(context.frame)
        selected = rank_candidates(context.frame, generate_hybrid_candidates(context.frame, intent))
        action = PolicyAction(
            mode="local_fallback_trajectory",
            trajectory=selected,
            control={
                "target_speed_mps": float(selected.metadata.get("speed_multiplier", 1.0)) * 6.0,
                "yield": intent.target_behavior.startswith("yield"),
                "memory_guided": bool(context.memories),
            },
            safety_notes=["Deterministic hybrid fallback ranked trajectory candidates locally."],
        )
        return PolicyDecision(
            policy_id=self.policy_id,
            adapter_kind="local_hybrid",
            intent=intent,
            action=action,
            latency_ms=round((perf_counter() - started) * 1000.0, 4),
            reason_summary="Local hybrid adapter used mock intent plus motion-prior candidates.",
            retrieved_memory_ids=context.memory_ids,
        )


class SetupCheckedStubPolicyAdapter:
    def __init__(self, policy_id: str, guidance: str) -> None:
        self.policy_id = policy_id
        self.guidance = guidance

    def decide(self, context: PolicyContext) -> PolicyDecision:
        raise PolicySetupError(self.guidance)


def select_policy_adapter(name: str, *, memory_aware: bool = False) -> PolicyAdapter:
    normalized = name.replace("_", "-").lower()
    if normalized == "mock":
        return MockPolicyAdapter(memory_aware=memory_aware)
    if normalized in {"mock-memory", "memory-mock"}:
        return MockPolicyAdapter(memory_aware=True)
    if normalized == "hybrid":
        return HybridPlannerPolicyAdapter()
    if normalized in {"vlm-api", "api-vlm"}:
        return SetupCheckedStubPolicyAdapter(
            "vlm-api",
            "Set VLM_API_KEY and provider routing before using the API VLM adapter.",
        )
    if normalized in {"simlingo", "carllava"}:
        return SetupCheckedStubPolicyAdapter(
            "simlingo",
            "Run inspect-simlingo and plan-simlingo-run, then provide Linux NVIDIA, CARLA 0.9.15, and a SimLingo checkpoint before live CARLA policy runs.",
        )
    if normalized == "alpamayo":
        return SetupCheckedStubPolicyAdapter(
            "alpamayo",
            "Provide Alpamayo checkpoint/runtime access on a Linux NVIDIA host before selecting this adapter.",
        )
    if normalized == "alpamayo-live":
        return AlpamayoLiveAdapter()
    raise ValueError(f"Unknown policy adapter: {name}")


def _memory_lateral_bias(context: PolicyContext) -> str:
    text = " ".join(
        [
            *(memory.recommended_behavior for memory in context.memories),
            *(" ".join(memory.tags) for memory in context.memories),
        ]
    ).lower()
    if "side clearance" in text or "motorcycle" in text or "lateral" in text:
        return "left"
    return "center"


def _simple_trajectory(context: PolicyContext, intent: DrivingIntent) -> TrajectoryCandidate:
    (x0, y0), (x1, y1) = context.frame.ego_history_xy[-2], context.frame.ego_history_xy[-1]
    vx = max(0.05, x1 - x0)
    y = y1
    x = x1
    lateral_target = 0.5 if intent.lateral_bias == "left" else -0.5 if intent.lateral_bias == "right" else 0.0
    speed_scale = 0.45 if intent.speed_profile == "decelerate_then_creep" else 0.9
    points: list[tuple[float, float]] = []
    for _step in range(20):
        x += vx * speed_scale
        y += (lateral_target - y) * 0.08
        points.append((round(x, 4), round(y, 4)))
    return TrajectoryCandidate(
        points_xy=points,
        source="policy_mock_memory" if context.memories else "policy_mock",
        score=intent.uncertainty,
        metadata={"policy_id": "mock", "speed_scale": speed_scale},
    )


__all__ = [
    "HybridPlannerPolicyAdapter",
    "AlpamayoLiveAdapter",
    "MockPolicyAdapter",
    "SetupCheckedStubPolicyAdapter",
    "select_policy_adapter",
]
