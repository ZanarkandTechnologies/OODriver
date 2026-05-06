# Live Alpamayo Hero Scenario Status

## Verdict

Alpamayo 1.5 is now running on the Kasm RunPod pod for DriverX evidence.

This proof is open-loop: the model consumed captured CARLA OOD frames and
returned reasoning plus a trajectory. It did not yet steer the CARLA ego vehicle
live.

## Run Facts

- model_id: `nvidia/Alpamayo-1.5-10B`
- attention: `eager`
- inference_state: `completed`
- latency_ms: `111765.05`
- vram_peak_mb: `23559.71`
- input `image_frames`: `[3, 4, 3, 360, 640]`
- input `ego_history_xyz`: `[1, 1, 16, 3]`
- output `pred_xyz`: `[1, 1, 1, 64, 3]`
- output `pred_rot`: `[1, 1, 1, 64, 3, 3]`
- output `extra.cot`: `[1, 1, 1]`

## Reasoning Trace

`Yield to the cut-in vehicle since it is turning into our lane ahead`

## DriverX Conversion

The live prediction was converted into a DriverX `alpamayo-live` policy
decision with:

- `trajectory_chunk_open_loop`
- 20 output waypoints at the local 4Hz target interface
- first point `[1.9914, 0.0035]`
- final point `[26.1181, 0.1002]`

## Scenario Generation State

DriverX can already generate deterministic scenario recipes, environment
families, regional behavior variants, quality-gated CARLA campaigns, scenario
catalogs, and submission-browser packs.

DriverX cannot yet generate new CARLA scenarios from natural-language prompts
with an LLM loop. That should be the next simulator-contribution layer: compile
descriptions like "Malaysian motorbike filtering through wet construction
traffic" into a behavior DSL, stock CARLA assets, weather/lighting, route
constraints, and quality gates.

## Why The Current Video Looks Buggy

The current hero video is a deterministic stress-test proof, not a polished
driving simulation.

Known fidelity gaps:

- actor movement is scripted for repeatable OOD stress testing, so it can look
  less natural than CARLA Traffic Manager traffic
- traffic density is intentionally sparse to keep first-pass risk measurement
  stable
- the Alpamayo package duplicates one RGB camera into three camera slots because
  the source proof was a single rendered CARLA video, not a calibrated
  multi-camera sensor rig
- the current proof records the model's reaction after capture; it does not yet
  close the loop by steering CARLA from Alpamayo output

Next contribution target: high-fidelity scenario runner with route-following
ego, denser traffic, smooth actor controllers, camera polish, natural-language
scenario generation, and Alpamayo reasoning overlays.
