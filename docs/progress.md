# Progress

Live orchestration log for 0xDriver.

## Current Goal

Build the CARLA/Fail2Drive-first minimal-shot VLA harness:

- keep the Waymo/open-loop support track archived and available
- use Fail2Drive seeds as OOD scenario sources
- generate regional behavior and object novelty
- log CARLA entity tracks and policy outputs
- compare frozen policy behavior with and without retrieved safety memory

## Completed

- [x] TASK-001 fixture-backed pipeline
- [x] TASK-002 optional real Waymo integration
- [x] TASK-003 Waymo Linux Docker runtime
- [x] TASK-004 real Waymo batch baseline
- [x] TASK-005 experiment harness and deterministic baselines
- [x] TASK-006 motion-prior hybrid planner
- [x] TASK-007 local scenario forge, memory bank, CARLA smoke, Fail2Drive dry-run planning
- [x] TASK-008 live CARLA Python API probe through Docker
- [x] TASK-009 ego spawn, camera capture, and entity tracks
- [x] TASK-010 regional driving behavior library
- [x] TASK-011 scenario-to-CARLA script compiler
- [x] TASK-012 generated asset pipeline
- [x] TASK-013 policy adapter interface
- [x] TASK-014 retrieval-augmented VLA comparison harness
- [x] TASK-015 SimLingo backend readiness and run planner
- [x] TASK-016 local CARLA 0.9.16 Docker client proof
- [x] TASK-017 remote GPU SimLingo one-route proof with precise runtime blocker
- [x] TASK-019 SimLingo result ingestion
- [x] TASK-018 generated Bench2Drive route pack export
- [x] TASK-021 overlay injection dry-run plan
- [x] TASK-022 live companion actor injector interface
- [x] TASK-023 SimLingo sidecar orchestration plan
- [x] TASK-024 local timed sidecar process runner
- [x] TASK-025 OOD suite evidence report
- [x] TASK-026 remote SimLingo evidence classifier
- [x] TASK-027 OOD suite remote evidence ingestion
- [x] TASK-028 GPU host suitability report
- [x] TASK-029 remote GPU probe script
- [x] TASK-030 SimLingo CLI extraction
- [x] TASK-031 submission dossier builder
- [x] TASK-032 board normalized for route-video-first execution
- [x] TASK-033 Fail2Drive route video smoke
- [x] TASK-034 video and telemetry evidence pipeline
- [x] TASK-035 live OOD overlay injection evidence
- [x] TASK-036 generated OOD suite runner
- [x] TASK-037 policy runtime matrix
- [x] TASK-038 Alpamayo offline probe
- [x] TASK-040 submission demo pack
- [x] TASK-041 DriverX route video assembler
- [x] TASK-042 local Fail2Drive route runner
- [x] TASK-043 Dockerized Fail2Drive client runner
- [x] TASK-044 Alpamayo remote probe host prep
- [x] TASK-045 Alpamayo release contract extractor
- [x] TASK-046 Alpamayo trajectory conversion
- [x] TASK-047 Alpamayo input package manifest
- [x] TASK-048 Alpamayo remote release bootstrap script
- [x] TASK-049 Alpamayo offline policy rehearsal
- [x] TASK-050 live local CARLA 0.9.16 probe refresh
- [x] TASK-051 live CARLA Alpamayo input capture
- [x] TASK-052 RunPod Alpamayo bootstrap, download, and eager load proof
- [x] TASK-053 live Alpamayo inference shape probe
- [x] TASK-054 Alpamayo tensor materializer from DriverX/CARLA captures
- [x] TASK-039 Alpamayo CARLA adapter
- [x] TASK-054B self-resolved Fail2Drive Docker/numpy route path
- [x] TASK-055 live OOD scenario video evidence
- [x] TASK-056 Alpamayo OOD evaluation harness

## Active Roadmap

- [ ] TASK-057 demo pack refresh

## Latest Evidence

- TASK-056 compares the real TASK-039 baseline Alpamayo CARLA capture against a
  memory-augmented Alpamayo rerun. Both are labeled open-loop only. Retrieved
  memory changed the CoC from accelerating through a green-light intersection to
  keeping lane because the intersection was clear, changed the 20-point
  trajectory by `0.9666m` mean L2 and `2.8886m` final L2, and added about
  `611.1ms` latency on the same RunPod/eager path.
- TASK-008 TCP smoke reached CARLA at `127.0.0.1:2000`.
- TASK-008 Docker probe reached CARLA through `host.docker.internal:2000`.
- Probe reported map `Carla/Maps/Town10HD_Opt`, actor count `23`, server
  version `0.9.16`, and client version `0.9.16`.
- TASK-009 live ego smoke spawned ego actor `24`, camera actor `25`, captured
  `ego_camera.png`, wrote `entity_tracks.json`, and destroyed actors `[25, 24]`.
- TASK-010 generated six OOD behavior traces covering no-signal cut-ins,
  sudden brakes, motorcycle filtering, wrong-way shoulder creep, informal
  right-of-way pushes, and fast low-profile two-wheeler proxies.
- TASK-011 compiled a generated recipe plus `motorcycle_filtering` into a
  CARLA script plan with ego actor, OOD actor, RGB sensor, ticks, expected
  outputs, and cleanup order.
- TASK-012 planned three generated OOD assets in dry-run mode, validated scale,
  collision, placement, license metadata, and emitted Meshy setup blockers when
  no API key is present.
- TASK-013 added mock, memory-aware mock, local hybrid fallback, and
  setup-checked VLM/API, SimLingo/CarLLaVA, and Alpamayo policy adapters.
- TASK-014 compared mock policy and mock+memory on the same
  `motorcycle_filtering` pressure case, improving the proxy driving score from
  `58.0` to `95.0` while keeping `live_model_claim=false`.
- TASK-015 cloned external SimLingo, inspected commit
  `743b243afd6cf5ff51b9fa1f8cac86f22d569684`, confirmed CARLA `0.9.15`,
  Python `3.8`, CUDA-required live inference, and generated a Bench2Drive
  dry-run command plan.
- TASK-016 built the Linux amd64 CARLA 0.9.16 Docker client bridge and local
  proof script for the Apple Silicon CARLA wrapper.
- TASK-017 synced the repo to a Prime Intellect RTX PRO 6000 host, installed
  CARLA 0.9.15 plus AdditionalMaps, installed SimLingo, downloaded the pinned
  checkpoint, reached CARLA route execution, and recorded the first-tick
  Blackwell `sm_120` / torch `sm_90` kernel blocker.
- TASK-019 parses the TASK-017 Bench2Drive result JSON and produces a compact
  SimLingo result report with CUDA compatibility and route-log signals.
- TASK-018 exports generated OOD recipes to stock-compatible Bench2Drive route
  XML, DriverX sidecar overlays, and a SimLingo command plan with an absolute
  `--routes` path.
- TASK-021 compiles TASK-018 sidecar overlays into dry-run companion CARLA
  actor/sensor/tick plans with `2` routes, distinct overlay actors
  (`occluder`, `distractor`), route-specific companion blueprints
  (`static.prop.streetbarrier`, `static.prop.trafficwarning`), preserved
  runtime contracts, `25` behavior samples plus `1` companion spawn tick per
  route (`26` ticks total), and zero validation errors.
- TASK-022 consumes a TASK-021 plan, spawns only `companion_actor_*` overlays,
  applies their planned ticks, writes entity tracks, and cleans up the spawned
  actors. Local native evidence records the expected missing-`carla` package
  setup blocker; fake-CARLA tests prove spawn/tick/track/cleanup behavior.
- TASK-023 pairs the TASK-018 SimLingo command plan with the TASK-021 overlay
  injection plan into a manual two-process sidecar launch plan, preserving
  SimLingo blockers, DriverX overlay validation state, expected outputs, and a
  Docker CARLA-client command for local overlay injection.
- TASK-020 RunPod H100 direct TCP SSH is reachable with x86_64 Linux, H100
  80GB HBM3, driver `580.126.09`, and persistent `/workspace`; root disk is
  only `20G`, so conda, cache, models, CARLA, and artifacts must stay under
  `/workspace`.
- TASK-020 now has `scripts/pull_remote_simlingo_artifacts.sh` so compact H100
  evidence can be pulled back without copying model weights, CARLA files,
  archives, media, caches, or generated videos into the repo.
- TASK-020 now has `scripts/run_remote_simlingo_route.sh` so the generated
  remote stock-route script can be launched, logged, and followed by compact
  artifact pullback whether it succeeds or hits a precise runtime blocker.
- TASK-026 adds `summarize-simlingo-evidence`, a local classifier for pulled
  H100 SimLingo artifacts. It detects missing roots, incomplete/completed
  bootstraps, route logs, CUDA compatibility JSON, `*_res.json` route results,
  and writes a compact JSON/Markdown verdict without requiring CARLA,
  SimLingo, TensorFlow, or a GPU.
- TASK-020 H100 route wrapper pulled compact live evidence. CUDA compatibility
  is good for SimLingo on H100 (`sm_90`), but CARLA 0.9.15 exits before
  opening port `20000`; diagnostics show default Vulkan only exposes
  `llvmpipe` and the NVIDIA Vulkan ICD fails with
  `ERROR_INCOMPATIBLE_DRIVER`. This blocks closed-loop route proof on the
  current H100 container before model inference begins.
- TASK-027 lets the OOD suite report consume both old TASK-019
  `simlingo_result_record.json` artifacts and new TASK-026
  `remote_simlingo_evidence.json` artifacts. Current report evidence now
  surfaces `simlingo_state=route_infrastructure_blocked`, the H100 route log,
  the CARLA runtime diagnostics path, and the TASK-020 CARLA/Vulkan blocker in
  one top-level manifest.
- TASK-028 adds `assess-gpu-host`, a local host suitability report over
  torch/CUDA compatibility, CARLA graphics diagnostics, pulled SimLingo
  evidence, and optional GPU snapshots. Current H100 evidence is classified as
  `blocked`: SimLingo CUDA support is ready for `sm_90`, but CARLA graphics are
  blocked by the Vulkan/port failure; the report recommends a graphics-capable
  NVIDIA host instead of another compute-only H100/H200 container.
- TASK-029 adds `scripts/run_remote_gpu_probe.sh`, a compact SSH preflight that
  writes `gpu_snapshot.txt`, `torch_cuda_compatibility.json`, and
  `carla_runtime_diagnostics.md` remotely, then pulls only those small probe
  artifacts back for `assess-gpu-host`. A live H100 probe ran successfully and
  reproduced the same split verdict: CUDA/model support is ready, but CARLA
  graphics are blocked by llvmpipe/NVIDIA ICD `ERROR_INCOMPATIBLE_DRIVER`.
- TASK-030 extracted SimLingo readiness, run planning, result ingestion,
  evidence, and sidecar CLI handlers into `driverx.simulators.simlingo_cli`,
  reducing the central `src/driverx/cli.py` from the size-gate edge to `823`
  lines while preserving command help and focused CLI tests.
- TASK-031 adds `build-submission-dossier`, producing one Markdown/JSON dossier
  from the OOD suite manifest, GPU host suitability report, progress ledger,
  and blocker ledger. The current dossier is a submission-facing summary of the
  minimal-shot OOD harness, evidence metrics, live GPU blocker, and demo outline.
- TASK-032 archives completed setup tickets and creates the route-video-first
  phase from TASK-033 through TASK-040. The project should now prove
  Fail2Drive/CARLA video evidence before spending more time on any one VLA
  backend.
- TASK-033 adds `plan-fail2drive-video-smoke`, a dry-run route-video proof
  command that writes Fail2Drive evaluator command, `LIVE_VISU=1`/`SAVE_PATH`,
  expected result/debug/RGB/video paths, and actionable live blockers. Current
  local evidence also records that the external Fail2Drive checkout lacks
  `tools/generate_video.py`, so TASK-034 should accept external videos or add a
  DriverX-owned assembler.
- TASK-034 adds `build-route-evidence`, a route evidence bundle that reads
  planned or explicit result JSON, entity tracks, videos, screenshots, and logs.
  It writes `run_evidence.json` plus `run_evidence.md`, extracts score/route
  completion/track/video metadata when present, and turns missing live artifacts
  into blockers instead of crashes.
- TASK-035 adds `build-overlay-evidence`, connecting overlay plans and live
  overlay runs back to generated recipe ids. It validates behavior-pressure
  assertions for cut-in, sudden-brake, and motorcycle-filtering traces, reports
  actor tracks plus cleanup state, and returns a clean missing-live-CARLA
  blocker when no overlay run exists yet.
- TASK-036 adds `run-generated-ood-suite`, which turns scenario seeds into a
  repeatable suite: generated recipes, Bench2Drive route pack, overlay plan,
  per-recipe Fail2Drive video-smoke plans, per-recipe route evidence bundles,
  overlay evidence, aggregate readiness, and a `--limit` ramp for 1 -> 10
  scenario runs.
- TASK-037 adds `build-policy-runtime-matrix`, which records policy adapter
  rows with runtime kind, required hardware, ready state, command/config path,
  and blocker. Current evidence marks `mock`, `mock-memory`, `hybrid`,
  `fail2drive-basic`, and `fail2drive-expert` ready or dry-run-ready while
  keeping SimLingo and Alpamayo blocked independently.
- TASK-038 adds `probe-alpamayo` plus
  `scripts/run_remote_alpamayo_probe.sh`, a download/load-gated offline probe
  that records GPU snapshot, package versions, model load state, memory usage,
  latency, expected adapter schema, and secret-redacted failure classification.
- TASK-040 adds `build-demo-pack`, producing the judge-facing 1-5 minute demo
  outline, concrete artifact map, model/data declarations, short write-up
  draft, and a named failure case from the generated OOD suite.
- TASK-041 adds `assemble-route-video`, a DriverX-owned ffmpeg route-video
  assembler that replaces the missing Fail2Drive `tools/generate_video.py`
  dependency once a route run writes RGB frames. Current evidence is blocked
  only by the absent RGB folder.
- TASK-042 adds `run-fail2drive-route`, a structured route-command runner for
  Fail2Drive video-smoke plans. Local CARLA was running, but the native Mac
  attempt failed before CARLA connection because the evaluator's Python
  environment lacked `numpy`; the next implementation should use a Dockerized
  Fail2Drive client env.
- TASK-043 adds a Dockerized Fail2Drive client image, build script, run script,
  and container config that mount both `0xDriver` and `../external/fail2drive`
  and target host CARLA at `host.docker.internal:2000`. Local build was
  stopped after the pip wheel layer stalled, so rerun it on a faster network or
  remote host.
- TASK-044 hardens `scripts/run_remote_alpamayo_probe.sh` for real rented-GPU
  access: custom SSH port/key via `GPU_SSH_OPTS`, local `.env` sourcing without
  secret printing, gated download/load flags, safe remote token handoff, and
  compact rsync/tar artifact pullback. The earlier RunPod `36723` TCP mapping
  was stale; TASK-052 now resolves the current SSH target from RunPod metadata.
- TASK-045 adds `inspect-alpamayo-release`, a GPU-free contract extractor over
  the local `../external/alpamayo1.5` checkout. Current evidence records
  commit `2eff703`, Python `3.12`, CUDA `12.x`, 22GB weights, 24/40/60GB VRAM
  modes, default camera ids `[0, 1, 2, 6]`, four frames per camera, 16 history
  steps, native 64-waypoint 10Hz trajectory output, CoC text output, VQA
  support, and DriverX's 20-point 4Hz conversion target.
- TASK-046 adds `convert-alpamayo-trajectory`, converting native Alpamayo
  `pred_xyz` outputs into DriverX `TrajectoryCandidate` chunks by selecting one
  sample and resampling 64 ego-local 10Hz xyz waypoints to 20 ego-local 4Hz xy
  points over 5 seconds.
- TASK-047 adds `build-alpamayo-input`, a fixture-backed Alpamayo input
  manifest with camera-major windows, camera ids/names, 16-step ego history,
  identity rotation scaffolding, nav text, and memory context. It remains
  GPU-free and marks repeated fixture images as placeholders for future live
  CARLA temporal capture.
- TASK-048 adds `scripts/bootstrap_remote_alpamayo_release.sh`, a secret-safe
  remote setup path for cloning Alpamayo 1.5, installing uv, creating the
  Python 3.12 venv, choosing SDPA or flash-attn dependency sync, and optionally
  running upstream `test_inference.py`. Current remote execution now uses
  RunPod direct TCP SSH resolved from live pod metadata.
- TASK-052 adds `resolve-runpod-ssh`, hardens remote Alpamayo cache placement
  on `/workspace`, bootstraps Alpamayo 1.5 on the RunPod RTX 6000 Ada pod,
  downloads the `nvidia/Alpamayo-1.5-10B` snapshot, resolves the nested
  `nvidia/Cosmos-Reason2-8B` access gate, and proves load-only execution with
  `ALPAMAYO_ATTN_IMPLEMENTATION=eager`. The successful eager load took about
  `32.1s` and peaked at about `21.1GB` VRAM; SDPA mode is not compatible with
  Alpamayo's custom architecture.
- TASK-053 adds live Alpamayo inference shape probing. The upstream
  `nvidia/PhysicalAI-Autonomous-Vehicles` sample dataset is gated, so the probe
  falls back to synthetic Alpamayo-shaped tensors and still exercises the real
  `sample_trajectories_from_data_with_vlm_rollout` path. Observed shapes are
  `pred_xyz=[1,1,1,64,3]`, `pred_rot=[1,1,1,64,3,3]`,
  `extra.cot=[1,1,1]`, with about `96.7s` live latency and `24.5GB` peak VRAM.
- TASK-054 materializes live TASK-051 CARLA captures into a torch-ready
  Alpamayo contract with `image_frames=[3,4,3,90,160]`,
  `camera_indices=[3]`, `ego_history_xyz=[1,1,16,3]`, and
  `ego_history_rot=[1,1,16,3,3]`; local validation does not require CUDA and
  the actual tensor loader is lazy for the remote Alpamayo environment.
- TASK-039 adds an open-loop `alpamayo-live` policy path. The RunPod RTX 6000
  Ada live inference completed on a TASK-051 CARLA capture with
  `pred_xyz=[1,1,1,64,3]`, `pred_rot=[1,1,1,64,3,3]`,
  `extra.cot=[1,1,1]`, `99.8s` latency, and `23.2GB` peak VRAM, then converted
  the native trajectory into a 20-point DriverX policy decision labeled
  `closed_loop_control=false`.
- TASK-055 bundles the TASK-054B Town10 live route video proof into compact
  route evidence. The evidence links the route result JSON, stdout/stderr logs,
  DriverX-assembled MP4 metadata, and realistic limitations: no entity tracks,
  no completed route score because the run was smoke-bounded, and stock
  Fail2Drive OOD split routes still require unavailable Town13.
- TASK-054B resolves the local Fail2Drive Docker/numpy blocker. The lightweight
  Docker client imports `carla` and `numpy`; the Torch image also imports
  `torch` and CARLA PythonAPI `agents`. The runner now exports Fail2Drive's
  required `TOWN`, `REPETITION`, `SCENARIO_RUNNER_ROOT`, and `VIZ_PATH`, and it
  classifies failed checkpoints, missing maps, missing RGB, and timeout output
  safely. Stock Fail2Drive split routes reach local CARLA but block on missing
  `Town13`; the Town10 fallback route produced `41` RGB frames and an MP4
  before the bounded smoke timeout.
- TASK-049 adds `run-alpamayo-offline`, an end-to-end adapter rehearsal that
  writes an Alpamayo input manifest, converts saved native `pred_xyz`, and
  emits a normal DriverX policy decision with `offline_replay=true`. This proves
  the handoff path without claiming live model execution.
- TASK-050 refreshed live local CARLA evidence through
  `scripts/run_carla_client_docker.sh`; Docker Python connected to
  `host.docker.internal:2000`, reporting `Carla/Maps/Town10HD_Opt`, `23`
  actors, and matching server/client version `0.9.16`.
- TASK-051 adds `capture-alpamayo-carla-input` and live evidence from local
  CARLA. The run spawned one ego vehicle plus three RGB cameras for Alpamayo ids
  `[0, 1, 2]`, saved `12` PNG frames, wrote an Alpamayo-shaped input package
  with tensor shape `3 x 4 x 3 x 90 x 160`, and cleaned up all spawned actors.
- TASK-024 adds `run-simlingo-sidecar`, a timed process runner for existing
  TASK-023 plans. Local evidence executed harmless SimLingo/overlay sample
  commands, wrote process logs, timings, exit codes, JSON, and Markdown.
- TASK-025 adds `build-ood-suite-report`, a single manifest/report over the
  generated scenario summary, Bench2Drive route pack, overlay plan, sidecar
  plan/run evidence, RAG comparison, SimLingo result, and blocker ledger.
  Current evidence reports `2` generated recipes, `2` route-pack routes, `2`
  companion actors, sidecar runner success, mock RAG score delta `37.0`, and
  the prior RTX PRO 6000 SimLingo CUDA blocker while TASK-020 reruns on H100.
- Focused local tests during TASK-024:
  `PYTHONPATH=src python3 -m unittest tests.test_simlingo_sidecar_runner tests.test_cli_simlingo_sidecar_runner`
  passed with 4 tests.
- Full local gate during TASK-024: `bash scripts/pre_push_check.sh` passed with
  143 tests.
- Focused local tests during TASK-020 pullback helper:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_docker_scripts` passed
  with 13 tests, including a local execution fixture for the compact pullback
  allowlist, heavy-directory exclusions, and non-zero remote route wrapper
  pullback/exit-code behavior.
- Full local gate during TASK-020 pullback helper:
  `bash scripts/pre_push_check.sh` passed with 154 tests after the route
  wrapper was added.
- Focused local tests during TASK-023:
  `PYTHONPATH=src python3 -m unittest tests.test_simlingo_sidecar tests.test_cli_simlingo_sidecar`
  passed with 4 tests.
- Full local gate during TASK-023: `bash scripts/pre_push_check.sh` passed with
  139 tests.
- Focused local tests during TASK-022:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_injection tests.test_cli_carla_injection`
  passed with 5 tests.
- Full local gate during TASK-022: `bash scripts/pre_push_check.sh` passed with
  135 tests.
- Full local gate during TASK-021: `bash scripts/pre_push_check.sh` passed with
  130 tests.
- Full local gate during TASK-018: `bash scripts/pre_push_check.sh` passed with
  125 tests.
- Full local gate during TASK-019: `bash scripts/pre_push_check.sh` passed with
  118 tests.
- Full local gate during TASK-017: `bash scripts/pre_push_check.sh` passed with
  114 tests.

## Operator Inputs

Useful soon:

- Meshy or equivalent API key for real TASK-012 asset generation
- SimLingo checkpoint path or Hugging Face access
- graphics-capable CARLA host for live route video proof
- Keep the RunPod `/workspace` cache alive while TASK-039 runs live Alpamayo
  policy decisions from materialized CARLA captures

Missing inputs should be logged as blockers on the relevant ticket while local
mock/dry-run work continues.
