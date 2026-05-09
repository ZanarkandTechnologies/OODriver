#!/usr/bin/env bash
set -euo pipefail

TMP_ROOT="$(mktemp -d)"
TRACE_PATH="${TMP_ROOT}/closed_loop_trace.json"
MANIFEST_PATH="${TMP_ROOT}/closed_loop_video_manifest.json"
VIDEO_PATH="${TMP_ROOT}/hero.mp4"

python3 - "$TMP_ROOT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
steps = []
for step_index in range(2):
    infer = root / f"infer_{step_index}.json"
    pred = root / f"pred_{step_index}.json"
    pred.write_text(json.dumps({"inference_state": "completed"}), encoding="utf-8")
    infer.write_text(
        json.dumps(
            {
                "mode": "remote-kasm",
                "status": "cached",
                "prediction_json_path": str(pred),
                "reasoning_snippet": "Nudge toward the cone, slow, and keep a safe offset.",
            }
        ),
        encoding="utf-8",
    )
    steps.append(
        {
            "step_index": step_index,
            "input_frame_id": 100 + step_index * 8,
            "post_action_frame_id": 106 + step_index * 8,
            "applied_control_count": 6,
            "inference_result_path": str(infer),
            "planned_vs_actual_error_m": 0.4,
            "visual_rgb_frame_paths": [str(root / f"visual_{step_index}_{i}.png") for i in range(6)],
            "action_rgb_frame_paths": [str(root / f"action_{step_index}_{i}.png") for i in range(4)],
            "ego_vehicle_visible": True,
            "visual_camera_role": "third_person_chase",
        }
    )

(root / "entity_tracks.json").write_text(json.dumps({"tracks": []}), encoding="utf-8")
Path(sys.argv[1], "hero.mp4").write_bytes(b"fixture manifest supplies deterministic video metrics")
Path(sys.argv[1], "closed_loop_trace.json").write_text(
    json.dumps(
        {
            "run_id": "closed-loop-visual-fixture",
            "scenario_id": "ego-drives-toward-cone",
            "mode": "paused_receding_horizon",
            "backend": "carla-live",
            "policy": "alpamayo-remote",
            "steps": steps,
            "control_applied_count": 12,
            "observed_after_action_count": 2,
            "source_frame_count": 12,
            "action_rgb_frame_count": 8,
            "ego_vehicle_visible": True,
            "visual_camera_role": "third_person_chase",
            "visible_ood_object": True,
            "entity_tracks_path": str(root / "entity_tracks.json"),
            "claim_boundaries": [
                "closed_loop_vla_control=paused_receding_horizon",
                "real_time_vla_control=false",
                "time_warped_offline_demo=true",
                "live_carla_provenance=true",
            ],
        }
    ),
    encoding="utf-8",
)
Path(sys.argv[1], "closed_loop_video_manifest.json").write_text(
    json.dumps(
        {
            "status": "passed",
            "output_video": str(root / "hero.mp4"),
            "sample_frame_paths": [str(root / "sample.png")],
            "source_frame_count": 12,
            "frame_count": 96,
            "duration_s": 4.0,
            "seconds_per_source_frame": 0.3333,
            "fps": 24,
            "backend": "carla-live",
            "policy": "alpamayo-remote",
            "step_count": 2,
            "live_carla_provenance": True,
            "recurrence_visible": True,
            "action_rgb_frame_count": 8,
            "ego_vehicle_visible": True,
            "visual_camera_role": "third_person_chase",
            "claim_boundaries": [
                "real_time_vla_control=false",
                "time_warped_offline_demo=true",
                "closed_loop_vla_control=paused_receding_horizon",
            ],
        }
    ),
    encoding="utf-8",
)
PY

PYTHONPATH=src python3 -m oodrive score-closed-loop-video \
  --trace "${TRACE_PATH}" \
  --manifest "${MANIFEST_PATH}" \
  --video "${VIDEO_PATH}" \
  --output-root "${TMP_ROOT}" \
  --run-id score \
  --metric-only

PYTHONPATH=src python3 -m oodrive f2d-evaluate-model \
  --routes tests/fixtures/fail2drive_routes \
  --fail2drive-root third_party/fail2drive \
  --output-root "${TMP_ROOT}" \
  --run-id f2d-matrix \
  --limit 2 \
  --dry-run \
  --reason \
  --demo-video \
  --metric-only

PYTHONPATH=src python3 -m oodrive f2d-demo-video \
  --evidence tests/fixtures/fail2drive_evidence/run_evidence.json \
  --reasoning tests/fixtures/fail2drive_reasoning/f2d_reasoning.json \
  --route tests/fixtures/fail2drive_routes/valid_roadblocked.xml \
  --input-video tests/fixtures/fail2drive_evidence/source.mp4 \
  --output-root "${TMP_ROOT}" \
  --run-id f2d-demo \
  --metric-only
