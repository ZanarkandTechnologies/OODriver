# TASK-058/TASK-059/TASK-060 Build Review

- reviewed_at: `2026-05-06 03:28 +0800`
- reviewer_mode: local fallback after native subagent thread limit
- scope: CARLA maps installer/probe, PhysicalAI-backed Alpamayo shape probe,
  and prebuilt stock Town13 route plan
- verdict: `pass_with_known_runtime_wait`
- overall_score: `4.1/5.0`

## Rubrics

- code-quality: `4.2/5.0`
- integration-readiness: `4.0/5.0`
- evidence-quality: `4.1/5.0`

## Search Scope

- `src/driverx/simulators/carla_maps.py`
- `src/driverx/simulators/carla_maps_cli.py`
- `src/driverx/policies/alpamayo_shape_probe.py`
- `src/driverx/simulators/fail2drive_video.py`
- `tests/test_carla_maps.py`
- `tests/test_carla_maps_cli.py`
- `tests/test_alpamayo_shape_probe.py`
- `tests/test_fail2drive_video_smoke.py`
- `tickets/TASK-058/artifacts/**`
- `tickets/TASK-059/artifacts/**`
- `tickets/TASK-060/artifacts/**`
- `blockers.md`
- `docs/progress.md`

## Findings

- No blocking code findings.
- The CARLA map installer is intentionally conservative: dry-run/preflight and
  probe evidence exist before any stock route is claimed. Real Town13 route
  execution remains blocked until the 7.25 GB AdditionalMaps package completes,
  extracts, and CARLA is restarted/probed.
- PhysicalAI dataset access is no longer speculative. The RunPod shape probe
  used `shape_source_used=dataset`, observed the expected Alpamayo trajectory
  tensors, and produced compact artifacts without raw image/model cache pullback.
- The stock Town13 route plan is ready and carries `TOWN=Town13`, `--timeout
  900`, result/debug/RGB/video expected paths, and the known missing upstream
  video helper blocker. DriverX's assembler remains the intended video path
  after RGB frames exist.

## Checks

- `PYTHONPATH=src python3 -m unittest tests.test_carla_maps tests.test_alpamayo_shape_probe tests.test_cli.CliTest.test_install_carla_additional_maps_cli_writes_install_artifacts tests.test_cli.CliTest.test_probe_carla_maps_cli_writes_inventory_artifacts`
- `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_video_smoke tests.test_carla_maps tests.test_alpamayo_shape_probe`
- `bash scripts/pre_push_check.sh` passed with `266` tests.
- Secret scan found no secrets; the only hit was the existing false positive
  phrase `task-specific` in `docs/prd.md`.
- Heavy artifact scan found no files over `1MB` in active ticket artifacts.

## Next Action

Continue TASK-058 once `artifacts/cache/carla/AdditionalMaps_0.9.16.zip.partial`
finishes downloading: rename to `.zip`, run the DriverX installer against the
cached package, restart/probe CARLA, then execute TASK-060's prepared route
plan.
