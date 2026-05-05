# TASK-012: Generated Asset Pipeline

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-010
- location: `src/driverx/assets`, configs, tests, docs
- enter when: scenario recipes need object novelty beyond built-in CARLA assets
- leave when: asset requests, dry-run provider, manifest validation, and Meshy-ready provider seam exist
- blockers: real Meshy/API key needed only for live generation
- spawned follow-ups: CARLA import validation
- complexity: M

## Summary

Add an asset generation pipeline for random artifacts and OOD objects. Start
with dry-run manifests and placeholder mappings; add Meshy or equivalent API
behind a provider seam when a key is available.

## Acceptance Criteria

- [x] Asset requests include prompt, semantic tags, dimensions, collision proxy,
  intended placement, and license/source metadata.
- [x] Dry-run provider writes deterministic asset manifests.
- [x] Manifest validator rejects missing scale/collision/license fields.
- [x] Real provider is disabled without an API key and fails with setup guidance.
- [x] Scenario recipes can reference generated asset ids.

## Verification

- `bash scripts/pre_push_check.sh`
- `PYTHONPATH=src python3 -m driverx plan-assets --run-id task12-assets`

## Autonomy Readiness

- Meshy API key is useful but not required. Without it, implementation ships
  provider interfaces, dry-run manifests, and validation.

## Blockers

- Real asset generation requires API key and provider docs.

## Evidence

- Local tests: `PYTHONPATH=src python3 -m unittest tests.test_assets tests.test_cli` passed with 22 tests.
- Dry-run command: `PYTHONPATH=src python3 -m driverx plan-assets --run-id task12-assets`.
- Meshy setup-block command: `PYTHONPATH=src python3 -m driverx plan-assets --provider meshy --run-id task12-assets-meshy-blocked`.
- Dry-run manifest: `artifacts/runs/task12-assets/asset_manifests.json`.
- Dry-run report: `artifacts/runs/task12-assets/asset_report.md`.
- Meshy blocked manifest: `artifacts/runs/task12-assets-meshy-blocked/asset_manifests.json`.
- External blocker retained: live asset generation still requires `MESHY_API_KEY` and provider submission docs.
