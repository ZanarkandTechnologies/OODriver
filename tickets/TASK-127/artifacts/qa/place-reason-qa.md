# TASK-127 QA: Place-And-Reason Product Loop

## Commands

```bash
PYTHONPATH=src python3 -m oodrive place \
  --db artifacts/runs/oodrive-generate-place-smoke-v2/scenario_studio_db.json \
  --placement artifacts/runs/oodrive-generate-place-smoke-v2/placements/oodrive-generate-place-smoke-v2-placement/carla_placement_plan.json \
  --run-id oodrive-smoke-v2-dry-place

PYTHONPATH=src python3 -m oodrive reason \
  --db artifacts/runs/oodrive-generate-place-smoke-v2/scenario_studio_db.json \
  --run artifacts/runs/oodrive-generate-place-smoke-v2/runs/oodrive-smoke-v2-dry-place/run_manifest.json \
  --prediction-json artifacts/runs/oodrive-generate-place-smoke-v2/fake_alpamayo_prediction.json \
  --run-id oodrive-smoke-v2-reason

scripts/run_carla_client_docker.sh python -m oodrive place \
  --db artifacts/runs/oodrive-generate-place-smoke-v2/scenario_studio_db.json \
  --placement artifacts/runs/oodrive-generate-place-smoke-v2/placements/oodrive-generate-place-smoke-v2-placement/carla_placement_plan.json \
  --config configs/carla_ood_demo.local.sample.yaml \
  --run-id oodrive-smoke-v2-live-place \
  --live
```

## Result

- Dry-run `place`: PASS. Wrote a run manifest with
  `runtime=carla-placement-dry-run`.
- Cached `reason`: PARTIAL/PASS for local evidence. Wrote Alpamayo cached
  reasoning evaluation and replay bundle; package construction is skipped
  because the dry-run manifest has no live RGB/tracks.
- Live Docker `place --live`: BLOCKED cleanly. The CARLA client package ran,
  but Docker could not reach `host.docker.internal:2000` within the configured
  timeout.

## Evidence

- Dry-run manifest:
  `artifacts/runs/oodrive-generate-place-smoke-v2/runs/oodrive-smoke-v2-dry-place/run_manifest.json`
- Cached evaluation:
  `artifacts/runs/oodrive-generate-place-smoke-v2/reasoning/evaluations/oodrive-smoke-v2-reason-evaluation/policy_evaluation.json`
- Replay bundle:
  `artifacts/runs/oodrive-generate-place-smoke-v2/reasoning/bundles/oodrive-smoke-v2-reason-bundle/scenario_run_bundle.json`
- Live blocked manifest:
  `artifacts/runs/oodrive-generate-place-smoke-v2/runs/oodrive-smoke-v2-live-place/run_manifest.json`

## Acceptance Reconciliation

- AC-1: PASS. `oodrive place` writes a run manifest.
- AC-2: PASS/PARTIAL. `oodrive place --live` calls the CARLA OOD demo runner
  and records a clean simulator-readiness blocker when CARLA is unreachable.
- AC-3: PASS. `oodrive reason --prediction-json` writes an evaluation with
  cached Alpamayo reasoning text and a replay bundle.
- AC-4: PASS. The artifacts label dry-run placement, scripted CARLA, sampled
  open-loop reasoning, and `real_time_vla_control=false`.

## Blocker

Live object placement was not proved in this local pass because Docker timed
out connecting to `host.docker.internal:2000`. The implementation path is ready;
rerun the same `place --live` command once CARLA is reachable from the Docker
client or from the graphics-capable RunPod desktop.
