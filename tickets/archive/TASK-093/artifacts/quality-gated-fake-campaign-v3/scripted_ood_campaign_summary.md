# Scripted OOD Campaign

- status: `quality_blocked`
- requested_case_count: `2`
- case_count: `2`
- attempt_count: `8`
- quality_retry_limit: `3`
- quality_retried_case_count: `2`
- quality_selected_passed_count: `0`
- live_case_count: `0`
- mean_min_distance_m: `0.875`
- worst_case: `001-retry03-generated-generalization-customobstacles-1028-visual-noise-007-sudden_brake`
- quality_passed_count: `0`

## Cases

- `000-retry03-generated-base-animals-0076-obstacle-substitution-003-motorcycle_filtering`: behavior=`motorcycle_filtering`, status=`passed`, min_distance_m=`1.75`, video_status=`None`, road_alignment=`None`, video=`None`
- `001-retry03-generated-generalization-customobstacles-1028-visual-noise-007-sudden_brake`: behavior=`sudden_brake`, status=`blocked`, min_distance_m=`0.0`, video_status=`None`, road_alignment=`None`, video=`None`

## Blockers

- 001-retry03-generated-generalization-customobstacles-1028-visual-noise-007-sudden_brake: behavior_validation:max_deceleration_mps2 13.60 exceeds 9.00
- 001-retry03-generated-generalization-customobstacles-1028-visual-noise-007-sudden_brake: behavior_validation:time_to_conflict_s 0.00 is too early for a solvable setup
- 000-retry03-generated-base-animals-0076-obstacle-substitution-003-motorcycle_filtering: video evidence is required but missing
- 000-retry03-generated-base-animals-0076-obstacle-substitution-003-motorcycle_filtering: road alignment is required but missing or failed
- 001-retry03-generated-generalization-customobstacles-1028-visual-noise-007-sudden_brake: video evidence is required but missing
- 001-retry03-generated-generalization-customobstacles-1028-visual-noise-007-sudden_brake: road alignment is required but missing or failed
