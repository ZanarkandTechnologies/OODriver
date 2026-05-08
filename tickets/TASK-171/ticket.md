# TASK-171: Scenario Choreography CLI For Timed Actors And Hazards

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-141, TASK-166
- location: `src/driverx/scenarios`, `src/driverx/evaluation`, `tests`, `artifacts/runs`
- enter when: OODrive can generate CARLA-ready environments and behavior traces, but needs a single agent-operable CLI to choreograph vehicles, pedestrians, props, triggers, and expected safe responses.
- leave when: `oodrive choreograph` produces a replayable choreography manifest with timed actors/hazards, object spawn specs, behavior traces, fake-CARLA track proof, claim boundaries, and a mechanical `scenario_choreography_score`.
- blockers: live CARLA video proof is TASK-172; this ticket may use fake-CARLA/local proof only.
- spawned follow-ups: TASK-172 live CARLA choreography videos; TASK-173 judge demo pack.
- complexity: M
- assignee: generalPurpose

### Summary
Build the missing bridge between “scenario specs” and “convincing edge-case task examples.” A user or AI agent should be able to say: block the road, make a vehicle cut in, make an object roll across, and require stop/slow/yield/replan labels, then get one manifest that proves the choreography is replayable.

### Scope
In scope:
- Product CLI commands: `oodrive choreograph` and `oodrive score-choreography`.
- Default bad-path choreography cases for static blocker, moving cut-in, rolling/accident object, and compound detour.
- Timed actor/object tracks using existing behavior traces and asset spawn specs.
- Mechanical score rewarding actor/object diversity, timing, traces, expected response labels, cleanup/lineage, and honest claims.

Out of scope:
- Meshy/custom blueprint import. That is TASK-170.
- Live CARLA video promotion. That is TASK-172.
- Closed-loop Alpamayo claim upgrades.

### Plan

#### Change
Add a scenario choreography layer that composes existing environment templates, behavior traces, object kinds, trigger timings, and safe-response labels into one agent-facing run artifact.

#### Why
The demo needs task examples that are concrete: “object blocks road,” “moving object enters lane,” “accident object rolls,” and “compound case requires stop/replan.” The current generator can create pieces, but a judge cannot yet see one clear choreography contract.

#### Before -> After
- Before: `generate-run` proves behaviors and objects, but the intended scenario timing is implicit.
- After: `choreograph` writes a scenario timeline with actors, objects, triggers, response labels, tracks, and scoreable proof.

#### Touch
- `src/driverx/scenarios/choreography.py` new core builder.
- `src/driverx/scenarios/studio_product_choreography_runtime.py` new product runtime.
- `src/driverx/scenarios/studio_product_choreography_cli.py` new CLI registration.
- `src/driverx/scenarios/studio_product_cli.py` register commands.
- `src/driverx/evaluation/scenario_choreography_score.py` new score.
- `src/driverx/evaluation/__init__.py` exports.
- `tests/test_scenario_choreography.py` new tests.
- `tests/test_oodrive_cli.py` command registration.

#### Inspect
- `src/driverx/scenarios/generated_runtime.py`
- `src/driverx/scenarios/production_pack.py`
- `src/driverx/behaviors/library.py`
- `src/driverx/evaluation/generator_runtime_score.py`

#### Signature Delta
- `build_choreography_plan(prompt, case_ids, behavior_ids, object_kinds, seed): dict`
- `run_choreography_fake_carla(plan, run_dir): dict`
- `run_studio_choreograph(...): StudioCommandResult`
- `score_scenario_choreography(inputs): ScenarioChoreographyScoreReport`

#### Type Sketch
```python
ChoreographyPlan = {
  "actors": [{"actor_id": str, "kind": "vehicle|pedestrian|motorcycle", "behavior_id": str}],
  "objects": [{"object_id": str, "kind": str, "motion": "static|moving"}],
  "triggers": [{"at_s": float, "event": str, "target": str}],
  "expected_responses": ["stop", "slow", "yield", "replan"],
  "tracks_path": str,
  "claim_boundaries": list[str]
}
```

#### Typed Flow Example
Prompt “crane blocks road, scooter cuts in, rolling debris crosses” -> default compound plan -> behavior traces and static object spawns -> fake entity tracks -> `choreography_manifest.json` -> `score-choreography`.

#### Execution Steps
1. Add core choreography builder with four default cases.
2. Convert behavior traces into actor timeline records and entity tracks.
3. Add static/moving object records with trigger times and road-local placement.
4. Write JSON/Markdown manifest plus fake-CARLA proof.
5. Add score module and CLI command.
6. Register product CLI commands.
7. Add tests for default case richness, score passing, overclaim boundaries, and CLI registration.
8. Generate TASK-171 artifact and update evidence.

#### Recommendation
Build `choreograph` as a local/fake proof first. Live CARLA video should consume the manifest in TASK-172 rather than being mixed into this ticket.

#### Options Considered
- Extend `generate-run`: faster, but keeps timing/response semantics implicit.
- New `choreograph` command: recommended; clearer for judges and AI agents.
- Build live video first: rejected; weak without a replayable choreography contract.

#### Blast Radius
New command/evaluation path plus CLI registration. Existing `generate-run` and `carla-suite` behavior should remain unchanged.

#### Risks
- Behavior validators reject some aggressive traces; use passing templates for default proof and label harder maneuvers as future live-tuning cases.
- Fake proof can be mistaken for live CARLA; manifests must label `live_carla_execution=false`.

### Acceptance Criteria
- [x] AC-1: `oodrive choreograph` writes a `choreography_manifest.json` and Markdown report.
- [x] AC-2: Default output includes at least four task cases, four behavior types, four object kinds, static and moving hazards, and response labels including stop/slow/yield/replan.
- [x] AC-3: Fake-CARLA proof writes entity tracks and cleanup ids.
- [x] AC-4: `oodrive score-choreography --metric-only` emits `METRIC scenario_choreography_score=<number>` and passes at `>=90`.
- [x] AC-5: Claims include `live_carla_execution=false`, `closed_loop_vla_control=false`, and `custom_unreal_map_import=false`.

### Verification
- `PYTHONPATH=src python3 -m oodrive choreograph "wet urban OOD bad paths: static blocker, cut-in vehicle, rolling object, compound detour" --run-id task171-choreography-v2`
- `PYTHONPATH=src python3 -m oodrive score-choreography --choreography-manifest artifacts/runs/task171-choreography-v2/choreography_manifest.json --run-id task171-choreography-v2-score --metric-only`
- `PYTHONPATH=src python3 -m unittest tests.test_scenario_choreography tests.test_oodrive_cli`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- No external service required.
- Live CARLA promotion is explicitly deferred to TASK-172.
- The command is safe for unattended local runs because it writes ignored artifacts only.

### Evidence
- Choreography manifest: `artifacts/runs/task171-choreography-v2/choreography_manifest.json`
- Choreography report: `artifacts/runs/task171-choreography-v2/choreography_report.md`
- Entity tracks: `artifacts/runs/task171-choreography-v2/entity_tracks.json`
- Score JSON: `artifacts/runs/task171-choreography-v2/choreography-scores/task171-choreography-v2-score/scenario_choreography_score.json`
- Metric: `METRIC scenario_choreography_score=100.0000`
- Focused tests: `12 tests OK`
- Pre-push: `478 tests OK, 6 skipped`
- Review artifact: `tickets/TASK-171/artifacts/review/task171-impl-review.json`
