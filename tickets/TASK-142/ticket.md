# TASK-142: CARLA Live Bad-Path Scenario Render

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-140, TASK-141
- location: `artifacts/runs/task142-carla-bad-path-live`, `src/driverx/scenarios`, `src/driverx/simulators`, `tickets/TASK-142`
- enter when: The local lane-safe bad-path stress reel is corrected, but the submission still needs the same idea rendered inside CARLA rather than as a 2D scripted presentation.
- leave when: Kasm CARLA produces at least one judge-visible bad-path MP4 or a precise live-CARLA blocker with the exact command, log path, and next recovery command.
- blockers: requires Kasm RunPod CARLA 0.9.16 graphics path and Python client; local Mac currently blocks with `No module named 'carla'`.
- spawned follow-ups: TASK-143 visual/metric gate, TASK-144 final packet refresh.
- complexity: M

### Description

Run the corrected bad-path scenario family in CARLA, prioritizing the compound case: moving object first, lane blocker, trench/detour, stop/replan/slow/recover. Use the existing `oodrive generate-run --backend carla-live` and/or `oodrive place --live` lane. Do not spend time on new model claims; this is simulator proof.

### Goal

Replace the confusing local-only stress proof with an in-simulator CARLA artifact that shows the OODrive-generated environment/objects and the ego response in a believable lane-aligned scene.

### Acceptance Criteria
- [ ] AC-1: A selected TASK-140/TASK-141 bad-path case is converted into a live CARLA run command with frozen seed/config.
- [ ] AC-2: CARLA run produces RGB frames, entity/object tracks, and run manifest, or records a precise blocker.
- [ ] AC-3: MP4 is 30-90s, shows the obstacle/hazard in-frame, and includes visible claim labels.
- [ ] AC-4: Claim boundaries remain honest: scripted/live CARLA proof is not closed-loop Alpamayo control.

### Agent Contract
- Open: `tickets/TASK-140/ticket.md`, `tickets/TASK-141/ticket.md`, `src/driverx/scenarios/generated_runtime.py`, `src/driverx/simulators/carla_ood_demo.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_generated_carla_runtime tests.test_carla_ood_demo tests.test_bad_path_stress_demo tests.test_oodrive_cli`
- Stabilize: use Kasm CARLA only for live render; keep generated videos under ignored `artifacts/runs`.
- Inspect: CARLA run manifest, object spawn proof, entity tracks, RGB frame folder, MP4.
- Expected artifacts: `generated_scenario_runtime.json`, `run_manifest.json`, `entity_tracks.json`, `bad_path_carla_demo.mp4`, CARLA log.

### Planned Commands

```bash
PYTHONPATH=src python3 -m oodrive generate-run \
  "compound blocked road with moving object, lane blocker, and trench detour" \
  --template-id construction_lane_closure \
  --behavior-id motorcycle_filtering \
  --object-kind construction_debris \
  --object-kind roadside_vendor \
  --backend carla-live \
  --run-id task142-carla-bad-path-live
```

If the generated-runtime live backend is too thin for video capture, use the proven product path:

```bash
PYTHONPATH=src python3 -m oodrive place \
  --db artifacts/runs/task141-realistic-ood-generation-v1/scenario_studio_db.json \
  --scenario-id studio-0056-compound-blocked-road-moving-object-crosses-firs-v00 \
  --config configs/carla_ood_demo.runpod.high_fidelity.yaml \
  --run-id task142-compound-place-live \
  --live
```

### Required Evidence
- [ ] Kasm/CARLA command output recorded.
- [ ] MP4 path or blocker path recorded.
- [ ] Claim labels checked.
- [ ] Review before completion claim.
