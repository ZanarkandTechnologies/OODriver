# OODrive Command Cookbook

Use from `/Users/kenjipcx/SOTA/0xDriver` unless the user gives another checkout.

## Product Loop

```bash
PYTHONPATH=src python3 -m oodrive generate \
  "wet urban roadwork, lane blocked by cart, pedestrian occlusion" \
  --count 4 \
  --run-id oodrive-generated

PYTHONPATH=src python3 -m oodrive place \
  --db artifacts/runs/<run>/scenario_studio_db.json \
  --placement artifacts/runs/<run>/carla_placement_plan.json \
  --live

PYTHONPATH=src python3 -m oodrive reason \
  --db artifacts/runs/<run>/scenario_studio_db.json \
  --run artifacts/runs/<run>/run_manifest.json \
  --prediction-json artifacts/runs/<run>/prediction.json

PYTHONPATH=src python3 -m oodrive demo-video \
  --db artifacts/runs/<run>/scenario_studio_db.json \
  --run artifacts/runs/<run>/run_manifest.json \
  --evaluation artifacts/runs/<run>/policy_evaluation.json \
  --input-video artifacts/exported/<source>.mp4 \
  --speed-factor 4

PYTHONPATH=src python3 -m oodrive score-demo \
  --db artifacts/runs/<run>/scenario_studio_db.json \
  --run artifacts/runs/<run>/run_manifest.json \
  --evaluation artifacts/runs/<run>/policy_evaluation.json \
  --video artifacts/runs/<run>/demo-videos/<id>/oodrive_hero_demo.mp4 \
  --overlay-report artifacts/runs/<run>/demo-videos/<id>/hero_demo_video.json \
  --metric-only
```

## Fail2Drive Agent XML Lane

```bash
PYTHONPATH=src python3 -m oodrive f2d-catalog \
  --fail2drive-root third_party/fail2drive \
  --format both

PYTHONPATH=src python3 -m oodrive f2d-write-route \
  --example RoadBlocked \
  --validate \
  --run-id f2d-roadblocked

PYTHONPATH=src python3 -m oodrive f2d-validate-route \
  --route artifacts/runs/<run>/route.xml \
  --fail2drive-root third_party/fail2drive \
  --metric-only

PYTHONPATH=src python3 -m oodrive f2d-run-route \
  --route artifacts/runs/<run>/route.xml \
  --fail2drive-root third_party/fail2drive \
  --dry-run

# Default agent is OODrive's RGB capture agent. Use `--agent pdm-lite` only for
# Fail2Drive's upstream display-oriented visualizer path.

PYTHONPATH=src python3 -m oodrive f2d-reason \
  --evidence artifacts/runs/<run>/run_evidence.json \
  --route artifacts/runs/<run>/route.xml \
  --mode fake

PYTHONPATH=src python3 -m oodrive f2d-demo-video \
  --evidence artifacts/runs/<run>/run_evidence.json \
  --reasoning artifacts/runs/<run>/f2d_reasoning.json \
  --route artifacts/runs/<run>/route.xml \
  --input-video artifacts/runs/<run>/route.mp4 \
  --metric-only

PYTHONPATH=src python3 -m oodrive f2d-evaluate-model \
  --routes tests/fixtures/fail2drive_routes \
  --fail2drive-root third_party/fail2drive \
  --limit 3 \
  --dry-run \
  --reason \
  --demo-video \
  --metric-only
```

## OpenSCENARIO / ScenarioRunner

```bash
PYTHONPATH=src python3 -m oodrive validate-osc2 --osc2 <file.osc>
PYTHONPATH=src python3 -m oodrive scenario-runner-package --osc2 <file.osc>
PYTHONPATH=src python3 -m oodrive scenario-runner-run --package <scenario_runner_package.json>
```

## CARLA Tools

```bash
PYTHONPATH=src python3 -m oodrive carla-control --help
PYTHONPATH=src python3 -m oodrive carla-compose --help
PYTHONPATH=src python3 -m oodrive carla-map-probe --map Town10HD_Opt --live
PYTHONPATH=src python3 -m oodrive score-visual-fidelity --media-manifest <media_manifest.json> --metric-only
```

## RunPod Direct SSH Pattern

Use direct TCP SSH when provided:

```bash
ssh -p <port> -i ~/.ssh/id_ed25519_runpod root@<host>
```

On a Kasm/CARLA pod, relaunch CARLA as `kasm-user`, not root:

```bash
cd /workspace/carla/CARLA_0.9.16
sudo -u kasm-user env \
  HOME=/home/kasm-user \
  DISPLAY=:1 \
  XAUTHORITY=/home/kasm-user/.Xauthority \
  VK_ICD_FILENAMES=/workspace/carla/nvidia_icd.json \
  nohup ./CarlaUE4.sh -RenderOffScreen -nosound -quality-level=Low -carla-port=2000 \
  > /workspace/0xDriver/artifacts/runs/carla_server.log 2>&1 &
```

Never send Hugging Face tokens or secrets through Kasm proxy heredocs.
