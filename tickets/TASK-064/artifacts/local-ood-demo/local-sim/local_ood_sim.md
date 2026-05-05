# Local OOD Simulator

- recipe_id: `generated-base-animals-0076-regional-driving-behavior-000`
- behavior_id: `motorcycle_filtering`
- simulator_kind: `driverx_local_2d_ood_sim`
- closed_loop_carla_claim: `False`
- worst_risk_level: `near_miss_proxy`
- min_distance_m: `1.7781`
- svg_path: `tickets/TASK-064/artifacts/local-ood-demo/local-sim/local_ood_sim.svg`
- html_path: `tickets/TASK-064/artifacts/local-ood-demo/local-sim/local_ood_sim.html`

## Policy Tracks

### policy

- policy_id: `mock`
- adapter_kind: `mock`
- risk_level: `near_miss_proxy`
- closest_actor_distance_m: `1.9679`
- target_behavior: `probe_then_continue`
- target_speed_mps: `7.5`
- retrieved_memory_ids: ``

### policy+memory

- policy_id: `mock`
- adapter_kind: `mock_memory`
- risk_level: `near_miss_proxy`
- closest_actor_distance_m: `1.8457`
- target_behavior: `yield_then_proceed`
- target_speed_mps: `3.0`
- retrieved_memory_ids: `mem-0002-fixture-prior-motorcycle-filtering, mem-0000-generalization-animals-1078, mem-0001-generalization-pedestriansonroad-1088`

### hybrid

- policy_id: `hybrid`
- adapter_kind: `local_hybrid`
- risk_level: `near_miss_proxy`
- closest_actor_distance_m: `1.7781`
- target_behavior: `stop`
- target_speed_mps: `2.52`
- retrieved_memory_ids: ``
