# TASK-166: CARLA Capability Matrix And Ten-Scenario Suite

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-165
- location: `src/driverx/scenarios`, `src/driverx/simulators`, `src/driverx/evaluation`, `tests`, `artifacts/runs`
- enter when: OODrive has agent-facing CARLA catalog/control/compose commands and the user needs proof of what this installed CARLA runtime can actually vary before generating a gallery.
- leave when: one command probes or records a CARLA capability matrix, then generates exactly 10 candidate scenario cases from installed maps, weather presets, anchors, cameras, and known blueprint/proxy families.
- blockers: live CARLA screenshot/image-diversity promotion is handled by TASK-167; TASK-166 must not claim visual variety from prompt text alone.
- spawned follow-ups: TASK-167 consumes the suite for live CARLA screenshots; TASK-168 consumes selected cases for behavior simulation/video.
- complexity: M
- assignee: generalPurpose

### Description
Generate a CARLA capability matrix first, then a deliberate 10-case CARLA scenario suite. The matrix must reflect installed CARLA facts: available maps, weather controls, spawn anchors, camera poses, and installed blueprint/proxy families. The suite must cover different towns, weather presets, static blockers, moving actors, rolling/collision-course objects, lane narrowing, occlusions, and route pressure.

### Goal
Give judges and the user a clear matrix of what OODrive can actually generate in this CARLA install: not one repeated cart/shop scene, and not fake prompt variety, but ten simulator setups selected from real map/weather/blueprint/camera capabilities.

### Live CARLA Facts To Preserve
- Available maps on the current install: `Town01`, `Town02`, `Town03`, `Town04`, `Town05`, `Town10HD`, plus `_Opt` variants.
- Recent live control proof loaded `Town03_Opt` from `Town10HD_Opt` and `Town05_Opt` from `Town03_Opt`.
- Weather was applied through the CARLA API.
- Screenshots are live CARLA captures, not generated 2D mockups.
- CARLA can load installed maps, switch towns, control sun/rain/fog/wetness, spawn installed blueprints, spawn vehicles/pedestrians/props, move cameras, capture frames, and render videos.
- CARLA cannot prompt-generate brand-new city/map geometry at runtime.
- CARLA cannot spawn arbitrary generated 3D meshes unless they are imported/packaged into Unreal/CARLA and registered as blueprints.
- CARLA wetness gives reflective/wet roads; true flood water physics needs custom assets/materials/map work.

### Acceptance Criteria
- [x] AC-1: `oodrive carla-matrix` or `oodrive carla-suite --probe-capabilities` emits an installed-capability matrix covering maps, weather presets, camera/spawn anchors, and available/proxy blueprint families.
- [x] AC-2: `oodrive carla-suite` generates exactly 10 cases by default from that matrix.
- [x] AC-3: Each case includes town/map, weather preset, road anchor, camera pose, environment template, behavior ids, object kinds, static-vs-moving classification, and expected policy pressure.
- [x] AC-4: The suite writes per-case `carla_ood_demo_config.yaml`, generated runtime spec, generated runtime manifest, and a suite summary JSON/Markdown.
- [x] AC-5: The suite includes at least four distinct towns, five weather/environment families, four dynamic behavior types, and four static object classes/proxies.
- [x] AC-6: A capability matrix report and storyboard artifact exist locally even before live CARLA render, with honest labels: `carla_existing_map_composition=true`, `custom_unreal_map_import=false`, `arbitrary_mesh_spawn=false`, and `true_flood_physics=false`.
- [x] AC-7: The suite does not enter a generator gallery until TASK-167 live image-diversity scoring passes.

### Agent Contract
- Open: `src/driverx/scenarios/studio_product_carla_composer_runtime.py`, `src/driverx/scenarios/studio_product_carla_composer_cli.py`, `src/driverx/simulators/carla_catalog.py`, `src/driverx/pipeline/environment_demo_pack.py`, `tests/test_carla_scenario_composer.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_carla_scenario_composer tests.test_oodrive_cli`
- Stabilize: keep generated suite deterministic by seed; do not require CARLA for TASK-166 tests.
- Inspect: suite manifest, per-case composition manifests, generated configs, fake-CARLA runtime manifests, contact sheet/storyboard.
- QA cookbook: run the suite command, count 10 cases, check case diversity metrics, inspect contact sheet.
- Expected artifacts: `carla_capability_matrix.json`, `carla_capability_matrix.md`, `carla_suite_manifest.json`, `carla_suite_report.md`, `carla_suite_storyboard.html`, `carla_suite_contact_sheet.png` or SVG/HTML fallback.

### Plan

#### Change
Add a capability-matrix layer on top of `carla-catalog`/`carla-control`, then add a suite-generation layer on top of `carla-compose` that emits ten curated case specs from real installed capabilities.

#### Why
The current user-visible artifact still feels repetitive. A capability matrix prevents fake prompt variation, and a 10-case suite turns the real CARLA generator claim into a skimmable set of varied scenarios.

#### Before -> After
- Before: one prompt/run gives one town/anchor/object family, and visual variety depends too much on trust.
- After: one matrix command exposes what CARLA can vary, then one suite command gives a replayable 10-case suite with static and moving hazards across multiple towns/weather families.

#### Touch
- `src/driverx/scenarios/studio_product_carla_composer_runtime.py`
- `src/driverx/scenarios/studio_product_carla_composer_cli.py`
- `src/driverx/evaluation/carla_capability_matrix_score.py` (new if scoring grows beyond simple counts)
- `src/driverx/pipeline/carla_suite_storyboard.py` (new if contact-sheet/storyboard logic grows)
- `src/driverx/evaluation/carla_suite_score.py` (new if diversity metric is needed)
- `tests/test_carla_scenario_composer.py`
- `tests/test_oodrive_cli.py`

#### Inspect
- TASK-165 composition artifacts
- TASK-165 live control facts and screenshots
- `src/driverx/environments/library.py`
- `src/driverx/behaviors/library.py`
- `src/driverx/assets/carla_mapping.py`

#### Signature Delta
- `build_carla_capability_matrix(catalog: dict, live_probe: dict | None) -> CarlaCapabilityMatrix`
- `build_default_carla_suite(seed: int, count: int = 10) -> list[CarlaSuiteCase]`
- `run_studio_carla_suite(output_root: Path | None, run_id: str, seed: int, backend: str) -> StudioCommandResult`
- `write_carla_suite_storyboard(manifest: dict, output_dir: Path) -> dict[str, str]`

#### Type Sketch
```python
CarlaCapabilityMatrix = {
  "available_maps": list[str],
  "weather_controls": list[str],
  "camera_anchor_modes": list[str],
  "blueprint_families": list[str],
  "can": list[str],
  "cannot": list[str],
  "claim_labels": dict[str, bool]
}

CarlaSuiteCase = {
  "case_id": str,
  "prompt": str,
  "town": str,
  "map_name": str,
  "weather_preset": str,
  "template_ids": list[str],
  "behavior_ids": list[str],
  "object_kinds": list[str],
  "hazards": [{"kind": "static" | "moving", "role": str}],
  "expected_policy_pressure": str
}
```

#### Typed Flow Example
`case-03-rolling-object-town05` -> `run_studio_carla_compose(... backend=fake-carla)` -> per-case `carla_ood_demo_config.yaml` + runtime manifest -> suite summary row -> contact sheet/storyboard.

Capability example: installed maps + weather controls + probed proxy blueprint families -> `carla_capability_matrix.json` -> ten cases constrained to supported maps/assets -> promotion blocked until TASK-167 live screenshot diversity passes.

#### Execution Steps
1. Add capability matrix builder using catalog plus optional live probe metadata.
2. Add case library with ten hand-curated defaults selected from the matrix.
3. Add CLI command registration.
4. Reuse `run_studio_carla_compose` per case and collect artifacts.
5. Add diversity summary counts and capability-boundary labels.
6. Write HTML/contact-sheet storyboard.
7. Add tests for count, diversity, claim boundaries, capability facts, artifact existence, and CLI help.
8. Update docs with one command and sample output.

#### Recommendation
Build the capability matrix first, then the curated default suite. Add fully prompt-generated suite expansion later after live matrix/reel evidence proves the shape.

#### Options Considered
- Pure random generation: more breadth, weaker judge legibility and too easy to fake with text.
- Capability-matrix-gated curated defaults: recommended; strongest demo clarity under deadline.
- Full custom 3D asset generation: out of scope until live import chain is proved.

#### Blast Radius
New command and artifacts only; reuses existing compose/runtime machinery.

#### Risks
- Contact sheet can look fake if it uses only text/cards. TASK-167 must replace placeholders with live CARLA screenshots and score image diversity.
- Some “flooded” prompts can overclaim. Use wet-road labels unless custom water assets/materials are proved.

### Verification
- `PYTHONPATH=src python3 -m oodrive carla-suite --probe-capabilities --run-id task166-capability-suite-v2`
- `PYTHONPATH=src python3 -m oodrive score-carla-suite --suite-manifest artifacts/runs/task166-capability-suite-v2/carla_suite_manifest.json --run-id task166-capability-suite-v2-score --metric-only`
- `./autoresearch.sh`
- `./autoresearch.checks.sh`
- `PYTHONPATH=src python3 -m unittest tests.test_carla_scenario_composer tests.test_oodrive_cli`

### Evidence
- Capability matrix JSON: `artifacts/runs/task166-capability-suite-v2/carla_capability_matrix.json`
- Capability matrix Markdown: `artifacts/runs/task166-capability-suite-v2/carla_capability_matrix.md`
- Suite manifest: `artifacts/runs/task166-capability-suite-v2/carla_suite_manifest.json`
- Suite report: `artifacts/runs/task166-capability-suite-v2/carla_suite_report.md`
- Storyboard: `artifacts/runs/task166-capability-suite-v2/carla_suite_storyboard.html`
- Score JSON: `artifacts/runs/task166-capability-suite-v2-score-final/carla_capability_suite_score.json`
- Metric: `METRIC carla_capability_suite_score=100.0000`
- Focused tests: `18 tests OK`
- Autoresearch guard: `18 tests OK`
- Pre-push: `471 tests OK, 5 skipped`
- Planning review: `tickets/TASK-166/artifacts/review/task166-169-plan-review.json`
- Implementation review: `tickets/TASK-166/artifacts/review/task166-impl-review.json`
