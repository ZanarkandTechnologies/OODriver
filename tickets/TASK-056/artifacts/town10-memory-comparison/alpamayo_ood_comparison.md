# Alpamayo OOD Evaluation

- scenario_id: `alpamayo-open-loop::alpamayo-live`
- open_loop_policy_evaluation: `True`
- closed_loop_control: `False`
- memory_augmented_live_run_available: `True`
- route_video_available: `True`

## Trajectory Delta

- `available`: `True`
- `point_count`: `20`
- `mean_l2_m`: `0.9666`
- `max_l2_m`: `2.8886`
- `final_l2_m`: `2.8886`

## Memory

- `mem-sample-motorcycle-filtering`: Slow early, yield, and keep extra side clearance before committing. (confidence `0.82`)

## Records

### alpamayo

- policy_id: `alpamayo-live`
- latency_ms: `99795.97`
- vram_peak_mb: `23235.75`
- closed_loop_control: `False`
- retrieved_memory_ids: ``
- target_behavior: `open_loop_trajectory_eval`
- speed_profile: `trajectory_chunk`

CoC snippet:

> [[['Accelerate to proceed through the intersection since the traffic light turns green']]]


### alpamayo+memory

- policy_id: `alpamayo-live`
- latency_ms: `100407.07`
- vram_peak_mb: `23373.31`
- closed_loop_control: `False`
- retrieved_memory_ids: `mem-sample-motorcycle-filtering`
- target_behavior: `open_loop_trajectory_eval`
- speed_profile: `trajectory_chunk`

CoC snippet:

> [[['Keep lane since the intersection is clear and no lead vehicle is present']]]


## Memory-Augmented Package

- json_path: `tickets/TASK-056/artifacts/town10-memory-comparison/memory_augmented_alpamayo_carla_input_package.json`
- torch_ready: `True`
- memory_context_count: `1`
