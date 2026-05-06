# TASK-097: RunPod Quality-Gated CARLA OOD Campaign

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-093, TASK-096
- location: `configs`, `scripts`, `tickets/TASK-097/artifacts`, remote `/workspace/0xDriver`
- enter when: RunPod Kasm CARLA 0.9.16 graphics runtime is reachable and DriverX has quality-gated scripted OOD campaign support
- leave when: at least one RunPod-hosted live CARLA OOD scenario produces duration/video/tracks/quality artifacts, or a precise blocker is logged and the next ticket can proceed from recorded evidence
- blockers: none at start
- spawned follow-ups: TASK-098 submission browser refresh from RunPod evidence
- complexity: M

### Summary

Run the DriverX scenario forge against the GPU-hosted CARLA server instead of
the local Mac/Wine path. This is the first pass that should turn the simulator
contribution into judge-visible evidence: a longer road-aligned OOD scenario
video with entity tracks, quality gates, and a report that can feed the scenario
catalog and policy evaluation harness.

### Scope

- In scope: sync repo to RunPod, install a minimal Python 3.12 DriverX runtime,
  run focused tests remotely, execute `run-scripted-ood-campaign` with the
  RunPod CARLA config, pull back compact JSON/Markdown evidence and selected
  MP4 if produced, and update blockers.
- Out of scope: Alpamayo inference, SimLingo, Meshy/custom GLB import, and
  stock Fail2Drive route scoring.

### Acceptance Criteria

- [x] AC-1: Latest repo syncs to `/workspace/0xDriver` on the Kasm RunPod pod.
- [x] AC-2: Remote Python 3.12 runtime can import DriverX and the CARLA client.
- [x] AC-3: Focused remote tests for CARLA OOD/campaign code pass.
- [x] AC-4: A live RunPod campaign is attempted with
  `configs/scripted_ood_campaign.runpod.sample.yaml`.
- [x] AC-5: The campaign writes summary, quality report, tracks, RGB or video
  artifacts, and labels any failed quality gate precisely.

### Build Notes

- CARLA server: `127.0.0.1:2000` on the RunPod Kasm desktop pod.
- Python runtime: `/workspace/driverx_py312`.
- Repo sync path: `scripts/sync_runpod_proxy_workspace.sh`.
- Run command target:
  `PYTHONPATH=src /workspace/driverx_py312/bin/python -m driverx run-scripted-ood-campaign --config configs/scripted_ood_campaign.runpod.sample.yaml --run-id task97-runpod-campaign`.

### Evidence

- Repo sync proof: `DRIVERX_REMOTE_TEST=1 scripts/sync_runpod_proxy_workspace.sh
  poz4gv6ryu2571-644111cc@ssh.runpod.io ~/.ssh/id_ed25519_runpod
  /workspace/0xDriver` unpacked the repo on the Kasm RunPod workspace and ran
  the focused remote tests.
- Remote focused tests: `tests.test_carla_road_frame`,
  `tests.test_carla_ood_demo`, `tests.test_scripted_ood_campaign`, and
  `tests.test_submission_scenario_browser` passed on `/workspace/driverx_py312`;
  latest sync rerun passed `17` tests.
- Direct live smoke: `run-carla-ood-demo` with
  `wrong_way_shoulder_creep`, `--tick-count 180`, and `--no-default-assets`
  passed against RunPod CARLA `Carla/Maps/Town10HD_Opt`, writing `180` frames
  over `36.0s`.
- Campaign proof: `run-scripted-ood-campaign` with run id
  `task97-runpod-campaign-v2` passed with `case_count=1`, `attempt_count=1`,
  `quality_selected_passed_count=1`, `live_case_count=1`, `frame_count=300`,
  and `duration_s=60.0`.
- Quality proof:
  `tickets/TASK-097/artifacts/pulled/artifacts/runs/task97-runpod-campaign-v2/quality/scenario_quality_summary.json`
  records the selected road-aligned case and its gates.
- Entity-track proof:
  `tickets/TASK-097/artifacts/pulled/artifacts/runs/task97-runpod-campaign-v2/cases/000-generated-base-animals-0076-visual-noise-000-wrong_way_shoulder_creep/carla/entity_tracks.json`.
- Overlay video proof:
  `tickets/TASK-097/artifacts/pulled/artifacts/runs/task97-runpod-overlay-v2/generated-base-animals-0076-visual-noise-000_ood.mp4`
  is `60.0s`, `640x360`, `5fps`, `300` frames, and includes visible DriverX
  OOD overlay text.
- Overlay preview:
  `tickets/TASK-097/artifacts/pulled/previews/task97_overlay_t05.png`.
- Follow-up browser/catalog proof is implemented under TASK-098.
- Full local gate after writeback: `bash scripts/pre_push_check.sh` passed with
  `357` tests, `2` skips, and compileall lint.

### Blockers

- None.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
