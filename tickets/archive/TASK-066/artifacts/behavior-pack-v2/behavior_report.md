# Behavior Suite

## no_signal_cut_in

- actor_kind: `vehicle`
- tags: `cut_in, no_signal, lateral_aggression`
- expected_pressure: Actor cuts across lane without indicator or sufficient gap.
- samples: `25`
- `lateral_displacement_m`: `3.5`
- `longitudinal_displacement_m`: `48.0`
- `max_lateral_speed_mps`: `0.8333`
- `max_deceleration_mps2`: `0.0`
- `max_heading_abs_deg`: `8.0`
- `wrong_way_distance_m`: `0.0`

## sudden_brake

- actor_kind: `vehicle`
- tags: `sudden_brake, rear_end_risk`
- expected_pressure: Lead actor brakes hard after a steady approach.
- samples: `25`
- `lateral_displacement_m`: `0.0`
- `longitudinal_displacement_m`: `27.75`
- `max_lateral_speed_mps`: `0.0`
- `max_deceleration_mps2`: `13.6`
- `max_heading_abs_deg`: `0.0`
- `wrong_way_distance_m`: `0.0`

## motorcycle_filtering

- actor_kind: `motorcycle`
- tags: `motorcycle, filtering, lateral_uncertainty`
- expected_pressure: Fast two-wheeler filters between lanes with lateral weave.
- samples: `25`
- `lateral_displacement_m`: `2.0`
- `longitudinal_displacement_m`: `78.0`
- `max_lateral_speed_mps`: `4.3592`
- `max_deceleration_mps2`: `0.0`
- `max_heading_abs_deg`: `6.0`
- `wrong_way_distance_m`: `0.0`

## wrong_way_shoulder_creep

- actor_kind: `vehicle`
- tags: `wrong_way, shoulder, creep`
- expected_pressure: Actor creeps against route direction along the shoulder.
- samples: `25`
- `lateral_displacement_m`: `0.0`
- `longitudinal_displacement_m`: `-15.0`
- `max_lateral_speed_mps`: `0.0`
- `max_deceleration_mps2`: `0.0`
- `max_heading_abs_deg`: `180.0`
- `wrong_way_distance_m`: `15.0`

## informal_right_of_way_push

- actor_kind: `vehicle`
- tags: `right_of_way, creep, assertive_gap`
- expected_pressure: Actor slowly pushes into a conflict zone instead of yielding.
- samples: `25`
- `lateral_displacement_m`: `3.5`
- `longitudinal_displacement_m`: `13.5`
- `max_lateral_speed_mps`: `1.4`
- `max_deceleration_mps2`: `0.0`
- `max_heading_abs_deg`: `20.0`
- `wrong_way_distance_m`: `0.0`

## stunt_motorcycle_proxy

- actor_kind: `motorcycle`
- tags: `motorcycle, stunt_proxy, fast_low_profile`
- expected_pressure: Low-profile fast two-wheeler surrogate creates perception and prediction stress.
- samples: `25`
- `lateral_displacement_m`: `2.3852`
- `longitudinal_displacement_m`: `90.0`
- `max_lateral_speed_mps`: `7.2774`
- `max_deceleration_mps2`: `0.0`
- `max_heading_abs_deg`: `10.0`
- `wrong_way_distance_m`: `0.0`

## double_parked_door_swerve

- actor_kind: `vehicle`
- tags: `double_parked, door_open, sudden_swerve, urban_clutter`
- expected_pressure: Double-parked actor abruptly intrudes into lane as if avoiding an opening door.
- samples: `25`
- `lateral_displacement_m`: `2.85`
- `longitudinal_displacement_m`: `24.0`
- `max_lateral_speed_mps`: `3.1667`
- `max_deceleration_mps2`: `0.0`
- `max_heading_abs_deg`: `24.0`
- `wrong_way_distance_m`: `0.0`

## unsignaled_u_turn

- actor_kind: `vehicle`
- tags: `u_turn, no_signal, opposing_conflict, heading_reversal`
- expected_pressure: Actor begins an unsignaled U-turn across ego's path with rapid heading reversal.
- samples: `25`
- `lateral_displacement_m`: `4.6`
- `longitudinal_displacement_m`: `5.0`
- `max_lateral_speed_mps`: `3.5207`
- `max_deceleration_mps2`: `5.0`
- `max_heading_abs_deg`: `180.0`
- `wrong_way_distance_m`: `0.0`
