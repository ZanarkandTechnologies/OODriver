"""Policy fixture execution and artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from driverx.core.artifacts import prepare_run_dir
from driverx.datasets.fixtures import load_fixture_frame
from driverx.memory import MemoryEntry
from driverx.policies.adapters import select_policy_adapter
from driverx.policies.types import PolicyContext, PolicyDecision, PolicySetupError


def run_policy_fixture(
    *,
    policy: str,
    fixture: str,
    output_root: Path,
    run_id: str,
    memory_entries: list[MemoryEntry] | None = None,
    memory_aware: bool = False,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    frame = load_fixture_frame(fixture)
    run_dir = prepare_run_dir(output_root, run_id)
    adapter = select_policy_adapter(policy, memory_aware=memory_aware)
    context = PolicyContext(frame=frame, memories=memory_entries or [], metadata=metadata or {})
    try:
        decision = adapter.decide(context)
    except PolicySetupError as exc:
        return _write_setup_blocker(run_dir, policy, str(exc))
    return write_policy_decision(run_dir, decision)


def write_policy_decision(run_dir: Path, decision: PolicyDecision) -> dict[str, object]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "policy_decision.json"
    report_path = run_dir / "policy_report.md"
    payload = decision.to_jsonable()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_decision_markdown(decision), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def sample_memory_entries() -> list[MemoryEntry]:
    return [
        MemoryEntry(
            entry_id="mem-sample-motorcycle-filtering",
            situation="regional two-wheeler filtering between lanes",
            observed_failure="Policy committed to lane center while a fast motorcycle crossed laterally.",
            principle="Regional two-wheeler behavior should be treated as lateral occupancy uncertainty.",
            recommended_behavior="Slow early, yield, and keep extra side clearance before committing.",
            source_scenario="fixture_memory_motorcycle_filtering",
            confidence=0.82,
            tags=["motorcycle", "filtering", "lateral", "regional"],
        )
    ]


def memory_entries_from_json(path: Path) -> list[MemoryEntry]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw.get("entries", raw) if isinstance(raw, dict) else raw
    loaded: list[MemoryEntry] = []
    for item in list(entries):
        payload = dict(item)
        loaded.append(
            MemoryEntry(
                entry_id=str(payload["entry_id"]),
                situation=str(payload["situation"]),
                observed_failure=str(payload["observed_failure"]),
                principle=str(payload["principle"]),
                recommended_behavior=str(payload["recommended_behavior"]),
                source_scenario=str(payload["source_scenario"]),
                confidence=float(payload["confidence"]),
                tags=[str(tag) for tag in list(payload.get("tags", []))],
            )
        )
    return loaded


def _write_setup_blocker(run_dir: Path, policy: str, guidance: str) -> dict[str, object]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "policy_id": policy,
        "setup_blocker": guidance,
        "json_path": str(run_dir / "policy_setup_blocker.json"),
        "report_path": str(run_dir / "policy_report.md"),
    }
    Path(payload["json_path"]).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    Path(payload["report_path"]).write_text(
        "\n".join(["# Policy Setup Blocker", "", f"- policy: `{policy}`", f"- blocker: {guidance}", ""]),
        encoding="utf-8",
    )
    return payload


def _decision_markdown(decision: PolicyDecision) -> str:
    return "\n".join(
        [
            "# Policy Decision",
            "",
            f"- policy_id: `{decision.policy_id}`",
            f"- adapter_kind: `{decision.adapter_kind}`",
            f"- latency_ms: `{decision.latency_ms}`",
            f"- retrieved_memory_ids: `{', '.join(decision.retrieved_memory_ids)}`",
            f"- target_behavior: `{decision.intent.target_behavior}`",
            f"- speed_profile: `{decision.intent.speed_profile}`",
            f"- action_mode: `{decision.action.mode}`",
            "",
            "## Reason",
            "",
            decision.reason_summary,
            "",
        ]
    )


__all__ = [
    "memory_entries_from_json",
    "run_policy_fixture",
    "sample_memory_entries",
    "write_policy_decision",
]
