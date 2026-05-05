# TASK-020: H100 Stock SimLingo Rerun

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-017, TASK-019, H100 RunPod SSH access, Hugging Face model
  access
- location: `scripts`, `src/driverx/simulators`, `tickets/TASK-020/artifacts`,
  remote `/workspace`
- enter when: x86_64 H100/H200-class GPU host is reachable over SSH
- leave when: stock SimLingo produces one Bench2Drive route result on H100 or a
  precise H100-specific runtime blocker is captured with artifacts
- blockers: H100 CUDA is compatible, but CARLA 0.9.15 exits before opening
  port `20000` because the container lacks a working NVIDIA Vulkan/graphics
  runtime
- spawned follow-ups: TASK-024 live timed sidecar execution on H100/H200
- complexity: L

## Summary

Rerun the stock SimLingo one-route proof on an H100 host. TASK-017 proved the
pipeline reached route execution but failed at the first model tick on RTX PRO
6000 Blackwell because the upstream SimLingo torch stack lacked `sm_120`
kernels. This ticket uses an H100 `sm_90` runtime to validate the stock path
before adding DriverX sidecar overlays.

## Scope

- Sync the local repo to the RunPod H100 under `/workspace/0xDriver`.
- Keep all large installs, caches, model weights, CARLA files, and artifacts
  under `/workspace`.
- Install or reuse CARLA 0.9.15, AdditionalMaps, SimLingo, conda env, and the
  pinned checkpoint.
- Run one stock Bench2Drive route with SimLingo.
- Pull back and ingest only compact evidence artifacts.
- Record any exact blocker in `blockers.md` and this ticket before moving to
  the next unblocked ticket.

## Plan

### Change

Extend the remote execution scripts so RunPod SSH-over-TCP targets with custom
ports and identity keys work without editing commands by hand. Then execute the
existing SimLingo bootstrap/run flow on the H100 host.

### Why

The project needs a live policy baseline before generated OOD overlays can make
a meaningful claim. H100 matches the upstream torch CUDA architecture envelope,
so it is the fastest route from setup work to real closed-loop evidence.

### Before -> After

Before:
- Remote scripts defaulted to a plain `root@host` SSH target.
- TASK-020 existed in the roadmap but not as an executable ticket.
- No H100 stock SimLingo route result existed.

After:
- Remote scripts accept `GPU_SSH_OPTS` for RunPod ports and key paths.
- TASK-020 has a visible ticket and artifact surface.
- H100 evidence records success or a precise blocker.

### Touch

- `blockers.md`
- `tickets/TASK-020/ticket.md`
- `scripts/sync_remote_gpu.sh`
- `scripts/run_remote_simlingo_bootstrap.sh`
- `scripts/remote_gpu_snapshot.sh`
- `scripts/pull_remote_simlingo_artifacts.sh`
- `scripts/run_remote_simlingo_route.sh`
- `docs/progress.md`
- `docs/HISTORY.md`

### Inspect

- `docs/prd.md`
- `docs/specs/minimal-shot-vla-roadmap.md`
- `docs/MEMORY.md`
- `scripts/remote_simlingo_bootstrap.sh`
- `src/driverx/simulators/simlingo_results.py`

### Signature Delta

```bash
GPU_SSH_HOST="root@38.80.152.148" \
GPU_SSH_OPTS="-p 31257 -i ~/.ssh/id_ed25519_runpod" \
bash scripts/sync_remote_gpu.sh

GPU_SSH_HOST="root@38.80.152.148" \
GPU_SSH_OPTS="-p 31257 -i ~/.ssh/id_ed25519_runpod" \
SESSION_NAME="task20" \
bash scripts/run_remote_simlingo_bootstrap.sh
```

### Type Sketch

```python
RemoteSnapshot = {
  "host": str,
  "arch": "x86_64",
  "gpu": "NVIDIA H100 80GB HBM3",
  "workspace_mount": "/workspace",
  "root_disk_gb": 20,
}

Task20Evidence = {
  "torch_cuda_compatibility": "tickets/TASK-020/artifacts/.../torch_cuda_compatibility.json",
  "bootstrap_log": "tickets/TASK-020/artifacts/.../bootstrap.log",
  "route_result": "tickets/TASK-020/artifacts/.../res/seed_1_res.json",
  "report": "tickets/TASK-020/artifacts/.../simlingo_result_report.md",
}
```

### Typed Flow Example

`RunPod H100 SSH` -> remote snapshot says `x86_64` + `NVIDIA H100` ->
`sync_remote_gpu.sh` writes `/workspace/0xDriver` ->
`run_remote_simlingo_bootstrap.sh` creates tmux `task20` ->
`remote_simlingo_bootstrap.sh` writes `/workspace/artifacts/task20` ->
`run_one_route_as_user.sh` writes `res/seed_1_res.json` ->
`driverx ingest-simlingo-results` creates a compact report.

### Execution Steps

1. Patch SSH-port support into local remote scripts.
2. Run local syntax/tests for changed scripts and Python suite.
3. Sync repo to RunPod `/workspace/0xDriver`.
4. Capture remote snapshot into TASK-020 artifacts.
5. Start remote bootstrap in tmux session `task20`.
6. Poll bootstrap log and handle concrete install/runtime blockers.
7. Run one route after bootstrap completes.
8. Pull compact artifacts back with `rsync`.
9. Ingest results or blocker locally.
10. Update ticket, progress, history, and blocker ledger.
11. Run local gate and review before a completion claim.

### Recommendation

Keep TASK-020 focused on stock SimLingo. Do not add DriverX overlays until the
base policy proves it can run on the selected GPU.

### Options Considered

- **Stock SimLingo first:** best path because it validates the external policy
  before DriverX changes the scenario.
- **Overlay sidecar first:** tempting, but it can only prove actor injection,
  not policy behavior, until SimLingo runs.
- **Blackwell rebuild:** useful later, but too risky for the current deadline
  because it changes torch/CUDA/CARLA assumptions at once.

### Blast Radius

- Remote scripts become more flexible but must remain compatible with plain
  SSH hosts.
- Large remote installs can consume `/workspace`; root disk must stay clean.
- Hugging Face token must never be committed or printed into repo artifacts.

### Risks

- CARLA download or AdditionalMaps import may be slow or flaky.
- SimLingo dependency installation may pin old packages that need small fixes.
- Route execution may need EGL/display/runtime-user adjustments.
- H100 can still hit a non-architecture upstream runtime bug.

## Acceptance Criteria

- [x] AC-1: RunPod H100 snapshot is captured and linked.
- [x] AC-2: Remote scripts work with `GPU_SSH_OPTS` and still pass local checks.
- [x] AC-3: Stock SimLingo route run succeeds or fails with a precise
  artifact-backed blocker.
- [x] AC-4: Compact TASK-020 evidence is pulled back; large model/simulator
  assets are not committed.
- [x] AC-5: `blockers.md`, `docs/progress.md`, and `docs/HISTORY.md` reflect
  the final state.

## Verification

- `bash scripts/pre_push_check.sh`
- Remote `nvidia-smi` snapshot
- Remote `torch_cuda_compatibility.json`
- Remote `bootstrap.log`
- SimLingo result or blocker log
- Review artifact under `docs/reviews/` or `tickets/TASK-020/artifacts/review/`

## Autonomy Readiness

- Inputs available: H100 SSH, public key access, root privileges, `/workspace`
  persistent mount, local repo clean.
- Continue autonomously through install, bootstrap, route execution, artifact
  pullback, and ingestion.
- If blocked by external service/auth/runtime, log the blocker in
  `blockers.md`, preserve artifacts, and continue with TASK-024 dry/live
  scaffolding that does not require the missing dependency.

## Evidence

- `tickets/TASK-020/artifacts/2026-05-05T151900+0800/remote_gpu_snapshot.txt`
- Remote `/workspace/0xDriver` synced successfully after adding RunPod
  SSH-option support and disabling rsync owner/group preservation on the
  network volume.
- Remote 0xDriver test gate passed with 139 tests before SimLingo bootstrap.
- Remote tmux session `task20` is running
  `/workspace/0xDriver/scripts/remote_simlingo_bootstrap.sh`.
- Patched CARLA and AdditionalMaps extraction to use `tar --no-same-owner`
  after the RunPod `/workspace` network volume rejected upstream uid/gid
  restoration. The `task20` bootstrap was restarted without re-downloading the
  CARLA tarball; CARLA 0.9.15 base files extracted and AdditionalMaps download
  is in progress.
- Added repo-side bootstrap generation for `start_carla_server.sh`,
  `stop_carla_server.sh`, and `run_one_route_with_carla_as_user.sh` so future
  bootstraps can launch headless CARLA, wait for port `20000`, run the route,
  and stop the server from one artifact script.
- Added `scripts/pull_remote_simlingo_artifacts.sh`, a compact artifact
  pullback helper that preserves logs, JSON, Markdown, checksums, and generated
  run scripts while excluding model weights, simulator archives, media, caches,
  and CARLA files.
- Added `scripts/run_remote_simlingo_route.sh`, a post-bootstrap route wrapper
  that runs the generated remote `run_one_route_with_carla_as_user.sh`, writes
  `run_one_route_with_carla.log`, then pulls compact artifacts back even when
  the route exits non-zero with a runtime blocker.
- Focused script test:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_docker_scripts` passed
  with `13` tests, including a local execution fixture that proves `carla/`,
  `models/`, `software/`, `viz/`, `.cache/`, weights, and media are excluded
  even when compact-looking filenames appear inside those trees, plus a fake
  SSH route-wrapper test that proves non-zero route exits still trigger
  artifact pullback and remain the primary exit code even if pullback also
  fails.
- Local gate after pullback helper:
  `bash scripts/pre_push_check.sh` passed with `154` tests after the route
  wrapper was added.
- H100 bootstrap completed enough to produce SimLingo readiness, command-plan,
  checkpoint checksum, CUDA compatibility, and live route scripts under
  `/workspace/artifacts/task20`.
- H100 route wrapper executed
  `/workspace/artifacts/task20/run_one_route_with_carla_as_user.sh` and pulled
  compact evidence back to
  `tickets/TASK-020/artifacts/task20-remote`.
- H100 route result:
  `tickets/TASK-020/artifacts/task20-evidence-final/remote_simlingo_evidence.md`
  classifies the run as `route_infrastructure_blocked`: CARLA did not open
  port `20000` within `120s`, no SimLingo `*_res.json` exists, and policy
  inference did not begin.
- CARLA diagnostics:
  `tickets/TASK-020/artifacts/task20-remote/carla_runtime_diagnostics.md`
  shows CUDA compatibility on H100 but no working NVIDIA Vulkan device inside
  the container. Default `vulkaninfo` only exposes `llvmpipe`; forcing
  `/etc/vulkan/icd.d/nvidia_icd.json` fails with `ERROR_INCOMPATIBLE_DRIVER`.
- Review:
  `tickets/TASK-026/artifacts/review/2026-05-05_171339_review.md`
  covers the TASK-020 evidence classifier and H100 blocker handoff with overall
  score `4.0`.

## Blockers

- H100 is not sufficient for the current stock closed-loop CARLA proof because
  the RunPod container exposes CUDA but not a working NVIDIA graphics/Vulkan
  runtime for CARLA 0.9.15. Use a graphics-capable Ampere GPU host
  (`sm_86`, e.g. RTX 3090 / RTX A6000 / A40 / A10) or rebuild the SimLingo
  torch stack for the earlier RTX PRO 6000 Blackwell host where CARLA launched.
