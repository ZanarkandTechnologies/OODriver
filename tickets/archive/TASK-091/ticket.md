# TASK-091: Environment And Roadwork Generator Pack

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-089, TASK-090
- location: `src/driverx/scenarios`, `src/driverx/assets`, `src/driverx/environments`, `configs`, docs, `tickets/TASK-091/artifacts`
- enter when: road-relative placement exists and the catalog can manage generated scenarios
- leave when: DriverX can deterministically generate environment variants such as construction, market-side obstruction, wet/flooded road, night/rain/fog, lane closure, dense regional traffic, and school-zone pedestrian occlusion
- blockers: no Meshy/API key required; live CARLA proof waits on TASK-089 if not complete
- spawned follow-ups: Meshy/custom GLB import ticket after stock-proxy generator is credible
- complexity: M

### Summary

Make the simulator contribution concrete: a generator that creates environment
families, not just behavior traces. This is where we start showing new
minimal-shot stress-test cases that extend Fail2Drive-style OOD testing.

### Scope

- In scope: deterministic environment recipes, stock CARLA proxy assets,
  roadwork layouts, weather presets, Malaysian/regional environment tags,
  generator reports, and Meshy-ready prompts as deferred metadata.
- Out of scope: importing new GLB assets into CARLA, Unreal Editor map baking,
  or live Meshy API calls.

### Gap Analysis

- Current state: asset manifests are fixed examples and scenario mutations are
  mostly prose fields.
- Production expectation: the harness should generate suites like "rainy night
  construction lane closure with food-cart occlusion and unsignaled motorbike
  filtering" from seed + policy.
- Missing gaps: environment-family types, road-relative asset layouts, weather
  controls, density/severity knobs, and repeatable suite reports.
- Recommendation: use stock CARLA props first, preserve Meshy prompts for later
  visual polish, and make generator quality measurable.

### Plan

#### Change

Add environment generation as a first-class module with deterministic recipes
that map to road-relative assets, weather, lighting, and traffic-style intent.

#### Why

The commission rewards randomized scenario generation. This ticket turns that
from a claim into a usable API.

#### Before -> After

- Before: "construction" is a mutation tag with maybe one generic prop.
- After: "construction" expands into lane cones, debris, work-zone occlusion,
  reduced target speed, visibility constraints, and expected failure modes.

#### Touch

- `src/driverx/environments/types.py`: new environment recipe types.
- `src/driverx/environments/library.py`: construction, roadside-market,
  flood/wet-road, night-rain-fog, lane-closure, dense-urban packs.
- `src/driverx/environments/generator.py`: deterministic selection and severity.
- `src/driverx/assets/pipeline.py`: generate stock-proxy asset requests from
  environment layouts.
- `src/driverx/scenarios/generator.py`: attach environment recipes to
  `ScenarioRecipe`.
- `src/driverx/scenarios/reports.py`: environment suite report.
- `configs/environment_forge.sample.yaml`.
- `tests/test_environment_generator.py`.

#### Inspect

- `src/driverx/assets/types.py`
- `src/driverx/assets/pipeline.py`
- `src/driverx/assets/carla_mapping.py`
- `src/driverx/scenarios/generator.py`
- `configs/scenario_forge.sample.yaml`

#### Signature Delta

```python
load_environment_pack(path: Path | None = None) -> list[EnvironmentTemplate]
generate_environment_recipe(template_id: str, severity: int, random_seed: int) -> EnvironmentRecipe
environment_to_asset_requests(recipe: EnvironmentRecipe, road_frame_hint: RoadFrameHint) -> list[AssetRequest]
environment_to_carla_weather(recipe: EnvironmentRecipe) -> dict[str, float | str]
write_environment_suite_report(recipes: list[EnvironmentRecipe], output_dir: Path) -> dict[str, Path]
```

#### Type Sketch

```python
EnvironmentRecipe = {
  "environment_id": str,
  "family": "construction" | "roadside_market" | "wet_road" | "night_fog" | "lane_closure" | "dense_regional",
  "severity": int,
  "weather": {"cloudiness": float, "precipitation": float, "fog_density": float, "sun_altitude_angle": float},
  "road_layout": {"blocked_lanes": list[str], "shoulder_usable": bool, "speed_limit_hint_mps": float},
  "asset_layouts": list[{"asset_kind": str, "x_m": float, "y_m": float, "yaw_delta_deg": float, "scale": float}],
  "expected_challenge": str,
  "meshy_prompt": str | None,
}
```

#### Typed Flow Example

`seed + environment_family=construction + severity=3`
-> environment recipe
-> road-relative stock-proxy asset requests
-> CARLA weather plan
-> scenario catalog record
-> TASK-093 quality-gated campaign.

#### Execution Steps

1. Add environment domain types and built-in templates.
2. Connect templates to existing scenario recipe generation.
3. Convert environment layouts into stock CARLA proxy assets using TASK-089
   road-frame placement.
4. Add fixture tests for deterministic output and CARLA-compatible mapping.
5. Write a report showing generated environment families and example layouts.

#### Recommendation

Do not use Meshy in this ticket. The strongest near-term contribution is
structured generation and reliable CARLA placement; custom meshes are later
visual polish once the road-aligned suite works.

#### Options Considered

- Meshy-first GLB import: visually exciting but risky because CARLA runtime
  assets usually need Unreal packaging/import steps.
- Weather-only generation: easy but too shallow.
- Environment pack over stock CARLA proxies: best; immediate runnable value and
  clean path to custom assets later.

#### Blast Radius

- Moderate: scenario generation payloads gain environment details. Keep old
  fields backward compatible.

#### Risks

- Some weather controls may differ across CARLA maps; report the exact applied
  values and tolerate unsupported fields.
- Stock proxy assets can look generic; offset with good labels, overlays, and
  future Meshy prompt metadata.

### Acceptance Criteria

- [x] AC-1: Generator produces at least six deterministic environment families
  with severity controls.
- [x] AC-2: Each environment recipe emits CARLA-compatible stock-proxy asset
  requests and optional weather settings.
- [x] AC-3: Environment suite report shows generated cases, expected challenge,
  and Meshy-ready prompt metadata without requiring an API key.
- [x] AC-4: Scenario catalog records include environment family and severity.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_environment_generator tests.test_asset_pipeline`
- `PYTHONPATH=src python3 -m driverx forge-environments --config configs/environment_forge.sample.yaml --run-id task91-environments`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Fully local. No CARLA, GPU, or Meshy key required for implementation.

### Evidence

- Planned 2026-05-06 to shift from setup toward the simulator-generation
  contribution.
- Plan review: `docs/reviews/TASK-089-095-impl-plan-review.md`.
- Implemented `src/driverx/environments` with deterministic construction,
  roadside market, flooded-road, night/rain/fog, dense regional traffic, and
  school-zone pedestrian occlusion packs plus stock CARLA proxy asset requests.
- Focused tests passed:
  `PYTHONPATH=src python3 -m unittest tests.test_environment_generator tests.test_scenario_quality tests.test_policy_evaluation_campaign tests.test_submission_scenario_browser`.
- Generated environment-pack evidence:
  `tickets/TASK-091/artifacts/environment-forge-v2/environment_suite_report.md`.

### Blockers

- None.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
