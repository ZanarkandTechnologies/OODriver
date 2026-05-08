# TASK-180: Prompt-To-CARLA Visual Fidelity And Behavior QA Gate

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-167, TASK-172, TASK-179
- location: `src/driverx/evaluation`, `src/driverx/pipeline`, `src/driverx/simulators`, `tests`, `artifacts/runs`
- enter when: OODrive can capture CARLA images/videos, but promotion still depends too much on manual eyeballing.
- leave when: OODrive scores whether a generated CARLA image/video visibly matches the prompt, shows requested hazards, keeps actors road-aligned, shows motion when required, and is diverse from previous gallery entries.
- blockers: local image scoring starts with metadata/geometric checks; stronger VLM-based scoring needs a provider/runtime and must be labeled.
- spawned follow-ups: gallery promotion automation and judge pack refresh.
- complexity: M
- assignee: generalPurpose

### Description
Add the visual QA gate that prevents weak or repetitive CARLA scenes from reaching the demo gallery. This is the answer to “why are they all the same?” and “why is the car out of lane?”

### Goal
Make generated environments promotable only when the media visibly proves the prompt and behavior.

### Integration Decision
Do not rely only on OODrive metadata or self-reported spawn manifests. CARLA media promotion needs a visual/evidence gate. Use deterministic checks first and optionally integrate a VLM reviewer later; do not make VLM required for local CI.

### Plan

#### Change
Add a visual fidelity score for generated CARLA images/videos and behavior evidence.

#### Why
The user has repeatedly caught weak artifacts: same-looking scenes, missing visible hazards, and off-road-looking avoidance. A scorer should block those before they reach the gallery or judge pack.

#### Before -> After
- Before: CARLA media can pass because metadata says objects spawned.
- After: `score-visual-fidelity` evaluates whether media visibly matches prompt/resolution and blocks weak proof.

#### Touch
- `src/driverx/evaluation/visual_fidelity_score.py` new score.
- `src/driverx/pipeline/visual_fidelity.py` new media manifest helpers.
- `src/driverx/scenarios/studio_product_visual_cli.py` new CLI registration.
- `src/driverx/scenarios/studio_product_visual_runtime.py` new runtime wrapper.
- `src/driverx/scenarios/studio_product_cli.py` register commands.
- `tests/test_visual_fidelity_score.py` new tests.
- `tests/test_oodrive_cli.py` command registration.

#### Inspect
- `src/driverx/evaluation/carla_suite_score.py`
- `src/driverx/evaluation/hero_demo_score.py`
- `src/driverx/evaluation/environment_reasoned_carla_score.py`
- `src/driverx/pipeline/keyframe_analysis.py`
- `src/driverx/simulators/carla_control.py`

#### Signature Delta
- `load_visual_fidelity_inputs(prompt: str, media_manifest_path: Path, resolution_path: Path | None = None) -> VisualFidelityInputs`
- `score_visual_fidelity(inputs: VisualFidelityInputs, threshold: float = 85.0) -> VisualFidelityScoreReport`
- `write_visual_fidelity_report(report: VisualFidelityScoreReport, output_dir: Path) -> dict[str, str]`

#### Type Sketch
```python
VisualFidelityScoreReport = {
  "prompt_to_carla_visual_score": float,
  "components": {"media_presence": float, "hazard_visibility": float, "motion": float, "road_alignment": float, "diversity": float},
  "blockers": list[str],
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example
Media manifest for a moving cut-in video -> scorer checks MP4/frame presence, track deltas, hazard labels, lane-departure flags, frame count/duration, and diversity hash -> blocks if actor never moves or ego leaves road.

#### Execution Steps
1. Define media manifest input shape compatible with TASK-167/TASK-172 outputs.
2. Implement deterministic scoring from media existence, frame counts, track deltas, lane flags, prompt/resolution tags, and duplicate hashes.
3. Add hard blockers for missing media, invisible/metadata-only hazards, off-road flags, and false custom claims.
4. Add optional VLM review attachment field without requiring provider execution.
5. Register CLI and tests for good/bad cases.

#### Recommendation
Make this a hard promotion gate for gallery/demo packs, but keep initial scoring deterministic so CI remains reliable.

#### Options Considered
- Manual visual review only: too easy to regress.
- VLM-only review: attractive but introduces provider/runtime fragility.
- Deterministic gate plus optional VLM: recommended; stable now, extensible later.

#### Blast Radius
Moderate. It will affect promotion decisions but should not mutate scenario generation or CARLA execution.

#### Risks
- Deterministic checks cannot fully judge aesthetics; focus on blockers that matter: media, motion, road alignment, prompt tags, and false claims.
- Existing artifacts may fail; that is desirable if they are weak.

### Acceptance Criteria
- [ ] AC-1: `oodrive score-visual-fidelity` consumes prompt/resolution plus CARLA frame/video manifest and emits `prompt_to_carla_visual_score`.
- [ ] AC-2: Score includes map/weather match, requested object visibility, static/moving hazard evidence, road/lane alignment, motion evidence, camera framing, and diversity from a previous gallery.
- [ ] AC-3: Hard blockers reject missing media, invisible hazard, off-road ego/avoidance, zero-motion moving actors, and false custom-asset/custom-map claims.
- [ ] AC-4: Optional provider hook can attach VLM/image-review results while preserving deterministic local checks.
- [ ] AC-5: Tests cover good static blocker, good moving cut-in, bad off-road swerve, missing custom crane, and duplicate-looking scene.

### Agent Contract
- Open: `src/driverx/evaluation/carla_suite_score.py`, `src/driverx/evaluation/hero_demo_score.py`, `src/driverx/evaluation/environment_reasoned_carla_score.py`, `src/driverx/pipeline/keyframe_analysis.py`, `src/driverx/simulators/carla_control.py`
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_visual_fidelity_score tests.test_environment_to_carla_visual_proof tests.test_oodrive_cli`
- Stabilize: deterministic checks must run without network/model access; VLM provider output is advisory unless explicitly configured.
- Inspect: visual score JSON/Markdown, contact sheet, per-frame blockers, diversity hashes/features.
- QA cookbook: run against the 10 live CARLA snapshot contact sheet, TASK-172 videos, and one known-bad off-road scripted case.
- Expected artifacts: `visual_fidelity_score.json`, `visual_fidelity_score.md`, `visual_blockers.json`, optional `vlm_review.json`.

### Build Notes
- This is a promotion gate, not a model benchmark.
- It must penalize metadata-only proof when the visual artifact does not show the requested hazard.

### Verification
- `PYTHONPATH=src python3 -m oodrive score-visual-fidelity --prompt <prompt> --media-manifest <manifest> --run-id task180-score --metric-only`
- `PYTHONPATH=src python3 -m unittest tests.test_visual_fidelity_score tests.test_oodrive_cli`
- `bash scripts/pre_push_check.sh`

### Evidence
- Visual score report
- Contact sheet
- Blocker list
- Optional VLM review
- Planning review: `tickets/TASK-174/artifacts/review/task174-180-integration-plan-review.json`
