# Prompt-To-CARLA Image QA

- verdict: `partial`
- prompt: `wet Malaysian roadwork with scooter filtering around construction debris and a roadside vendor`
- image: `artifacts/runs/task153-live-prompt-to-carla-pulled/artifacts/runs/task153-live-prompt-to-carla-pack/task153-live-prompt-to-carla-assets/task153-live-prompt-to-carla-run/live-generated-runtime/live_cases/behavior-00-motorcycle-filtering/rgb/frame_000240.png`

## Visible

- Motorcycle/scooter is visible in traffic.
- Roadside vendor or food cart with umbrella is visible.
- Cones and road objects are visible near the roadside.

## Weak Or Missing

- Road surface does not clearly read as wet.
- Scene does not read as Malaysian; `E 79 St` makes it read as generic/US-style CARLA city.
- Roadwork and construction debris are weakly suggested rather than strongly proved.
- One frame does not strongly prove scooter filtering around debris.

## Real CARLA Boundary

This is likely real CARLA evidence rather than 2D/fake evidence because the
manifest reports `backend=carla-live`, `objects_spawned_in_carla=true`,
`objects_spawned_in_fake_carla=false`, and the runtime proof reports 450 frames.

Bottom line: this proves live CARLA stock-proxy spawning with a scooter and
vendor better than it proves exact Malaysian wet-roadwork prompt fidelity.
