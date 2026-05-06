# TASK-060: Stock Fail2Drive Town13 Route Score And Video

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-058
- location: `src/driverx/simulators`, `src/driverx/pipeline`, tests,
  `tickets/TASK-060/artifacts`
- enter when: TASK-058 proves `Town13` is loadable in local CARLA
- leave when: a stock Fail2Drive Town13 OOD route writes route result, logs,
  RGB/video evidence, and a route evidence bundle
- blockers: local Mac/Kegworks/Wine route runtime is too slow to finish route
  scoring inside 300s; route starts and partial RGB/video evidence exists
- spawned follow-ups: TASK-061 route-aligned Alpamayo capture and comparison
- complexity: M

### Description
TASK-054B proved the Docker Fail2Drive client and Town10 fallback video, but not
the actual Fail2Drive OOD split route. Once Town13 is installed, this ticket runs
the stock route long enough to collect score/completion/video evidence.

### Goal
Replace the current partial Town10 smoke proof with one stock Town13 Fail2Drive
route run that is judge-visible and mechanically auditable.

## Plan

### Change
Run `plan-fail2drive-video-smoke` and `run-fail2drive-route` against
`fail2drive_split/Generalization_PedestriansOnRoad_1088.xml` with a longer
timeout, then assemble/bundle route evidence.

### Why
The SoTA story needs randomized/OOD simulation evidence. Town13 stock Fail2Drive
is a stronger proof than the fallback Town10 video.

### Before -> After
- Before: video exists, but route score/completion are missing and the OOD split
  map is blocked.
- After: route evidence reports stock route result, route completion/driving
  score if produced, logs, video, and any residual route timeout/infraction.

### Touch
- `configs/fail2drive_town13.local.yaml`: stock Town13 route config.
- `src/driverx/simulators/fail2drive_route_runner.py`: improve timeout/result
  handling if the route writes partial checkpoints.
- `src/driverx/pipeline/route_evidence.py`: parse and present stock result
  fields if Fail2Drive shape differs.
- `tests/test_fail2drive_route_runner.py`, `tests/test_route_evidence.py`.
- `README.md`, `blockers.md`, `docs/progress.md`.

### Inspect
- `tickets/archive/TASK-054B/artifacts/docker-route-run-town13-map-blocker-classified/`
- `tickets/archive/TASK-054B/artifacts/docker-route-plan-town13-map-blocker/`
- `src/driverx/simulators/fail2drive_video.py`
- `src/driverx/pipeline/route_evidence.py`

### Signature Delta
No new public API is required unless result shape drift appears. Expected seam:

```python
src/driverx/simulators/fail2drive_route_runner.py / run_fail2drive_route(config: Fail2DriveRouteRunConfig) -> Fail2DriveRouteRunResult
src/driverx/pipeline/route_evidence.py / build_route_evidence(run_dir: Path, inputs: RouteEvidenceInputs) -> dict[str, Any]
```

### Type Sketch
```python
Town13RouteEvidence = {
  "route_name": "Generalization_PedestriansOnRoad_1088",
  "town": "Town13",
  "status": "passed" | "partial" | "blocked" | "failed",
  "driving_score": float | None,
  "route_completion": float | None,
  "infractions": dict[str, int],
  "video": {"exists": bool, "duration_s": float | None, "path": str},
  "logs": list[RouteLogAsset],
}
```

### Typed Flow Example
`configs/fail2drive_town13.local.yaml`
-> `plan-fail2drive-video-smoke`
-> Docker `run-fail2drive-route --timeout-s 900`
-> RGB frames/result JSON
-> `assemble-route-video`
-> `build-route-evidence`
-> `run_evidence.md` with score/video/logs.

### Execution Steps
1. Create Town13 config and regenerate a video-smoke plan.
2. Run the plan through `scripts/run_fail2drive_client_docker.sh` against local
   CARLA.
3. If route runs but times out, preserve partial RGB/result/logs and classify
   the stop reason.
4. Assemble MP4 from RGB frames if needed.
5. Build route evidence and update blockers/progress.

### Recommendation
Use a single known stock route first, not a generated suite. The goal is to
prove the exact blocked path is now unblocked before multiplying scenarios.

### Options Considered
- Full Fail2Drive split suite: too slow/risky before one route is stable.
- Town10-compatible generated route: useful fallback, but weaker than stock
  OOD evidence.
- Single Town13 stock route: best next proof boundary.

### Blast Radius
Runtime artifacts and route-evidence parsing only. Generated videos remain
ignored by `.gitignore`.

### Risks
- Route may exceed local Mac/Wine performance limits.
- Stock evaluator may require route-specific agents/configs not covered by the
  Town10 fallback.
- The route result JSON may differ from SimLingo result parser assumptions.

## Acceptance Criteria
- [x] AC-1: Route run reaches local CARLA Town13 through Docker.
- [x] AC-2: Route evidence links result JSON, stdout/stderr logs, RGB/video
  evidence, and score/completion if parseable.
- [x] AC-3: Any failure is classified as timeout, route infractions, agent
  setup, or simulator issue, not "unknown."
- [x] AC-4: Generated media stays ignored/uncommitted.
- [x] AC-5: `blockers.md` no longer lists Town13 as unresolved if the route
  starts successfully.

## Verification
- Unit: `PYTHONPATH=src python3 -m unittest tests.test_fail2drive_route_runner tests.test_route_evidence`
- Local live:
  `scripts/run_fail2drive_client_docker.sh python -m driverx run-fail2drive-route --plan ... --timeout-s 900`
- Gate: `bash scripts/pre_push_check.sh`
- Evidence:
  `tickets/TASK-060/artifacts/town13-route-evidence/run_evidence.md`

## Autonomy Readiness
- I can run the route while CARLA is up.
- Human gate only if local CARLA has to be manually restarted after TASK-058 map
  install or if the Mac cannot sustain the route runtime.

## Evidence
- 2026-05-06 03:24 +0800: Prepared
  `configs/fail2drive_town13.local.yaml` while the TASK-058 AdditionalMaps
  package download was in progress, so route execution can start immediately
  once `Town13` is loadable.
- 2026-05-06 03:25 +0800: Docker `plan-fail2drive-video-smoke` produced a
  stock Town13 route command with `--timeout 900`, `TOWN=Town13`, and expected
  result/debug/RGB/video paths under
  `tickets/TASK-060/artifacts/town13-video-plan/`. Remaining live blocker is
  still map availability plus missing upstream `tools/generate_video.py`, which
  the DriverX assembler already replaces after RGB frames exist.
- 2026-05-06 03:28 +0800: Build review attached:
  `docs/reviews/TASK-058-060-build-review.md`.

- 2026-05-06 04:33 +0800: TASK-068 proved Town13 is loadable and the stock
  Fail2Drive route starts. Current route result remains partial because local
  CARLA under Kegworks/Wine advances around `0.075x`; after 300s wall clock the
  route checkpoint still had `entry_status: Started` and no completed records.
  Partial evidence:
  `tickets/TASK-068/artifacts/town13-route-evidence-partial-001/run_evidence.md`.
- 2026-05-06 11:34 +0800: TASK-071 produced the first fresh Town13 MP4 from
  the stock `Generalization_PedestriansOnRoad_1088` route after the CARLA
  restart. The runner captured 5 RGB frames, assembled a 0.5s MP4, and wrote
  partial evidence at
  `tickets/TASK-071/artifacts/town13-early-route-evidence/run_evidence.md`.
  This resolves the video proof gap but intentionally leaves score/completion
  open because the route stopped after early video capture.

## Blockers
- Route completion/score now needs either a faster graphics-capable Linux
  NVIDIA CARLA host or a much longer local run without `--stop-after-video`.
  This is no longer a Town13 map install or video blocker.
