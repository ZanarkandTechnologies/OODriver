# TASK-131 QA: Score-Gated Hero Demo

## Verdict

PASS. TASK-128 live OODrive evidence was recovered from the Kasm RunPod host and
used with the stronger TASK-102 CARLA source clip to render a judge-visible
OODrive hero demo. The passing artifact scores `100.0 / 100` with no blockers.

## Evidence Intake

- Source host: RunPod Kasm pod `poz4gv6ryu2571`
- Remote repo: `/workspace/0xDriver`
- Local artifact root: `artifacts/runs/task128-oodrive-live-product`
- Pulled evidence:
  - `scenario_studio_db.json`
  - `runs/task128-oodrive-live-place/run_manifest.json`
  - `runs/task128-oodrive-live-place/carla_ood_demo.json`
  - `runs/task128-oodrive-live-place/entity_tracks.json`
  - `runs/task128-oodrive-live-place/road_alignment_report.json`
  - `runs/task128-oodrive-live-place/placement_trace.json`
  - `reasoning/evaluations/task128-oodrive-live-alpamayo-fresh-evaluation/policy_evaluation.json`
  - `reasoning/policy-decisions/task128-oodrive-live-alpamayo-fresh-policy/alpamayo_policy_decision.json`

## Render Attempts

### v1

```bash
PYTHONPATH=src python3 -m oodrive demo-video \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --run artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/run_manifest.json \
  --evaluation artifacts/runs/task128-oodrive-live-product/reasoning/evaluations/task128-oodrive-live-alpamayo-fresh-evaluation/policy_evaluation.json \
  --input-video artifacts/exported/task102_high_fidelity_hero_v6_full.mp4 \
  --speed-factor 4 \
  --run-id task131-score-gated-hero-v1
```

Result: rendered successfully, but score status was `blocked` because
`output_duration_s=21.0` is below the `30.0s` minimum.

### v2

```bash
PYTHONPATH=src python3 -m oodrive demo-video \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --run artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/run_manifest.json \
  --evaluation artifacts/runs/task128-oodrive-live-product/reasoning/evaluations/task128-oodrive-live-alpamayo-fresh-evaluation/policy_evaluation.json \
  --input-video artifacts/exported/task102_high_fidelity_hero_v6_full.mp4 \
  --speed-factor 2 \
  --run-id task131-score-gated-hero-v2
```

Result: rendered successfully.

## Passing Score

```bash
PYTHONPATH=src python3 -m oodrive score-demo \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --run artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/run_manifest.json \
  --evaluation artifacts/runs/task128-oodrive-live-product/reasoning/evaluations/task128-oodrive-live-alpamayo-fresh-evaluation/policy_evaluation.json \
  --video artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/oodrive_hero_demo.mp4 \
  --overlay-report artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/hero_demo_video.json \
  --output-root artifacts/runs/task128-oodrive-live-product/demo-scores \
  --run-id task131-score-gated-hero-v2-score \
  --metric-only
```

Output:

```text
METRIC hero_demo_score=100.0000
```

Score report:

- Status: `passed`
- Score: `100.0 / 100`
- Threshold: `72.0`
- Output duration: `42.0s`
- Frame count: `630`
- Frame/time overlay coverage: `1.0`
- Visible generated object count: `3`
- Risk event count: `591`
- Reasoning event count: `8`
- RAG event count: `8`
- Alpamayo prediction count: `1`
- Blockers: `[]`

## Artifact Links

- Hero MP4:
  `artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/oodrive_hero_demo.mp4`
- Overlay report:
  `artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/hero_demo_video.json`
- Overlay Markdown:
  `artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/hero_demo_video.md`
- Score JSON:
  `artifacts/runs/task128-oodrive-live-product/demo-scores/task131-score-gated-hero-v2-score/hero_demo_score.json`
- Score Markdown:
  `artifacts/runs/task128-oodrive-live-product/demo-scores/task131-score-gated-hero-v2-score/hero_demo_score.md`
- Sample overlay frame:
  `artifacts/runs/task128-oodrive-live-product/demo-videos/task131-score-gated-hero-v2/overlay/frames/frame_000001.png`

## Claim Boundaries

- `closed_loop_vla_control=false`
- `real_time_vla_control=false`
- `sampled_open_loop_reasoning=true`
- `time_warped_offline_demo=true`
- `overlay_uses_simulator_ground_truth_risk=true`
- `objects_placed_in_carla=true`

The artifact remains sampled open-loop Alpamayo reasoning over captured CARLA
frames. It does not claim real-time closed-loop VLA control.
