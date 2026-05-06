# Memory

2026-05-02 05:23 +0800 | RESOURCE | MEM-0001 | challenge,sota | SoTA Commission I asks for a minimal-shot autonomy submission with repo, analysis notebook, 1-5 minute video or slide deck, motivation/write-up, and optional Waymo E2E driving deliverable; prompt-captured deadline is May 10, 2026.

2026-05-02 05:23 +0800 | RESOURCE | MEM-0002 | flashdrive,vla,latency | FlashDrive inspiration should be treated as algorithm-system design guidance, not copied wholesale: streaming cache reuse, compact reasoning, speculative decoding, adaptive action generation, quantization, CUDA graphs, and kernel fusion all target different VLA latency stages.

2026-05-02 05:23 +0800 | RESOURCE | MEM-0003 | realtime-vla-v2,robotics,deployment | Realtime-VLA V2 inspiration should guide deployment structure: server/client split, time-axis action planning, action chunking/prefill, local smoothing or MPC, aligned logs, async video/log recording, and mock runtime paths.

2026-05-02 05:23 +0800 | RESOURCE | MEM-0004 | waymo,e2e,dataset | Waymo E2E tutorial shows the practical target shape: load E2EDFrame TFRecords, inspect front cameras, use future ego states, predict a single 5-second trajectory at 4 Hz as 20 `(x, y)` points, package E2EDChallengeSubmission shards, and use ADE as a local proxy metric.

2026-05-02 05:23 +0800 | RULE | MEM-0005 | architecture,vla,planning | 0xDriver v1 must not depend on training a new VLA from scratch; it should use VLA/VLM reasoning as structured scene-intent input to deterministic trajectory generation, smoothing, safety checks, and ranking.

2026-05-02 05:23 +0800 | RULE | MEM-0006 | hardware,cloud,latency | Local Mac development is suitable for docs, dataset parsing, notebooks, mock runs, and light experiments; heavy CUDA/Triton VLA inference should remain optional cloud GPU work and must be timed separately from local offline evaluation.

2026-05-02 05:23 +0800 | RULE | MEM-0007 | artifacts,data | Do not commit Waymo dataset shards, generated videos, submission archives, model weights, or credentials unless a later ticket explicitly defines an artifact policy change.

2026-05-02 19:05 +0800 | RULE | MEM-0008 | waymo,runtime,docker | Official Waymo E2E dependencies must be treated as a Linux x86_64 runtime boundary; on Apple Silicon, use the Docker bridge for real TFRecord parsing and keep fixture/mock paths dependency-light.

2026-05-02 20:50 +0800 | RULE | MEM-0009 | waymo,baseline,evaluation | Before adding or comparing VLA/GPU backends, establish a small real Waymo batch baseline with `batch_summary.json`, `batch_report.md`, per-frame artifacts, mean ADE, mean timings, and best/worst ADE scenes.

2026-05-02 21:34 +0800 | RULE | MEM-0010 | waymo,baselines,vla | Future VLA/GPU comparisons must include deterministic rule baselines from TASK-005; on the first 10-frame validation slice, `constant_acceleration` mean ADE `3.73323` beat the mock `intent_planner` mean ADE `6.204769`.

2026-05-03 14:27 +0800 | RULE | MEM-0011 | planning,realtime-vla,hybrid | The default main planner must stay hybrid: structured VLA/VLM intent can steer semantic candidates, but the deployable local action layer must include motion-prior candidates, smoothing, and label-free ranking; future VLA/GPU backends should beat this hybrid baseline rather than bypass it.

2026-05-03 18:37 +0800 | RULE | MEM-0012 | carla,fail2drive,simulation | The main simulation path for the SoTA pivot is CARLA plus Fail2Drive scenario generation and OOD evaluation; the local Mac is the default authoring, fixture, report, and dry-run environment, with an optional community Wine/Kegworks Apple Silicon CARLA smoke-test path, while reproducible Fail2Drive runtime and heavy VLA inference should target Linux NVIDIA GPU infrastructure unless the Mac wrapper proves stable end to end.

2026-05-03 19:31 +0800 | RULE | MEM-0013 | external-repos,fail2drive | Fail2Drive must be treated as an external read-only checkout by default (`../external/fail2drive`), not vendored into 0xDriver; commit only tiny fixtures, parsers, adapters, and config paths needed for reproducible local tests.

2026-05-03 19:50 +0800 | RULE | MEM-0014 | carla,fail2drive,planning | Fail2Drive command plans must be route-faithful: generated recipes need an explicit `route_path`, multi-recipe files require `--recipe-id`, and planner validation must fail fast when the checkout, evaluator, agent, or selected route is missing.

2026-05-04 18:58 +0800 | RULE | MEM-0015 | roadmap,autonomy | After TASK-007, autonomous work should continue through dependency-light implementations of CARLA probing, entity tracks, behavior traces, asset manifests, policy adapters, and RAG comparison harnesses; missing Meshy keys, real VLA checkpoints, or cloud GPU access should be logged as ticket blockers rather than stopping unrelated local work.

2026-05-05 02:35 +0800 | RULE | MEM-0016 | carla,docker,apple-silicon | Local CARLA 0.9.16 development should use the dedicated Linux amd64 `driverx-carla-client:0.9.16` Docker image for Python API commands; keep this client bridge separate from later SimLingo/CUDA/GPU serving images and do not auto-inject repo `.env` into containers unless `DRIVERX_DOCKER_ENV_FILE` is explicitly set.

2026-05-05 03:47 +0800 | RULE | MEM-0017 | simlingo,gpu,cuda | Stock SimLingo on CARLA 0.9.15 uses a Python 3.8 environment with `torch==2.2.0+cu121`, whose wheel supports CUDA arches through `sm_90`; do not choose Blackwell `sm_120` GPUs for this stock path unless a separate PyTorch/CARLA rebuild ticket is opened. Prefer H100/H200-class `sm_90` hosts for the next live SimLingo proof.

2026-05-05 04:18 +0800 | RULE | MEM-0018 | bench2drive,simlingo,ood-scenarios | Generated Bench2Drive route packs must keep route XML stock-compatible for SimLingo/Bench2Drive and store DriverX-specific OOD actors, generated assets, regional behavior ids, memory queries, and expected failure intent in sidecar overlays until a companion CARLA actor injector or scenario-runner adapter is actually running.

2026-05-06 00:05 +0800 | RULE | MEM-0019 | alpamayo,runpod,attention | On the current RunPod RTX 6000 Ada Alpamayo lane, load probes must use `ALPAMAYO_ATTN_IMPLEMENTATION=eager`; SDPA mode is rejected by Alpamayo's custom architecture, while eager load has been proven at about 21.1GB peak VRAM. Flash-attn remains a separate optional bootstrap path for hosts with a working CUDA Toolkit and `nvcc`.

2026-05-06 11:48 +0800 | RULE | MEM-0020 | carla,docker,paths | The two local Docker wrappers use different in-container repo roots: `scripts/run_carla_client_docker.sh` mounts the repo at `/workspace`, while `scripts/run_fail2drive_client_docker.sh` mounts it at `/workspace/0xDriver`; use the matching output-root path or artifacts may be written only inside the ephemeral container.

2026-05-06 19:49 +0800 | RULE | MEM-0021 | carla,assets,blueprints | Local CARLA 0.9.16 scripted OOD asset proxies must prefer installed blueprint ids validated by TASK-078: `static.prop.dirtdebris01`, `static.prop.foodcart`, and `static.prop.constructioncone`; do not reintroduce absent `static.prop.trafficcone` placeholders without a target-install blueprint probe.

2026-05-06 20:41 +0800 | RULE | MEM-0022 | carla,docker,video | The minimal CARLA Docker client may not include Pillow or ffmpeg; live CARLA capture should still proceed, overlay rendering must fall back to raw-frame copying when Pillow is absent, and final MP4 assembly may be run on the host from captured RGB folders.

2026-05-06 21:34 +0800 | RULE | MEM-0023 | carla,scenario-quality,submission | Future CARLA OOD evidence must pass road-alignment, visibility, conflict, duration, and artifact-completeness quality gates before being promoted as submission-grade; setup-only proof and off-road scripted videos should be labeled as partial, failed, or legacy evidence rather than hero artifacts.
2026-05-06 22:35 +0800 | RULE | MEM-0024 | catalog,submission,evidence | Scenario catalog promotion, policy evaluation, and submission browser hero selection must use propagated `quality_status` as the authoritative gate; legacy/open-loop artifacts without road-aligned video proof can be indexed for context but must not be promoted as hero or counted as closed-loop policy evidence.
2026-05-07 00:52 +0800 | RULE | MEM-0025 | runpod,carla,vulkan | The working RunPod CARLA graphics path is the Kasm desktop pod with CARLA 0.9.16 installed under `/workspace/carla`, `DISPLAY=` plus `VK_ICD_FILENAMES=/workspace/carla/nvidia_icd.json`, and a Python 3.12 uv venv at `/workspace/driverx_py312` using the official CARLA cp312 wheel; do not reuse the old non-desktop RTX 6000 Ada container path for CARLA rendering.
2026-05-07 01:22 +0800 | RULE | MEM-0026 | runpod,carla,video,evidence | Fresh RunPod CARLA evidence pods must install `ffmpeg` and Pillow into `/workspace/driverx_py312`; without Pillow, `assemble-ood-video` can still copy raw frames but cannot render the judge-facing DriverX OOD overlay.
2026-05-07 01:40 +0800 | RULE | MEM-0027 | runpod,kasm,secrets,alpamayo | The Kasm RunPod proxy SSH path requires a PTY and echoes submitted command input, so do not transmit HF tokens or other secrets through heredocs/base64 command streams; live Alpamayo on that pod requires token installation through the Kasm web terminal or a direct TCP SSH/SFTP endpoint.
2026-05-07 02:04 +0800 | RULE | MEM-0028 | alpamayo,claims,submission | Alpamayo 1.5 is live on the Kasm RunPod lane for open-loop DriverX CARLA OOD evidence, but current output must be described as captured-frame reasoning plus trajectory intent, not real-time closed-loop CARLA driving; the first hero proof measured 111765.05ms latency and 23559.71MB peak VRAM.
2026-05-07 02:31 +0800 | RULE | MEM-0029 | submission,prioritization,deadline | With the SoTA deadline near, prioritize the final evidence loop over new setup: scenario selection, high-fidelity generated CARLA evidence, prompt-to-scenario generation, Alpamayo+RAG comparison, Fail2Drive extension framing, and final packaging. Stock Fail2Drive scoring, Meshy/custom GLB import, SimLingo, and runtime acceleration are optional only after those artifacts exist.
2026-05-07 02:55 +0800 | RULE | MEM-0030 | tickets,submission,board | For the final SoTA sprint, treat TASK-101 through TASK-106 as the only active board. TASK-058 through TASK-100 are archived historical evidence and should not be reopened unless the direction owner explicitly pulls one back into the sprint.
