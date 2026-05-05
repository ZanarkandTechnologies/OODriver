# TASK-008: Live CARLA Probe And Docker Bridge

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-007, live CARLA 0.9.16 app, Docker Desktop
- location: `src/driverx/simulators`, `src/driverx/cli.py`, `scripts`, tests, docs
- enter when: CARLA app is running and TCP smoke reaches `127.0.0.1:2000`
- leave when: Docker CARLA client probe writes simulator-state artifacts and local tests pass
- blockers: none; live CARLA is currently reachable on port `2000`
- spawned follow-ups: TASK-009 ego spawn and camera capture
- complexity: M

## Summary

Prove API-level access to the running CARLA server through a disposable Linux
amd64 Docker Python client pinned to `carla==0.9.16`. TASK-007 only proved TCP
reachability; this ticket records map, actors, weather, settings, and version
evidence.

## Scope

In scope:

- Docker helper for CARLA Python client commands.
- `probe-carla` CLI command.
- dependency-light probe result type and artifact writer.
- clean unavailable-package/server error handling.
- local tests with fake CARLA modules.
- live QA against the running Wine/Kegworks CARLA app when available.

Out of scope:

- spawning actors or sensors.
- running Fail2Drive routes.
- SimLingo/Alpamayo policy execution.

## Plan

### Change

Add a Docker-backed CARLA API probe that writes `carla_probe.json` and
`carla_probe.md`.

### Why

The next proof boundary is whether 0xDriver can inspect the simulator through
the official Python API, not merely detect an open TCP port.

### Before -> After

- Before: `smoke-carla` proves only `host:port` reachability.
- After: `probe-carla` imports `carla`, connects, reads world state, and writes
  artifacts.

### Touch

- `src/driverx/simulators/carla.py`
- `src/driverx/simulators/carla_probe.py`
- `src/driverx/simulators/__init__.py`
- `src/driverx/cli.py`
- `scripts/run_carla_client_docker.sh`
- `configs/carla_local.sample.yaml`
- `tests/test_carla_probe.py`
- `tests/test_cli.py`
- docs and ticket evidence

### Signature Delta

```python
CarlaProbeConfig(host: str, port: int, timeout_s: float)
CarlaProbeResult(...).to_jsonable() -> dict[str, Any]
probe_carla_client(config: CarlaProbeConfig) -> CarlaProbeResult
write_carla_probe(run_dir: Path, result: CarlaProbeResult) -> dict[str, Any]
```

### Type Sketch

```python
CarlaProbeResult = {
  "connected": bool,
  "host": str,
  "port": int,
  "map_name": str | None,
  "actor_count": int | None,
  "weather": dict | None,
  "settings": dict | None,
  "server_version": str | None,
  "client_version": str | None,
  "elapsed_seconds": float | None,
  "error": str | None,
}
```

### Typed Flow Example

`CARLA.app` -> Docker `python:3.10-bullseye` -> `carla.Client("host.docker.internal", 2000)` -> `world.get_map().name` -> `artifacts/runs/task8-carla-probe/carla_probe.json`.

### Execution Steps

1. Add result/config types and probe function.
2. Add artifact writer.
3. Add CLI parser and Docker helper.
4. Add fake-module tests and CLI tests.
5. Run local gate.
6. Run live Docker probe if CARLA remains open.
7. Attach review/QA evidence and commit.

## Acceptance Criteria

- [x] `smoke-carla` still reaches live CARLA on `127.0.0.1:2000`.
- [x] Docker helper runs repo commands in Python 3.10 amd64.
- [x] `probe-carla` writes JSON and Markdown artifacts.
- [x] Probe records map name and actor count when CARLA is available.
- [x] Missing `carla` package or server failure returns actionable JSON, not traceback.
- [x] Tests pass without live CARLA.
- [x] Live QA evidence records the real CARLA probe result or a documented runtime blocker.

## Verification

- `bash scripts/pre_push_check.sh`
- `PYTHONPATH=src python3 -m driverx smoke-carla --config configs/carla_local.sample.yaml`
- `bash scripts/run_carla_client_docker.sh python -m driverx probe-carla --host host.docker.internal --port 2000 --run-id task8-carla-probe`

## Autonomy Readiness

- Available: CARLA 0.9.16 app is running; Docker is running; package pulls approved.
- Needed from user only if blocked: relaunch CARLA if Wine crashes or hangs.

## Evidence

- Live TCP smoke: `PYTHONPATH=src python3 -m driverx smoke-carla --config configs/carla_local.sample.yaml` returned `reachable: true`.
- Live Docker probe: `artifacts/runs/task8-carla-probe/carla_probe.json`.
- Probe result: map `Carla/Maps/Town10HD_Opt`, actor count `23`, server/client version `0.9.16`.
- Local tests: `PYTHONPATH=src python3 -m unittest tests.test_carla_probe tests.test_cli tests.test_simulator_adapters` passed with 19 tests.
- Full gate: `bash scripts/pre_push_check.sh` passed with 61 tests.
- Review: `docs/reviews/TASK-008-carla-probe-review.md`.
- QA report: `tickets/TASK-008/artifacts/qa/2026-05-04T185800Z/report.md`.
- QA JSON: `tickets/TASK-008/artifacts/qa/2026-05-04T185800Z/result.json`.

## Blockers

- None at ticket start.
