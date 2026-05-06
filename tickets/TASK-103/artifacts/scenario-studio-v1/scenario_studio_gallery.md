# Scenario Studio Gallery

- Batch: `scenario-studio-v1-001`
- Prompts: `10`
- Candidates: `20`
- Curation counts: `{'accept_partial': 20}`

## Generated Candidates

| candidate | status | score | environment | behavior | next action |
|---|---|---|---|---|---|
| studio-0017-malaysian-wet-roadwork-motorbike-filters-between-v00 | accept_partial | 0.7 | construction_lane_closure | motorcycle_filtering | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0017-malaysian-wet-roadwork-motorbike-filters-between-v01 | accept_partial | 0.7 | construction_lane_closure | motorcycle_filtering | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0018-school-zone-occlusion-parked-van-hides-a-child-c-v00 | accept_partial | 0.7 | school_zone_unstructured_crossing | no_signal_cut_in | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0018-school-zone-occlusion-parked-van-hides-a-child-c-v01 | accept_partial | 0.7 | school_zone_unstructured_crossing | no_signal_cut_in | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0019-flooded-urban-road-low-obstacle-blends-into-wate-v00 | accept_partial | 0.7 | flooded_road | informal_right_of_way_push | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0019-flooded-urban-road-low-obstacle-blends-into-wate-v01 | accept_partial | 0.7 | flooded_road | informal_right_of_way_push | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0020-night-rain-glare-reflective-sign-distracts-the-p-v00 | accept_partial | 0.7 | night_rain_fog | no_signal_cut_in | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0020-night-rain-glare-reflective-sign-distracts-the-p-v01 | accept_partial | 0.7 | night_rain_fog | no_signal_cut_in | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0021-double-parked-market-street-door-swerve-vehicle--v00 | accept_partial | 0.7 | roadside_market_occlusion | double_parked_door_swerve | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0021-double-parked-market-street-door-swerve-vehicle--v01 | accept_partial | 0.7 | roadside_market_occlusion | double_parked_door_swerve | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0022-dense-malaysian-traffic-wrong-way-shoulder-creep-v00 | accept_partial | 0.7 | roadside_market_occlusion | wrong_way_shoulder_creep | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0022-dense-malaysian-traffic-wrong-way-shoulder-creep-v01 | accept_partial | 0.7 | roadside_market_occlusion | wrong_way_shoulder_creep | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0023-construction-merge-no-signal-cut-in-happens-besi-v00 | accept_partial | 0.7 | construction_lane_closure | no_signal_cut_in | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0023-construction-merge-no-signal-cut-in-happens-besi-v01 | accept_partial | 0.7 | construction_lane_closure | no_signal_cut_in | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0024-roadside-market-occlusion-informal-right-of-way--v00 | accept_partial | 0.7 | roadside_market_occlusion | informal_right_of_way_push | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0024-roadside-market-occlusion-informal-right-of-way--v01 | accept_partial | 0.7 | roadside_market_occlusion | informal_right_of_way_push | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0025-monsoon-school-zone-scooter-filters-through-fog--v00 | accept_partial | 0.7 | school_zone_unstructured_crossing | motorcycle_filtering | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0025-monsoon-school-zone-scooter-filters-through-fog--v01 | accept_partial | 0.7 | school_zone_unstructured_crossing | motorcycle_filtering | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0026-visual-noise-stress-irrelevant-ufo-like-billboar-v00 | accept_partial | 0.7 | construction_lane_closure | no_signal_cut_in | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |
| studio-0026-visual-noise-stress-irrelevant-ufo-like-billboar-v01 | accept_partial | 0.7 | construction_lane_closure | no_signal_cut_in | Run TASK-102 high-fidelity CARLA evidence, then TASK-104 Alpamayo baseline vs memory. |

## Prompt Plans

### `studio-0017-malaysian-wet-roadwork-motorbike-filters-between`

- Prompt: Malaysian wet roadwork: motorbike filters between cars while a lorry brakes without signal
- Environment: `construction_lane_closure`
- Behavior: `motorcycle_filtering`
- Memory query: `construction, malaysian_driving, motorcycle_filtering, roadwork, sudden_brake, visual_noise, wet_road`
- Safe behavior: slow early, keep lateral buffer, and avoid squeezing two-wheelers

### `studio-0018-school-zone-occlusion-parked-van-hides-a-child-c`

- Prompt: School-zone occlusion: parked van hides a child crossing while a dropped bag sits near the lane edge
- Environment: `school_zone_unstructured_crossing`
- Behavior: `no_signal_cut_in`
- Memory query: `no_signal_cut_in, occlusion, pedestrian_occlusion, school_zone`
- Safe behavior: creep around occlusion and yield before the hidden crossing point

### `studio-0019-flooded-urban-road-low-obstacle-blends-into-wate`

- Prompt: Flooded urban road: low obstacle blends into water while traffic creeps around cones
- Environment: `flooded_road`
- Behavior: `informal_right_of_way_push`
- Memory query: `flood, informal_right_of_way_push, obstacle_substitution, weather_surface`
- Safe behavior: reduce speed, avoid low obstacles, and preserve a dry bypass when available

### `studio-0020-night-rain-glare-reflective-sign-distracts-the-p`

- Prompt: Night rain glare: reflective sign distracts the policy near a lane closure
- Environment: `night_rain_fog`
- Behavior: `no_signal_cut_in`
- Memory query: `glare, night, no_signal_cut_in, rain, visibility, visual_noise`
- Safe behavior: slow, yield, and choose the locally safest route around the hazard

### `studio-0021-double-parked-market-street-door-swerve-vehicle-`

- Prompt: Double-parked market street: door-swerve vehicle intrudes while a scooter passes on the shoulder
- Environment: `roadside_market_occlusion`
- Behavior: `double_parked_door_swerve`
- Memory query: `double_parked_door_swerve, motorcycle_filtering, obstacle_substitution, regional_market, roadside_market`
- Safe behavior: slow, yield, and choose the locally safest route around the hazard

### `studio-0022-dense-malaysian-traffic-wrong-way-shoulder-creep`

- Prompt: Dense Malaysian traffic: wrong-way shoulder creep appears beside roadside food stalls
- Environment: `roadside_market_occlusion`
- Behavior: `wrong_way_shoulder_creep`
- Memory query: `malaysian_driving, regional_driving_behavior, regional_market, wrong_way, wrong_way_shoulder_creep`
- Safe behavior: slow, yield, and choose the locally safest route around the hazard

### `studio-0023-construction-merge-no-signal-cut-in-happens-besi`

- Prompt: Construction merge: no-signal cut-in happens beside cone taper and stalled lorry proxy
- Environment: `construction_lane_closure`
- Behavior: `no_signal_cut_in`
- Memory query: `construction, no_signal_cut_in, visual_noise`
- Safe behavior: slow, yield, and choose the locally safest route around the hazard

### `studio-0024-roadside-market-occlusion-informal-right-of-way-`

- Prompt: Roadside market occlusion: informal right-of-way push from a side street behind food carts
- Environment: `roadside_market_occlusion`
- Behavior: `informal_right_of_way_push`
- Memory query: `informal_right_of_way_push, occlusion, regional_market, roadside_market`
- Safe behavior: slow, yield, and choose the locally safest route around the hazard

### `studio-0025-monsoon-school-zone-scooter-filters-through-fog-`

- Prompt: Monsoon school zone: scooter filters through fog near an unsignalized crossing
- Environment: `school_zone_unstructured_crossing`
- Behavior: `motorcycle_filtering`
- Memory query: `monsoon, motorcycle_filtering, pedestrian_occlusion, school_zone, visual_noise`
- Safe behavior: slow early, keep lateral buffer, and avoid squeezing two-wheelers

### `studio-0026-visual-noise-stress-irrelevant-ufo-like-billboar`

- Prompt: Visual-noise stress: irrelevant UFO-like billboard appears outside the drivable corridor near debris
- Environment: `construction_lane_closure`
- Behavior: `no_signal_cut_in`
- Memory query: `construction, debris, no_signal_cut_in, visual_noise`
- Safe behavior: slow, yield, and choose the locally safest route around the hazard

## Claim Boundaries

- `prompt_to_ood_compiler=true`
- `deterministic_reproducible_generation=true`
- `ai_scenario_authoring=false_without_provider_run`
- `closed_loop_carla_execution=false`
- `dataset_curation_heuristic=true`
