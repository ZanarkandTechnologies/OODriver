# TASK-016: Local CARLA 0.9.16 Docker Proof

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: local Docker; optional host CARLA 0.9.16 server on port 2000
- location: docker/, scripts/, README.md
- enter when: RunPod/GPU provisioning is blocked but local CARLA 0.9.16 work can continue
- leave when: reusable Docker client image, proof script, docs, and tests exist
- blockers: live host CARLA smoke evidence currently times out from Docker on `host.docker.internal:2000`; rerun proof with CARLA.app open and fully loaded
- spawned follow-ups:
- complexity: S

### Description
The project needs a stable local runtime lane before cloud GPU work lands.
CARLA 0.9.16 already works through the Apple Silicon wrapper, so the Docker
Python client bridge should be reusable instead of reinstalling `carla==0.9.16`
on every invocation.

### Goal
Make local CARLA 0.9.16 Docker execution boring: build one reusable client
image, run DriverX CLI commands through it, and provide a proof script for API
probe plus ego-camera smoke artifacts.

### Acceptance Criteria
- [x] AC-1: A dedicated CARLA client Dockerfile builds `carla==0.9.16` by default.
- [x] AC-2: The run wrapper prefers the built image, supports explicit
  `DRIVERX_DOCKER_ENV_FILE`, and keeps the previous on-the-fly install fallback
  when the default image is missing.
- [x] AC-3: A single proof script builds the image, prints the CARLA Python API
  version, probes the host CARLA server, and attempts ego-camera smoke.
- [x] AC-4: README and Docker docs describe the local CARLA 0.9.16 path.
- [x] AC-5: Docker import proof runs locally; pre-push remains the final gate.

### Agent Contract
- Open: `docker/README.md`, `scripts/run_carla_client_docker.sh`
- Test hook: `bash scripts/pre_push_check.sh`
- Stabilize: keep GPU/SimLingo runtime separate from this CPU client image
- Inspect: `scripts/run_carla_client_docker.sh python -c 'import carla; from importlib.metadata import version; print(version("carla"))'`
- Key screens/states: not UI-bearing
- QA cookbook: build the image, run the import proof, run repo checks
- Taste refs: none
- Expected artifacts: Docker image, CLI JSON/Markdown under `artifacts/runs/` when CARLA is live
- Delegate with: reviewer/QA lanes can inspect shell behavior and proof output

### Evidence Checklist
- [x] Snapshot: Docker import proof output
- [x] Snapshot: `bash scripts/pre_push_check.sh`
- [x] QA report linked: `tickets/TASK-016/artifacts/qa/task16-qa.md`
- [x] Machine-readable QA summary linked: `tickets/TASK-016/artifacts/qa/result.json`

### Build Notes
- Added `docker/carla-client.Dockerfile`.
- Added `scripts/build_carla_client_docker.sh`.
- Updated `scripts/run_carla_client_docker.sh` to use the built image when
  present, support explicit env-file injection, and fall back to
  `python:3.10-bullseye` otherwise.
- Added `scripts/prove_carla_0916_docker.sh`.
- Built `driverx-carla-client:0.9.16`; `scripts/run_carla_client_docker.sh`
  successfully imported `carla` and printed package version `0.9.16`.
- `scripts/prove_carla_0916_docker.sh` captured timeout artifacts for both
  `probe-carla` and `spawn-ego-smoke` because no host CARLA server answered on
  `host.docker.internal:2000` during this pass.
- Added a fake-Docker subprocess test so proof-script run ids, timeout defaults,
  and Docker command shape are checked mechanically.

### QA Reconciliation
- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS
- AC-5: PASS for Docker image/import and pending only for live simulator reachability

### Artifact Links
- `tickets/TASK-016/artifacts/qa/result.json`
- `tickets/TASK-016/artifacts/qa/task16-qa.md`
- `artifacts/runs/task16-proof-probe/carla_probe.json`
- `artifacts/runs/task16-proof-probe/carla_probe.md`
- `artifacts/runs/task16-proof-ego/ego_smoke.json`
- `artifacts/runs/task16-proof-ego/ego_smoke.md`
- `artifacts/runs/task16-proof-probe-001/carla_probe.json`
- `artifacts/runs/task16-proof-probe-001/carla_probe.md`
- `artifacts/runs/task16-proof-ego-001/ego_smoke.json`
- `artifacts/runs/task16-proof-ego-001/ego_smoke.md`

### User Evidence
- Hero screenshot:
- Supporting evidence: Docker package import printed `CARLA Python API: 0.9.16`; live probe and ego smoke wrote timeout artifacts while the simulator was unreachable from Docker.
- QA report: `tickets/TASK-016/artifacts/qa/task16-qa.md`
- Final verdict: PASS for local Docker runtime setup; live simulator reachability is the only remaining external blocker.

### Required Evidence
- [x] Unit/integration/e2e tests pass
- [x] Typecheck passes or is not configured
- [x] Lint passes
