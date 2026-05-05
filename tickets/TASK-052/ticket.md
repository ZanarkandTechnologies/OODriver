# TASK-052: RunPod Alpamayo Bootstrap And Probe

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-044, TASK-048
- location: `scripts/`, `src/driverx/remote/`, `tickets/TASK-052/`
- enter when: user confirms RunPod is the active GPU lane and the RunPod SSH key should be used
- leave when: RunPod SSH is resolved from live pod metadata, Alpamayo remote setup/probe is attempted, and evidence or blockers are recorded
- blockers: gated Hugging Face access to `nvidia/Cosmos-Reason2-8B` blocks load-only inference after Alpamayo snapshot download
- spawned follow-ups:
- complexity: M

### Description
Resolve the current RunPod direct TCP SSH target without relying on stale
Connect-tab values, then use the existing Alpamayo remote bootstrap/probe
scripts against that host. Keep secrets out of artifacts and force heavyweight
caches into `/workspace` because this pod has a small container root disk.

### Goal
Turn the current RunPod instance into the live Alpamayo proof lane, or produce a
precise blocker that lets the next remote attempt resume without rediscovery.

### Acceptance Criteria
- [x] AC-1: Add a dependency-light RunPod SSH resolver that reads pod metadata and emits `GPU_SSH_HOST` / `GPU_SSH_OPTS` without printing API keys.
- [x] AC-2: Update remote Alpamayo scripts so model, Python, and package caches default to `/workspace`.
- [x] AC-3: Record a live RunPod SSH proof artifact with GPU, disk, and resolved TCP mapping.
- [x] AC-4: Run the Alpamayo remote bootstrap or probe as far as the pod permits, then record pass/fail evidence.
- [x] AC-5: Update `blockers.md`, `docs/HISTORY.md`, and user-facing docs with the current RunPod flow.

### Agent Contract
- Open: `blockers.md`, `scripts/bootstrap_remote_alpamayo_release.sh`, `scripts/run_remote_alpamayo_probe.sh`, `README.md`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_runpod_remote tests.test_alpamayo_remote_bootstrap_script`
- Stabilize: no secrets in stdout/artifacts; no model weights committed; no generated remote artifacts outside ignored `artifacts/`
- Inspect: live SSH `nvidia-smi` and `df -h /workspace /`
- Expected artifacts: `tickets/TASK-052/artifacts/runpod-ssh/runpod_ssh_resolution.{json,md}`, remote bootstrap/probe pulled artifacts if available
- Delegate with: no delegation needed unless remote bootstrap errors become ambiguous

### Evidence Checklist
- [x] Snapshot: RunPod SSH resolver artifact
- [x] Snapshot: live SSH GPU/disk probe
- [x] Snapshot: Alpamayo bootstrap/probe artifact or blocker
- [x] QA report linked:

### Build Notes
- Resolved current RunPod TCP SSH from REST metadata:
  `root@195.26.233.80 -p 55050 -i ~/.ssh/id_ed25519_runpod`.
- Live SSH proof recorded RTX 6000 Ada Generation, 48GB VRAM, compute
  capability 8.9, Python 3.11 base image, and `/workspace` persistent storage.
- `scripts/bootstrap_remote_alpamayo_release.sh` installed managed Python
  3.12.13 through `uv`, synced Alpamayo 1.5 in SDPA mode, and kept caches under
  `/workspace/.cache/driverx`.
- Lightweight model-info probe observed `nvidia/Alpamayo-1.5-10B` commit
  `f11cd25b758ab560114019b555dde2a8b92d88b4`.
- Download probe fetched the Alpamayo snapshot to
  `/workspace/.cache/driverx/huggingface/hub/models--nvidia--Alpamayo-1.5-10B`.
- Load-only probe failed on `403 Forbidden` for gated base model
  `nvidia/Cosmos-Reason2-8B`; this is now the live blocker.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS with external blocker
- AC-5: PASS

### Artifact Links
- RunPod SSH resolver:
  `tickets/TASK-052/artifacts/runpod-ssh/runpod_ssh_resolution.md`
- Live SSH proof:
  `tickets/TASK-052/artifacts/live-ssh/runpod_live_ssh_proof.md`
- Bootstrap log:
  `tickets/TASK-052/artifacts/bootstrap/bootstrap.log`
- Remote cache state:
  `tickets/TASK-052/artifacts/bootstrap/remote_cache_state.md`
- Model-info probe:
  `tickets/TASK-052/artifacts/probe-model-info-summary/alpamayo_probe_report.md`
- Snapshot download probe:
  `tickets/TASK-052/artifacts/probe-download-summary/alpamayo_probe_report.md`
- Load-only probe:
  `tickets/TASK-052/artifacts/probe-load-summary/alpamayo_probe_report.md`
- Review:
  `tickets/TASK-052/artifacts/review/20260505T235100-review.md`
- QA:
  `tickets/TASK-052/artifacts/qa/qa_report.md`

### User Evidence
- Supporting evidence: RunPod SSH, bootstrap, model-info, download, and load
  blocker reports listed above.
- QA report: `tickets/TASK-052/artifacts/qa/qa_report.md`
- Final verdict: RunPod setup and Alpamayo download path are working; live load
  is blocked only by nested Hugging Face access to `nvidia/Cosmos-Reason2-8B`.

### Required Evidence
- [x] Unit/integration/e2e tests pass (as applicable)
- [x] Lint passes
