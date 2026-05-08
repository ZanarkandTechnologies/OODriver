# TASK-169: Judge Commentary And Quote Layer For CARLA Suite

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-166, TASK-167, TASK-168
- location: `src/driverx/pipeline`, `src/driverx/scenarios`, `docs`, `artifacts/runs`, `tests`
- enter when: the suite has visual or video artifacts and the final demo needs clear commentary explaining what OODrive is doing and what it is not claiming.
- leave when: OODrive can generate a concise commentary/quote pack from existing docs, claim boundaries, run manifests, and scenario evidence for use in videos, captions, and submission write-up.
- blockers: final video assembly depends on TASK-168; commentary pack can be built with snapshots only.
- spawned follow-ups: final 1-5 minute submission video/deck refresh.
- complexity: S
- assignee: generalPurpose

### Description
Extract the best existing phrasing from README/docs/tickets and turn it into judge-visible commentary: what the scenario is, why it is OOD/minimal-shot, what entered or blocked the path, what behavior is expected, and what claim boundary applies.

### Goal
Stop the demo from feeling like unexplained simulator footage. Every screenshot/video segment should have one crisp explanation and one honest claim label.

### Acceptance Criteria
- [ ] AC-1: A command or helper builds `carla_suite_commentary.json` and `.md` from suite/snapshot/video artifacts.
- [ ] AC-2: Each case gets a short title, one-sentence scenario explanation, expected safe behavior, hazard labels, and claim-boundary text.
- [ ] AC-3: The pack includes reusable “quote” lines from existing docs such as OODrive’s existing-map composition boundary, open-loop Alpamayo boundary, and minimal-shot motivation.
- [ ] AC-4: The commentary explicitly distinguishes static objects, moving objects, background traffic/pedestrians, and scripted versus model-driven control.
- [ ] AC-5: Tests prevent closed-loop or arbitrary-world-generation overclaims.

### Agent Contract
- Open: `docs/prd.md`, `README.md`, `docs/MEMORY.md`, `tickets/TASK-165/ticket.md`, suite manifests from TASK-166/167/168
- Test hook: `PYTHONPATH=src python3 -m unittest tests.test_carla_suite_commentary tests.test_oodrive_cli`
- Stabilize: no invented claims; quote/commentary must point back to source artifacts or durable docs.
- Inspect: commentary JSON/Markdown, source doc references, per-case captions.
- QA cookbook: build commentary from a fake suite and verify overclaim guards.
- Expected artifacts: `carla_suite_commentary.json`, `carla_suite_commentary.md`, optional `captions.srt`.

### Plan

#### Change
Add a small commentary generator for the suite evidence.

#### Why
The user wants “comment whatever quote we have written so far,” and judges need captions that explain the product contribution quickly.

#### Before -> After
- Before: artifacts require repo context to understand.
- After: each case has a caption-ready explanation and claim boundary.

#### Touch
- `src/driverx/pipeline/carla_suite_commentary.py` (new)
- `src/driverx/scenarios/studio_product_carla_composer_cli.py`
- `src/driverx/scenarios/studio_product_carla_composer_runtime.py`
- `tests/test_carla_suite_commentary.py` (new)

#### Signature Delta
- `build_carla_suite_commentary(suite_manifest_path: Path, snapshot_manifest_path: Path | None, video_manifest_path: Path | None) -> dict`
- `run_studio_carla_suite_commentary(...) -> StudioCommandResult`

#### Type Sketch
```python
CaseCommentary = {
  "case_id": str,
  "title": str,
  "caption": str,
  "expected_behavior": str,
  "hazard_labels": list[str],
  "claim_label": str,
  "source_refs": list[str]
}
```

#### Typed Flow Example
Suite case + snapshot record + MEM-0047 -> caption: “Existing CARLA Town05, flooded-surface preset, low obstacle and cut-in actor; OODrive composes the scenario and records simulator evidence, not a custom Unreal map.”

#### Execution Steps
1. Define approved quote snippets with source refs.
2. Parse suite/snapshot/video manifests.
3. Generate per-case commentary.
4. Add overclaim guard tests.
5. Register CLI command.
6. Update docs and final handoff path.

#### Recommendation
Keep commentary generated from artifacts, not manually written per video, so the demo stays reproducible.

#### Options Considered
- Hand-write narration only: faster but drifts from artifacts.
- Artifact-derived commentary: recommended; auditable and reusable.
- Full slide-deck generator: later, after media is locked.

#### Blast Radius
New pipeline helper and command only.

#### Risks
- Quotes can become stale; source refs and tests should catch claim drift.

### Verification
- `PYTHONPATH=src python3 -m oodrive carla-suite-commentary --suite-manifest <...>`
- `PYTHONPATH=src python3 -m unittest tests.test_carla_suite_commentary tests.test_oodrive_cli`
- `bash scripts/pre_push_check.sh`

### Evidence
- Commentary JSON/Markdown
- Source refs
- Overclaim guard test output
- Planning review: `tickets/TASK-166/artifacts/review/task166-169-plan-review.json`
