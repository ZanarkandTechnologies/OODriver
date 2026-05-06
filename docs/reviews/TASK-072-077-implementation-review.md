# Review: TASK-072 Through TASK-077 Implementation

- Date: 2026-05-06 19:05 +0800
- Scope: TASK-072 through TASK-077 implementation, generated evidence, tickets,
  docs, and tests.
- Rubrics: code-quality, evidence-quality, integration-readiness, video-quality.
- Verdict: pass with live-runtime caveat.
- Overall score: 4.0 / 5.0.

## Search Scope

- Code: `src/driverx/simulators/carla_ood_demo.py`,
  `src/driverx/simulators/ood_video_overlay.py`,
  `src/driverx/assets/carla_mapping.py`,
  `src/driverx/pipeline/ood_video_evidence.py`,
  `src/driverx/pipeline/alpamayo_ood_scene.py`,
  `src/driverx/pipeline/alpamayo_ood_evaluation.py`,
  `src/driverx/pipeline/submission_demo_pack.py`, and CLI/export neighbors.
- Tests: `tests/test_carla_ood_demo.py`, `tests/test_carla_asset_mapping.py`,
  `tests/test_ood_video_evidence.py`, `tests/test_alpamayo_ood_scene.py`,
  `tests/test_alpamayo_ood_evaluation.py`,
  `tests/test_submission_demo_pack.py`.
- Evidence: TASK-072 through TASK-077 artifact folders.
- Docs: `README.md`, `ARCHITECTURE.md`, `docs/progress.md`, `blockers.md`.

## Findings

None blocking after the review fix pass.

Resolved review findings:

- TASK-074 now preserves `package_scenario_id`, `scenario_report_id`, and
  `video_scenario_id`, and emits `linkage_warnings` when fixture/video/scenario
  evidence is linked rather than same-capture.
- TASK-075 now sets `memory_augmented_live_run_available=false` when evidence is
  not same-capture or the generated package is not torch-ready, while preserving
  `memory_augmented_decision_available=true` for cached live decisions.
- TASK-077 now declares the Alpamayo comparison as
  `linked_cached_evidence_with_warnings` instead of
  `live_memory_comparison_ready`.
- TASK-072 timeout evidence now uses `status=blocked`, matching blocker/progress
  semantics.
- V3 storyboard now says `latency not available` instead of `Nonems`, and the
  next-run beat points at the active TASK-072 blocker.

## Scores

- code-quality: 4.0 / 4.0
  - Modular seams are clear and local: CARLA runner, video overlay, asset
    mapping, Alpamayo scene, comparison, and pack generation are separately
    owned.
  - Remaining caveat: `submission_demo_pack.py` is large and warned by the
    pre-push gate, but this ticket did not introduce a hard block.
- evidence-quality: 4.0 / 4.0
  - Focused tests, full pre-push gate, ticket evidence artifacts, blocker
    ledger, and regenerated JSON/Markdown evidence are traceable.
  - Live CARLA capture is still blocked, but the artifacts label that directly.
- integration-readiness: 4.0 / 4.0
  - CLI commands register, contracts are exported, and failure states degrade to
    setup blockers instead of unhandled tracebacks.
  - Remaining live-runtime dependency is explicit in `blockers.md`.
- video-quality: 3.7 / 3.5
  - The 20s fixture MP4 is review-useful for overlay/risk-track proof.
  - It is intentionally not treated as a live CARLA artifact.

## Verification

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_submission_demo_pack \
  tests.test_alpamayo_ood_evaluation \
  tests.test_alpamayo_ood_scene \
  tests.test_ood_video_evidence \
  tests.test_carla_ood_demo \
  tests.test_carla_asset_mapping
```

Result: 21 tests passed.

```bash
PYTHONPATH=src python3 -m compileall -q src tests
```

Result: passed.

```bash
bash scripts/pre_push_check.sh
```

Result: passed, with existing large-file warnings and two Pillow-dependent
video fixture skips in the baseline shell.

## Residual Risk

The only material blocker is live CARLA frame capture from the Docker client to
local CARLA. The implementation is ready to rerun once the simulator bridge is
responsive.
