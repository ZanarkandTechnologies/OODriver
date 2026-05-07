"""Shared helpers for OODrive product CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.scenarios.studio_db import ScenarioStudioDb, replace_db

OODRIVE_COMMAND_PREFIX = "PYTHONPATH=src python3 -m oodrive"


def oodrive_command(args: str) -> str:
    clean_args = args.strip()
    return OODRIVE_COMMAND_PREFIX if not clean_args else f"{OODRIVE_COMMAND_PREFIX} {clean_args}"


def queue_next_commands(db_path: Path, records: list[dict[str, Any]]) -> list[str]:
    commands: list[str] = []
    for record in records[:3]:
        scenario_id = record.get("scenario_id")
        if scenario_id:
            commands.append(
                oodrive_command(f"run --db {db_path} --scenario-id {scenario_id} --policy mock")
            )
    return commands


def artifact_paths(payload: dict[str, Any]) -> dict[str, str]:
    return {
        key: str(value)
        for key, value in payload.items()
        if key.endswith("_path") and isinstance(value, str)
    }


def select_queue_record(db: ScenarioStudioDb, scenario_id: str | None) -> dict[str, Any]:
    if not db.queue:
        raise ValueError("Studio DB queue is empty. Run oodrive queue first.")
    if scenario_id is None:
        for record in db.queue:
            if str(record.get("run_status", "")) in {"needs_runtime", "blocked", "partial", ""}:
                return dict(record)
        return dict(db.queue[0])
    for record in db.queue:
        if scenario_id in {str(record.get("scenario_id", "")), str(record.get("candidate_id", ""))}:
            return dict(record)
    raise ValueError(f"Scenario id not found in queue: {scenario_id}")


def update_queue_record(db: ScenarioStudioDb, candidate_id: str, run_status: str) -> ScenarioStudioDb:
    queue = []
    for record in db.queue:
        row = dict(record)
        if str(row.get("candidate_id", "")) == candidate_id:
            row["run_status"] = run_status
        queue.append(row)
    return replace_db(db, queue=queue)


def mock_actions_for_record(record: dict[str, Any]) -> list[dict[str, Any]]:
    tags = list(record.get("ood_tags", [])) if isinstance(record.get("ood_tags"), list) else []
    return [
        {"tick": 0, "action": "observe", "reason": f"detect OOD pressure: {', '.join(tags[:4]) or 'unknown'}"},
        {"tick": 1, "action": "slow", "reason": "reserve margin for actor uncertainty"},
        {
            "tick": 2,
            "action": "yield_or_creep",
            "reason": "maintain solvable progress without memorized scenario assumptions",
        },
    ]


def load_or_latest_run(db: ScenarioStudioDb, run_manifest_path: Path | None) -> dict[str, Any]:
    if run_manifest_path is not None:
        payload = json.loads(run_manifest_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
        raise ValueError("Run manifest JSON must be a mapping.")
    if db.runs:
        return dict(db.runs[-1])
    raise ValueError("No run manifest supplied and the Studio DB has no runs.")


def load_or_latest_evaluation(db: ScenarioStudioDb, evaluation_path: Path | None) -> dict[str, Any]:
    if evaluation_path is not None:
        payload = json.loads(evaluation_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
        raise ValueError("Evaluation JSON must be a mapping.")
    if db.evaluations:
        return dict(db.evaluations[-1])
    return {}


def candidate_for_run(db: ScenarioStudioDb, run_payload: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(run_payload.get("candidate_id", ""))
    for candidate in db.candidates:
        if str(candidate.get("candidate_id", "")) == candidate_id:
            return dict(candidate)
    return {}


def memory_ids_for_candidate(candidate: dict[str, Any]) -> list[str]:
    recipe = candidate.get("compiled_recipe", {})
    query = recipe.get("memory_query", []) if isinstance(recipe, dict) else []
    if not isinstance(query, list):
        return []
    return [f"tag:{item}" for item in query[:6]]


def load_prediction(path: Path | None, blockers: list[str]) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        blockers.append(f"Could not load Alpamayo prediction JSON: {exc}")
        return {}
    if not isinstance(payload, dict):
        blockers.append("Alpamayo prediction JSON must be a mapping.")
        return {}
    return payload


def cot_from_prediction(prediction: dict[str, Any]) -> str | None:
    raw = prediction.get("cot") or prediction.get("reasoning") or prediction.get("coc")
    extra = prediction.get("extra")
    if raw is None and isinstance(extra, dict):
        raw = extra.get("cot") or extra.get("reasoning")
    if isinstance(raw, list):
        raw = " ".join(str(item) for item in raw[:3])
    if raw is None:
        return None
    text = str(raw).strip()
    return text[:500] if text else None


def latency_from_prediction(prediction: dict[str, Any]) -> float | None:
    raw = prediction.get("latency_ms")
    if raw is None and isinstance(prediction.get("timings_ms"), dict):
        raw = sum(float(value) for value in prediction["timings_ms"].values() if isinstance(value, (int, float)))
    if isinstance(raw, list):
        values = [float(item) for item in raw if isinstance(item, (int, float))]
        return round(sum(values) / len(values), 3) if values else None
    if isinstance(raw, (int, float)):
        return round(float(raw), 3)
    return None


def trajectory_summary_from_prediction(prediction: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key in ("pred_xyz_shape", "pred_rot_shape", "trajectory_shape"):
        if key in prediction:
            summary[key] = prediction[key]
    pred_xyz = prediction.get("pred_xyz")
    if isinstance(pred_xyz, list):
        summary["pred_xyz_outer_len"] = len(pred_xyz)
    if not summary:
        summary["status"] = "missing_prediction_trajectory"
    return summary


__all__ = [
    "OODRIVE_COMMAND_PREFIX",
    "artifact_paths",
    "candidate_for_run",
    "cot_from_prediction",
    "latency_from_prediction",
    "load_or_latest_evaluation",
    "load_or_latest_run",
    "load_prediction",
    "memory_ids_for_candidate",
    "mock_actions_for_record",
    "oodrive_command",
    "queue_next_commands",
    "select_queue_record",
    "trajectory_summary_from_prediction",
    "update_queue_record",
]
