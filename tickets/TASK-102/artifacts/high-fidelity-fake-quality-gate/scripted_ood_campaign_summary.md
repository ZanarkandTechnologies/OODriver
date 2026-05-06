# Scripted OOD Campaign

- status: `quality_blocked`
- requested_case_count: `1`
- case_count: `1`
- attempt_count: `3`
- quality_retry_limit: `2`
- quality_retried_case_count: `1`
- quality_selected_passed_count: `0`
- live_case_count: `0`
- mean_min_distance_m: `5.3151`
- fidelity: `{'mean_visible_actor_count': 2.0, 'mean_ego_route_progress_m': 30.0, 'max_ood_step_m': 0.8276, 'background_actor_count': 0, 'camera_presets': ['synthetic']}`
- worst_case: `000-retry02-generated-generalization-pedestriansonroad-1088-visual-noise-002-informal_right_of_way_push`
- quality_passed_count: `0`

## Cases

- `000-retry02-generated-generalization-pedestriansonroad-1088-visual-noise-002-informal_right_of_way_push`: behavior=`informal_right_of_way_push`, status=`blocked`, min_distance_m=`5.3151`, visible_actors=`2.0`, max_ood_step_m=`0.8276`, video_status=`None`, road_alignment=`None`, video=`None`

## Blockers

- 000-retry02-generated-generalization-pedestriansonroad-1088-visual-noise-002-informal_right_of_way_push: behavior_validation:max_acceleration_mps2 10.00 exceeds 8.00
- 000-retry02-generated-generalization-pedestriansonroad-1088-visual-noise-002-informal_right_of_way_push: duration_s 5.00 below 45.00
- 000-retry02-generated-generalization-pedestriansonroad-1088-visual-noise-002-informal_right_of_way_push: frame_count 0 below 180
- 000-retry02-generated-generalization-pedestriansonroad-1088-visual-noise-002-informal_right_of_way_push: visible_actor_count_mean 2.00 below 6.00
