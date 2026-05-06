# TASK-078..TASK-082 QA Report

## Scope

This QA pass covers the live scripted CARLA OOD capture train:

- TASK-078 live scripted CARLA OOD capture
- TASK-079 live OOD MP4/evidence assembly
- TASK-080 same-scene Alpamayo package/materialization
- TASK-081 same-capture Alpamayo memory comparison
- TASK-082 V4 submission pack refresh

## Evidence Checks

- Live CARLA capture passed:
  `tickets/TASK-078/artifacts/task78-live-ood-capture-v3/carla_ood_demo.json`
  reports `status=passed`, `frame_count=120`, and `duration_s=24.0`.
- Live OOD video passed:
  `tickets/TASK-079/artifacts/task79-live-ood-video/ood_video_evidence.json`
  reports `status=passed`, `source_kind=live_carla`, and `duration_s=24.0`.
- MP4 probe passed:
  `ffprobe` reports `duration=24.000000` and `size=1399358` for
  `tickets/TASK-079/artifacts/task79-live-ood-video/generated-base-animals-0076-regional-driving-behavior-000_ood.mp4`.
- Alpamayo materialization passed:
  `tickets/TASK-080/artifacts/task80-live-same-scene-materialized-v2/alpamayo_tensor_manifest.json`
  reports `torch_ready=true`.
- Same-capture Alpamayo comparison passed:
  `tickets/TASK-081/artifacts/task81-live-same-scene-comparison/alpamayo_ood_comparison.json`
  reports `open_loop_policy_evaluation=true`, `closed_loop_control=false`, and
  `trajectory_delta.final_l2_m=2.6886`.
- V4 pack passed:
  `tickets/TASK-082/artifacts/submission-pack-v4-live-carlasame-v3/submission_demo_pack.json`
  reports `headline_artifact=long_carla_ood_video`.

## Commands

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_carla_ood_demo \
  tests.test_carla_asset_mapping \
  tests.test_ood_video_evidence \
  tests.test_alpamayo_ood_package \
  tests.test_alpamayo_materializer \
  tests.test_alpamayo_ood_scene \
  tests.test_alpamayo_ood_evaluation \
  tests.test_submission_demo_pack
```

Result: `Ran 26 tests in 0.331s`, `OK`.

```bash
PYTHONPATH=src python3 -m compileall -q src tests
bash scripts/pre_push_check.sh
```

Result: `Ran 309 tests in 10.215s`, `OK (skipped=2)`, `Pre-push checks passed.`

```bash
rg -n "hf_[A-Za-z0-9]{20,}|RUNPOD_API_KEY|MESHY_API_KEY|api[_-]?key|token" \
  . \
  --glob '!tickets/**/artifacts/**/*.json' \
  --glob '!tickets/**/artifacts/**/*.md' \
  --glob '!tickets/archive/**' \
  --glob '!data/**' \
  --glob '!artifacts/**' \
  --glob '!.env' \
  --glob '!*.mp4' \
  --glob '!*.png'
```

Result: no credential values were found; hits were expected code/docs/tests
that mention token handling or placeholder env names.

```bash
rg -n "hf_[A-Za-z0-9]{20,}|RUNPOD_API_KEY=[A-Za-z0-9]|MESHY_API_KEY=[A-Za-z0-9]" \
  . \
  --glob '!data/**' \
  --glob '!artifacts/**' \
  --glob '!.env' \
  --glob '!*.mp4' \
  --glob '!*.png'
```

Result: no live credential values were found in tracked or ticket-artifact
surfaces.

## Claim Boundaries

- The 24s video is live scripted CARLA OOD evidence, not a stock Fail2Drive
  route score.
- Alpamayo evidence is open-loop reasoning/trajectory intent, not live
  closed-loop VLA driving.
- The Alpamayo package duplicates one live ego RGB camera across three camera
  slots; this is enough for same-scene reasoning proof, not a calibrated
  multi-camera rig.
- MP4 and PNG frame artifacts remain ignored by git. JSON/Markdown evidence is
  commit-safe.

## Remaining Blockers

- Full stock Fail2Drive route score/completion remains open under TASK-060.
- Route-aligned Alpamayo live capture remains open under TASK-069.
- Stock SimLingo closed-loop execution remains blocked on graphics/Vulkan host
  suitability under TASK-020.
