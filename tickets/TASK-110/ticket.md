# TASK-110: CARLA Risk And Perception Timeline

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-102, TASK-108
- location: `src/driverx/simulators`, `src/driverx/perception`, `tickets/TASK-110/artifacts`
- enter when: CARLA tracks exist but the demo does not explain what objects/risks the system detects
- leave when: a `risk_timeline.json` names front-of-ego hazards, nearest actor, conflict events, OOD actor behavior, and memory query triggers over time
- blockers: none; use CARLA simulator ground truth tracks instead of computer vision
- spawned follow-ups: TASK-111, TASK-112
- complexity: M

### Summary

Add simulator-grounded perception for the demo. We do not need to build a CV
detector before the deadline; CARLA already gives actor tracks. TASK-110
converts those tracks into a readable risk timeline: who is in front, how close,
what behavior is happening, when memory should be retrieved, and what the
policy should attend to.

### Scope

- In scope: track parser, ego-frame projection, front/side/behind
  classification, risk events, memory-query triggers, Markdown/JSON reports,
  fixture tests.
- Out of scope: image-based object detection, closed-loop policy control.

### Plan

#### Change

Add `driverx.perception` or `driverx.simulators.risk_timeline` module that
turns `entity_tracks.json` into time-indexed risk events.

#### Why

The video currently looks like a car driving around because no one can see the
system's perception. A risk timeline creates the missing explanatory layer.

#### Before -> After

- Before: overlay shows scenario id, behavior id, and nearest actor distance.
- After: overlay can show "motorcycle filtering front-left at 2.4m", "memory
  trigger: lateral clearance", and "recommended behavior: slow / yield".

#### Touch

- Add `src/driverx/perception/AGENTS.md`
- Add `src/driverx/perception/README.md`
- Add `src/driverx/perception/risk_timeline.py`
- Add CLI in `src/driverx/perception/risk_timeline_cli.py`
- Register in `src/driverx/cli_extensions.py`
- Add tests in `tests/test_risk_timeline.py`

#### Inspect

- `src/driverx/simulators/ood_video_overlay.py`
- `src/driverx/simulators/carla_ood_demo.py`
- `src/driverx/scenarios/quality.py`
- Existing `entity_tracks.json` shape under TASK-102 artifacts.

#### Signature Delta

```python
load_entity_tracks(path: Path) -> list[EntityTrackPoint]
build_risk_timeline(tracks: list[EntityTrackPoint], config: RiskTimelineConfig) -> RiskTimeline
write_risk_timeline(run_dir: Path, timeline: RiskTimeline) -> dict[str, Any]
```

#### Type Sketch

```python
RiskEvent = {
  "tick": int,
  "time_s": float,
  "actor_ref": str,
  "zone": "front" | "front_left" | "front_right" | "side" | "behind",
  "distance_m": float,
  "relative_speed_mps": float | None,
  "risk_label": str,
  "memory_query": list[str],
  "recommended_behavior": str,
}
```

#### Typed Flow Example

`entity_tracks.json`
-> ego-relative projection
-> `RiskEvent(tick=91, zone="front_left", distance_m=2.4, risk_label="motorcycle_filtering")`
-> `risk_timeline.json`
-> TASK-111 overlay.

#### Execution Steps

1. Parse tracks into typed points grouped by tick.
2. Locate ego pose per tick and transform other actors into ego-relative
   coordinates.
3. Classify actor zones and compute nearest/front hazards.
4. Infer event labels from `actor_ref`, behavior id, distance, and lateral
   crossing.
5. Attach memory query terms and recommended behavior.
6. Write JSON/Markdown reports and tests.

#### Recommendation

Use simulator ground truth and label it clearly. That is standard for a
simulation evaluation harness and avoids a fake CV detour.

#### Options Considered

- Real image detector: impressive but unnecessary and noisy.
- Manual overlay labels: quick but not a system.
- Recommended: CARLA track-derived perception timeline.

#### Blast Radius

Low. New module consumed by overlay/demo tickets.

#### Risks

- Ego-relative math can be wrong if rotation conventions differ. Mitigation:
  fixture tests with known positions and visual sanity report.

### Gap Analysis

The submission needs to show "the system detects the chaos." Current artifacts
only imply that through tracks. This ticket turns tracks into explicit
perception events.

### Acceptance Criteria

- [x] AC-1: Risk timeline identifies nearest and front-of-ego hazards per tick.
- [x] AC-2: Events include memory query triggers and recommended behavior.
- [x] AC-3: Fixture tests cover front, front-left, side, behind, and nearest.
- [x] AC-4: Existing local CARLA tracks can produce a timeline without live CARLA.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_risk_timeline`
- `PYTHONPATH=src python3 -m driverx build-risk-timeline --tracks ...`
- JSON validation over `risk_timeline.json`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Inputs: existing `entity_tracks.json`.
- Compute: local only.
- Human gates: none.

### Evidence

- Built: `tickets/TASK-110/artifacts/risk-timeline-v1/risk_timeline.json`
- Built: `tickets/TASK-110/artifacts/risk-timeline-v1/risk_timeline.md`

### Blockers

- TASK-102 video evidence references a track path that is not present locally;
  TASK-110 used the best available local live CARLA motorcycle-filtering track
  artifact from TASK-085 to prove the timeline path.
