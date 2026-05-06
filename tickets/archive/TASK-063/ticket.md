# TASK-063: Final Submission Evidence Refresh

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-059, TASK-060, TASK-061
- location: `src/driverx/pipeline`, `README.md`, `ARCHITECTURE.md`, docs,
  `tickets/TASK-063/artifacts`
- enter when: at least dataset-backed Alpamayo proof and either Town13 route
  evidence or precise Town13 failure evidence exist
- leave when: demo pack, dossier, progress, blockers, and canonical docs reflect
  the strongest current story
- blockers: none; V2 local-first refresh completed in TASK-070
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
- [x] AC-1: Demo pack includes latest PhysicalAI, Town13, and Alpamayo OOD
  evidence where available.
- [x] AC-2: README/ARCHITECTURE no longer describe already-completed work as
  active or blocked.
- [x] AC-3: Remaining blockers are short, current, and human-actionable.
- [x] AC-4: Claim boundaries explicitly separate open-loop, cached replay, and
  closed-loop control.
- [x] AC-5: Final review artifact passes evidence/integration readiness.

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
- 2026-05-06 03:34 +0800: Added cached replay evidence to the demo-pack
  contract while Town13 was still downloading. The pack now records
  `claim_boundaries`, `live_evidence.cached_replay`, and
  `artifact_map.cached_replay_path` so final docs can separate open-loop
  Alpamayo, cached replay, and future closed-loop control.
- 2026-05-06 03:34 +0800: Generated partial demo-pack evidence at
  `tickets/TASK-063/artifacts/cached-replay-demo-pack/submission_demo_pack.md`
  using the PhysicalAI shape probe, Town10 route evidence, live Alpamayo memory
  comparison, and cached replay report.
- Review: `docs/reviews/TASK-063-cached-replay-demo-pack-review.md` passed the
  partial cached-replay refresh at 4.0/5.0; final review still waits on
  TASK-060/TASK-061 live evidence.
- 2026-05-06 04:33 +0800: Final refresh is superseded and completed by
  TASK-070's local-first V2 submission pack:
  `tickets/TASK-070/artifacts/submission-pack-v2-final/submission_demo_pack.md`.
- Final review:
  `docs/reviews/TASK-068-070-local-first-submission-review.md`.

## Blockers
- None. TASK-060/TASK-069 remain separate live-runtime follow-ups.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
