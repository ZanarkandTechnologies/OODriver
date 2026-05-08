# TASK-141: Usable Generator-To-CARLA Behavior And Object Runtime

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-135, TASK-136, TASK-137, TASK-138, TASK-140
- location: `src/driverx/scenarios/generated_runtime.py`, `src/driverx/evaluation/generator_runtime_score.py`, `artifacts/runs/task141-fake-carla-smoke`, `artifacts/runs/task141-runpod-carla-live`, `artifacts/runs/task141-runpod-carla-live-video`, `tickets/TASK-141`
- enter when: OODrive needs the generator to produce more than static prompt proofs: selectable other-vehicle behavior actors, generated object spawn specs, and a runtime surface that can run locally now and connect to live CARLA later.
- leave when: `oodrive generate-run` can produce a behavior/object runtime manifest, fake-CARLA proof records spawned/destroyed actors and entity tracks, the live Kasm CARLA backend writes RGB/tracks/object-spawn proof, local Mac CARLA absence still blocks cleanly, and a metric scores the artifact for usability.
- blockers: no TASK-141 blocker remains for generated behavior/object spawning in CARLA; local Mac live-CARLA remains unavailable, and closed-loop/model-driven VLA control remains out of scope.
- spawned follow-ups: TASK-139 should consume the live runtime manifest/video for the time-warped VLA drive/video loop, while keeping `closed_loop_vla_control=false` until Alpamayo outputs directly drive CARLA controls.
- complexity: M

### Summary

Build the missing usable bridge from generated OODrive scenarios to CARLA runtime intent. The generator now emits a spec with an environment recipe, selectable behavior traces for other vehicles, generated object asset requests and CARLA spawn specs. The runtime proves the integration locally through a fake-CARLA backend and on the Kasm RunPod CARLA host through a live `carla-live` backend that captured RGB frames, entity tracks, spawned object ids, and a judge-facing MP4.

This ticket does not claim closed-loop Alpamayo control. It deliberately labels the result as generated behavior/object runtime proof, with `closed_loop_vla_control=false` and `real_time_vla_control=false`, so the final video can use the manifest honestly for time-warped or paused-inference driving.

### Acceptance Criteria
- [x] AC-1: Product CLI exposes `oodrive generate-run` for a prompt plus repeatable `--behavior-id` and `--object-kind` selections.
- [x] AC-2: Runtime spec writes generated behavior cases with deterministic traces, dynamic actor spawn transforms, generated object asset requests, and CARLA object spawn specs.
- [x] AC-3: Dry-run backend writes a manifest without importing CARLA and preserves claim boundaries.
- [x] AC-4: Fake-CARLA backend records static object spawns, dynamic behavior actors, entity tracks, spawned actor ids, and destroyed actor ids.
- [x] AC-5: Live CARLA backend either writes RGB/tracks/object-spawn proof on a configured CARLA host or writes a clean blocked manifest with setup commands when CARLA is unavailable.
- [x] AC-6: Product CLI exposes `oodrive score-generator-runtime` with a metric suitable for autoresearch or promotion gating.
- [x] AC-7: Documentation names the user-facing command path and the honest claim boundaries.
- [x] AC-8: Focused tests cover dry-run, fake-CARLA, live blocked, score command, and CLI registration.

### Agent Contract
- Open: `PYTHONPATH=src python3 -m oodrive generate-run --help`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_generated_carla_runtime tests.test_bad_path_stress_demo tests.test_oodrive_cli`
- Stabilize: keep generated artifacts under `artifacts/runs`, and do not import the real `carla` Python package at module import time.
- Inspect: `generated_scenario_runtime.json`, `generated_runtime_fake_carla_proof.json`, `generated_runtime_live_carla_proof.json`, `entity_tracks.json`, `ood_video_evidence.json`, and `generator_runtime_score.json`.
- QA cookbook: run a fake-CARLA smoke, score it, confirm local live blocking, then run the same manifest on the Kasm CARLA host for RGB/tracks/object-spawn proof.
- Expected artifacts: runtime manifest, runtime report, fake-CARLA proof JSON, live-CARLA proof JSON, entity tracks, live MP4, score JSON/Markdown, QA report, review report.

### Build Notes

Implemented:

- `src/driverx/scenarios/generated_runtime.py`
  - `build_generated_scenario_runtime_spec(...)`
  - `run_generated_scenario_runtime(...)`
  - `dry-run`, `fake-carla`, and `carla-live` backends
  - dry-run and fake-CARLA do not require a CARLA config file or `carla` package
- `src/driverx/scenarios/studio_product_generated_runtime.py`
  - product wrappers for generate and score commands
- `src/driverx/evaluation/generator_runtime_score.py`
  - `generator_runtime_score` with scenario generation, behavior breadth, object spawn readiness, runtime proof, cleanup/lineage, and claim-honesty components
- `src/driverx/scenarios/studio_product_cli.py`
  - CLI registration for `generate-run` and `score-generator-runtime`
- `tests/test_generated_carla_runtime.py`
  - unit coverage for dry-run, fake-CARLA, live blocked, and score command behavior

### Commands Run

```bash
PYTHONPATH=src python3 -m oodrive generate-run --help
PYTHONPATH=src python3 -m oodrive score-generator-runtime --help
```

Result: PASS.

```bash
rm -rf /tmp/driverx-task141 && PYTHONPATH=src python3 -m oodrive generate-run \
  "wet Malaysian roadwork, scooter cut-in, lane debris" \
  --template-id construction_lane_closure \
  --behavior-id motorcycle_filtering \
  --behavior-id no_signal_cut_in \
  --behavior-id unsignaled_u_turn \
  --object-kind construction_debris \
  --object-kind roadside_vendor \
  --backend fake-carla \
  --output-root /tmp/driverx-task141 \
  --run-id fake

PYTHONPATH=src python3 -m oodrive score-generator-runtime \
  --runtime-manifest /tmp/driverx-task141/fake/generated_scenario_runtime.json \
  --metric-only
```

Result: PASS, `generator_runtime_score=98.0000`.

```bash
rm -rf /tmp/driverx-task141-live && PYTHONPATH=src python3 -m oodrive generate-run \
  "wet Malaysian roadwork, scooter cut-in, lane debris" \
  --template-id construction_lane_closure \
  --behavior-id motorcycle_filtering \
  --object-kind construction_debris \
  --object-kind roadside_vendor \
  --backend carla-live \
  --output-root /tmp/driverx-task141-live \
  --run-id live
```

Result: PASS as blocked proof; blocker says the CARLA Python package is unavailable and includes Kasm setup commands.

```bash
python3 -m compileall -q src/driverx/scenarios src/driverx/evaluation tests/test_generated_carla_runtime.py
PYTHONPATH=src python3 -m unittest tests.test_generated_carla_runtime tests.test_bad_path_stress_demo tests.test_oodrive_cli
```

Result: PASS, `Ran 19 tests`.

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

PYTHONPATH=src python3 -m oodrive score-generator-runtime \
  --runtime-manifest artifacts/runs/task141-fake-carla-smoke/generated_scenario_runtime.json \
  --metric-only
```

Result: PASS, `generator_runtime_score=98.0000`, `static_object_spawn_count=4`, `dynamic_actor_spawn_count=3`, `track_count=79`.

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

Result: PASS as local blocked proof with `No module named 'carla'` and Kasm setup commands.

```bash
scripts/sync_runpod_proxy_workspace.sh \
  poz4gv6ryu2571-644111cc@ssh.runpod.io \
  ~/.ssh/id_ed25519_runpod \
  /workspace/0xDriver

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

PYTHONPATH=src "$PY" -m oodrive score-generator-runtime \
  --runtime-manifest artifacts/runs/task141-runpod-carla-live/generated_scenario_runtime.json \
  --run-id task141-runpod-carla-live-generator-runtime-score-fixed \
  --metric-only
```

Result: PASS on the Kasm RunPod CARLA host. The live manifest reports
`runtime_status=passed`, `frame_count=450`, `track_count=7650`,
`static_object_spawn_count=5`, `dynamic_actor_spawn_count=1`, `blockers=[]`,
and `objects_spawned_in_carla=true`. The live metric is
`generator_runtime_score=85.0000`; it is below the 90 promotion threshold only
because this proof used one generated behavior case rather than the
three-behavior breadth smoke used by fake-CARLA.

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

Result: PASS. The pulled MP4 is 1280x720, 450 frames, 5 FPS, 90.0s, with
`generated_runtime_live_carla=true` and `closed_loop_vla_control=false`.

```bash
PYTHONPATH=src python3 -m unittest tests.test_generated_carla_runtime tests.test_bad_path_stress_demo tests.test_environment_to_carla_visual_proof tests.test_carla_ood_demo tests.test_oodrive_cli
python3 -m compileall -q src tests
bash scripts/pre_push_check.sh
```

Result: PASS, focused suite `Ran 31 tests`; pre-push `Ran 436 tests`, skipped 5.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS. Local Mac live-CARLA blocks cleanly, and Kasm RunPod live-CARLA proof passed with RGB, tracks, object spawns, and cleanup evidence.
- AC-6: PASS
- AC-7: PASS
- AC-8: PASS

### Claim Boundaries
- `generated_vehicle_behaviors=true`
- `generated_static_objects=true`
- `objects_spawned_in_fake_carla=true` for fake-CARLA proof
- `objects_spawned_in_carla=true` for `artifacts/runs/task141-runpod-carla-live`
- `objects_spawned_in_carla=false` for local Mac runs unless a live CARLA host is configured
- `closed_loop_vla_control=false`
- `real_time_vla_control=false`

### Artifact Links
- Runtime implementation: `src/driverx/scenarios/generated_runtime.py`
- Score implementation: `src/driverx/evaluation/generator_runtime_score.py`
- Product wrapper: `src/driverx/scenarios/studio_product_generated_runtime.py`
- Tests: `tests/test_generated_carla_runtime.py`
- Root docs: `README.md`
- Scenario docs: `src/driverx/scenarios/README.md`
- Evaluation docs: `src/driverx/evaluation/README.md`
- Fake-CARLA evidence: `artifacts/runs/task141-fake-carla-smoke/generated_scenario_runtime.json`
- Fake-CARLA tracks: `artifacts/runs/task141-fake-carla-smoke/entity_tracks.json`
- Live blocked evidence: `artifacts/runs/task141-live-blocked/generated_scenario_runtime.json`
- Live Kasm manifest: `artifacts/runs/task141-runpod-carla-live/generated_scenario_runtime.json`
- Live Kasm CARLA proof: `artifacts/runs/task141-runpod-carla-live/generated_runtime_live_carla_proof.json`
- Live Kasm entity tracks: `artifacts/runs/task141-runpod-carla-live/live_cases/behavior-00-motorcycle-filtering/entity_tracks.json`
- Live Kasm RGB samples: `artifacts/runs/task141-runpod-carla-live/live_cases/behavior-00-motorcycle-filtering/rgb/frame_000000.png`, `artifacts/runs/task141-runpod-carla-live/live_cases/behavior-00-motorcycle-filtering/rgb/frame_000224.png`, `artifacts/runs/task141-runpod-carla-live/live_cases/behavior-00-motorcycle-filtering/rgb/frame_000449.png`
- Live Kasm MP4: `artifacts/runs/task141-runpod-carla-live-video/wet-malaysian-roadwork-scooter-cut-in-lane-debris-0041_ood.mp4`
- Live Kasm video evidence: `artifacts/runs/task141-runpod-carla-live-video/ood_video_evidence.json`
- Score evidence: `artifacts/runs/task141-fake-carla-smoke/generator-runtime-scores/task141-fake-carla-smoke-generator-runtime-score/generator_runtime_score.json`
- Live score evidence: `artifacts/runs/task141-runpod-carla-live/generator-runtime-scores/task141-runpod-carla-live-generator-runtime-score-fixed/generator_runtime_score.json`
- QA report: `tickets/TASK-141/artifacts/qa/generator-runtime-qa.md`
- Review: `tickets/TASK-141/artifacts/review/task141-live-carla-review.json`

### Required Evidence
- [x] Unit/integration tests pass
- [x] Python compile check passes for touched modules
- [x] Full `scripts/pre_push_check.sh` pass
- [x] Live Kasm CARLA proof passes with generated object and behavior spawns
- [x] Local MP4 evidence pulled from RunPod and verified with `ffprobe`
- [x] Review artifact attached
