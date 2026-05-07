# TASK-112: Longer Smooth Time-Warped CARLA Scenario Render

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-102, TASK-109, TASK-110
- location: `src/driverx/simulators/carla_ood_demo.py`, `src/driverx/pipeline/scripted_ood_campaign.py`, `configs`, `tickets/TASK-112/artifacts`
- enter when: the demo needs clearer source footage with longer trajectory, denser context, and less "what am I seeing?" confusion
- leave when: one longer CARLA source run and one sped-up export pass quality gates and feed TASK-111/TASK-113
- blockers: requires working CARLA runtime; can use current RunPod Kasm or local CARLA if available
- spawned follow-ups: TASK-113
- complexity: M

### Summary

Improve the source simulation footage, not by forcing real-time VLA, but by
recording a longer smoother CARLA scenario and exporting it at 2x-4x. This
matches the actual near-term claim: time-warped simulator evaluation today,
real-time VLA control later.

### Scope

- In scope: campaign config for longer trajectory, better camera preset,
  optional speed-up exporter, denser but quality-gated actors, smoother OOD
  motion, quality report, and local/RunPod command plan.
- Out of scope: SimLingo setup, official Fail2Drive score, live Alpamayo steering.

### Plan

#### Change

Add a "paper demo" CARLA campaign profile and a speed-up export utility.

#### Why

The existing 84s clip is technically valid but visually weak. A longer source
trajectory with speed-up gives reviewers more context and watchability.

#### Before -> After

- Before: 84s source clip embedded almost raw.
- After: 2-3 minute source capture can be exported to a 45-90s sped-up segment
  with quality gates and overlay compatibility.

#### Touch

- Add `configs/carla_ood_paper_demo.sample.yaml`
- Extend `src/driverx/pipeline/ood_video_evidence.py` or add
  `src/driverx/simulators/video_timewarp.py`
- Possibly add camera preset in `src/driverx/simulators/carla_ood_fidelity.py`
- Add tests in `tests/test_video_timewarp.py`
- Add scripts/notes for RunPod execution in `scripts/`

#### Inspect

- `src/driverx/simulators/carla_ood_demo.py`
- `src/driverx/simulators/carla_ood_fidelity.py`
- `src/driverx/pipeline/scripted_ood_campaign.py`
- `scripts/build_final_demo_video.sh`

#### Signature Delta

```python
timewarp_video(input_path: Path, output_path: Path, speed_factor: float, fps: int) -> VideoTimewarpResult
paper_demo_carla_config(...) -> CarlaOodDemoConfig
```

#### Type Sketch

```python
VideoTimewarpResult = {
  "status": "passed" | "blocked",
  "input_path": str,
  "output_path": str,
  "speed_factor": float,
  "input_duration_s": float,
  "output_duration_s": float,
  "claim_boundary": "time_warped_offline_demo=true",
}
```

#### Typed Flow Example

`240s CARLA source @ 5fps`
-> `timewarp_video(speed_factor=3.0)`
-> `80s sped-up MP4`
-> TASK-111 reasoning overlay.

#### Execution Steps

1. Define paper-demo config with longer tick count, wide camera, background
   vehicles/pedestrians, and strict smoothing.
2. Add reusable timewarp utility that shells to ffmpeg safely.
3. Add quality gates for input/output duration, road alignment, and visible actor density.
4. Run locally against existing MP4 first to prove speed-up.
5. If CARLA is up, run one fresh longer live campaign.
6. Pull/export MP4 locally and write evidence.

#### Recommendation

Use time-warped CARLA as the explicit demo format. Future work can be real-time
VLA serving; the current contribution is generation/evaluation.

#### Options Considered

- Keep current video: safe but not persuasive.
- Chase SimLingo comparison: interesting but high setup risk.
- Recommended: improve DriverX CARLA source footage and time-warp it.

#### Blast Radius

Medium. New config and video utility are additive; live run risk is external.

#### Risks

- CARLA runtime may be unavailable or slow. Mitigation: speed up existing
  exported clip first; fresh render is best-effort.

### Gap Analysis

The current clip passes quality gates but lacks cinematic clarity. Production
simulation demos often render offline, then time-compress for presentation. This
ticket adopts that pattern honestly.

### Acceptance Criteria

- [ ] AC-1: Existing hero MP4 can be sped up reproducibly with an evidence JSON.
- [ ] AC-2: Fresh paper-demo config exists for longer smoother CARLA capture.
- [ ] AC-3: If CARLA is reachable, one fresh longer source run is attempted and logged.
- [ ] AC-4: Final evidence labels the video as time-warped offline demo.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_video_timewarp`
- `PYTHONPATH=src python3 -m driverx timewarp-video ...`
- `ffprobe` duration checks before/after.
- Optional live CARLA run through RunPod/local Docker.
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Inputs: existing local MP4 is available.
- Compute: local ffmpeg; optional CARLA host for fresh source.
- Human gates: none unless CARLA host is down.

### Evidence

- Pending: `tickets/TASK-112/artifacts/<run-id>/video_timewarp.json`
- Pending: ignored sped-up MP4 under `artifacts/exported/`
- Pending optional fresh CARLA run evidence.

### Blockers

- Fresh CARLA render depends on CARLA runtime availability. Existing-video
  timewarp has no blocker.
