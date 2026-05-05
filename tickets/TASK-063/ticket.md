# TASK-063: Final Submission Evidence Refresh

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-059, TASK-060, TASK-061
- location: `src/driverx/pipeline`, `README.md`, `ARCHITECTURE.md`, docs,
  `tickets/TASK-063/artifacts`
- enter when: at least dataset-backed Alpamayo proof and either Town13 route
  evidence or precise Town13 failure evidence exist
- leave when: demo pack, dossier, progress, blockers, and canonical docs reflect
  the strongest current story
- blockers: waits on the preceding evidence tickets for final inputs
- spawned follow-ups: final video/deck assembly outside code if needed
- complexity: S

### Description
The repo story has moved faster than the canonical docs. This ticket refreshes
the judge-facing evidence pack after the Town13 and PhysicalAI unblocks.

### Goal
Make the repository handoff clear enough that the final video/deck can be cut
from current artifacts without spelunking chat history.

## Plan

### Change
Regenerate the demo pack and submission dossier using the newest route,
Alpamayo, and blocker evidence; patch stale docs that still describe old active
tickets or setup blockers.

### Why
The final deliverable should lead with the current strongest proof, not old
setup state.

### Before -> After
- Before: `README.md` and `ARCHITECTURE.md` still contain stale language about
  the Alpamayo adapter being blocked.
- After: docs and demo pack tell the current story: scenario forge, Town13 or
  precise Town13 status, PhysicalAI-backed Alpamayo proof, route-aligned
  comparison if available, and known limitations.

### Touch
- `src/driverx/pipeline/submission_demo_pack.py`: small fields only if new
  evidence needs them.
- `src/driverx/pipeline/submission_dossier.py`: include Town13 and
  PhysicalAI-backed Alpamayo evidence.
- `README.md`, `ARCHITECTURE.md`, `docs/prd.md`, `docs/progress.md`,
  `docs/HISTORY.md`, `blockers.md`.
- `tests/test_submission_demo_pack.py`, `tests/test_submission_dossier.py`.

### Inspect
- `tickets/archive/TASK-057/artifacts/refreshed-demo-pack/`
- TASK-059/TASK-060/TASK-061 artifacts once available.
- `docs/MEMORY.md` for durable constraints on artifacts and claim wording.

### Signature Delta
Likely no new signature; optional additions:

```python
src/driverx/pipeline/submission_demo_pack.py / build_submission_demo_pack(..., town13_route_evidence_path: Path | None = None, physicalai_probe_path: Path | None = None) -> dict[str, Any]
```

### Type Sketch
```python
FinalEvidencePack = {
  "town13_route": RouteEvidence | None,
  "physicalai_alpamayo_probe": AlpamayoShapeProbe | None,
  "route_aligned_alpamayo_comparison": AlpamayoOODComparison | None,
  "remaining_blockers": list[str],
  "claim_boundaries": ["open_loop", "cached_replay", "not real-time closed-loop"],
}
```

### Typed Flow Example
TASK-059 report + TASK-060 route evidence + TASK-061 comparison
-> `build-demo-pack`
-> `build-submission-dossier`
-> README/ARCHITECTURE progress patch
-> final review artifact.

### Execution Steps
1. Gather newest evidence paths and classify which claims are now safe.
2. Regenerate demo pack/dossier.
3. Patch stale canonical docs and blocker/progress ledgers.
4. Run tests and review.
5. Archive completed tickets and commit the final evidence refresh.

### Recommendation
Run this after the evidence tickets, not in parallel. Its value is coherence and
claim discipline, so it should consume final facts.

### Options Considered
- Patch docs immediately: useful but risks churn as Town13/PhysicalAI results
  change.
- Regenerate final pack after evidence: best final-deliverable path.
- Skip docs and rely on artifacts: too hard for judges/reviewers to follow.

### Blast Radius
Docs and report generators only. No new simulator/model runtime behavior.

### Risks
- Claim inflation: docs must not imply real-time closed-loop Alpamayo unless
  TASK-062 actually proves cached replay and labels it correctly.
- Stale paths: all new evidence should point at active ticket paths until
  archived, then regenerate archive-path reports during closeout.

## Acceptance Criteria
- [ ] AC-1: Demo pack includes latest PhysicalAI, Town13, and Alpamayo OOD
  evidence where available.
- [ ] AC-2: README/ARCHITECTURE no longer describe already-completed work as
  active or blocked.
- [ ] AC-3: Remaining blockers are short, current, and human-actionable.
- [ ] AC-4: Claim boundaries explicitly separate open-loop, cached replay, and
  closed-loop control.
- [ ] AC-5: Final review artifact passes evidence/integration readiness.

## Verification
- Unit:
  `PYTHONPATH=src python3 -m unittest tests.test_submission_demo_pack tests.test_submission_dossier`
- Gate: `bash scripts/pre_push_check.sh`
- Review:
  `docs/reviews/TASK-063-final-evidence-review.md`

## Autonomy Readiness
- Fully autonomous after predecessor evidence exists.
- Human gate only for final editorial preference on the video/deck, not for repo
  evidence generation.

## Evidence
- Pending predecessor tickets.

## Blockers
- Waits on TASK-059/TASK-060/TASK-061 evidence.
