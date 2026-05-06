# 0xDriver

0xDriver is a research engineering project for the SoTA Commission I
minimal-shot autonomy challenge. The current thesis is:

> Use CARLA/Fail2Drive to generate closed-loop long-tail scenarios, turn policy
> failures into compact safety memory, and test whether VLA/VLM policies improve
> with minimal retrieved context instead of fine-tuning.

The earlier Waymo E2E work remains in the repo as an open-loop real-data support
track. The main submission direction is now CARLA/Fail2Drive scenario
generation and evaluation.

## Project Goal

Build a minimal-shot scenario forge that can:

- load Fail2Drive route seeds or tiny local fixtures
- generate deterministic weird-but-plausible OOD scenario recipes
- build retrieval memory from closed-loop failures
- prepare CARLA/Fail2Drive dry-run command plans
- smoke-check a local CARLA server when available
- preserve Waymo ADE/batch evidence as supporting real-world context

## Core Architecture Direction

```mermaid
flowchart TD
    A["Fail2Drive routes / fixture seeds"] --> B["Scenario seed loader"]
    B --> C["OOD recipe generator"]
    C --> D["Scenario suite artifacts"]
    E["Policy result records"] --> F["Failure memory bank"]
    F --> G["Retrieved safety context"]
    C --> G
    G --> H["VLA/VLM policy prompt or adapter"]
    C --> I["CARLA/Fail2Drive dry-run command plan"]
    I --> J["Mac smoke path or Linux NVIDIA runtime"]
    K["Waymo E2E support track"] --> L["Open-loop ADE evidence"]
```

## Shared Inspiration Resources

- SoTA Commission I: Minimal-Shot Autonomy. The challenge asks for a simulation
  environment or autonomy demo, plus repo, analysis, video/deck, and motivation.
- [Fail2Drive](https://github.com/autonomousvision/fail2drive): paired
  CARLA routes for closed-loop generalization, 17 unseen scenario classes, novel
  assets, result parser, and route toolbox.
- [CARLA](https://carla.readthedocs.io/en/latest/start_introduction/): Unreal
  client/server simulator for autonomous-driving research.
- [SimLingo](https://github.com/RenzKa/simlingo): CARLA-native VLA-style policy
  target for the first real closed-loop policy proof.
- [Alpamayo 1.5](https://github.com/NVlabs/alpamayo1.5): later higher-prestige
  reasoning VLA adapter target.
- [Waymo Open Dataset](https://waymo.com/open/): retained as real logged
  open-loop evidence and trajectory baseline support.

## Repository Shape

- `docs/prd.md`: current scenario-forge PRD.
- `ARCHITECTURE.md`: top-level system map.
- `tickets/archive/`: completed ticket records and compact evidence artifacts,
  including the live Alpamayo and CARLA route proofs.
- `src/driverx/scenarios/`: scenario seeds, recipes, and reports.
- `src/driverx/memory/`: failure memory and retrieval.
- `src/driverx/simulators/`: CARLA smoke checks and Fail2Drive command plans.
- `src/driverx/datasets/`, `planning/`, `pipeline/`, `submission/`: Waymo and
  open-loop support-track code.

## Current Status

TASK-001 through TASK-006 established a working Waymo/open-loop measuring stick:
fixture runs, optional real Waymo TFRecords through Docker, streaming batch
reports, deterministic baselines, and a hybrid semantic-intent plus motion-prior
planner.

The current closed-loop pivot has scenario generation, failure memory,
CARLA/Fail2Drive dry-run planning, local CARLA probing, route-pack export,
overlay plans, sidecar orchestration, policy readiness reports, live Alpamayo
open-loop inference, and a judge-facing demo pack. TASK-064 adds the first
dependency-light end-to-end runnable artifact: one command generates an OOD
scenario, simulates a regional behavior, retrieves safety memory, compares
policy reactions, converts trajectories into cached controls, and renders a
local 2D simulator report. TASK-068 proved Town13 can load and the stock
Fail2Drive route can start. TASK-071 then added the fast route-video path and
produced a fresh Town13 MP4 from `Generalization_PedestriansOnRoad_1088` after
CARLA was relaunched. TASK-078 through TASK-082 are now the strongest
submission evidence: a 24.0s live scripted CARLA OOD video, same-scene Alpamayo
1.5 reasoning on that generated capture, a same-capture memory/no-memory
comparison, and a V4 demo pack that keeps closed-loop VLA control claims out of
scope until a route controller consumes the trajectory. TASK-083 through
TASK-088 add the current final submission train: an 8.0s live CARLA cached
Alpamayo replay video, a reasoning/trajectory HTML pack, a two-case live
scripted OOD campaign, cached Alpamayo batch comparison, a V5 dossier/video
script, and a stock Fail2Drive full-score host handoff.

## Current Submission Packet

- V5 dossier:
  `tickets/TASK-087/artifacts/submission-dossier-v5-live/submission_dossier.md`
- Video script:
  `tickets/TASK-087/artifacts/submission-dossier-v5-live/video_script.md`
- Reasoning pack:
  `tickets/TASK-084/artifacts/task84-reasoning-pack/reasoning_video_pack.html`
- Live cached Alpamayo replay:
  `tickets/TASK-083/artifacts/task83-live-cached-replay-video/ood_video_evidence.md`
- Live generated OOD campaign:
  `tickets/TASK-085/artifacts/task85-live-campaign-2b/scripted_ood_campaign_summary.md`

## Quickstart: End-To-End OOD Demo

```bash
PYTHONPATH=src python3 -m driverx run-end-to-end-ood-demo \
  --output-root artifacts/runs \
  --run-id local-ood-demo
```

Key outputs:

- `end_to_end_demo.md`: generated scenario, memory ids, policy reactions, and
  claim boundaries.
- `local-sim/local_ood_sim.html`: top-down local simulator evidence.
- `policy/policy_reaction_matrix.md`: baseline, memory-guided, and hybrid
  policy comparison table.

## Quickstart: Scenario Forge

```bash
# Generate deterministic OOD scenario recipes from fixture seeds
PYTHONPATH=src python3 -m driverx forge-scenarios \
  --config configs/scenario_forge.sample.yaml \
  --count 8 \
  --seed 7

# Build compact safety memory from fixture policy failures
PYTHONPATH=src python3 -m driverx build-memory \
  --results tests/fixtures/fail2drive_like/results.json \
  --run-id memory-bank

# Plan a dry-run Fail2Drive/CARLA command from one generated recipe file
PYTHONPATH=src python3 -m driverx plan-carla-run \
  --config configs/carla_local.sample.yaml \
  --recipe artifacts/runs/scenario-forge/scenario_recipes.json \
  --recipe-id generated-base-animals-0076-visual-noise-000

# Check whether a local CARLA server is reachable
PYTHONPATH=src python3 -m driverx smoke-carla \
  --config configs/carla_local.sample.yaml

# Probe the live CARLA Python API through Docker
bash scripts/build_carla_client_docker.sh
bash scripts/run_carla_client_docker.sh python -m driverx probe-carla \
  --host host.docker.internal \
  --port 2000 \
  --run-id task8-carla-probe

# Install/probe CARLA 0.9.16 AdditionalMaps for stock Fail2Drive Town13 routes
PYTHONPATH=src python3 -m driverx install-carla-additional-maps \
  --config configs/carla_maps.local.sample.yaml \
  --dry-run \
  --run-id task58-town13-dry-run
PYTHONPATH=src python3 -m driverx install-carla-additional-maps \
  --config configs/carla_maps.local.sample.yaml \
  --run-id task58-town13-install
bash scripts/run_carla_client_docker.sh python -m driverx probe-carla-maps \
  --config configs/carla_maps.local.sample.yaml \
  --host host.docker.internal \
  --port 2000 \
  --map Town13 \
  --run-id task58-town13-probe

# Spawn one ego vehicle/camera, capture a frame, log tracks, and clean up
bash scripts/run_carla_client_docker.sh python -m driverx spawn-ego-smoke \
  --host host.docker.internal \
  --port 2000 \
  --run-id task9-ego-smoke

# Build the local CARLA 0.9.16 client image and run both live proofs
bash scripts/prove_carla_0916_docker.sh

# If Docker times out on host.docker.internal:2000, the client image is still
# valid; keep CARLA.app open, wait for the town to finish loading, and rerun.
# Use DRIVERX_DOCKER_ENV_FILE=.env only when a container needs local env vars.

# Generate regional/OOD behavior traces and metrics
PYTHONPATH=src python3 -m driverx generate-behaviors \
  --run-id task10-behaviors

# Compile one generated recipe and behavior into a CARLA script plan
PYTHONPATH=src python3 -m driverx compile-carla-script \
  --recipe artifacts/runs/scenario-forge/scenario_recipes.json \
  --recipe-id generated-base-animals-0076-visual-noise-000 \
  --behavior-id motorcycle_filtering \
  --run-id task11-carla-script

# Export generated recipes as stock-compatible Bench2Drive route XML plus
# DriverX sidecar overlays for OOD actors/assets/behavior intent
PYTHONPATH=src python3 -m driverx export-bench2drive-suite \
  --recipe artifacts/runs/scenario-forge/scenario_recipes.json \
  --recipe-id generated-base-animals-0076-visual-noise-000 \
  --route-root ../external/fail2drive \
  --behavior-id motorcycle_filtering \
  --config configs/simlingo.sample.yaml \
  --run-id task18-route-pack
PYTHONPATH=src python3 -m driverx plan-overlay-injection \
  --route-pack artifacts/runs/task18-route-pack/bench2drive_route_pack.json \
  --run-id task21-overlay-injection
bash scripts/run_carla_client_docker.sh python -m driverx run-overlay-injection \
  --config configs/carla_local.sample.yaml \
  --plan artifacts/runs/task21-overlay-injection/overlay_injection_plan.json \
  --route-limit 1 \
  --run-id task22-overlay-injection-run
PYTHONPATH=src python3 -m driverx plan-simlingo-sidecar \
  --simlingo-plan artifacts/runs/task18-route-pack/simlingo_command_plan.json \
  --overlay-plan artifacts/runs/task21-overlay-injection/overlay_injection_plan.json \
  --docker-carla-client \
  --run-id task23-sidecar-plan
PYTHONPATH=src python3 -m driverx run-simlingo-sidecar \
  --plan artifacts/runs/task23-sidecar-plan/simlingo_sidecar_plan.json \
  --timeout-s 900 \
  --run-id task24-sidecar-run

# Combine the generated scenarios, route pack, overlay plan, sidecar run,
# policy comparison, SimLingo result/evidence, and blocker ledger into one report
PYTHONPATH=src python3 -m driverx build-ood-suite-report \
  --scenario-summary artifacts/runs/scenario-forge/scenario_suite_summary.json \
  --route-pack artifacts/runs/task18-route-pack/bench2drive_route_pack.json \
  --overlay-plan artifacts/runs/task21-overlay-injection/overlay_injection_plan.json \
  --sidecar-plan artifacts/runs/task23-sidecar-plan/simlingo_sidecar_plan.json \
  --sidecar-run artifacts/runs/task24-sidecar-run/simlingo_sidecar_run.json \
  --rag-comparison artifacts/runs/task14-rag/rag_comparison.json \
  --simlingo-result artifacts/runs/task19-simlingo-result/simlingo_result_record.json \
  --blockers blockers.md \
  --run-id task25-ood-suite-report
# `--simlingo-result` also accepts remote evidence from
# `summarize-simlingo-evidence`, such as
# tickets/archive/TASK-020/artifacts/task20-evidence-final/remote_simlingo_evidence.json.

# Run a generated OOD mini-suite and build per-recipe evidence bundles
PYTHONPATH=src python3 -m driverx run-generated-ood-suite \
  --config configs/scenario_forge.sample.yaml \
  --carla-config configs/carla_local.sample.yaml \
  --limit 1 \
  --run-id task36-suite

# Report which policy adapters are ready, dry-run-ready, or blocked
PYTHONPATH=src python3 -m driverx build-policy-runtime-matrix \
  --carla-config configs/carla_local.sample.yaml \
  --simlingo-config configs/simlingo.sample.yaml \
  --suite artifacts/runs/task36-suite/route-pack/bench2drive_routes/generated_routes.xml \
  --run-id task37-policy-matrix

# Summarize local or remote Alpamayo probe artifacts without leaking secrets
PYTHONPATH=src python3 -m driverx probe-alpamayo \
  --artifact-root artifacts/remote/alpamayo-probe/latest \
  --run-id task38-alpamayo-probe

# On the current RunPod RTX 6000 Ada lane, Alpamayo load probes should use
# eager attention. The SDPA fallback path is rejected by Alpamayo's custom
# architecture; flash-attn can be tested separately on hosts with nvcc.
DRIVERX_ENV_FILE=.env \
GPU_SSH_OPTS="-p 55050 -i ~/.ssh/id_ed25519_runpod" \
PYTHON_BIN=/workspace/alpamayo1.5/a1_5_venv/bin/python \
ALPAMAYO_LOAD=1 \
ALPAMAYO_ATTN_IMPLEMENTATION=eager \
REMOTE_CACHE_ROOT=/workspace/.cache/driverx \
bash scripts/run_remote_alpamayo_probe.sh root@195.26.233.80 \
  artifacts/remote/alpamayo-probe/latest

# Capture Alpamayo-shaped camera windows from an existing CARLA route actor.
# Use this during a Fail2Drive route run once Town13 is loadable.
bash scripts/run_carla_client_docker.sh python -m driverx capture-alpamayo-carla-input \
  --config configs/carla_local.sample.yaml \
  --host host.docker.internal \
  --attach-role-name hero \
  --no-fallback-spawn \
  --route-name Generalization_PedestriansOnRoad_1088 \
  --route-evidence tickets/TASK-060/artifacts/town13-route-evidence/run_evidence.json \
  --run-id task61-route-aligned-capture

# Compare live Alpamayo open-loop policy decisions with and without retrieved
# DriverX safety memory. The comparison is intentionally not a closed-loop
# CARLA-control claim.
PYTHONPATH=src python3 -m driverx build-alpamayo-ood-comparison \
  --baseline-decision tickets/archive/TASK-039/artifacts/live-capture-summary/alpamayo_policy_decision.json \
  --memory-decision tickets/archive/TASK-056/artifacts/live-memory-run-summary/alpamayo_policy_decision.json \
  --source-package artifacts/runs/task51-live-alpamayo-capture/alpamayo_carla_input_package.json \
  --route-evidence tickets/archive/TASK-055/artifacts/town10-route-evidence/run_evidence.json \
  --run-id task56-alpamayo-ood-comparison

# Convert a cached Alpamayo/DriverX policy decision into bounded CARLA-style
# controls. This is a dry-run bridge for trajectory intent, not real-time VLA
# closed-loop driving.
PYTHONPATH=src python3 -m driverx replay-policy-decision \
  --decision tickets/archive/TASK-039/artifacts/live-capture-summary/alpamayo_policy_decision.json \
  --trajectory-frame ego \
  --run-id task62-cached-replay

# Build the judge-facing demo pack with storyboard, artifact map, declarations,
# write-up draft, and first understood failure case
PYTHONPATH=src python3 -m driverx build-demo-pack \
  --local-demo tickets/TASK-064/artifacts/local-ood-demo/end_to_end_demo.json \
  --generated-suite tickets/TASK-064/artifacts/local-ood-demo/scenario/scenario_suite_summary.json \
  --policy-matrix tickets/TASK-064/artifacts/local-ood-demo/policy/policy_reaction_matrix.json \
  --alpamayo-probe tickets/TASK-059/artifacts/physicalai-shape-probe-summary/alpamayo_shape_probe_report.json \
  --route-evidence tickets/TASK-071/artifacts/town13-early-route-evidence/run_evidence.json \
  --alpamayo-comparison tickets/archive/TASK-056/artifacts/town10-memory-comparison/alpamayo_ood_comparison.json \
  --cached-replay tickets/TASK-062/artifacts/cached-alpamayo-replay/carla_policy_replay.json \
  --blockers blockers.md \
  --progress docs/progress.md \
  --run-id submission-pack-v2-final

# Run the DriverX-owned scripted CARLA OOD demo. Launch this through the CARLA
# 0.9.16 client container while CARLA.app is fully loaded.
bash scripts/run_carla_client_docker.sh python -m driverx run-carla-ood-demo \
  --config configs/carla_ood_demo.local.sample.yaml \
  --tick-count 120 \
  --run-id task78-live-retry

# Assemble OOD video evidence from RGB frames and entity tracks. Use
# source-kind=fixture only for synthetic/local proof frames; omit it for live
# scripted CARLA frames.
PYTHONPATH=src python3 -m driverx assemble-ood-video \
  --rgb-folder tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb \
  --tracks tickets/TASK-078/artifacts/task78-live-ood-capture-v3/entity_tracks.json \
  --scenario-id generated-base-animals-0076-regional-driving-behavior-000 \
  --behavior-id motorcycle_filtering \
  --ood-tags motorcycle,filtering,roadside_vendor,regional_context,generated_assets \
  --source-kind live_carla \
  --claim-label live_scripted_carla_ood_demo \
  --fps 5 \
  --min-frames 120 \
  --run-id live-ood-video

# Build an Alpamayo package from the same live generated scene. This duplicates
# the single CARLA ego RGB camera across Alpamayo's three camera slots and keeps
# the claim explicitly open-loop.
PYTHONPATH=src python3 -m driverx build-alpamayo-ood-package \
  --rgb-folder tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb \
  --tracks tickets/TASK-078/artifacts/task78-live-ood-capture-v3/entity_tracks.json \
  --scenario-report tickets/TASK-078/artifacts/task78-live-ood-capture-v3/carla_ood_demo.json \
  --video-evidence tickets/TASK-079/artifacts/task79-live-ood-video/ood_video_evidence.json \
  --run-id live-same-scene-package
PYTHONPATH=src python3 -m driverx materialize-alpamayo-input \
  --package artifacts/runs/live-same-scene-package/alpamayo_carla_input_package.json \
  --run-id live-same-scene-materialized

# Build the V4 demo pack with live CARLA OOD video, same-scene Alpamayo memory
# comparison, and stock proxy asset evidence.
PYTHONPATH=src python3 -m driverx build-demo-pack \
  --local-demo tickets/TASK-064/artifacts/local-ood-demo/end_to_end_demo.json \
  --generated-suite tickets/TASK-064/artifacts/local-ood-demo/scenario/scenario_suite_summary.json \
  --policy-matrix tickets/TASK-064/artifacts/local-ood-demo/policy/policy_reaction_matrix.json \
  --alpamayo-probe tickets/TASK-059/artifacts/physicalai-shape-probe-summary/alpamayo_shape_probe_report.json \
  --route-evidence tickets/TASK-071/artifacts/town13-early-route-evidence/run_evidence.json \
  --alpamayo-comparison tickets/TASK-081/artifacts/task81-live-same-scene-comparison/alpamayo_ood_comparison.json \
  --ood-video-evidence tickets/TASK-079/artifacts/task79-live-ood-video/ood_video_evidence.json \
  --alpamayo-scene tickets/TASK-080/artifacts/task80-live-same-scene-alpamayo-scene-v2/alpamayo_ood_scene.json \
  --generated-asset-evidence tickets/TASK-076/artifacts/stock-proxy-assets-v2/asset_summary.json \
  --cached-replay tickets/TASK-062/artifacts/cached-alpamayo-replay/carla_policy_replay.json \
  --blockers blockers.md \
  --progress docs/progress.md \
  --run-id submission-pack-v4

# Once a live route run has written RGB frames under SAVE_PATH, assemble MP4
# evidence without relying on Fail2Drive's missing tools/generate_video.py
PYTHONPATH=src python3 -m driverx assemble-route-video \
  --rgb-folder artifacts/runs/task36-suite/recipes/000_example/fail2drive_outputs/visualizations/RouteName/rgb \
  --output-video artifacts/runs/task36-suite/RouteName.mp4 \
  --run-id task41-route-video

# For slow local CARLA runs, capture judge-visible video as soon as frames exist
# and label the route evidence as partial unless the route finishes scoring.
bash scripts/run_fail2drive_client_docker.sh python -m driverx run-fail2drive-route \
  --plan tickets/TASK-060/artifacts/town13-video-plan-after-restart/fail2drive_video_smoke_plan.json \
  --timeout-s 600 \
  --min-video-frames 5 \
  --video-timeout-s 420 \
  --video-fps 10 \
  --stop-after-video \
  --run-id town13-early-video

# Plan generated OOD assets and attach asset ids to scenario recipes
PYTHONPATH=src python3 -m driverx plan-assets \
  --recipe artifacts/runs/scenario-forge/scenario_recipes.json \
  --run-id task12-assets

# Run a fixture through the policy adapter surface
PYTHONPATH=src python3 -m driverx run-policy-fixture \
  --policy mock \
  --with-memory \
  --run-id task13-policy-memory

# Compare a policy with and without retrieved safety memory
PYTHONPATH=src python3 -m driverx run-rag-comparison \
  --policy mock \
  --run-id task14-rag

# Inspect and plan the external SimLingo/CarLLaVA backend
PYTHONPATH=src python3 -m driverx inspect-simlingo \
  --run-id task15-simlingo-readiness
PYTHONPATH=src python3 -m driverx plan-simlingo-run \
  --config configs/simlingo.sample.yaml \
  --run-id task15-simlingo-plan
PYTHONPATH=src python3 -m driverx ingest-simlingo-result \
  --result tickets/archive/TASK-017/artifacts/qa/2026-05-04T194700Z/seed_1_res.json \
  --compatibility tickets/archive/TASK-017/artifacts/qa/2026-05-04T194700Z/torch_cuda_compatibility.json \
  --route-log tickets/archive/TASK-017/artifacts/qa/2026-05-04T194700Z/run_one_route.log \
  --run-id task19-simlingo-result

# On a Linux NVIDIA GPU host, sync this repo and launch the SimLingo bootstrap
# in tmux. `HF_TOKEN` is read from the local environment or ignored `.env`,
# copied through a temporary remote file, then that temporary file is removed
# after the tmux job starts. Existing host Hugging Face login state is preserved.
bash scripts/sync_remote_gpu.sh root@31.22.104.74 /workspace/0xDriver
bash scripts/run_remote_simlingo_bootstrap.sh root@31.22.104.74 /workspace/0xDriver

# For RunPod direct TCP SSH, resolve the current pod port first. RunPod TCP
# mappings change when pods are replaced or restarted, so do not reuse stale
# Connect-tab ports blindly.
PYTHONPATH=src python3 -m driverx resolve-runpod-ssh \
  --env-file .env \
  --ssh-key ~/.ssh/id_ed25519_runpod \
  --run-id runpod-current

# Then export the emitted GPU_SSH_HOST / GPU_SSH_OPTS values before running
# remote helpers.
GPU_SSH_HOST=root@195.26.233.80 \
GPU_SSH_OPTS="-p 55050 -i ~/.ssh/id_ed25519_runpod" \
bash scripts/sync_remote_gpu.sh
GPU_SSH_HOST=root@195.26.233.80 \
GPU_SSH_OPTS="-p 55050 -i ~/.ssh/id_ed25519_runpod" \
SESSION_NAME=task20 \
REMOTE_RUN_ID=task20 \
bash scripts/run_remote_simlingo_bootstrap.sh

# Pull only compact logs, JSON, Markdown, checksums, and generated run scripts
# back from the remote artifact directory. This deliberately excludes model
# weights, simulator archives, videos, images, caches, and CARLA files.
GPU_SSH_HOST=root@195.26.233.80 \
GPU_SSH_OPTS="-p 55050 -i ~/.ssh/id_ed25519_runpod" \
REMOTE_RUN_ID=task20 \
bash scripts/pull_remote_simlingo_artifacts.sh

# After the bootstrap emits run_one_route_with_carla_as_user.sh, launch the
# stock route, keep the remote route log, and pull compact evidence back even
# when the route fails with a runtime blocker.
GPU_SSH_HOST=root@195.26.233.80 \
GPU_SSH_OPTS="-p 55050 -i ~/.ssh/id_ed25519_runpod" \
REMOTE_RUN_ID=task20 \
bash scripts/run_remote_simlingo_route.sh

# Classify whatever compact evidence came back into a small verdict report.
PYTHONPATH=src python3 -m driverx summarize-simlingo-evidence \
  --artifact-root tickets/archive/TASK-020/artifacts/task20-remote \
  --output-root tickets/archive/TASK-020/artifacts \
  --run-id task20-evidence

# On a fresh GPU host, collect the small preflight artifacts used by
# assess-gpu-host before launching an expensive route job.
GPU_SSH_HOST=root@195.26.233.80 \
GPU_SSH_OPTS="-p 55050 -i ~/.ssh/id_ed25519_runpod" \
LOCAL_PROBE_DIR=tickets/archive/TASK-029/artifacts/gpu-host-probe \
bash scripts/run_remote_gpu_probe.sh

# Convert CUDA, CARLA graphics, and remote evidence into a host recommendation.
PYTHONPATH=src python3 -m driverx assess-gpu-host \
  --gpu-snapshot tickets/archive/TASK-020/artifacts/2026-05-05T151900+0800/remote_gpu_snapshot.txt \
  --torch-compatibility tickets/archive/TASK-020/artifacts/task20-remote/torch_cuda_compatibility.json \
  --carla-diagnostics tickets/archive/TASK-020/artifacts/task20-remote/carla_runtime_diagnostics.md \
  --simlingo-evidence tickets/archive/TASK-020/artifacts/task20-evidence-final/remote_simlingo_evidence.json \
  --run-id h100-host-suitability

# Build a submission-facing Markdown/JSON dossier from current evidence.
PYTHONPATH=src python3 -m driverx build-submission-dossier \
  --ood-suite-manifest tickets/archive/TASK-027/artifacts/ood-suite-report-task20-blocker/ood_suite_manifest.json \
  --gpu-host-suitability tickets/archive/TASK-029/artifacts/h100-probe-live-suitability/gpu_host_suitability.json \
  --output-root tickets/archive/TASK-031/artifacts \
  --run-id current-submission-dossier
```

Stock SimLingo currently targets Python 3.8 and `torch==2.2.0+cu121`. That
works best on CUDA architectures already compiled into that wheel, especially
H100/H200-class `sm_90` hosts. RTX PRO 6000 Blackwell requires `sm_120`, so it
needs a separate PyTorch/CARLA rebuild lane before it can run the stock route.
Generated Bench2Drive route packs keep route XML stock-compatible and store OOD
object/behavior intent in DriverX sidecar overlays until a companion CARLA
actor injector is running.
`run-simlingo-sidecar` executes an existing sidecar plan with per-process logs,
exit codes, and timings; use it after the stock SimLingo route path is stable
on the same CARLA host.

Generated run artifacts are written under `artifacts/runs/` and remain ignored
by git.

## External Fail2Drive Checkout

Fail2Drive and SimLingo are used as read-only external references, not vendored
into this repo:

```bash
mkdir -p ../external
git clone https://github.com/autonomousvision/fail2drive.git ../external/fail2drive
git clone https://github.com/RenzKa/simlingo.git ../external/simlingo
```

`configs/carla_local.sample.yaml` defaults to `../external/fail2drive`. The
SimLingo planner defaults to `../external/simlingo`. Local tests use tiny
fixtures, so they do not require CARLA, Conda, model checkpoints, or CUDA.

## Optional CARLA On Apple Silicon

CARLA can reportedly run on Apple Silicon through a community
Wine/Kegworks/D3DMetal wrapper for the Windows CARLA package. Treat that as a
local smoke-test path until CARLA server, Python client, Fail2Drive routes, and
policy execution all work together.

For reproducible Fail2Drive + VLA experiments, use Linux NVIDIA hardware.

## Waymo Support Track

The existing Waymo commands remain available:

```bash
PYTHONPATH=src python3 -m driverx inspect-scene --config configs/mock.yaml
PYTHONPATH=src python3 -m driverx run-scene --config configs/mock.yaml --run-id demo
PYTHONPATH=src python3 -m driverx run-batch --config configs/mock.yaml --run-id demo-batch
PYTHONPATH=src python3 -m driverx run-experiment --config configs/mock.yaml --run-id demo-experiment
bash scripts/pre_push_check.sh
```

Real Waymo TFRecords still use the Docker compatibility bridge documented by
the archived TASK-003 through TASK-006 evidence.
