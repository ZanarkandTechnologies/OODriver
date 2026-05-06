# TASK-077: Submission Demo Pack V3 And Final Storyboard

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-072, TASK-073, TASK-074, TASK-075
- location: `src/driverx/pipeline`, `README.md`, `ARCHITECTURE.md`, docs,
  `tickets/TASK-077/artifacts`
- enter when: at least one long CARLA scripted OOD video or precise blocker
  exists, plus current Alpamayo reasoning evidence
- leave when: the judge-facing pack centers the final story, artifact map,
  video outline, model declarations, claim boundaries, failure case, and next
  funding step
- blockers: final pack quality depends on which live artifacts land from
  TASK-072 through TASK-075
- spawned follow-ups: final deck/video editing outside code if needed
- complexity: M

### Summary
Refresh the submission pack around the stronger final thesis: randomized CARLA
OOD scenario generation plus retrieval-guided Alpamayo open-loop reasoning
evaluation. This replaces the current "short video plus local sim" emphasis if
the long scripted video lands.

### Scope
- In scope: submission pack generator inputs, write-up draft, artifact map,
  storyboard, claim boundaries, model/data declarations, failure case, blockers,
  README/ARCHITECTURE progress patch.
- Out of scope: producing a polished narrated video file or slide deck unless
  those tools are separately requested.

### Gap Analysis
- Current state: TASK-070 pack is honest and useful, but it leads with the local
  simulator because the CARLA video is only 0.5s.
- Production expectation: final submission should lead with the strongest
  visible end-to-end artifact and show model reasoning if available.
- Missing gaps: new long video fields, Alpamayo reasoning panel, generated
  object/behavior details, and final 1-5 minute outline.
- Recommendation: update the pack generator after the evidence tickets land, not
  before.

### Plan

#### Change
Extend `build-demo-pack` to accept long OOD video evidence, generated object
spawn evidence, Alpamayo scene reasoning, and memory comparison reports.

#### Why
The final repo handoff should be readable without chat archaeology.

#### Before -> After
- Before: pack says current local route video is 0.5s and full scoring is open.
- After: pack leads with long CARLA scripted OOD video if present, then
  Alpamayo reasoning/memory comparison, while keeping stock Fail2Drive score as
  optional blocker.

#### Touch
- `src/driverx/pipeline/submission_demo_pack.py`
- `src/driverx/pipeline/submission_demo_pack_cli.py`
- `src/driverx/pipeline/submission_dossier.py`
- `README.md`, `ARCHITECTURE.md`, `docs/prd.md`, `docs/progress.md`,
  `docs/HISTORY.md`, `blockers.md`.
- `tests/test_submission_demo_pack.py`,
  `tests/test_submission_dossier.py`.

#### Inspect
- `tickets/TASK-070/artifacts/submission-pack-v2-final/submission_demo_pack.md`
- TASK-072 through TASK-075 artifact schemas after implementation.
- `docs/MEMORY.md` claim-boundary rules.

#### Signature Delta
```python
src/driverx/pipeline/submission_demo_pack.py / build_submission_demo_pack(..., ood_video_evidence_path: Path | None = None, alpamayo_scene_path: Path | None = None, generated_asset_evidence_path: Path | None = None) -> dict[str, Any]
```

#### Type Sketch
```python
SubmissionDemoPackV3 = {
  "headline_artifact": "long_carla_ood_video" | "local_ood_demo" | "partial_route_video",
  "storyboard": list[dict[str, str]],
  "live_evidence": dict[str, Any],
  "model_declarations": list[dict[str, str]],
  "claim_boundaries": list[str],
  "failure_case": dict[str, Any],
  "artifact_map": dict[str, str | None],
}
```

#### Typed Flow Example
`ood_video_evidence.json + alpamayo_ood_scene.json + alpamayo_ood_comparison.json`
-> `build-demo-pack`
-> `submission_demo_pack.md`
-> README final quickstart points to the one-command local demo and the best
CARLA/Alpamayo evidence.

#### Execution Steps
1. Add optional V3 inputs to CLI and builder.
2. Select headline artifact by strongest available proof: long CARLA video,
   then local OOD demo, then partial route video.
3. Update storyboard beats to show scenario generation, CARLA video, Alpamayo
   reasoning, memory comparison, and known failure.
4. Preserve explicit labels for open-loop Alpamayo and non-scored scripted
   CARLA demos.
5. Add tests for all input combinations and missing-artifact fallback.
6. Regenerate final pack and docs after implementation evidence exists.

#### Recommendation
Make TASK-077 the final consolidation ticket after the new evidence train. Do
not keep patching TASK-070 repeatedly.

#### Options Considered
- Edit README manually only: fast but loses testable artifact mapping.
- Generate a whole deck: useful later, but pack is the canonical repo artifact.
- Pack V3 with optional evidence inputs: durable and testable.

#### Blast Radius
- Submission narrative/report generation and docs.
- No simulator/model runtime changes.

#### Risks
- The pack can overclaim if it does not preserve boundaries; tests should assert
  open-loop/partial labels.
- Missing live evidence should degrade gracefully instead of producing empty
  sections.

### Acceptance Criteria
- [ ] AC-1: Pack V3 selects the strongest available headline artifact.
- [ ] AC-2: Pack includes long video, generated scenario/object, Alpamayo
  reasoning, memory comparison, and blockers when provided.
- [ ] AC-3: Pack keeps claim boundaries explicit for scripted CARLA, open-loop
  Alpamayo, cached replay, and missing stock Fail2Drive score.
- [ ] AC-4: README/ARCHITECTURE point to the current final artifact paths.

### Verification
- Focused:
  `PYTHONPATH=src python3 -m unittest tests.test_submission_demo_pack tests.test_submission_dossier`
- Full gate:
  `bash scripts/pre_push_check.sh`
- Review:
  run `review` before claiming final submission pack readiness.

### Autonomy Readiness
- Can implement after TASK-072 through TASK-075 produce artifacts or blockers.
- No external services required unless regenerating live evidence.

### Refs
- `MEM-0001`, `MEM-0007`, `MEM-0012`.
- TASK-070 V2 pack.

### Evidence
- Planning created 2026-05-06 18:16 +0800.
- Review: `docs/reviews/TASK-072-077-impl-plan-review.md`.
- Implementation review: `docs/reviews/TASK-072-077-implementation-review.md`.
- Build: `src/driverx/pipeline/submission_demo_pack.py`,
  `src/driverx/pipeline/submission_demo_pack_cli.py`, and
  `tests/test_submission_demo_pack.py`.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_submission_demo_pack`.
- V3 pack:
  `tickets/TASK-077/artifacts/submission-pack-v3-v2/submission_demo_pack.md`.

### Blockers
- Final live-CARLA headline waits for TASK-072 frame capture. Current V3 pack
  correctly keeps fixture video as non-live evidence and uses the local OOD
  simulator as the strongest headline artifact.
