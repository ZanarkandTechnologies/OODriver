# Scripted OOD Campaign

- status: `passed`
- campaign_id: `task102-high-fidelity-hero-v6`
- case: `000-generated-base-animals-0076-regional-driving-behavior-000-motorcycle_filtering`
- live_case_count: `1`
- frame_count: `420`
- duration_s: `84.0`
- min_distance_m: `0.2`
- quality_passed_count: `1`
- video_status: `passed`
- remote_video_path: `/workspace/0xDriver/artifacts/runs/task102-high-fidelity-hero-v6/cases/000-generated-base-animals-0076-regional-driving-behavior-000-motorcycle_filtering/video/task102_high_fidelity_hero_v6_full.mp4`
- fidelity: `{"background_actor_count": 1, "camera_presets": ["wide_context"], "max_ood_step_m": 1.2, "mean_ego_route_progress_m": 418.0, "mean_visible_actor_count": 6.0}`

## Quality Gates

| gate | value | status |
|---|---:|---|
| duration_s >= 45 | 84.0 | passed |
| frame_count >= 180 | 420 | passed |
| min_distance_m <= 6 | 0.2 | passed |
| road_aligned | true | passed |
| visible_actor_count_mean >= 6 | 6.0 | passed |
| max_ood_step_m <= 1.25 | 1.2 | passed |

## Claim Boundaries

- `scripted_ood_campaign=true`
- `stock_fail2drive_score=false`
- `real_time_vla_control=false`
- heavy MP4 kept on RunPod, not committed
