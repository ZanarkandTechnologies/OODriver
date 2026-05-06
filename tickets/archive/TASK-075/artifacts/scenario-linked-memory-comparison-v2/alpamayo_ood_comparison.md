# Alpamayo OOD Evaluation

- scenario_id: `generated-base-animals-0076-regional-driving-behavior-000`
- open_loop_policy_evaluation: `True`
- closed_loop_control: `False`
- memory_augmented_live_run_available: `False`
- route_video_available: `False`
- video_evidence_path: `tickets/TASK-073/artifacts/fixture-long-ood-video-v2/ood_video_evidence.json`
- scenario_report_path: `tickets/TASK-072/artifacts/task72-live-candidate/carla_ood_demo.json`

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

- json_path: `tickets/TASK-075/artifacts/scenario-linked-memory-comparison-v2/memory_augmented_alpamayo_carla_input_package.json`
- torch_ready: `False`
- memory_context_count: `1`

## Evidence Warnings

- Generated-scene CARLA run did not pass; Alpamayo records should be treated as cached open-loop evidence.
- Scenario report id and video evidence id differ; this comparison is linked evidence, not same-capture proof.
- Memory-augmented package is not torch-ready yet; live rerun requires a successful CARLA capture package.
