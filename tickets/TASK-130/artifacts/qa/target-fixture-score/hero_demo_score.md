# Hero Demo Score

- Status: `passed`
- Score: `100.0` / 100
- Threshold: `72.0`
- Candidate: `target-hero-demo-contract`
- Video: `artifacts/exported/oodrive_hero_reasoning_overlay.mp4`

## Metrics

| metric | value |
| --- | --- |
| `source_duration_s` | `120.0` |
| `output_duration_s` | `45.0` |
| `frame_count` | `675` |
| `mean_ego_speed_mps` | `4.5` |
| `visible_generated_object_count` | `5` |
| `risk_event_count` | `8` |
| `reasoning_event_count` | `4` |
| `rag_event_count` | `4` |
| `alpamayo_prediction_count` | `4` |
| `frame_time_overlay_coverage` | `1.0` |
| `min_distance_m` | `1.4` |

## Components

| component | points |
| --- | --- |
| `hero_demo_score` | `100.0` |
| `duration_points` | `20.0` |
| `motion_points` | `14.0` |
| `visible_ood_points` | `12.0` |
| `risk_points` | `12.0` |
| `reasoning_points` | `14.0` |
| `rag_points` | `10.0` |
| `alpamayo_points` | `8.0` |
| `evidence_points` | `20.0` |
| `penalty_points` | `0.0` |

## Warnings

- fixture_mode=true; do not promote this score as live simulator evidence.

## Claim Boundaries

- `time_warped_offline_demo=true`
- `sampled_open_loop_reasoning=true`
- `real_time_vla_control=false`
