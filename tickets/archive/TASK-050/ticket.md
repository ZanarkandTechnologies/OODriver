# TASK-050: Live Local CARLA 0.9.16 Probe Refresh

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: local CARLA app running, TASK-016 Docker client path
- location: CARLA evidence artifacts
- enter when: user confirms CARLA is running locally
- leave when: Docker Python client proves CARLA 0.9.16 reachability and records
  map/settings/weather
- blockers: none
- spawned follow-ups: TASK-039 Alpamayo CARLA adapter
- complexity: S

## Summary

Refresh live CARLA evidence through the Docker client path so the next adapter
work has a current simulator proof.

## Acceptance Criteria

- [x] Docker client connects to host CARLA at `host.docker.internal:2000`.
- [x] Probe records map name, actor count, server/client version, weather, and settings.
- [x] Evidence paths are recorded.

## Verification

- `scripts/run_carla_client_docker.sh python -m driverx probe-carla --config configs/fail2drive_docker.local.yaml --output-root artifacts/runs --run-id task50-live-carla-probe`
- `bash scripts/pre_push_check.sh`

## Evidence

- Probe JSON: `artifacts/runs/task50-live-carla-probe/carla_probe.json`
- Probe report: `artifacts/runs/task50-live-carla-probe/carla_probe.md`
- Review: `tickets/archive/TASK-050/artifacts/review/20260505T231000-review.json`

## Result

CARLA is reachable from the Docker client. The probe reported map
`Carla/Maps/Town10HD_Opt`, actor count `23`, server version `0.9.16`, client
version `0.9.16`, and rendered mode enabled.
