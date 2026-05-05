# driverx.simulators

## Purpose

Owns adapter surfaces for external simulators. The local path covers CARLA
server smoke checks, CARLA Python API probing through Docker, and Fail2Drive
dry-run command planning.

## Public API

- `load_carla_run_config(path)`
- `smoke_carla_server(host, port, timeout_s)`
- `probe_carla_client(config)`
- `write_carla_probe(run_dir, result)`
- `install_carla_additional_maps(config)`
- `probe_carla_map_inventory(config)`
- `write_carla_maps_report(run_dir, result)`
- `plan_fail2drive_run(config, recipe)`
- `build_bench2drive_route_suite(run_dir, recipes, route_root, behavior_id)`
- `write_bench2drive_route_suite(run_dir, suite, simlingo_plan=...)`
- `compile_overlay_injection_plan(route_pack_path, output_dir, behavior_id=...)`
- `write_overlay_injection_plan(run_dir, plan)`
- `run_overlay_injection_plan(config, plan_path, run_dir)`
- `write_overlay_injection_run(run_dir, result)`
- `build_simlingo_sidecar_plan(simlingo_plan_path=..., overlay_plan_path=..., ...)`
- `write_simlingo_sidecar_plan(run_dir, plan)`
- `run_simlingo_sidecar_processes(plan_path, run_dir, timeout_s=...)`
- `write_simlingo_sidecar_run(run_dir, result)`
- `parse_simlingo_result(path)`
- `write_simlingo_result_report(run_dir, record, ...)`
- `scan_simlingo_evidence(artifact_root)`
- `write_simlingo_evidence_report(run_dir, scan)`

## Example

```bash
PYTHONPATH=src python3 -m driverx smoke-carla --config configs/carla_local.sample.yaml
bash scripts/run_carla_client_docker.sh python -m driverx probe-carla \
  --host host.docker.internal \
  --port 2000 \
  --run-id task8-carla-probe
PYTHONPATH=src python3 -m driverx install-carla-additional-maps \
  --config configs/carla_maps.local.sample.yaml \
  --dry-run \
  --run-id task58-town13-dry-run
bash scripts/run_carla_client_docker.sh python -m driverx probe-carla-maps \
  --config configs/carla_maps.local.sample.yaml \
  --host host.docker.internal \
  --port 2000 \
  --map Town13 \
  --run-id task58-town13-probe
bash scripts/run_carla_client_docker.sh python -m driverx spawn-ego-smoke \
  --host host.docker.internal \
  --port 2000 \
  --run-id task9-ego-smoke
PYTHONPATH=src python3 -m driverx plan-carla-run \
  --config configs/carla_local.sample.yaml \
  --recipe artifacts/runs/scenario-forge/scenario_recipes.json \
  --recipe-id generated-base-animals-0076-visual-noise-000
PYTHONPATH=src python3 -m driverx export-bench2drive-suite \
  --recipe artifacts/runs/scenario-forge/scenario_recipes.json \
  --recipe-id generated-base-animals-0076-visual-noise-000 \
  --route-root ../external/fail2drive \
  --behavior-id motorcycle_filtering
PYTHONPATH=src python3 -m driverx plan-overlay-injection \
  --route-pack artifacts/runs/bench2drive-route-pack/bench2drive_route_pack.json
bash scripts/run_carla_client_docker.sh python -m driverx run-overlay-injection \
  --config configs/carla_local.sample.yaml \
  --plan artifacts/runs/overlay-injection/overlay_injection_plan.json \
  --route-limit 1
PYTHONPATH=src python3 -m driverx plan-simlingo-sidecar \
  --simlingo-plan artifacts/runs/bench2drive-route-pack/simlingo_command_plan.json \
  --overlay-plan artifacts/runs/overlay-injection/overlay_injection_plan.json
PYTHONPATH=src python3 -m driverx run-simlingo-sidecar \
  --plan artifacts/runs/simlingo-sidecar/simlingo_sidecar_plan.json \
  --timeout-s 900
PYTHONPATH=src python3 -m driverx ingest-simlingo-result \
  --result tickets/archive/TASK-017/artifacts/qa/2026-05-04T194700Z/seed_1_res.json \
  --compatibility tickets/archive/TASK-017/artifacts/qa/2026-05-04T194700Z/torch_cuda_compatibility.json \
  --route-log tickets/archive/TASK-017/artifacts/qa/2026-05-04T194700Z/run_one_route.log
PYTHONPATH=src python3 -m driverx summarize-simlingo-evidence \
  --artifact-root tickets/archive/TASK-020/artifacts/task20-remote \
  --output-root tickets/archive/TASK-020/artifacts
PYTHONPATH=src python3 -m driverx assess-gpu-host \
  --torch-compatibility tickets/archive/TASK-020/artifacts/task20-remote/torch_cuda_compatibility.json \
  --carla-diagnostics tickets/archive/TASK-020/artifacts/task20-remote/carla_runtime_diagnostics.md \
  --simlingo-evidence tickets/archive/TASK-020/artifacts/task20-evidence-final/remote_simlingo_evidence.json
```

The OOD suite report accepts either the older
`ingest-simlingo-result` output or the newer
`summarize-simlingo-evidence` output as `--simlingo-result`.

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_simulator_adapters
PYTHONPATH=src python3 -m unittest tests.test_bench2drive_route_export
PYTHONPATH=src python3 -m unittest tests.test_overlay_injection
PYTHONPATH=src python3 -m unittest tests.test_carla_injection
PYTHONPATH=src python3 -m unittest tests.test_simlingo_sidecar
PYTHONPATH=src python3 -m unittest tests.test_simlingo_sidecar_runner
PYTHONPATH=src python3 -m unittest tests.test_simlingo_result_ingestion
PYTHONPATH=src python3 -m unittest tests.test_simlingo_evidence
PYTHONPATH=src python3 -m unittest tests.test_gpu_host_suitability
PYTHONPATH=src python3 -m unittest tests.test_carla_maps
```
