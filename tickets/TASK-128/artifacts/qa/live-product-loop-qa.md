# TASK-128 QA: Live OODrive Generate-Place-Reason Loop

## Verdict

PASS for the current submission-grade user story in open-loop VLA form:
`oodrive generate <scenario>` produced a CARLA placement plan, `oodrive place
--live` placed/generated the scenario in live CARLA, Alpamayo 1.5 reasoned over
fresh captured frames, and `oodrive reason` attached that fresh prediction to
the OODrive DB.

## Remote Runtime

- Host: RunPod Kasm pod `poz4gv6ryu2571`
- Repo path: `/workspace/0xDriver`
- Python: `/workspace/driverx_py312/bin/python`
- CARLA: `/workspace/carla/CARLA_0.9.16`
- CARLA server: `127.0.0.1:2000`
- Map: `Carla/Maps/Town10HD_Opt`

## Commands Proved

```bash
PYTHONPATH=src /workspace/driverx_py312/bin/python -m oodrive --help
```

Result: PASS, product commands included `generate`, `place`, and `reason`.

```bash
PYTHONPATH=src /workspace/driverx_py312/bin/python -m oodrive generate \
  "Malaysian wet roadwork: a roadside food cart, construction debris, uneven cones, a motorcycle filtering beside ego, sudden brake traffic, low-visibility rain reflections" \
  --output-root artifacts/runs \
  --run-id task128-oodrive-live-product \
  --count 4 \
  --seed 128 \
  --severity 5 \
  --accept top:3 \
  --config configs/carla_ood_demo.runpod.high_fidelity.yaml \
  --force
```

Result: PASS.

- Generated candidates: `4`
- Queued candidates: `4`
- Selected scenario:
  `studio-0128-malaysian-wet-roadwork-a-roadside-food-cart-cons-v00`
- Placement plan:
  `/workspace/0xDriver/artifacts/runs/task128-oodrive-live-product/placements/task128-oodrive-live-product-placement/carla_placement_plan.json`
- Object spawn specs: `3`

```bash
PYTHONPATH=src /workspace/driverx_py312/bin/python -m oodrive place \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --placement artifacts/runs/task128-oodrive-live-product/placements/task128-oodrive-live-product-placement/carla_placement_plan.json \
  --config configs/carla_ood_demo.runpod.high_fidelity.yaml \
  --run-id task128-oodrive-live-place \
  --live
```

Result: PASS.

- `status`: `passed`
- `objects_placed`: `true`
- `frame_count`: `450`
- `duration_s`: `90.0`
- `spawned_actor_count`: `16`
- generated stock CARLA proxy assets:
  - `env-school-zone-unstructured-crossing-s5-0128-school-crossing-board`
  - `env-school-zone-unstructured-crossing-s5-0128-parked-van-occluder`
  - `env-school-zone-unstructured-crossing-s5-0128-loose-school-bag`
- blockers: `[]`

Fresh Alpamayo inference over the live CARLA package:

- Prediction:
  `/workspace/driverx_remote_artifacts/task128_live_alpamayo/alpamayo_live_prediction.json`
- `inference_state`: `completed`
- `latency_ms`: `69564.85`
- `vram_peak_mb`: `23515.09`
- `pred_xyz`: `[1, 1, 1, 64, 3]`
- `pred_rot`: `[1, 1, 1, 64, 3, 3]`
- `extra.cot`: `[1, 1, 1]`
- CoC: `Keep distance to the lead vehicle since it is directly ahead in our lane`

```bash
PYTHONPATH=src /workspace/driverx_py312/bin/python -m oodrive reason \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --run artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/run_manifest.json \
  --prediction-json /workspace/driverx_remote_artifacts/task128_live_alpamayo/alpamayo_live_prediction.json \
  --run-id task128-oodrive-live-alpamayo-fresh
```

Result: PASS.

- Evaluation:
  `/workspace/0xDriver/artifacts/runs/task128-oodrive-live-product/reasoning/evaluations/task128-oodrive-live-alpamayo-fresh-evaluation/policy_evaluation.json`
- Policy decision:
  `/workspace/0xDriver/artifacts/runs/task128-oodrive-live-product/reasoning/policy-decisions/task128-oodrive-live-alpamayo-fresh-policy/alpamayo_policy_decision.json`
- Memory ids:
  `construction`, `debris`, `malaysian_driving`, `motorcycle_filtering`,
  `occlusion`, `pedestrian_occlusion`

```bash
PYTHONPATH=src /workspace/driverx_py312/bin/python -m driverx assemble-ood-video \
  --rgb-folder artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/rgb \
  --tracks artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/entity_tracks.json \
  --scenario-id studio-0128-malaysian-wet-roadwork-a-roadside-food-cart-cons-v00 \
  --behavior-id motorcycle_filtering \
  --ood-tags construction,debris,malaysian_driving,motorcycle_filtering,occlusion \
  --source-kind oodrive_live_carla \
  --claim-label oodrive_generated_scripted_carla \
  --output-root artifacts/runs/task128-oodrive-live-product/video \
  --run-id task128-live-video \
  --fps 15 \
  --min-frames 300
```

Result: PASS.

- MP4:
  `/workspace/0xDriver/artifacts/runs/task128-oodrive-live-product/video/task128-live-video/studio-0128-malaysian-wet-roadwork-a-roadside-food-cart-cons-v00_ood.mp4`
- overlay frames: `450`
- video duration: `30.0s`
- worst risk: tick `29`, actor
  `generated_asset_env_school_zone_unstructured_crossing_s5_0128_loose_school_bag`,
  distance `1.8214m`

## Claim Boundary

This ticket proves live generated-scenario placement plus open-loop Alpamayo
reasoning over the resulting frames. It does not prove real-time VLA control or
Alpamayo steering the CARLA vehicle.
