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
2026-05-06 03:34 +0800 | QA | TASK-058 installed CARLA 0.9.16 AdditionalMaps locally, confirmed Town13 map markers and available_maps visibility, and narrowed the remaining Fail2Drive blocker to CARLA relaunch/readiness after a Town13 load timeout
2026-05-06 04:08 +0800 | SHIP | TASK-064 added a dependency-light end-to-end OOD demo runner with scenario generation, regional behavior simulation, memory retrieval, policy reaction comparison, cached controls, and local 2D simulator evidence
2026-05-06 04:08 +0800 | SHIP | TASK-066 expanded the deterministic regional OOD behavior suite to eight traces with double-parked door swerve and unsignaled U-turn cases
2026-05-06 04:33 +0800 | QA | TASK-068 proved Town13 load and stock Fail2Drive route startup through Docker, produced a partial RGB/video evidence bundle, and reclassified the remaining live blocker as local Mac/Kegworks/Wine runtime speed rather than setup
2026-05-06 04:33 +0800 | SHIP | TASK-070 refreshed the judge-facing demo pack so the submission now leads with the runnable local OOD simulator and treats CARLA/Town13 and Alpamayo as measured supporting evidence with explicit claim boundaries
2026-05-06 11:34 +0800 | SHIP | TASK-071 added early RGB-frame watching and host MP4 assembly for slow Town13 Fail2Drive runs, producing fresh partial video evidence for Generalization_PedestriansOnRoad_1088 while leaving full route score as TASK-060 follow-up
2026-05-06 11:48 +0800 | QA | TASK-060/TASK-069 long local route attempt started the Town13 stock route, reached game time 0.600s at about 0.142x, then exposed CARLA second-client/capture timeout under Mac/Kegworks/Wine synchronous Fail2Drive execution
2026-05-06 18:16 +0800 | PLAN | created TASK-072 through TASK-077 as the submission-first train: long DriverX CARLA OOD video, evidence overlays, Alpamayo scene reasoning, memory comparison, stock prop/object spawning, and demo pack V3
2026-05-06 18:47 +0800 | BUILD | implemented TASK-072 through TASK-077 first pass: scripted CARLA OOD runner, OOD overlay video evidence, scenario-linked Alpamayo reports, stock CARLA proxy asset mapping, and V3 demo pack with fixture/live claim boundaries
2026-05-06 19:49 +0800 | SHIP | TASK-078 through TASK-082 produced the first 24s live scripted CARLA OOD video, same-scene Alpamayo 1.5 open-loop reasoning, same-capture memory comparison, corrected stock proxy asset evidence, and V4 submission pack
2026-05-06 20:06 +0800 | PLAN | created TASK-083 through TASK-088 as the next submission train: cached Alpamayo CARLA replay, reasoning overlay pack, scripted OOD campaign, Alpamayo campaign batch comparison, V5 dossier, and stock Fail2Drive graphics-host handoff
2026-05-06 20:41 +0800 | BUILD | landed TASK-083 through TASK-088 submission train: live cached Alpamayo CARLA replay, reasoning HTML pack, two-case live scripted OOD campaign, cached Alpamayo batch comparison, V5 dossier/video script, and Fail2Drive graphics-host handoff
2026-05-06 21:35 +0800 | QA | resolved TASK-083 through TASK-088 implementation-review gaps by adding Alpamayo batch VRAM aggregation, source-reproducible campaign video evidence reuse, explicit V5 live-video/comparison checklist rows, and final QA/review artifacts
2026-05-06 21:34 +0800 | PLAN | created TASK-089 through TASK-095 to pivot the next milestone from setup proof to road-aligned scenario generation, catalog management, environment/behavior generation, quality-gated campaigns, policy evaluation, and V6 submission packaging
2026-05-06 22:22 +0800 | BUILD | implemented TASK-089 through TASK-095 simulator-contribution train: road-local CARLA placement, scenario catalog, environment packs, behavior DSL variants, quality gates, policy evaluation campaign, and V6 static scenario browser/dossier
2026-05-06 22:22 +0800 | BLOCKER | installed CARLA 0.9.16 on the RTX 6000 Ada RunPod host and synced DriverX there, but live CARLA launch remains blocked by the container NVIDIA Vulkan ICD failing with ERROR_INCOMPATIBLE_DRIVER
2026-05-06 22:35 +0800 | QA | tightened TASK-091/TASK-093 evidence by expanding environment generation to six families, adding school-zone pedestrian occlusion, and proving deterministic campaign retry/resampling with quality-retry artifacts
2026-05-06 22:35 +0800 | REVIEW | TASK-089 through TASK-095 review initially failed on inflated quality/policy/browser claims; follow-up build made strict video and road alignment gates authoritative, propagated quality status into catalog and policy evaluation, and regenerated honest no-hero submission packaging
2026-05-06 23:04 +0800 | REVIEW | TASK-089 through TASK-095 implementation review passed at 4.0/5 after fixing policy status-count reporting, browser quality/promotion labels, hero/failure separation, and regression tests for blocked policy evidence
2026-05-07 00:52 +0800 | QA | TASK-096 proved a RunPod Kasm RTX 6000 Ada graphics runtime for CARLA 0.9.16: NVIDIA Vulkan works through a per-process ICD, CARLA opens port 2000, and a Python 3.12 client connects to Town10HD_Opt with 23 actors
2026-05-07 01:22 +0800 | SHIP | TASK-097 produced a 60s RunPod-hosted, road-aligned CARLA OOD campaign video with entity tracks, quality gates, and visible DriverX overlay evidence
2026-05-07 01:22 +0800 | SHIP | TASK-098 promoted the pulled RunPod OOD video into the scenario catalog and regenerated the V6 submission browser/dossier with one hero scenario
2026-05-07 01:41 +0800 | REVIEW | TASK-098 fixed reviewer-found browser link resolution and nested overlay risk parsing, then regenerated the hero catalog/browser with locally resolvable artifact links
2026-05-07 01:40 +0800 | BUILD | TASK-099 converted the RunPod hero CARLA OOD MP4 into a torch-ready Alpamayo input package, planned a hero open-loop batch, and probed the Kasm Alpamayo env with CUDA visible on RTX 6000 Ada
2026-05-07 01:40 +0800 | BLOCKER | TASK-099 live Alpamayo inference on the Kasm pod is blocked only by secret-safe HF token installation because the proxy SSH path requires a PTY and echoes command input
2026-05-07 02:04 +0800 | SHIP | TASK-100 completed live Alpamayo 1.5 inference on the RunPod hero CARLA OOD package, recording CoC reasoning, pred_xyz/pred_rot shapes, 111765.05ms latency, 23559.71MB peak VRAM, and a DriverX open-loop policy decision
2026-05-07 02:31 +0800 | PLAN | created TASK-101 through TASK-106 as the final submission-focused train: evaluation matrix, high-fidelity CARLA evidence, prompt-to-scenario studio, Alpamayo+RAG batch, Fail2Drive extension report, and V7 submission pack
2026-05-07 02:55 +0800 | MAINT | archived TASK-058 through TASK-100 out of the active board, preserving them as historical evidence and leaving TASK-101 through TASK-106 as the final submission sprint
2026-05-07 03:05 +0800 | PLAN | expanded TASK-103 from prompt-to-OOD compilation into a Scenario Studio data-engine plan with parity research, curation gates, dataset records, and Alpamayo/RAG handoff
2026-05-07 04:16 +0800 | SHIP | TASK-103 added a deterministic Scenario Studio prompt compiler and curation batch that turns 10 natural-language OOD briefs into 20 scenario candidates with environment, behavior, assets, memory query, quality targets, and partial-evidence promotion gates
2026-05-07 04:23 +0800 | SHIP | TASK-105 added a Fail2Drive extension report layer that links generated DriverX OOD cases to fixture Fail2Drive seed/result families, failure-memory entries, and explicit no-official-score claim boundaries
2026-05-07 04:27 +0800 | SHIP | TASK-104 strengthened Alpamayo OOD batch summaries with reasoning-change, memory-case, safety-flag, latency, VRAM, and open-loop/closed-loop counts, then produced a three-case Alpamayo+memory comparison batch from existing live evidence
2026-05-07 04:33 +0800 | SHIP | TASK-106 added a final V7 submission pack builder and generated the judge-facing browser, dossier, video script, two-page write-up draft, artifact map, and proved/partial/blocked evidence rows around the final sprint artifacts
2026-05-07 05:42 +0800 | SHIP | TASK-102 added high-fidelity CARLA OOD mode with background actor spawning, wide/chase camera presets, OOD motion smoothing, density/smoothness quality gates, and an 84s RunPod hero video candidate that passes strict video/road/conflict/fidelity checks
2026-05-07 05:58 +0800 | SHIP | refreshed TASK-106 final V7 submission pack around the TASK-102 84s high-fidelity hero video and removed stale Alpamayo blocker leakage from the judge-facing write-up
2026-05-07 06:02 +0800 | REVIEW | hardened TASK-106 after review found the final pack overclaimed remote-only hero media; exported the 84s MP4 locally, added local/remote video status tests, regenerated the V7 pack as submission_ready, and opened TASK-107 for final demo assembly
2026-05-07 06:07 +0800 | SHIP | TASK-107 added a repeatable final demo video builder and rendered a 124s draft MP4 from evidence title cards plus the exported 84s CARLA hero clip, keeping generated videos under ignored artifacts/exported
2026-05-07 12:32 +0800 | PLAN | created TASK-108 through TASK-113 as Scenario Workbench V2: evidence bundle, agentic OOD generation loop, CARLA risk timeline, reasoning/RAG overlay video, longer time-warped CARLA render, and V8 paper-style submission pack
