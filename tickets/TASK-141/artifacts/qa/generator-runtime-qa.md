# TASK-141 QA: Generator Runtime

## Verdict

PASS. The generator runtime is usable locally through `dry-run` and
`fake-carla`, fails safely when the local `carla` Python package is unavailable,
and has now passed on the Kasm RunPod CARLA host with generated object spawns,
one generated vehicle behavior case, RGB frames, entity tracks, and an assembled
90s MP4.

## Evidence

- Fake-CARLA runtime manifest:
  `artifacts/runs/task141-fake-carla-smoke/generated_scenario_runtime.json`
- Fake-CARLA spawn proof:
  `artifacts/runs/task141-fake-carla-smoke/generated_runtime_fake_carla_proof.json`
- Fake-CARLA entity tracks:
  `artifacts/runs/task141-fake-carla-smoke/entity_tracks.json`
- Runtime score:
  `artifacts/runs/task141-fake-carla-smoke/generator-runtime-scores/task141-fake-carla-smoke-generator-runtime-score/generator_runtime_score.json`
- Live backend blocked manifest:
  `artifacts/runs/task141-live-blocked/generated_scenario_runtime.json`
- Live Kasm runtime manifest:
  `artifacts/runs/task141-runpod-carla-live/generated_scenario_runtime.json`
- Live Kasm CARLA proof:
  `artifacts/runs/task141-runpod-carla-live/generated_runtime_live_carla_proof.json`
- Live Kasm entity tracks:
  `artifacts/runs/task141-runpod-carla-live/live_cases/behavior-00-motorcycle-filtering/entity_tracks.json`
- Live Kasm RGB samples:
  `artifacts/runs/task141-runpod-carla-live/live_cases/behavior-00-motorcycle-filtering/rgb/frame_000000.png`,
  `artifacts/runs/task141-runpod-carla-live/live_cases/behavior-00-motorcycle-filtering/rgb/frame_000224.png`,
  `artifacts/runs/task141-runpod-carla-live/live_cases/behavior-00-motorcycle-filtering/rgb/frame_000449.png`
- Live Kasm MP4:
  `artifacts/runs/task141-runpod-carla-live-video/wet-malaysian-roadwork-scooter-cut-in-lane-debris-0041_ood.mp4`
- Live Kasm video evidence:
  `artifacts/runs/task141-runpod-carla-live-video/ood_video_evidence.json`
- Live Kasm score evidence:
  `artifacts/runs/task141-runpod-carla-live/generator-runtime-scores/task141-runpod-carla-live-generator-runtime-score-fixed/generator_runtime_score.json`

## Observations

- Fake-CARLA status: `passed`
- Static object spawns: `4`
- Dynamic behavior actors: `3`
- Applied behavior ticks: `75`
- Entity tracks: `79`
- Spawn cleanup: spawned actor ids `1..7` are all listed as destroyed.
- Score: `generator_runtime_score=98.0000`
- Live local status: `blocked` with `CARLA Python package is unavailable: No module named 'carla'`
- Dry-run coverage includes a missing CARLA config path to prove local generator use does not depend on simulator setup.
- Kasm pod: `poz4gv6ryu2571`, reached through
  `poz4gv6ryu2571-644111cc@ssh.runpod.io`.
- Remote CARLA client: `/workspace/driverx_py312/bin/python`, with
  `carla` import from `/workspace/driverx_py312/lib/python3.12/site-packages/carla/__init__.py`.
- Live Kasm backend status: `passed`, map `Carla/Maps/Town10HD_Opt`,
  `frame_count=450`, `duration_s=90.0`, `track_count=7650`,
  `static_object_spawn_count=5`, `dynamic_actor_spawn_count=1`, and
  `blockers=[]`.
- Live generated asset ids:
  `env-construction-lane-closure-s4-0041-construction-cone-line`,
  `env-construction-lane-closure-s4-0041-portable-work-barrier`,
  `construction-debris-00`, `roadside-vendor-01`, and `lane-cone-02`.
- Live cleanup evidence: actor ids `224..241` are listed as spawned and then
  destroyed.
- Live video evidence: `1280x720`, `450` frames, `5` FPS, `90.0s`,
  `generated_runtime_live_carla=true`, and
  `closed_loop_vla_control=false`.
- Live score: `generator_runtime_score=85.0000`; below the 90 threshold only
  because this Kasm proof intentionally used one behavior case, while the local
  fake-CARLA breadth proof used three behavior cases and scored `98.0000`.

## Commands

```bash
PYTHONPATH=src python3 -m oodrive generate-run \
  "wet Malaysian roadwork, scooter cut-in, lane debris" \
  --template-id construction_lane_closure \
  --behavior-id motorcycle_filtering \
  --behavior-id no_signal_cut_in \
  --behavior-id unsignaled_u_turn \
  --object-kind construction_debris \
  --object-kind roadside_vendor \
  --backend fake-carla \
  --run-id task141-fake-carla-smoke
```

PASS.

```bash
PYTHONPATH=src python3 -m oodrive score-generator-runtime \
  --runtime-manifest artifacts/runs/task141-fake-carla-smoke/generated_scenario_runtime.json \
  --metric-only
```

PASS, `generator_runtime_score=98.0000`.

```bash
PYTHONPATH=src python3 -m oodrive generate-run \
  "wet Malaysian roadwork, scooter cut-in, lane debris" \
  --template-id construction_lane_closure \
  --behavior-id motorcycle_filtering \
  --object-kind construction_debris \
  --object-kind roadside_vendor \
  --backend carla-live \
  --run-id task141-live-blocked
```

PASS as blocked proof.

```bash
scripts/sync_runpod_proxy_workspace.sh \
  poz4gv6ryu2571-644111cc@ssh.runpod.io \
  ~/.ssh/id_ed25519_runpod \
  /workspace/0xDriver
```

PASS.

```bash
cd /workspace/0xDriver
PY=/workspace/driverx_py312/bin/python
PYTHONPATH=src "$PY" -m oodrive generate-run \
  "wet Malaysian roadwork, scooter cut-in, lane debris" \
  --template-id construction_lane_closure \
  --behavior-id motorcycle_filtering \
  --object-kind construction_debris \
  --object-kind roadside_vendor \
  --object-kind lane_cone \
  --backend carla-live \
  --config configs/carla_ood_demo.runpod.high_fidelity.yaml \
  --run-id task141-runpod-carla-live
```

PASS. The live manifest contains `objects_spawned_in_carla=true`.

```bash
PYTHONPATH=src "$PY" -m oodrive score-generator-runtime \
  --runtime-manifest artifacts/runs/task141-runpod-carla-live/generated_scenario_runtime.json \
  --run-id task141-runpod-carla-live-generator-runtime-score-fixed \
  --metric-only
```

PASS, `generator_runtime_score=85.0000`.

```bash
PYTHONPATH=src "$PY" -m driverx assemble-ood-video \
  --rgb-folder artifacts/runs/task141-runpod-carla-live/live_cases/behavior-00-motorcycle-filtering/rgb \
  --tracks artifacts/runs/task141-runpod-carla-live/live_cases/behavior-00-motorcycle-filtering/entity_tracks.json \
  --scenario-id wet-malaysian-roadwork-scooter-cut-in-lane-debris-0041 \
  --behavior-id motorcycle_filtering \
  --ood-tags generated_runtime,construction_debris,roadside_vendor,lane_cone,motorcycle_filtering \
  --source-kind live_carla \
  --claim-label generated_runtime_live_carla \
  --fps 5 \
  --min-frames 120 \
  --run-id task141-runpod-carla-live-video
```

PASS, MP4 written remotely and pulled locally.

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,nb_frames,r_frame_rate,duration \
  -show_entries format=duration,size -of json \
  artifacts/runs/task141-runpod-carla-live-video/wet-malaysian-roadwork-scooter-cut-in-lane-debris-0041_ood.mp4
```

PASS: `1280x720`, `450` frames, `5/1` FPS, `90.000000s`, size `9579957`.

```bash
PYTHONPATH=src python3 -m unittest tests.test_generated_carla_runtime tests.test_bad_path_stress_demo tests.test_environment_to_carla_visual_proof tests.test_carla_ood_demo tests.test_oodrive_cli
```

PASS, `Ran 31 tests`.

```bash
python3 -m compileall -q src tests
bash scripts/pre_push_check.sh
```

PASS. Final pre-push ran `436` tests with `5` skipped.

## Claim Boundaries

- `generated_vehicle_behaviors=true`
- `generated_static_objects=true`
- `objects_spawned_in_fake_carla=true`
- `objects_spawned_in_carla=true` for `artifacts/runs/task141-runpod-carla-live`
- `objects_spawned_in_carla=false` for local Mac runs unless a live CARLA host is configured
- `closed_loop_vla_control=false`
- `real_time_vla_control=false`
