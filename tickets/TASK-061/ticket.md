# TASK-061: Route-Aligned Alpamayo OOD Capture And Comparison

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-059, TASK-060
- location: `src/driverx/simulators`, `src/driverx/policies`,
  `src/driverx/pipeline`, tests, `tickets/TASK-061/artifacts`
- enter when: dataset-backed Alpamayo proof exists and a Town13 route run can
  produce live CARLA evidence
- leave when: a route-aligned CARLA capture is evaluated by Alpamayo with and
  without retrieved memory
- blockers: waits on TASK-059 and TASK-060
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
- [ ] AC-1: Capture can attach to an existing CARLA vehicle in fake tests.
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
- Pending TASK-059 and TASK-060.

## Blockers
- Dataset-backed probe and stock Town13 route proof are prerequisites.
