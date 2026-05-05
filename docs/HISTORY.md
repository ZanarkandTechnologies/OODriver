# History

2026-05-02 05:23 +0800 | BOOTSTRAP | Initialized docs-first project scaffold for 0xDriver minimal-shot VLA autonomy planning.
2026-05-02 09:37 +0800 | TASK | started TASK-002 optional real Waymo E2E integration after fixture-backed v1 passed QA
2026-05-02 09:45 +0800 | SHIP | added optional Waymo TFRecord loading seam and official submission packaging mode behind lazy dependencies
2026-05-02 10:02 +0800 | QA | TASK-002 passed review and final QA with optional Waymo dependency paths kept non-blocking
2026-05-02 16:23 +0800 | TASK | started TASK-003 Waymo Linux Docker runtime after native macOS ARM dependency install failed
2026-05-02 19:05 +0800 | SHIP | built Linux amd64 Waymo Docker runtime and ran downloaded validation shard through inspect and baseline planner paths
2026-05-02 19:32 +0800 | QA | TASK-003 passed final runtime review with Docker, real-shard, and Linux requirements evidence
2026-05-02 20:42 +0800 | TASK | started TASK-004 real Waymo batch baseline after single-frame Docker proof passed
2026-05-02 20:50 +0800 | SHIP | added streaming Waymo batch execution with aggregate ADE and latency reporting
2026-05-02 21:02 +0800 | QA | TASK-004 passed final review and QA with real 10-frame Waymo batch baseline evidence
2026-05-02 21:34 +0800 | TASK | started TASK-005 batch experiment harness to compare current planner against deterministic baselines
2026-05-02 21:34 +0800 | SHIP | added rule trajectory baselines and cross-strategy experiment runner
2026-05-02 21:46 +0800 | QA | TASK-005 passed final review and QA with real Waymo experiment comparison evidence
2026-05-03 14:24 +0800 | TASK | started TASK-006 motion-prior hybrid planner after deterministic baselines beat mock intent planner
2026-05-03 14:27 +0800 | SHIP | routed main scene and batch pipeline through hybrid semantic-intent and motion-prior candidates
2026-05-03 14:34 +0800 | QA | TASK-006 passed review and QA with real hybrid Waymo batch and experiment evidence
2026-05-03 18:37 +0800 | PLAN | reframed project PRD around CARLA plus Fail2Drive scenario generation, retrieval memory, SimLingo-first policy proof, Alpamayo adapter extension, and later serving acceleration
2026-05-03 18:37 +0800 | PLAN | incorporated community Apple Silicon CARLA wrapper as optional local smoke-test path while preserving Linux NVIDIA as reproducible Fail2Drive/VLA runtime target
2026-05-03 19:31 +0800 | TASK | started TASK-007 local scenario forge and CARLA smoke adapter with Fail2Drive cloned externally
2026-05-03 19:50 +0800 | SHIP | added local scenario forge, failure memory bank, CARLA smoke check, and route-faithful Fail2Drive dry-run planning
2026-05-03 19:50 +0800 | QA | TASK-007 passed local review and QA with 57-test pre-push gate and explicit recipe-to-route evidence
2026-05-04 18:58 +0800 | PLAN | expanded roadmap through TASK-014 for live CARLA probing, entity tracking, regional behavior generation, asset generation, policy adapters, and retrieval-augmented VLA comparison
2026-05-04 18:58 +0800 | TASK | started TASK-008 live CARLA probe and Docker bridge after local CARLA app reached TCP smoke on port 2000
2026-05-04 18:58 +0800 | SHIP | TASK-008 live Docker probe reached CARLA 0.9.16 and recorded Town10HD_Opt with 23 actors
2026-05-04 19:00 +0800 | SHIP | TASK-009 live ego smoke spawned vehicle and RGB camera, captured a frame, logged entity tracks, and cleaned up actors
2026-05-04 19:02 +0800 | SHIP | TASK-010 added deterministic regional OOD behavior traces for no-signal cut-ins, sudden braking, motorcycle filtering, wrong-way creep, informal right-of-way pushes, and fast low-profile two-wheelers
2026-05-04 19:04 +0800 | SHIP | TASK-011 compiled scenario recipes and behavior traces into validated CARLA actor, sensor, tick, output, and cleanup script plans
2026-05-04 19:22 +0800 | SHIP | TASK-012 added generated OOD asset requests, dry-run manifests, Meshy setup blocking, manifest validation, and recipe asset references
2026-05-04 19:27 +0800 | SHIP | TASK-013 added policy adapter contracts, mock and memory-aware decisions, local hybrid fallback, and setup-checked VLM/SimLingo/Alpamayo stubs
2026-05-04 19:30 +0800 | SHIP | TASK-014 added retrieval-augmented policy comparison reports with matched no-memory and memory-guided runs plus live-model setup blocker logging
2026-05-04 23:05 +0800 | SHIP | TASK-015 added SimLingo checkout readiness and Bench2Drive dry-run command planning against external RenzKa/simlingo
2026-05-05 02:35 +0800 | TASK | started TASK-016 local CARLA 0.9.16 Docker proof while GPU provisioning was blocked
2026-05-05 02:42 +0800 | SHIP | TASK-016 added reusable CARLA 0.9.16 Docker client image, proof script, and timeout evidence path for local simulator reachability
2026-05-05 03:06 +0800 | TASK | started TASK-017 remote GPU SimLingo one-route proof on Prime Intellect RTX PRO 6000 host
2026-05-05 03:47 +0800 | BLOCKER | TASK-017 proved stock SimLingo reaches CARLA route execution on RTX PRO 6000 Blackwell but crashes at the first model tick because upstream torch 2.2.0 lacks sm_120 kernels
2026-05-05 04:00 +0800 | TASK | started TASK-019 SimLingo result ingestion to convert Bench2Drive route JSON and CUDA blocker logs into stable reports
2026-05-05 04:18 +0800 | TASK | started TASK-018 generated Bench2Drive route pack export with stock XML plus DriverX sidecar overlays
2026-05-05 04:36 +0800 | TASK | started TASK-021 overlay injection planning to compile DriverX sidecars into dry-run CARLA actor scripts
2026-05-05 04:48 +0800 | SHIP | TASK-021 compiled DriverX route-pack sidecar overlays into dry-run companion CARLA actor scripts with route-specific blueprints and runtime contracts
2026-05-05 04:48 +0800 | QA | TASK-021 passed focused overlay/CLI tests and the 130-test pre-push gate after splitting oversized CLI test coverage and adding contract-drift coverage
2026-05-05 05:15 +0800 | TASK | started TASK-022 live companion CARLA actor injector for TASK-021 overlay plans
2026-05-05 05:15 +0800 | SHIP | TASK-022 added a companion-only CARLA overlay runner with fake-CARLA spawn, tick, track, and cleanup coverage
2026-05-05 05:15 +0800 | QA | TASK-022 passed fake-CARLA focused tests and the 135-test pre-push gate; live CARLA proof remains optional Docker execution
2026-05-05 05:30 +0800 | TASK | started TASK-023 SimLingo sidecar orchestration planning for stock policy plus DriverX overlay injection
2026-05-05 05:30 +0800 | SHIP | TASK-023 added a dry-run two-process sidecar launch plan combining SimLingo and DriverX overlay injector commands
2026-05-05 05:30 +0800 | QA | TASK-023 passed sidecar planner focused tests and the 139-test pre-push gate
2026-05-05 15:19 +0800 | TASK | started TASK-020 H100 stock SimLingo rerun on RunPod after direct TCP SSH was fixed
2026-05-05 15:30 +0800 | SHIP | TASK-024 added a timed sidecar process runner that executes TASK-023 plans with per-process logs, timings, and exit-code reporting
2026-05-05 15:53 +0800 | SHIP | TASK-025 added an OOD suite evidence manifest that combines scenario, route, overlay, sidecar, RAG, SimLingo, and blocker artifacts
2026-05-05 16:33 +0800 | SHIP | TASK-020 added a compact remote SimLingo artifact pullback helper that excludes model weights, CARLA files, caches, archives, and media
2026-05-05 16:41 +0800 | SHIP | TASK-020 added a remote stock-route wrapper that logs the H100 SimLingo run and pulls compact artifacts back after success or failure
2026-05-05 16:54 +0800 | TASK | started TASK-026 remote SimLingo evidence classifier while H100 bootstrap continued installing dependencies
2026-05-05 17:07 +0800 | SHIP | TASK-026 added a remote SimLingo evidence classifier for pulled bootstrap, route, CUDA, and diagnostics artifacts
2026-05-05 17:07 +0800 | BLOCKER | TASK-020 H100 stock SimLingo route reached CARLA launch but CARLA exited before opening port 20000 because the container lacks a working NVIDIA graphics/Vulkan runtime
2026-05-05 17:17 +0800 | SHIP | TASK-027 taught the OOD suite report to ingest remote SimLingo evidence and surface the H100 CARLA/Vulkan blocker as top-level submission evidence
2026-05-05 17:31 +0800 | SHIP | TASK-028 added a GPU host suitability report that turns CUDA compatibility, CARLA graphics diagnostics, and remote SimLingo evidence into a next-host recommendation
2026-05-05 17:28 +0800 | SHIP | TASK-029 added a compact remote GPU probe script for collecting host snapshot, torch CUDA compatibility, and CARLA graphics diagnostics before route runs
2026-05-05 17:30 +0800 | QA | TASK-029 live H100 probe successfully pulled host snapshot, torch CUDA compatibility, and CARLA graphics diagnostics, then reproduced the CUDA-ready/CARLA-graphics-blocked suitability verdict
2026-05-05 17:39 +0800 | SHIP | TASK-030 extracted SimLingo and sidecar command registration into a simulator-owned CLI module, reducing the central CLI to 823 lines
2026-05-05 17:47 +0800 | SHIP | TASK-031 added a submission dossier builder that summarizes OOD readiness, GPU host status, blockers, and demo outline from current evidence
2026-05-05 21:10 +0800 | TASK | started route-video-first phase by archiving completed setup tickets and creating TASK-033 through TASK-040 for Fail2Drive video evidence, generated OOD suite execution, policy matrix, Alpamayo probe, and submission demo packaging
2026-05-05 18:58 +0800 | SHIP | TASK-033 added a Fail2Drive route-video smoke planner that writes evaluator/video commands, expected outputs, and live blockers without launching CARLA
2026-05-05 19:04 +0800 | SHIP | TASK-034 added a route evidence pipeline that bundles result JSON, entity tracks, video metadata, screenshots, logs, and missing-artifact blockers
2026-05-05 19:09 +0800 | SHIP | TASK-035 added overlay evidence that links route recipes, behavior assertions, actor tracks, cleanup state, and live-CARLA blockers
2026-05-05 19:13 +0800 | SHIP | TASK-036 added a generated OOD suite runner with per-recipe route/video plans, route evidence bundles, overlay evidence, aggregate blockers, and --limit ramping
2026-05-05 19:18 +0800 | SHIP | TASK-037 added a policy runtime matrix that marks local/mock/basic/expert rows ready and isolates SimLingo/Alpamayo blockers
2026-05-05 19:24 +0800 | SHIP | TASK-038 added an Alpamayo offline probe schema, artifact classifier, secret redaction, CLI report, and download-gated remote GPU probe script
2026-05-05 19:32 +0800 | SHIP | TASK-040 added a submission demo pack with storyboard, artifact map, model/data declarations, write-up draft, and understood failure case
2026-05-05 19:42 +0800 | SHIP | TASK-041 added a DriverX-owned ffmpeg route-video assembler so missing Fail2Drive video helper code no longer blocks future RGB-to-MP4 evidence
2026-05-05 22:10 +0800 | SHIP | TASK-042 added a structured Fail2Drive route runner and proved local native execution reaches the evaluator but blocks on missing numpy before CARLA connection
2026-05-05 22:33 +0800 | SHIP | TASK-043 added a Dockerized Fail2Drive client path with repo/external mounts and host-CARLA config; local build stalled in pip download and should be rerun on a faster network or remote host
2026-05-05 22:45 +0800 | SHIP | TASK-044 hardened the Alpamayo remote probe for custom SSH options, local env token loading, secret-safe remote handoff, and compact rsync pullback
2026-05-05 22:45 +0800 | BLOCKER | TASK-044 live A6000 probe could not start because the supplied endpoint refused SSH on port 36723
2026-05-05 22:51 +0800 | SHIP | TASK-045 added a GPU-free Alpamayo release contract extractor and CLI over the local upstream checkout
2026-05-05 22:55 +0800 | SHIP | TASK-046 added native Alpamayo pred_xyz selection and 10Hz-to-4Hz DriverX trajectory conversion
2026-05-05 23:00 +0800 | SHIP | TASK-047 added fixture-backed Alpamayo input package manifests with camera windows, ego history, nav text, and memory context
2026-05-05 23:03 +0800 | SHIP | TASK-048 added a remote Alpamayo release bootstrap script with SDPA/flash-attn sync modes and optional test-inference execution
2026-05-05 23:07 +0800 | SHIP | TASK-049 added an offline Alpamayo policy rehearsal that writes input, trajectory, and PolicyDecision artifacts from saved pred_xyz
2026-05-05 23:10 +0800 | QA | TASK-050 refreshed local CARLA 0.9.16 reachability through the Docker client and recorded Town10HD_Opt probe evidence
2026-05-05 23:14 +0800 | SHIP | TASK-051 added live CARLA RGB/ego capture for Alpamayo-shaped input packages and recorded a 12-image local proof
2026-05-05 23:35 +0800 | TASK | started TASK-052 RunPod Alpamayo bootstrap and probe after resolving the active direct TCP SSH mapping from RunPod REST metadata
2026-05-05 23:50 +0800 | BLOCKER | TASK-052 proved RunPod RTX 6000 Ada bootstrap, Alpamayo snapshot download, and CUDA availability, then blocked live model load on gated access to nvidia/Cosmos-Reason2-8B
2026-05-06 00:05 +0800 | SHIP | TASK-052 resolved the nested Cosmos access gate and loaded Alpamayo 1.5 on RunPod RTX 6000 Ada with eager attention, about 32.1s load latency and 21.1GB peak VRAM
2026-05-06 00:52 +0800 | SHIP | TASK-053 proved live Alpamayo inference shapes via synthetic fallback after the PhysicalAI sample dataset gate, observing pred_xyz 1x1x1x64x3 and 24.5GB peak VRAM
2026-05-06 01:03 +0800 | SHIP | TASK-054 added Alpamayo tensor materialization for DriverX/CARLA capture packages with real capture proof and lazy remote torch loading
2026-05-06 01:17 +0800 | SHIP | TASK-039 connected live Alpamayo inference to CARLA capture packages as an open-loop policy path with measured latency, VRAM, CoC, and converted DriverX trajectory intent
2026-05-06 01:50 +0800 | SHIP | TASK-054B resolved the Fail2Drive Docker/numpy path, mounted CARLA PythonAPI agents, classified route blockers, and produced Town10 RGB/video evidence while identifying Town13 as the remaining stock-split map blocker
2026-05-06 02:02 +0800 | SHIP | TASK-055 added live CARLA Town10 route video evidence from Docker Fail2Drive RGB frames while preserving Town13 as the stock Fail2Drive split map blocker
2026-05-06 02:17 +0800 | SHIP | TASK-056 added an Alpamayo OOD comparison harness and live memory-augmented RunPod proof, showing changed CoC and trajectory intent while preserving the open-loop/no-closed-control label
2026-05-06 02:31 +0800 | SHIP | TASK-057 refreshed the demo pack around route video evidence and live Alpamayo memory comparison, with the remaining failure framed as route-score/closed-loop proof rather than setup-only work
2026-05-06 02:38 +0800 | MAINT | archived completed Alpamayo/CARLA ticket batch TASK-039 and TASK-052 through TASK-057, normalized archived ticket states to done, regenerated archive-path evidence reports, and left the active ticket board empty
2026-05-06 03:02 +0800 | PLAN | created TASK-058 through TASK-063 to unblock Town13, rerun PhysicalAI-backed Alpamayo probes, collect stock Fail2Drive route evidence, align Alpamayo captures to that route, prepare cached trajectory replay, and refresh final submission evidence
2026-05-06 03:22 +0800 | QA | TASK-059 resolved the PhysicalAI dataset gate with a dataset-forced Alpamayo shape probe on real sample frames, observing pred_xyz 1x1x1x64x3, pred_rot 1x1x1x64x3x3, CoC output, 124987.44ms latency, and 24881.65MB peak VRAM
2026-05-06 03:34 +0800 | SHIP | TASK-062 added a cached Alpamayo policy-decision replay seam that converts trajectory intent into bounded CARLA-style control traces while preserving the no-real-time-closed-loop label
2026-05-06 03:34 +0800 | SHIP | TASK-061 added a fake-CARLA route-aligned capture attach seam so future Fail2Drive hero actors can be captured for Alpamayo without being spawned or destroyed by DriverX
2026-05-06 03:34 +0800 | SHIP | TASK-063 added cached replay inputs and claim-boundary fields to the demo-pack generator so final evidence can distinguish open-loop VLA evaluation from cached control replay
