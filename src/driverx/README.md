# driverx

## Purpose

`driverx` is the runtime package for the 0xDriver minimal-shot autonomy
prototype. The main path now covers scenario generation, failure memory, and
CARLA/Fail2Drive dry-run adapters; the Waymo trajectory pipeline remains as a
support track.

## Public Entrypoints

- `python3 -m driverx inspect-scene --config configs/mock.yaml`
- `python3 -m driverx run-scene --config configs/mock.yaml`
- `python3 -m driverx run-batch --config configs/mock.yaml`
- `python3 -m driverx forge-scenarios --config configs/scenario_forge.sample.yaml`
- `python3 -m driverx build-memory --results tests/fixtures/fail2drive_like/results.json`
- `python3 -m driverx plan-carla-run --config configs/carla_local.sample.yaml --recipe <recipe-json> --recipe-id <id>`
- `python3 -m driverx smoke-carla --config configs/carla_local.sample.yaml`
- `python3 -m driverx evaluate --run-dir <run-dir>`
- `python3 -m driverx package-submission --run-dir <run-dir>`
- `python3 -m driverx resolve-runpod-ssh --env-file .env`

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```
