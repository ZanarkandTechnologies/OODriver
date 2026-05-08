#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

python3 - <<'PY'
import json
import math
from pathlib import Path

def load(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}

def exists(path: str) -> bool:
    return Path(path).exists()

def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))

hero = load("artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/hero_demo_video.json")
batch = load("tickets/TASK-104/artifacts/alpamayo-rag-batch-v1/alpamayo_ood_batch_summary.json")
fail2drive = load("tickets/TASK-105/artifacts/fail2drive-extension-report/fail2drive_extension_report.json")

ledger_paths = [
    "artifacts/runs/task145-memory-ledger-v1/retrieval_ledger.json",
    "tickets/TASK-145/artifacts/retrieval-ledger/retrieval_ledger.json",
]
ledger = next((load(path) for path in ledger_paths if exists(path)), {})
diff = load("artifacts/runs/task146-reasoning-diff-v1/alpamayo_reasoning_diff.json")
panel = load("artifacts/runs/task147-evidence-panel-v1/reasoning_presentation_report.json")
ancestry = load("artifacts/runs/task148-ancestry-cards-v1/scenario_ancestry_cards.json")

ledger_candidates = ledger.get("candidates", []) if isinstance(ledger.get("candidates"), list) else []
ledger_selected = ledger.get("selected_memory_ids", []) if isinstance(ledger.get("selected_memory_ids"), list) else []
ledger_has_scores = any(isinstance(item, dict) and item.get("score") is not None for item in ledger_candidates)
ledger_has_rejections = any(isinstance(item, dict) and item.get("selected") is False for item in ledger_candidates)
ledger_has_sources = any(isinstance(item, dict) and item.get("source_scenario") for item in ledger_candidates)
retrieval_ledger_points = (
    7.0 * bool(ledger)
    + 5.0 * bool(ledger_selected)
    + 5.0 * ledger_has_scores
    + 4.0 * ledger_has_rejections
    + 4.0 * ledger_has_sources
)

batch_records = batch.get("records", []) if isinstance(batch.get("records"), list) else []
diff_cases = diff.get("cases", []) if isinstance(diff.get("cases"), list) else []
reasoning_diff_points = (
    6.0 * bool(batch and batch.get("status") == "passed")
    + 5.0 * clamp(float(batch.get("memory_case_count") or 0) / 3.0)
    + 5.0 * clamp(float(batch.get("reasoning_changed_count") or 0) / 2.0)
    + 4.0 * bool(batch.get("mean_latency_ms"))
    + 4.0 * bool(batch.get("mean_vram_peak_mb") or batch.get("max_vram_peak_mb"))
    + 6.0 * clamp(len(diff_cases) / 3.0)
)

hero_events = hero.get("events", []) if isinstance(hero.get("events"), list) else []
panel_chapters = panel.get("chapters", []) if isinstance(panel.get("chapters"), list) else []
max_hud_rows = float(panel.get("max_hud_rows") or 99)
citations = panel.get("citation_count")
decongested_points = (
    5.0 * clamp(len(hero_events) / 8.0)
    + 7.0 * bool(panel)
    + 6.0 * clamp(len(panel_chapters) / 4.0)
    + 4.0 * (max_hud_rows <= 3)
    + 3.0 * clamp(float(citations or 0) / 3.0)
)

cards = ancestry.get("cards", []) if isinstance(ancestry.get("cards"), list) else []
fd_records = fail2drive.get("records", []) if isinstance(fail2drive.get("records"), list) else []
ancestry_points = (
    4.0 * bool(fail2drive)
    + 3.0 * clamp(len(fd_records) / 4.0)
    + 4.0 * bool(ancestry)
    + 4.0 * clamp(len(cards) / 4.0)
)

claims = []
for payload in (hero, batch, ledger, diff, panel, ancestry):
    value = payload.get("claim_boundaries") if isinstance(payload, dict) else None
    if isinstance(value, list):
        claims.extend(str(item) for item in value)
claim_points = (
    2.0 * ("sampled_open_loop_reasoning=true" in claims)
    + 2.0 * ("real_time_vla_control=false" in claims)
    + 2.0 * ("closed_loop_vla_control=false" in claims or "closed_loop_carla_control=false" in claims)
    + 2.0 * any("retrieval_backend=" in claim for claim in claims)
    + 2.0 * any("citation" in claim or "source" in claim for claim in claims)
)

score = retrieval_ledger_points + reasoning_diff_points + decongested_points + ancestry_points + claim_points
score = round(max(0.0, min(100.0, score)), 4)

metrics = {
    "m4_m5_evidence_clarity_score": score,
    "retrieval_ledger_points": round(retrieval_ledger_points, 4),
    "reasoning_diff_points": round(reasoning_diff_points, 4),
    "decongested_presentation_points": round(decongested_points, 4),
    "scenario_ancestry_points": round(ancestry_points, 4),
    "claim_honesty_points": round(claim_points, 4),
}

for key, value in metrics.items():
    if not math.isfinite(float(value)):
        raise SystemExit(f"non-finite metric {key}={value}")
    print(f"METRIC {key}={value:.4f}")
PY
