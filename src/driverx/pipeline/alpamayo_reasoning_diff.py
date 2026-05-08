"""Summarize how memory changes sampled Alpamayo open-loop reasoning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CLAIM_BOUNDARIES = [
    "sampled_open_loop_reasoning=true",
    "closed_loop_vla_control=false",
    "real_time_vla_control=false",
    "reasoning_diff_uses_recorded_alpamayo_outputs=true",
    "source_citations=true",
]


def build_alpamayo_reasoning_diff(
    batch_path: Path,
    *,
    retrieval_ledger_paths: tuple[Path, ...] = (),
    output_root: Path = Path("artifacts/runs"),
    run_id: str = "oodrive-reasoning-diff",
) -> dict[str, Any]:
    batch = _load_json(batch_path)
    ledgers = [_load_json(path) for path in retrieval_ledger_paths if path.exists()]
    cases = [_case_from_record(record) for record in _list(batch.get("records"))]
    report = {
        "report_id": run_id,
        "batch_path": str(batch_path),
        "case_count": len(cases),
        "reasoning_changed_count": sum(1 for case in cases if case.get("reasoning_changed")),
        "memory_case_count": sum(1 for case in cases if case.get("memory_ids")),
        "retrieval_ledger_count": len(ledgers),
        "retrieval_ledgers": [_ledger_summary(ledger) for ledger in ledgers],
        "cases": cases,
        "claim_boundaries": CLAIM_BOUNDARIES,
    }
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "alpamayo_reasoning_diff.json"
    md_path = run_dir / "alpamayo_reasoning_diff.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    return {**report, "json_path": str(json_path), "report_path": str(md_path)}


def extract_reasoning_diff_events(diff_report: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for case in _list(diff_report.get("cases")):
        events.append(
            {
                "scenario_id": case.get("scenario_id"),
                "memory_ids": case.get("memory_ids", []),
                "before": case.get("baseline_reasoning_snippet"),
                "after": case.get("memory_reasoning_snippet"),
                "delta": case.get("reasoning_delta_summary"),
                "latency_ms": case.get("latency_ms"),
            }
        )
    return events


def _case_from_record(record: dict[str, Any]) -> dict[str, Any]:
    comparison = _comparison(record)
    comparison_records = _list(comparison.get("records")) if comparison else []
    baseline = _record_for_mode(comparison_records, "alpamayo")
    memory = _record_for_mode(comparison_records, "memory")
    memory_ids = _string_list(record.get("memory_ids") or comparison.get("memory_ids") if comparison else record.get("memory_ids"))
    return {
        "scenario_id": record.get("scenario_id") or record.get("case_id"),
        "case_id": record.get("case_id") or record.get("scenario_id"),
        "comparison_path": record.get("comparison_path"),
        "reasoning_changed": _reasoning_changed(record, comparison),
        "memory_ids": memory_ids,
        "baseline_reasoning_snippet": _snippet(baseline),
        "memory_reasoning_snippet": _snippet(memory),
        "reasoning_delta_summary": _delta_summary(record, baseline, memory, comparison),
        "latency_ms": record.get("latency_ms"),
        "latency_delta_ms": record.get("latency_delta_ms") or (comparison or {}).get("latency_delta_ms"),
        "trajectory_final_l2_m": record.get("trajectory_final_l2_m"),
        "vram_peak_mb": record.get("vram_peak_mb"),
        "open_loop_policy_evaluation": True,
        "closed_loop_control": False,
    }


def _comparison(record: dict[str, Any]) -> dict[str, Any]:
    comparison_path = record.get("comparison_path")
    if isinstance(comparison_path, str):
        path = Path(comparison_path)
        if path.exists():
            try:
                payload = _load_json(path)
                if isinstance(payload, dict):
                    return payload
            except (OSError, json.JSONDecodeError):
                return {}
    return {}


def _reasoning_changed(record: dict[str, Any], comparison: dict[str, Any]) -> bool:
    if "reasoning_changed" in record:
        return bool(record.get("reasoning_changed"))
    delta = comparison.get("reasoning_delta")
    if isinstance(delta, dict):
        return bool(delta.get("changed") or delta.get("reasoning_changed"))
    return bool(delta)


def _record_for_mode(records: list[Any], token: str) -> dict[str, Any]:
    for record in records:
        if isinstance(record, dict) and token in str(record.get("mode", "")):
            return record
    return {}


def _snippet(record: dict[str, Any]) -> str | None:
    for key in ("cot_snippet", "reason_summary", "target_behavior"):
        value = record.get(key)
        if value:
            return str(value)[:260]
    return None


def _delta_summary(
    record: dict[str, Any],
    baseline: dict[str, Any],
    memory: dict[str, Any],
    comparison: dict[str, Any],
) -> str:
    if comparison.get("reasoning_delta"):
        return str(comparison["reasoning_delta"])[:320]
    base_text = _snippet(baseline) or "baseline reasoning unavailable"
    memory_text = _snippet(memory) or "memory-augmented reasoning unavailable"
    changed = bool(record.get("reasoning_changed"))
    return f"reasoning_changed={changed}; baseline=`{base_text}`; memory=`{memory_text}`"


def _ledger_summary(ledger: dict[str, Any]) -> dict[str, Any]:
    return {
        "query_id": ledger.get("query_id"),
        "retrieval_backend": ledger.get("retrieval_backend"),
        "selected_memory_ids": ledger.get("selected_memory_ids", []),
        "selected_count": len(_list(ledger.get("selected_memory_ids"))),
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Alpamayo Memory Reasoning Diff",
        "",
        f"- Cases: `{report['case_count']}`",
        f"- Reasoning changed: `{report['reasoning_changed_count']}`",
        f"- Memory cases: `{report['memory_case_count']}`",
        "",
    ]
    for case in report["cases"]:
        lines.extend(
            [
                f"## {case.get('scenario_id')}",
                "",
                f"- Memory IDs: `{', '.join(case.get('memory_ids', [])) or 'none'}`",
                f"- Baseline: {case.get('baseline_reasoning_snippet') or 'unavailable'}",
                f"- Memory: {case.get('memory_reasoning_snippet') or 'unavailable'}",
                f"- Delta: {case.get('reasoning_delta_summary')}",
                "",
            ]
        )
    return "\n".join(lines)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in _list(value)]


__all__ = ["build_alpamayo_reasoning_diff", "extract_reasoning_diff_events"]
