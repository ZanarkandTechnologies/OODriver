# TASK-173: Judge Demo Pack For Agent-Operable CARLA Scenario Factory

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-167, TASK-170, TASK-171, TASK-172
- location: `src/driverx/pipeline`, `src/driverx/scenarios`, `src/driverx/evaluation`, `tests`, `artifacts/runs`
- enter when: OODrive has live snapshots, choreography proof, and at least one custom-asset/import status artifact.
- leave when: one command builds a judge-visible demo pack with screenshots, videos, choreography timeline, asset-status matrix, reasoning overlays, metrics, commands, and honest claim boundaries.
- blockers: live media availability.
- spawned follow-ups: final submission refresh.
- complexity: M
- assignee: generalPurpose

### Summary
Turn the separate proof artifacts into a coherent judge-facing story: an AI agent uses OODrive to create CARLA edge cases, choreograph actors, optionally import custom assets, run simulator evidence, and score the result.

### Scope
In scope:
- Product commands: `oodrive excellence-demo-pack` and `oodrive score-judge-replayability`.
- A single HTML/JSON pack with commands, images/videos, choreography timeline, asset import status, reasoning evidence, metrics, and claim matrix.
- Clear visual separation between live CARLA proof, local/fake proof, open-loop reasoning, paused closed-loop proof, stock proxy assets, and custom asset blockers.
- Mechanical `judge_replayability_score` target `>=90`.

Out of scope:
- New live media capture. TASK-173 only packages already-proved artifacts.
- New custom asset generation. It consumes TASK-170 status.
- Inflating claims to closed-loop or arbitrary world generation.

### Plan

#### Change
Build the judge-facing submission artifact that makes OODrive understandable without a terminal walkthrough: what was generated, which CARLA town/weather/assets were used, what hazards moved when, what the car was expected to do, what Alpamayo/RAG saw, and which claims are proved versus blocked.

#### Why
The codebase now has many strong pieces, but a judge will not read 40 tickets. The submission needs one coherent artifact that shows the product loop, the bad-path proof, the metrics, and the honesty boundaries in a minute.

#### Before -> After
- Before: evidence is scattered across generated run folders, score reports, tickets, and raw media.
- After: one command emits a replayable pack with a first-screen summary, media gallery, exact CLI commands, score cards, asset matrix, and claim boundaries.

#### Touch
- `src/driverx/pipeline/excellence_demo_pack.py` new pack builder.
- `src/driverx/scenarios/studio_product_excellence_cli.py` new CLI registration.
- `src/driverx/scenarios/studio_product_cli.py` register commands.
- `src/driverx/evaluation/judge_replayability_score.py` new score.
- `tests/test_excellence_demo_pack.py` new tests.
- `tests/test_oodrive_cli.py` command registration.
- `README.md`, `docs/HISTORY.md`, and final submission references after a passing pack exists.

#### Inspect
- `src/driverx/pipeline/submission_story_pack.py`
- `src/driverx/pipeline/environment_demo_pack.py`
- `src/driverx/pipeline/reasoning_evidence_panel.py`
- `src/driverx/pipeline/scenario_ancestry_cards.py`
- `src/driverx/evaluation/submission_readiness_score.py`
- `src/driverx/evaluation/hero_demo_score.py`

#### Signature Delta
- `build_excellence_demo_pack(inputs: ExcellenceDemoPackInputs, output_dir: Path) -> ExcellenceDemoPack`
- `score_judge_replayability(pack_path: Path, threshold: float = 90.0) -> JudgeReplayabilityScoreReport`
- `run_studio_excellence_demo_pack(...): StudioCommandResult`

#### Type Sketch
```python
ExcellenceDemoPack = {
  "schema_version": "oodrive.excellence_demo_pack.v1",
  "headline": str,
  "commands": list[str],
  "media": [{"path": str, "kind": "image|video|html", "proof_level": "live_carla|local_contract|blocked"}],
  "metrics": [{"name": str, "value": float, "threshold": float, "status": str}],
  "claim_matrix": [{"claim": str, "value": bool | str, "proof": str}],
  "cases": [{"case_id": str, "task": str, "hazards": list[str], "expected_response": list[str]}],
  "asset_status": [{"asset": str, "status": "stock_proxy|custom_registered|blocked"}],
  "next_steps": list[str]
}
```

#### Typed Flow Example
TASK-166 suite + TASK-167 live contact sheet + TASK-171 choreography manifest + TASK-172 video manifest + TASK-170 asset status -> `oodrive excellence-demo-pack` -> `index.html`, `pack.json`, media gallery, score cards -> `score-judge-replayability` returns `>=90`.

#### Execution Steps
1. Define pack input schema and resolver that accepts optional/missing artifacts without crashing.
2. Build a compact HTML gallery with first-screen story, commands, metrics, media, claim matrix, and replay instructions.
3. Add JSON output for auditability and downstream scoring.
4. Add `judge_replayability_score` with components for media proof, CLI replayability, metric breadth, claim honesty, scenario specificity, and asset status clarity.
5. Add tests for complete pack, missing live media blocker, claim honesty, and CLI registration.
6. Generate a pack from the best local/live artifacts.
7. Update README/final references only after the score passes.

#### Recommendation
Package only after TASK-172 has at least three live CARLA bad-path case videos. A pack built before that is useful as a local preview but should not be promoted as the final judge artifact.

#### Options Considered
- A slide deck: faster for judges, but weaker as a replayable engineering artifact.
- README-only submission: too diffuse for video/media-heavy proof.
- HTML/JSON demo pack: recommended because it is inspectable, replayable, and can embed local media plus exact commands.

#### Blast Radius
Adds packaging/evaluation surfaces and documentation references. It should not mutate scenario generation, CARLA execution, or scoring thresholds for existing tickets.

#### Risks
- Pack can become a pretty wrapper around weak proof; the score must block missing live media and missing command provenance.
- Too much information can be unreadable; first screen must prioritize three bad-path cases, the product loop, and honest claims.
- Asset status may still be blocked; the matrix must make that a visible next step rather than hiding it.

### Acceptance Criteria
- [ ] AC-1: `oodrive excellence-demo-pack` consumes suite, snapshots, choreography, asset, and video artifacts.
- [ ] AC-2: Pack includes first-screen story, exact commands, media gallery, metrics, and claim matrix.
- [ ] AC-3: Pack labels open-loop reasoning, local/fake proof, live-CARLA proof, and custom-asset blockers distinctly.
- [ ] AC-4: `judge_replayability_score >= 90`.

### Verification
- `PYTHONPATH=src python3 -m oodrive excellence-demo-pack ...`
- `PYTHONPATH=src python3 -m oodrive score-judge-replayability --pack <...> --metric-only`
- `bash scripts/pre_push_check.sh`

### Evidence
- Demo pack HTML/JSON
- Score report
- Media links
- Review artifact
