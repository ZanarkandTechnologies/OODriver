# Hero Demo Score

- Status: `blocked`
- Score: `30.4889` / 100
- Threshold: `72.0`
- Candidate: `task128-current-video-baseline`
- Video: `artifacts/exported/task128_oodrive_live_product.mp4`

## Metrics

| metric | value |
| --- | --- |
| `source_duration_s` | `90.0` |
| `output_duration_s` | `30.0` |
| `frame_count` | `450` |
| `mean_ego_speed_mps` | `1.1` |
| `visible_generated_object_count` | `3` |
| `risk_event_count` | `2` |
| `reasoning_event_count` | `1` |
| `rag_event_count` | `1` |
| `alpamayo_prediction_count` | `1` |
| `frame_time_overlay_coverage` | `0.0` |
| `min_distance_m` | `1.82` |

## Components

| component | points |
| --- | --- |
| `hero_demo_score` | `30.4889` |
| `duration_points` | `16.0` |
| `motion_points` | `3.4222` |
| `visible_ood_points` | `9.0` |
| `risk_points` | `4.8` |
| `reasoning_points` | `4.6667` |
| `rag_points` | `3.3333` |
| `alpamayo_points` | `2.6667` |
| `evidence_points` | `10.0` |
| `penalty_points` | `23.4` |

## Blockers

- hero_demo_score 30.49 below 72.00
- mean_ego_speed_mps 1.10 below 3.00
- risk_event_count 2 below 5
- reasoning_event_count 1 below 3
- rag_event_count 1 below 3
- frame_time_overlay_coverage 0.00 below 0.95

## Warnings

- fixture_mode=true; do not promote this score as live simulator evidence.

## Claim Boundaries

- `time_warped_offline_demo=true`
- `sampled_open_loop_reasoning=true`
- `real_time_vla_control=false`
