# Autoresearch: Production Scenario Generator Utility

## Objective

Maximize OODrive's production research value as a prompt-to-CARLA scenario generator. The loop should reward scenarios that start from a prompt, produce inspectable scenario packs, generate or ingest real 3D assets, install/probe those assets in CARLA, run behavior-rich simulator cases, record evidence-grade videos/tracks, expose a usable workbench, and export reproducible scenario-library records.

## Metric

- Primary: `research_scenario_generator_score` (0-100 points, higher is better)
- Verify: `./autoresearch.sh`
- Guard: `./autoresearch.checks.sh`
- Direction: higher
- Target: `>=85` for researcher-useful, `>=95` for flagship production proof
- Max iterations: 16
- Noise policy: deterministic artifact score; rerun gains above 6 points before treating them as durable.

## Scope

- Editable:
  - `src/driverx/assets/`
  - `src/driverx/scenarios/`
  - `src/driverx/simulators/`
  - `src/driverx/evaluation/`
  - `src/driverx/workbench/`
  - `src/oodrive/`
  - `tests/`
  - `tickets/TASK-149/`
  - `tickets/TASK-150/`
  - `tickets/TASK-151/`
  - `tickets/TASK-152/`
  - `tickets/TASK-153/`
  - `tickets/TASK-154/`
  - `tickets/TASK-155/`
  - `tickets/TASK-156/`
- Read-only:
  - root `autoresearch.*` commission-readiness session
  - completed archive tickets
  - prior generated videos/assets unless a ticket explicitly regenerates derived evidence
- Off limits:
  - credentials, API keys, paid provider calls, destructive remote package installs, model weights, dataset shards, and false claims that stock proxies are prompt-generated custom assets.

## Constraints

- Claim honesty is part of the metric. Stock proxy CARLA evidence earns simulator-spawn credit, not custom-asset credit.
- Live Kasm CARLA proof is preferred for simulator evidence when available, but local fake backends may support contract tests.
- Generated mesh files and media remain under ignored artifact paths.
- Root `autoresearch.*` is a separate commission-readiness loop and must not be overwritten by this session.

## Current Baseline

The baseline verify command now scores the best available TASK-149 through
TASK-156 artifact chain. Current score: `research_scenario_generator_score=92.0`
with status `partial`.

What improved:

- Scenario pack, local procedural mesh generation, CARLA registry/proxy fallback,
  scenario graph/OpenSCENARIO export, live Kasm CARLA run evidence, workbench,
  library export, and claim-honesty components are all present.
- Live simulator evidence is real CARLA stock-proxy spawning, not the local
  fake-CARLA backend.

What still blocks flagship proof:

- `prompt_image_match=partial`; the QA frame shows a scooter and vendor in live
  CARLA, but wet roadwork, Malaysia-specific scene fidelity, construction debris,
  and scooter-filtering-around-debris are weak.
- `carla_asset_import=5.0`; local procedural OBJ meshes exist, but CARLA still
  spawns stock proxies because no generated blueprint package has been installed
  and probed.

Execution note: this session ran in a heavily dirty workspace with overlapping
ticket implementation files, so autoresearch was executed as a metric/evidence
loop without per-experiment git commits or reverts to avoid risking user work.

## Next Ideas

- Add prompt-to-placement fidelity controls for wetness, map/town selection,
  roadwork density, debris visibility, and camera/keyframe selection.
- Implement true CARLA generated-asset package/import proof so generated meshes
  become installed blueprint ids instead of stock proxies.
- Add an automated image-QA loop over multiple live keyframes before promoting a
  run as exact prompt evidence.
