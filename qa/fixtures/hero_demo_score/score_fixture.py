#!/usr/bin/env python3
"""Fixture-only hero demo score runner for the autoresearch bootstrap."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else Path("qa/fixtures/hero_demo_score/candidate_demo.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    metrics = score_payload(payload)
    print(f"METRIC hero_demo_score={metrics['hero_demo_score']:.4f}")
    for name in (
        "duration_points",
        "motion_points",
        "visible_ood_points",
        "risk_points",
        "reasoning_points",
        "rag_points",
        "alpamayo_points",
        "evidence_points",
        "penalty_points",
    ):
        print(f"METRIC {name}={metrics[name]:.4f}")
    return 0


def score_payload(payload: dict[str, Any]) -> dict[str, float]:
    output_duration = _float(payload.get("output_duration_s"))
    source_duration = _float(payload.get("source_duration_s"))
    mean_speed = _float(payload.get("mean_ego_speed_mps"))
    visible_objects = _float(payload.get("visible_generated_object_count"))
    risk_events = _float(payload.get("risk_event_count"))
    reasoning_events = _float(payload.get("reasoning_event_count"))
    rag_events = _float(payload.get("rag_event_count"))
    alpamayo_events = _float(payload.get("alpamayo_prediction_count"))
    overlay_coverage = _clamp(_float(payload.get("frame_time_overlay_coverage")), 0.0, 1.0)
    min_distance = _float(payload.get("min_distance_m"))
    offroad_count = _float(payload.get("offroad_actor_count"))

    duration_points = 12.0 * _clamp(output_duration / 45.0, 0.0, 1.0)
    duration_points += 8.0 * _clamp(source_duration / 90.0, 0.0, 1.0)
    motion_points = 14.0 * _clamp(mean_speed / 4.5, 0.0, 1.0)
    visible_ood_points = 12.0 * _clamp(visible_objects / 4.0, 0.0, 1.0)
    risk_points = 12.0 * _clamp(risk_events / 5.0, 0.0, 1.0)
    reasoning_points = 14.0 * _clamp(reasoning_events / 3.0, 0.0, 1.0)
    rag_points = 10.0 * _clamp(rag_events / 3.0, 0.0, 1.0)
    alpamayo_points = 8.0 * _clamp(alpamayo_events / 3.0, 0.0, 1.0)
    evidence_points = 10.0 * overlay_coverage
    evidence_points += 5.0 if bool(payload.get("has_mp4")) else 0.0
    evidence_points += 5.0 if bool(payload.get("road_alignment_pass")) else 0.0

    penalty_points = 0.0
    if mean_speed < 3.0:
        penalty_points += (3.0 - mean_speed) * 6.0
    if output_duration < 30.0:
        penalty_points += (30.0 - output_duration) * 0.6
    if min_distance > 6.0:
        penalty_points += min((min_distance - 6.0) * 2.0, 16.0)
    penalty_points += offroad_count * 25.0
    penalty_points += (1.0 - overlay_coverage) * 12.0
    if not bool(payload.get("has_mp4")):
        penalty_points += 25.0
    if not bool(payload.get("road_alignment_pass")):
        penalty_points += 30.0

    raw_score = (
        duration_points
        + motion_points
        + visible_ood_points
        + risk_points
        + reasoning_points
        + rag_points
        + alpamayo_points
        + evidence_points
        - penalty_points
    )
    if not math.isfinite(raw_score):
        raw_score = 0.0
    return {
        "hero_demo_score": _clamp(raw_score, 0.0, 100.0),
        "duration_points": duration_points,
        "motion_points": motion_points,
        "visible_ood_points": visible_ood_points,
        "risk_points": risk_points,
        "reasoning_points": reasoning_points,
        "rag_points": rag_points,
        "alpamayo_points": alpamayo_points,
        "evidence_points": evidence_points,
        "penalty_points": penalty_points,
    }


def _float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
