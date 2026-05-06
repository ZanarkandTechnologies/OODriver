# TASK-061: Route-Aligned Alpamayo OOD Capture And Comparison

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-059, TASK-060
- location: `src/driverx/simulators`, `src/driverx/policies`,
  `src/driverx/pipeline`, tests, `tickets/TASK-061/artifacts`
- enter when: dataset-backed Alpamayo proof exists and a Town13 route run can
  produce live CARLA evidence
- leave when: a route-aligned CARLA capture is evaluated by Alpamayo with and
  without retrieved memory
- blockers: live route-aligned proof waits on TASK-060; fake-CARLA attach seam
  is implemented
- spawned follow-ups: TASK-062 trajectory-control dry run, TASK-063 final pack
- complexity: L

### Description
The current Alpamayo comparison uses a generic local CARLA capture, not a
Fail2Drive OOD split scene. This ticket captures Alpamayo-shaped frames from the
actual route context and reruns the no-memory vs memory comparison on the same
OOD route evidence.

### Goal
Move the Alpamayo story from "live model on a CARLA capture" to "live model on
the OOD route we are using as the scenario benchmark."

## Plan

### Change
Add a route-aligned Alpamayo capture mode that attaches to an existing ego/hero
actor during a Fail2Drive route, writes an Alpamayo package, runs remote
Alpamayo inference, builds a policy decision, then compares no-memory vs memory.

### Why
This is the strongest minimal-shot proof before closed-loop steering: same OOD
scenario, same frozen model, only retrieved safety memory changes.

### Before -> After
- Before: Alpamayo memory comparison is real but not route-aligned to stock
  Fail2Drive OOD.
- After: comparison report cites the Town13 route evidence, capture timestamp,
  hero actor id, CoC snippets, trajectory deltas, latency, and memory ids.

### Touch
- `src/driverx/simulators/carla_alpamayo_capture.py`: add attach-to-existing
  actor mode and optional route metadata.
- `src/driverx/simulators/carla_alpamayo_capture_cli.py`: add
  `--attach-role-name`, `--actor-id`, and route metadata args.
- `src/driverx/policies/alpamayo_live.py`: preserve route/capture metadata in
  policy decision evidence.
- `src/driverx/pipeline/alpamayo_ood_evaluation.py`: route-aligned labels and
  memory/no-memory comparison improvements if needed.
- `tests/test_carla_alpamayo_capture.py`, `tests/test_alpamayo_live.py`,
  `tests/test_alpamayo_ood_evaluation.py`.

### Inspect
- `src/driverx/simulators/carla_alpamayo_capture.py`
- `src/driverx/policies/alpamayo_materializer.py`
- `scripts/run_remote_alpamayo_carla_inference.sh`
- `tickets/archive/TASK-056/artifacts/town10-memory-comparison/`
- TASK-060 route evidence once available.

### Signature Delta
```python
src/driverx/simulators/carla_alpamayo_capture.py / run_carla_alpamayo_capture(config, run_dir, *, attach: CarlaActorAttachConfig | None = None, carla_module=None) -> CarlaAlpamayoCaptureResult
src/driverx/simulators/carla_alpamayo_capture.py / find_capture_actor(world, attach: CarlaActorAttachConfig) -> object
src/driverx/pipeline/alpamayo_ood_evaluation.py / build_alpamayo_ood_evaluation(..., route_evidence_path: Path | None = None) -> dict[str, Any]
```

### Type Sketch
```python
CarlaActorAttachConfig = {
  "role_name": "hero" | "driverx_alpamayo_capture",
  "actor_id": int | None,
  "blueprint_filter": "vehicle.*",
  "fallback_spawn": bool,
}

RouteAlignedAlpamayoPackage = {
  "frame_name": "town13::Generalization_PedestriansOnRoad_1088::t=...",
  "map_name": "Town13",
  "route_evidence_path": str,
  "hero_actor_id": int,
  "camera_windows": list[CameraWindow],
  "ego_history_xyz": list[list[float]],
  "memory_context": list[MemoryEntry],
}
```

### Typed Flow Example
Town13 route running or paused
-> sidecar capture finds `role_name=hero`
-> attaches 3 cameras and captures 4 ticks
-> writes `alpamayo_carla_input_package.json`
-> remote Alpamayo inference writes prediction JSON
-> `run-alpamayo-live`
-> `build-alpamayo-ood-comparison` with route evidence and memory context.

### Execution Steps
1. Extend capture code and tests with fake CARLA existing-actor mode.
2. Capture a route-aligned package after TASK-060 starts the route or via a
   controlled replay/paused route window.
3. Run no-memory remote Alpamayo inference on that package.
4. Build a memory-augmented package and run the same inference path.
5. Compare trajectory/CoC/latency and update demo evidence.

### Recommendation
Keep this open-loop. Do not let Alpamayo steer CARLA yet; this ticket proves
route-aligned reasoning and trajectory intent first.

### Options Considered
- Reuse generic TASK-051 capture: fastest but weaker evidence.
- Route-video frame ingestion: possible, but loses ego history and camera
  geometry.
- Attach-to-hero CARLA capture: best data fidelity without building closed-loop
  control.

### Blast Radius
Capture module, Alpamayo artifacts, and comparison reports. No change to route
execution semantics.

### Risks
- Fail2Drive hero role name may differ; support actor-id fallback.
- Capturing while the route runs may perturb simulation timing.
- Alpamayo latency is around 100s on the current eager path, so the result is
  still open-loop and must be labeled as such.

## Acceptance Criteria
- [x] AC-1: Capture can attach to an existing CARLA vehicle in fake tests.
- [ ] AC-2: Live route-aligned package records map, route, actor id, camera
  windows, ego history, and memory context.
- [ ] AC-3: Alpamayo no-memory and memory decisions both run on the same capture.
- [ ] AC-4: Comparison report includes route evidence path, CoC snippets,
  trajectory delta, latency, VRAM, and open-loop labels.
- [ ] AC-5: No raw model weights, HF caches, videos, or secrets are committed.

## Verification
- Unit:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_alpamayo_capture tests.test_alpamayo_live tests.test_alpamayo_ood_evaluation`
- Live:
  route-aligned capture + remote Alpamayo inference on RunPod
- Gate: `bash scripts/pre_push_check.sh`
- Evidence:
  `tickets/TASK-061/artifacts/route-aligned-alpamayo-comparison/alpamayo_ood_comparison.md`

## Autonomy Readiness
- I can implement and test fake-CARLA attach mode locally.
- Live proof depends on Town13 route availability and kept-alive RunPod.

## Evidence
- 2026-05-06 03:34 +0800: Implemented the local attach-to-existing-actor seam
  while the Town13 package download was in progress. Focused test:
  `PYTHONPATH=src python3 -m unittest tests.test_carla_alpamayo_capture` passed
  with 5 tests. The capture package now records `route_context`,
  `capture_actor.actor_id`, and whether the ego was `attached` or `spawned`.
- Review: `docs/reviews/TASK-061-route-capture-attach-review.md` passed the
  implemented AC-1 seam at 4.0/5.0 and keeps the live proof blocker on TASK-060.

## Blockers
- TASK-068 proved Town13 route startup, but the local Mac/Kegworks/Wine runtime
  timed out before a stable route-aligned capture handoff. AC-2 through AC-4
  now need either a faster graphics-capable Linux NVIDIA CARLA host or a much
  longer local run with capture attached during the route window.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
