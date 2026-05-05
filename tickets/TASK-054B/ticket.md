# TASK-054B: Self-Resolve Fail2Drive Docker And Numpy Blocker

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-041, TASK-042, TASK-043
- location: `docker/`, `scripts/`, `src/driverx/simulators`, tests
- enter when: local native Fail2Drive route execution blocks on missing numpy
- leave when: Fail2Drive route execution runs through the Docker client path or
  records a fresh precise Docker/runtime blocker
- blockers: stock Fail2Drive split routes require `Town13`, which is not in the
  local CARLA 0.9.16 install; Town10 fallback route produces RGB but route
  completion needs a longer runtime than the ticket smoke timeout
- spawned follow-ups: TASK-055 live OOD scenario video evidence
- complexity: M

### Description
TASK-042 reached Fail2Drive route execution but native macOS Python lacked
`numpy`. TASK-043 added a Dockerized Fail2Drive client but the build stalled in
pip. This ticket reruns and hardens that Docker path so video evidence can move.

### Goal
Resolve the numpy blocker without asking the user for more setup by running
Fail2Drive through a Linux amd64 Docker client, or produce a precise blocker
that TASK-055 can use.

### Acceptance Criteria
- [x] AC-1: Docker image build succeeds or records a precise build-layer
  blocker.
- [x] AC-2: Docker image smoke proves `import carla, numpy`.
- [x] AC-3: `run-fail2drive-route` runs inside Docker against a planned route
  path, targeting host CARLA at `host.docker.internal:2000`.
- [x] AC-4: Route run writes structured stdout/stderr, expected output status,
  and blockers if RGB frames are not produced.
- [x] AC-5: No generated media, route outputs, Docker caches, or credentials are
  committed.

### Agent Contract
- Open: `scripts/build_fail2drive_client_docker.sh`,
  `scripts/run_fail2drive_client_docker.sh`,
  `docker/fail2drive-client.Dockerfile`, TASK-042/TASK-043 artifacts
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_route_runner tests.test_fail2drive_docker_scripts`
- Stabilize: keep torch optional, prefer mounted external checkout, do not copy
  Fail2Drive into the repo
- Expected artifacts: `tickets/TASK-054B/artifacts/*`

### Evidence Checklist
- [x] Docker build log:
  `tickets/TASK-054B/artifacts/docker_build.log`
- [x] Docker build log with optional Torch:
  `tickets/TASK-054B/artifacts/docker_build_torch.log`
- [x] Docker import smoke:
  `tickets/TASK-054B/artifacts/docker_import_smoke.log`
- [x] Docker import smoke with Torch and CARLA agents:
  `tickets/TASK-054B/artifacts/docker_import_smoke_torch_agents.log`
- [x] Stock Fail2Drive split map blocker:
  `tickets/TASK-054B/artifacts/docker-route-run-town13-map-blocker-classified/fail2drive_route_run.md`
- [x] Town10 fallback route run report:
  `tickets/TASK-054B/artifacts/docker-route-run-town10-speedlimit/fail2drive_route_run.md`
- [x] Town10 route video assembly:
  `tickets/TASK-054B/artifacts/route-video-town10-speedlimit/route_video_assembly.md`
- [x] QA report:
  `tickets/TASK-054B/artifacts/qa_report.md`

### Build Notes
- Reran the lightweight `driverx-fail2drive-client:0.9.16` image and proved
  `import carla, numpy`.
- Built a separate `driverx-fail2drive-client:0.9.16-torch` image with
  `DRIVERX_FAIL2DRIVE_INSTALL_TORCH=1` because Fail2Drive's evaluator imports
  Torch before reaching CARLA.
- Added a CARLA PythonAPI sparse external checkout mount at
  `../external/carla/PythonAPI/carla` so Fail2Drive can import
  `agents.navigation.global_route_planner`.
- Added `VIZ_PATH`, `TOWN`, `REPETITION`, and `SCENARIO_RUNNER_ROOT` to the
  generated route plan environment. These are required by the upstream
  `viz_path_agent.py` / AutoPilot stack.
- Hardened `run-fail2drive-route` so exit-code-only success cannot mask failed
  route checkpoints, missing RGB frames, missing CARLA maps, or timeout output
  decoding quirks.
- Addressed review findings by requiring non-empty RGB image folders,
  preserving specific map/module/connectivity blockers on timeouts, keeping
  route-level failed checkpoint details alongside global failure, and ignoring
  ticket artifact `.png` files.
- Stock Fail2Drive split route
  `Generalization_PedestriansOnRoad_1088.xml` reaches CARLA but blocks because
  it requires `Town13`; local CARLA reports available maps:
  `Town01`, `Town02`, `Town03`, `Town04`, `Town05`, `Town10HD`, optimized
  variants, and `AnnotationColorLandscape`.
- A Town10-compatible route from
  `scenario_runner/srunner/data/routes_town10.xml` runs through Docker against
  host CARLA and produced `41` RGB frames plus an MP4 before the smoke timeout.
  The video and raw frames are intentionally ignored by git.

### QA Reconciliation
- AC-1: PASS; lightweight and Torch Docker images built locally.
- AC-2: PASS; Docker import smoke covers `carla`, `numpy`, `torch`, and CARLA
  PythonAPI `agents`.
- AC-3: PASS; route runner executed inside Docker against
  `host.docker.internal:2000`.
- AC-4: PASS; route reports include stdout/stderr, expected output status, map
  blockers, timeout blockers, checkpoint blockers, and RGB/video evidence.
- AC-5: PASS; `.gitignore` excludes ticket artifact `.jpg`, `.jpeg`, `.png`,
  and `.mp4` outputs.

### Artifact Links
- `tickets/TASK-054B/artifacts/docker-route-run-town13-map-blocker-classified/fail2drive_route_run.json`
- `tickets/TASK-054B/artifacts/docker-route-run-town10-speedlimit/fail2drive_route_run.json`
- `tickets/TASK-054B/artifacts/route-video-town10-speedlimit/route_video_assembly.json`

### User Evidence
- Supporting evidence: Docker route stack now reaches live local CARLA through
  Linux amd64 Docker. The original native `numpy` blocker is resolved.
- QA report: `tickets/TASK-054B/artifacts/qa_report.md`
- Final verdict: build complete; final review pending.

### Required Evidence
- [x] Unit/integration/e2e tests pass (as applicable)
- [x] Lint passes
- [x] Review fixes tested with `focused_tests_after_review.log` and
  `pre_push_check_after_review.log`
- [x] Final tests passed with `focused_tests_final.log` and
  `pre_push_check_final.log`
