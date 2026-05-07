# Reasoning Overlay Video

- Status: `passed`
- Output video: `artifacts/exported/task111_reasoning_overlay_v1.mp4`
- Sample frame: `tickets/TASK-111/artifacts/reasoning-overlay-v1/reasoning_overlay_frames/frames/frame_000001.png`
- Events: `10`
- Frames: `420`

## Events

| Start | Risk | Memory | Action |
| --- | --- | --- | --- |
| 2.0 | motorcycle_filtering | front | 1.111m from generated_asset_asset_fallen_cargo_sack | `mem-sample-motorcycle-filtering` | brake smoothly, hold lane, leave escape gap |
| 1.75 | motorcycle_filtering | front | 1.157m from generated_asset_asset_reflective_flood_barrier | `mem-sample-motorcycle-filtering` | brake smoothly, hold lane, leave escape gap |
| 1.833 | motorcycle_filtering | front | 1.21m from generated_asset_asset_reflective_flood_barrier | `mem-sample-motorcycle-filtering` | brake smoothly, hold lane, leave escape gap |
| 2.0 | motorcycle_filtering | front | 1.792m from ood_actor_0 | `mem-sample-motorcycle-filtering` | brake smoothly, hold lane, leave escape gap |
| 1.667 | motorcycle_filtering | front | 1.948m from generated_asset_asset_reflective_flood_barrier | `mem-sample-motorcycle-filtering` | brake smoothly, hold lane, leave escape gap |
| 2.0 | motorcycle_filtering | front | 2.114m from ood_actor_0 | `mem-sample-motorcycle-filtering` | brake smoothly, hold lane, leave escape gap |
| 2.0 | motorcycle_filtering | front | 2.164m from generated_asset_asset_fallen_cargo_sack | `mem-sample-motorcycle-filtering` | brake smoothly, hold lane, leave escape gap |
| 2.0 | motorcycle_filtering | front | 2.645m from ood_actor_0 | `mem-sample-motorcycle-filtering` | brake smoothly, hold lane, leave escape gap |
| 1.583 | motorcycle_filtering | front | 2.782m from generated_asset_asset_reflective_flood_barrier | `mem-sample-motorcycle-filtering` | brake smoothly, hold lane, leave escape gap |
| 2.0 | motorcycle_filtering | front | 3.003m from generated_asset_asset_fallen_cargo_sack | `mem-sample-motorcycle-filtering` | brake smoothly, hold lane, leave escape gap |

## Claim Boundaries

- `time_warped_offline_demo=true`
- `sampled_open_loop_reasoning=true`
- `real_time_vla_control=false`
- `overlay_uses_simulator_ground_truth_risk=true`
