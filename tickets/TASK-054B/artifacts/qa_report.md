# TASK-054B QA Report

## Verdict

PASS with residual live-simulation limits. The original native `numpy` blocker
is resolved through the Docker client path, and the route runner now records
precise blockers instead of silently passing failed CARLA runs.

## Acceptance Criteria

- AC-1: PASS. `docker_build.log` and `docker_build_torch.log` show the
  lightweight and Torch-enabled Docker images built successfully.
- AC-2: PASS. `docker_import_smoke.log` proves `carla` and `numpy`;
  `docker_import_smoke_torch_agents.log` additionally proves `torch` and CARLA
  PythonAPI `agents`.
- AC-3: PASS. `docker-route-run-town13-map-blocker-classified` and
  `docker-route-run-town10-speedlimit` both execute `run-fail2drive-route`
  inside Docker against `host.docker.internal:2000`.
- AC-4: PASS. Route artifacts include stdout/stderr logs, expected output
  status, route blockers, and classifier output. Town13 is correctly classified
  as a missing-map blocker. Town10 produced RGB frames but hit the smoke timeout.
- AC-5: PASS. `.gitignore` excludes ticket artifact JPG/JPEG/PNG/MP4 media.
  `git status --ignored` shows the generated MP4 and visualization folder are
  ignored, not tracked.

## Evidence

- Focused tests before review fixes: `focused_tests.log` (`15` tests passed).
- Focused tests after review fixes: `focused_tests_after_review.log` (`17`
  tests passed).
- Final focused tests after evidence wording/ignore regression:
  `focused_tests_final.log` (`18` tests passed).
- Full gate before review fixes: `pre_push_check.log` (`249` tests passed).
- Full gate after review fixes: `pre_push_check_after_review.log` (`251` tests
  passed).
- Final full gate: `pre_push_check_final.log` (`252` tests passed).
- Available CARLA maps: `carla_available_maps.log`.
- Town13 stock Fail2Drive split blocker:
  `docker-route-run-town13-map-blocker-classified/fail2drive_route_run.json`.
- Town10 fallback live route:
  `docker-route-run-town10-speedlimit/fail2drive_route_run.json`.
- Video assembly:
  `route-video-town10-speedlimit/route_video_assembly.json` (`41` frames,
  status `passed`).
- Review fixes: empty RGB folders now block, timeout logs preserve specific
  map/module/connectivity causes, failed checkpoint records retain route-level
  details, and `.png` media artifacts are ignored alongside JPG/MP4 outputs.

## Residual Risks

- Local CARLA 0.9.16 does not include `Town13`, while the checked-out
  Fail2Drive split routes are all `Town13`; true Fail2Drive OOD split video
  needs a CARLA build/package with Town13.
- The Town10 fallback video is useful for Docker/live-CARLA proof, but it is not
  the same as a Fail2Drive OOD split route.
- The Town10 route was cut off by a bounded smoke timeout after producing
  frames; a full route score requires a longer live run.
