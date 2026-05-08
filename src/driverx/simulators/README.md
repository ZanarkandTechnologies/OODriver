# driverx.simulators

## Purpose

Owns adapter surfaces for external simulators. The local path covers CARLA
server smoke checks, CARLA Python API probing through Docker, and Fail2Drive
dry-run command planning. It also owns the dependency-light local 2D OOD
simulator used to prove the full generated-scenario policy loop without CARLA.

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
- `find_capture_actor(world, attach)`
- `replay_policy_decision(config, actor=None)`
- `write_carla_policy_replay(run_dir, result)`
- `wait_for_rgb_frames(rgb_folder, min_frames, timeout_s, poll_interval_s=...)`
- `assemble_route_video_from_watch(watch, output_video, fps=..., ffmpeg_path=...)`
- `run_local_ood_sim(recipe, behavior, decisions, control_traces, output_dir)`
- `write_local_ood_sim_result(run_dir, result)`
- `run_carla_ood_demo(config, run_dir, recipe=..., behavior=..., asset_manifests=...)`
- `write_carla_ood_demo(run_dir, result)`
- `render_ood_video_overlay(config)`
- `build_agent_carla_catalog()`
- `resolve_map_name(town, map_name=None)`
- `control_carla_world(config, run_dir)`
- `write_carla_control_report(run_dir, result)`

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
bash scripts/run_carla_client_docker.sh python -m driverx capture-alpamayo-carla-input \
  --config configs/carla_local.sample.yaml \
  --host host.docker.internal \
  --attach-role-name hero \
  --no-fallback-spawn \
  --route-name Generalization_PedestriansOnRoad_1088 \
  --route-evidence tickets/TASK-060/artifacts/town13-route-evidence/run_evidence.json \
  --run-id task61-route-aligned-capture
PYTHONPATH=src python3 -m driverx replay-policy-decision \
  --decision tickets/archive/TASK-039/artifacts/live-capture-summary/alpamayo_policy_decision.json \
  --trajectory-frame ego \
  --run-id task62-cached-replay
PYTHONPATH=src python3 -m driverx assemble-route-video \
  --rgb-folder artifacts/runs/task36-suite/recipes/000_example/fail2drive_outputs/visualizations/RouteName/rgb \
  --output-video artifacts/runs/task36-suite/RouteName.mp4 \
  --run
PYTHONPATH=src python3 -m driverx run-end-to-end-ood-demo \
  --run-id local-ood-demo
bash scripts/run_carla_client_docker.sh python -m driverx run-carla-ood-demo \
  --config configs/carla_ood_demo.local.sample.yaml \
  --tick-count 240 \
  --run-id task72-live-retry
PYTHONPATH=src python3 -m driverx run-scripted-ood-campaign \
  --config configs/scripted_ood_campaign.runpod.high_fidelity.yaml \
  --run-id task102-high-fidelity-hero
PYTHONPATH=src python3 -m driverx assemble-ood-video \
  --rgb-folder tickets/TASK-073/artifacts/fixture-long-ood-source/rgb \
  --tracks tickets/TASK-073/artifacts/fixture-long-ood-source/entity_tracks.json \
  --scenario-id fixture-malaysia-motorcycle-filtering \
  --behavior-id motorcycle_filtering \
  --source-kind fixture \
  --claim-label fixture_video_evidence
```

OODrive's agent-facing CARLA composer uses the simulator adapter layer to select
existing towns, weather presets, road anchors, background traffic/pedestrians,
stock proxy props, and dynamic behavior actors:

```bash
PYTHONPATH=src python3 -m oodrive carla-catalog
PYTHONPATH=src python3 -m oodrive carla-control \
  --town Town03 \
  --load-map \
  --weather-preset night_rain_fog \
  --capture
PYTHONPATH=src python3 -m oodrive carla-compose \
  "Town05 flooded road with debris and a lane-change pressure case" \
  --town Town05 \
  --weather-preset flooded_surface \
  --template-id flooded_road \
  --behavior-id no_signal_cut_in \
  --object-kind construction_debris \
  --backend fake-carla
```

This is CARLA scenario composition, not arbitrary 3D world generation. The live
runner applies configured weather with `world.set_weather` when the CARLA Python
API exposes weather parameters.

When local CARLA is too slow for full route scoring, `run-fail2drive-route` can
watch the RGB output folder with `--min-video-frames` and assemble an MP4 before
optionally stopping the route with `--stop-after-video`. That path is partial
evidence only; score/completion remain unavailable unless the route finishes.

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
PYTHONPATH=src python3 -m unittest tests.test_carla_policy_replay
PYTHONPATH=src python3 -m unittest tests.test_carla_alpamayo_capture
PYTHONPATH=src python3 -m unittest tests.test_local_ood_sim
PYTHONPATH=src python3 -m unittest tests.test_route_video_assembly
PYTHONPATH=src python3 -m unittest tests.test_fail2drive_route_runner
PYTHONPATH=src python3 -m unittest tests.test_carla_ood_demo tests.test_ood_video_evidence
```
