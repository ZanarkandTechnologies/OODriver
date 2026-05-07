# TASK-128: OODrive Live Generate-Place-Reason Proof

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-126, TASK-127
- location: `src/driverx/scenarios`, `src/oodrive`, RunPod Kasm `/workspace/0xDriver`
- enter when: `oodrive generate`, `oodrive place`, and `oodrive reason` work locally but the live CARLA/Alpamayo product story is not proved on the graphics pod
- leave when: the Kasm CARLA pod proves `oodrive generate <prompt>` -> `oodrive place --live` -> fresh Alpamayo inference -> `oodrive reason` with linked artifacts and video evidence
- blockers: none for open-loop reasoning proof; closed-loop VLA actuation remains out of scope
- spawned follow-ups: TASK-129 productized Alpamayo inference command if we want to remove the manual remote inference bridge
- complexity: M

### Summary

Prove the complete OODrive product loop on the graphics-capable RunPod Kasm
pod. This ticket closes the practical gap between the local CLI loop and a real
CARLA render: a natural-language OOD scenario produced CARLA placement specs,
the specs were placed in live CARLA, and Alpamayo 1.5 reasoned over the
captured frames.

### Scope

- In scope: sync current OODrive code to the Kasm pod, run live CARLA placement,
  build Alpamayo package from the live frames, run Alpamayo 1.5 on that package,
  attach the fresh prediction through `oodrive reason`, and assemble an overlay
  MP4.
- Out of scope: real-time closed-loop Alpamayo steering, stock Fail2Drive score,
  custom GLB/Meshy import, and public video hosting.

### Plan

#### Change

Run this live proof sequence on the working Kasm CARLA host:

```bash
PYTHONPATH=src python -m oodrive generate "<scenario>" \
  --config configs/carla_ood_demo.runpod.high_fidelity.yaml

PYTHONPATH=src python -m oodrive place \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --placement artifacts/runs/task128-oodrive-live-product/placements/task128-oodrive-live-product-placement/carla_placement_plan.json \
  --config configs/carla_ood_demo.runpod.high_fidelity.yaml \
  --run-id task128-oodrive-live-place \
  --live

PYTHONPATH=src python -m oodrive reason \
  --db artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json \
  --run artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/run_manifest.json \
  --prediction-json /workspace/driverx_remote_artifacts/task128_live_alpamayo/alpamayo_live_prediction.json \
  --run-id task128-oodrive-live-alpamayo-fresh
```

#### Why

The submission needs one clear proof that OODrive is not only a scenario JSON
database. It must show the intended story: prompt-generated OOD case, concrete
CARLA placement, rendered simulator evidence, and a reasoning VLA response.

#### Before -> After

- Before: local dry-run placement and cached reasoning only.
- After: live CARLA objects were placed on the Kasm GPU desktop, Alpamayo 1.5
  ran on the fresh CARLA frames, and the OODrive DB links placement, run,
  reasoning, policy decision, replay bundle, and video evidence.

#### Touch

- `tickets/TASK-128/ticket.md`
- `tickets/TASK-128/artifacts/qa/live-product-loop-qa.md`
- `docs/reviews/TASK-128-live-product-loop-review.md`
- `docs/HISTORY.md`
- `docs/MEMORY.md`
- `blockers.md`

#### Inspect

- `src/driverx/scenarios/studio_product_runtime.py`
- `src/driverx/scenarios/studio_runtime.py`
- `src/driverx/scenarios/studio_product_cli.py`
- `src/driverx/simulators/carla_ood_demo.py`
- `src/driverx/policies/alpamayo_ood_package.py`
- `scripts/run_remote_alpamayo_carla_inference.sh`

#### Signature Delta

No source API delta in this ticket. It validates the TASK-126/TASK-127
interfaces:

```python
run_studio_generate(...): StudioCommandResult
run_studio_place(..., live=True): StudioCommandResult
run_studio_reason(..., prediction_json=Path): StudioCommandResult
```

#### Type Sketch

```python
LiveProductProof = {
  "prompt": str,
  "placement_plan": Path,
  "run_manifest": Path,
  "carla_ood_demo": Path,
  "alpamayo_live_prediction": Path,
  "policy_evaluation": Path,
  "policy_decision": Path,
  "video_path": Path,
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example

`oodrive generate "Malaysian wet roadwork ..."` -> `carla_placement_plan.json`
with 3 object spawn specs -> `oodrive place --live` -> 450 RGB frames,
entity tracks, 16 spawned actors, and `objects_placed_in_carla=true` ->
Alpamayo package -> fresh `alpamayo_live_prediction.json` ->
`oodrive reason` with CoC text, memory ids, trajectory summary, policy
decision, and replay bundle -> overlay MP4.

#### Execution Steps

1. Confirm the Kasm pod has CARLA 0.9.16 listening on port `2000`.
2. Sync the current OODrive source/config to `/workspace/0xDriver`.
3. Run `oodrive generate` with a dense Malaysian wet-roadwork prompt.
4. Run `oodrive place --live` against `configs/carla_ood_demo.runpod.high_fidelity.yaml`.
5. Build the Alpamayo package from live RGB/tracks through `oodrive reason`.
6. Run Alpamayo 1.5 on the fresh package and attach that prediction with a
   second `oodrive reason`.
7. Assemble the overlay MP4 with `driverx assemble-ood-video`.
8. Record evidence, claim boundaries, and review.

### Acceptance Criteria

- [x] AC-1: Kasm pod connects to CARLA `Town10HD_Opt` on `127.0.0.1:2000`.
- [x] AC-2: `oodrive generate` writes a placement plan for the live prompt.
- [x] AC-3: `oodrive place --live` passes and records `objects_placed_in_carla=true`.
- [x] AC-4: Live CARLA run writes RGB frames, entity tracks, road-alignment
  report, and run manifest.
- [x] AC-5: Alpamayo 1.5 completes on the freshly captured package and writes
  CoC reasoning plus trajectory shapes.
- [x] AC-6: `oodrive reason` attaches the fresh Alpamayo prediction to the DB.
- [x] AC-7: A 30s overlay MP4 is assembled from the live run.
- [x] AC-8: Claim boundaries remain explicit about open-loop VLA reasoning and
  no real-time closed-loop control.

### Verification

- Remote smoke: `PYTHONPATH=src /workspace/driverx_py312/bin/python -m oodrive --help`.
- Remote CARLA smoke: Python client connected to `Carla/Maps/Town10HD_Opt`.
- Remote live run: `oodrive place --live` returned status `passed`.
- Remote Alpamayo run: `inference_state=completed`, `pred_xyz=[1,1,1,64,3]`.
- Remote video assembly: `driverx assemble-ood-video` returned status `passed`.

### Evidence

- QA: `tickets/TASK-128/artifacts/qa/live-product-loop-qa.md`
- Review: `docs/reviews/TASK-128-live-product-loop-review.md`
- Review JSON: `tickets/TASK-128/artifacts/review/task128-review.json`
- Remote DB:
  `/workspace/0xDriver/artifacts/runs/task128-oodrive-live-product/scenario_studio_db.json`
- Remote placement plan:
  `/workspace/0xDriver/artifacts/runs/task128-oodrive-live-product/placements/task128-oodrive-live-product-placement/carla_placement_plan.json`
- Remote run manifest:
  `/workspace/0xDriver/artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/run_manifest.json`
- Remote CARLA report:
  `/workspace/0xDriver/artifacts/runs/task128-oodrive-live-product/runs/task128-oodrive-live-place/carla_ood_demo.json`
- Remote fresh Alpamayo prediction:
  `/workspace/driverx_remote_artifacts/task128_live_alpamayo/alpamayo_live_prediction.json`
- Remote fresh OODrive evaluation:
  `/workspace/0xDriver/artifacts/runs/task128-oodrive-live-product/reasoning/evaluations/task128-oodrive-live-alpamayo-fresh-evaluation/policy_evaluation.json`
- Remote policy decision:
  `/workspace/0xDriver/artifacts/runs/task128-oodrive-live-product/reasoning/policy-decisions/task128-oodrive-live-alpamayo-fresh-policy/alpamayo_policy_decision.json`
- Remote video:
  `/workspace/0xDriver/artifacts/runs/task128-oodrive-live-product/video/task128-live-video/studio-0128-malaysian-wet-roadwork-a-roadside-food-cart-cons-v00_ood.mp4`

### Blockers

- None for the open-loop OODrive generate-place-reason user story.
- Remaining product gap: live Alpamayo inference is still a manual remote step
  between `oodrive place` and `oodrive reason`; TASK-129 should productize it
  if we want a single `oodrive infer` command.
