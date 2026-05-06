# TASK-089: Road-Aligned CARLA Scenario Frame And Placement Validator

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-078, TASK-083, TASK-085
- location: `src/driverx/simulators`, `src/driverx/behaviors`, `tests`, `configs`, docs, `tickets/TASK-089/artifacts`
- enter when: scripted CARLA OOD evidence exists but starts actors from absolute world coordinates that can place the ego vehicle or OOD actor off-road
- leave when: every scripted CARLA demo uses a route/lane local frame, records road-alignment evidence, and rejects or resamples scenarios that start off-road
- blockers: fake/unit validation is complete; live remote proof is blocked by the RunPod container NVIDIA Vulkan ICD
- spawned follow-ups: TASK-093 quality gates consume the road-alignment metrics
- complexity: M

### Summary

Fix the current credibility problem before scaling scenario generation. The
existing scripted CARLA runner treats behavior traces as raw CARLA world
coordinates, so a motorbike trace that means "2m to the right of ego lane" can
spawn at arbitrary world `(x, y)` and start on the shoulder or off the route.

### Scope

- In scope: road/lane frame construction, local-to-CARLA transform conversion,
  start-point validation, road-aligned ego/OOD actor placement, metrics, and
  live evidence refresh.
- Out of scope: new behaviors, new assets, model integration, or full
  Fail2Drive route scoring.

### Gap Analysis

- Current state: `carla_ood_demo.py` and `carla_script.py` use absolute XY
  transforms and `spawn_points[0]` without lane-relative semantics.
- Production expectation: generated OOD cases must be route-relative and
  auditable: "motorbike starts in adjacent lane", "debris blocks right lane",
  "ego follows the road centerline" should map to actual CARLA road geometry.
- Missing gaps: a road-frame type, transform helpers, fake-map tests, live
  alignment metrics, and a hard gate that prevents off-road artifacts from
  entering the submission pack.
- Recommendation: implement road-frame correctness first; otherwise the next
  simulator contributions multiply bad evidence.

### Plan

#### Change

Add a road-frame module and route anchor selector, then consume it from both
script compilation and live scripted CARLA execution.

#### Why

The next milestone is not "more random scenes"; it is "many generated scenes
that start from physically meaningful road coordinates."

#### Before -> After

- Before: behavior sample `(x_m=12, y_m=2)` means CARLA world coordinates
  `(12, 2)`.
- After: behavior sample `(x_m=12, y_m=2)` means 12m forward and 2m lateral
  from a selected lane-center anchor in the CARLA map.

#### Touch

- `src/driverx/simulators/carla_road_frame.py`: new road-frame contract.
- `src/driverx/simulators/carla_ood_demo.py`: use road-frame transforms for
  ego, OOD actors, props, and metrics.
- `src/driverx/simulators/carla_script.py`: emit route-relative plans and
  road-frame metadata.
- `src/driverx/assets/carla_mapping.py`: support lane-relative placements.
- `tests/test_carla_road_frame.py`: fake-map transform and validation tests.
- `tests/test_carla_ood_demo.py`: prove fake live runner does not use absolute
  world XY for behavior traces.
- `tests/test_carla_script.py`: update plan assertions.
- `configs/carla_ood_demo.local.sample.yaml`: add anchor selector defaults.
- `README.md`, `ARCHITECTURE.md`, `docs/progress.md`, `docs/HISTORY.md`.

#### Inspect

- `src/driverx/simulators/carla_ood_demo.py`
- `src/driverx/simulators/carla_script.py`
- `src/driverx/behaviors/library.py`
- `src/driverx/assets/carla_mapping.py`
- `tickets/TASK-085/artifacts/task85-live-campaign-2b/scripted_ood_campaign_summary.md`

#### Signature Delta

```python
RoadFrame = dataclass(
    anchor_transform: CarlaLikeTransform,
    lane_width_m: float,
    road_id: int | None,
    lane_id: int | None,
    yaw_deg: float,
)

resolve_road_frame(world_map: Any, selector: RoadFrameSelector) -> RoadFrame
local_pose_to_carla(frame: RoadFrame, x_m: float, y_m: float, z_m: float = 0.2, yaw_delta_deg: float = 0.0) -> CarlaPose
validate_road_aligned_track(world_map: Any, poses: list[CarlaPose], max_lateral_error_m: float) -> RoadAlignmentReport
```

#### Type Sketch

```python
RoadAlignmentReport = {
  "anchor": {"road_id": int | None, "lane_id": int | None, "lane_width_m": float},
  "num_samples": int,
  "offroad_samples": int,
  "max_lateral_error_m": float | None,
  "starts_on_road": bool,
  "passes": bool,
}
```

#### Typed Flow Example

`behavior trace local XY`
-> `resolve_road_frame(world_map, selector)`
-> `local_pose_to_carla(...)`
-> CARLA actor transforms
-> `road_alignment_report.json`
-> campaign quality gate in TASK-093.

#### Execution Steps

1. Add pure Python road-frame math and fake CARLA shape adapters.
2. Update script compilation to preserve route-relative semantics.
3. Update live CARLA scripted runner so ego and OOD actor are transformed from
   road-local coordinates.
4. Add alignment reports to per-run artifacts.
5. Run fake tests first, then one live CARLA proof when the simulator is open.

#### Recommendation

Build this ticket before all other simulator work. It directly addresses the
bad video and creates a reusable geometry seam for environments, behaviors,
objects, and quality gates.

#### Options Considered

- Keep current absolute XY and hand-pick coordinates: fastest but not scalable
  and not credible.
- Use full Fail2Drive route execution only: more benchmark-pure but still slow
  and does not solve DriverX-generated scenes.
- Add a road-frame layer: best current tradeoff; minimal code, big evidence
  quality improvement.

#### Blast Radius

- Moderate: updates the coordinate contract used by scripts, live demos, and
  asset placement.
- Keep backward compatibility by accepting old absolute fixtures behind an
  explicit `coordinate_mode=absolute_world` only for legacy tests if needed.

#### Risks

- CARLA map waypoint APIs differ slightly under fake/local wrappers; keep the
  road-frame core adapter-based and dependency-light.
- Lane validation can become too strict for shoulders/construction scenes;
  support scenario-declared allowed zones instead of one global rule.

### Acceptance Criteria

- [x] AC-1: Behavior traces are interpreted in a road-local frame by default.
- [x] AC-2: Fake-map tests prove ego, motorbike, and prop placements are
  translated from lane-relative coordinates, not raw world XY.
- [ ] AC-3: Live scripted CARLA run writes `road_alignment_report.json` and
  reports `starts_on_road=true` for ego and OOD actor.
- [x] AC-4: Current off-road/side-road video cannot be promoted unless it is
  explicitly marked as failed evidence.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_carla_road_frame tests.test_carla_ood_demo tests.test_carla_script`
- `PYTHONPATH=src python3 -m driverx run-carla-ood-demo --config configs/carla_ood_demo.local.sample.yaml --run-id task89-road-aligned-proof`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Fully implementable locally with fake CARLA tests.
- Live proof only needs the already-working local CARLA 0.9.16 app to remain
  open; if it is down, record the blocker and continue to TASK-090/TASK-092.

### Evidence

- Planned 2026-05-06 after user correction that current video starts off-road
  and is not yet meaningful submission evidence.
- Plan review: `docs/reviews/TASK-089-095-impl-plan-review.md`.
- Implemented road-local placement in `src/driverx/simulators/carla_road_frame.py`,
  `carla_ood_demo.py`, and `carla_script.py`.
- Focused local tests passed:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_road_frame tests.test_carla_ood_demo tests.test_carla_script`.
- Remote RTX 6000 Ada focused tests passed after syncing to `/workspace/0xDriver`.
- Remote CARLA 0.9.16 installed at `/workspace/carla/CARLA_0.9.16`; setup
  evidence: `tickets/TASK-089/artifacts/remote-carla-setup/remote_carla_setup.md`.

### Blockers

- Remote CARLA server launch is blocked by the RunPod container NVIDIA Vulkan
  ICD failure (`ERROR_INCOMPATIBLE_DRIVER`). Local rendering path remains the
  fallback until a graphics-capable host is available.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
