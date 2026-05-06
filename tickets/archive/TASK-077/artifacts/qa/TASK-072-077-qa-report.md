# QA Report: TASK-072 Through TASK-077

- Date: 2026-05-06 18:47 +0800
- Scope: scripted CARLA OOD runner, stock proxy assets, OOD video evidence,
  Alpamayo scene/comparison reports, and submission demo pack V3.
- Verdict: local implementation proof passed; live generated-scene CARLA capture
  remains blocked.

## Commands

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_submission_demo_pack \
  tests.test_alpamayo_ood_evaluation \
  tests.test_alpamayo_ood_scene \
  tests.test_ood_video_evidence \
  tests.test_carla_ood_demo \
  tests.test_carla_asset_mapping
```

Result: `21 tests`, `OK`.

```bash
PYTHONPATH=src python3 -m compileall -q src tests
```

Result: passed.

```bash
bash scripts/pre_push_check.sh
```

Result: passed. The gate emitted existing large-file warnings and skipped two
Pillow-dependent video fixture tests in the baseline shell where `PIL` is not
installed.

## Evidence

- TASK-072 live attempt:
  `tickets/TASK-072/artifacts/task72-live-candidate/carla_ood_demo.md`
- TASK-073 fixture video proof:
  `tickets/TASK-073/artifacts/fixture-long-ood-video-v2/ood_video_evidence.md`
- TASK-074 Alpamayo setup report:
  `tickets/TASK-074/artifacts/generated-scene-open-loop-blocker-v2/alpamayo_ood_scene.md`
- TASK-075 scenario-linked comparison:
  `tickets/TASK-075/artifacts/scenario-linked-memory-comparison-v2/alpamayo_ood_comparison.md`
- TASK-076 asset plan:
  `tickets/TASK-076/artifacts/stock-proxy-assets/asset_report.md`
- TASK-077 V3 demo pack:
  `tickets/TASK-077/artifacts/submission-pack-v3-v2/submission_demo_pack.md`
- Review:
  `docs/reviews/TASK-072-077-implementation-review.md`

## Claim Boundaries

- The 20s MP4 is `source_kind=fixture`; it proves overlay/assembly evidence,
  not a live CARLA scene.
- The live scripted CARLA run currently has `status=blocked` after timing out
  against `host.docker.internal:2000`.
- The Alpamayo generated-scene report is a setup/blocker report because no
  policy decision was produced for the generated scene.
- The Alpamayo memory comparison uses cached live decisions and carries
  `evidence_warnings`; it is not same-capture proof and is not marked ready.

## Open Blocker

Rerun `run-carla-ood-demo` after verifying the Docker client can connect to the
local CARLA server:

```bash
bash scripts/run_carla_client_docker.sh python -m driverx run-carla-ood-demo \
  --config configs/carla_ood_demo.local.sample.yaml \
  --tick-count 240 \
  --run-id task72-live-retry
```
