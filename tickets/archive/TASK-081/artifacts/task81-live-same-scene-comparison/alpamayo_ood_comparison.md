# Alpamayo OOD Evaluation

- scenario_id: `generated-base-animals-0076-regional-driving-behavior-000`
- open_loop_policy_evaluation: `True`
- closed_loop_control: `False`
- memory_augmented_live_run_available: `True`
- route_video_available: `False`
- video_evidence_path: `tickets/TASK-079/artifacts/task79-live-ood-video/ood_video_evidence.json`
- scenario_report_path: `tickets/TASK-078/artifacts/task78-live-ood-capture-v3/carla_ood_demo.json`

## Trajectory Delta

- `available`: `True`
- `point_count`: `20`
- `mean_l2_m`: `1.0226`
- `max_l2_m`: `2.6886`
- `final_l2_m`: `2.6886`

## Memory

- `mem-sample-motorcycle-filtering`: Slow early, yield, and keep extra side clearance before committing. (confidence `0.82`)

## Records

### alpamayo

- policy_id: `alpamayo-live`
- latency_ms: `108765.59`
- vram_peak_mb: `23507.7`
- closed_loop_control: `False`
- retrieved_memory_ids: ``
- target_behavior: `open_loop_trajectory_eval`
- speed_profile: `trajectory_chunk`

CoC snippet:

> [[['Keep distance to the lead scooter since it is directly ahead in our path']]]


### alpamayo+memory

- policy_id: `alpamayo-live`
- latency_ms: `46129.12`
- vram_peak_mb: `23557.31`
- closed_loop_control: `False`
- retrieved_memory_ids: `mem-sample-motorcycle-filtering`
- target_behavior: `open_loop_trajectory_eval`
- speed_profile: `trajectory_chunk`

CoC snippet:

> [[['Keep distance to the lead scooter since it is directly ahead in our path']]]


## Memory-Augmented Package

- json_path: `tickets/TASK-081/artifacts/task81-live-same-scene-comparison/memory_augmented_alpamayo_carla_input_package.json`
- torch_ready: `True`
- memory_context_count: `1`
