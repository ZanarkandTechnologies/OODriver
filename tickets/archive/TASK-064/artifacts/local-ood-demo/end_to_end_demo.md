# End-To-End Local OOD Demo

- demo_id: `local-ood-demo`
- status: `ready`
- recipe_id: `generated-base-animals-0076-regional-driving-behavior-000`
- mutation: `regional_driving_behavior`
- behavior_id: `motorcycle_filtering`
- retrieved_memory_ids: `mem-0002-fixture-prior-motorcycle-filtering, mem-0000-generalization-animals-1078, mem-0001-generalization-pedestriansonroad-1088`
- local_simulator: `True`
- closed_loop_carla: `False`
- live_vla: `False`

## What Ran

1. Generated one deterministic OOD recipe from Fail2Drive-like seeds.
2. Simulated one erratic regional behavior trace.
3. Retrieved compact prior failure memory for the recipe.
4. Ran the mock policy once without memory and once with memory.
5. Converted both trajectories into bounded cached-replay controls.
6. Rendered a local top-down simulator artifact.

## Policy Reaction

### policy

- target_behavior: `probe_then_continue`
- speed_profile: `steady`
- target_speed_mps: `7.5`
- yield: `False`
- memory_guided: `False`
- latency_ms: `0.0478`

### policy+memory

- target_behavior: `yield_then_proceed`
- speed_profile: `decelerate_then_creep`
- target_speed_mps: `3.0`
- yield: `True`
- memory_guided: `True`
- latency_ms: `0.0275`

### hybrid

- target_behavior: `stop`
- speed_profile: `brake`
- target_speed_mps: `2.52`
- yield: `False`
- memory_guided: `False`
- latency_ms: `0.2375`

## Local Simulator Summary

- worst_risk_level: `near_miss_proxy`
- min_distance_m: `1.7781`
- svg: `tickets/TASK-064/artifacts/local-ood-demo/local-sim/local_ood_sim.svg`
- html: `tickets/TASK-064/artifacts/local-ood-demo/local-sim/local_ood_sim.html`
- reaction_matrix: `tickets/TASK-064/artifacts/local-ood-demo/policy/policy_reaction_matrix.json`

## Claim Boundary

This artifact proves the DriverX OOD generation, memory, policy, trajectory, and local simulation loop. It is not a live CARLA route score and not real-time closed-loop VLA driving.
