# TASK-087: Submission Dossier V5 And Deck Script

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-082, TASK-084, TASK-085, TASK-086
- location: `src/driverx/pipeline`, docs, `tickets/TASK-087/artifacts`
- enter when: the next evidence train has either replay/campaign/batch proof or precise blockers
- leave when: the repo has a final submission dossier, 1-5 minute video script, slide outline, artifact checklist, and claim-boundary table
- blockers: final quality depends on which evidence tickets land; can still build from current V4 evidence
- spawned follow-ups: optional rendered PPTX/video editing
- complexity: M

### Summary

Convert the current evidence into a final submission-facing packet. This is not
the polished deck itself; it is the canonical script, slide outline, artifact
map, write-up draft, and checklist that lets the final deck/video be cut
without spelunking the repo.

### Scope

- In scope: V5 dossier builder inputs, concise final story, video narration
  script, slide outline, artifact paths, model/data declarations, blockers,
  claim boundaries, and README/progress refresh.
- Out of scope: recording narration, editing the final MP4 manually, or
  submitting external forms.

### Plan

#### Change

Extend `submission_dossier` and/or `submission_demo_pack` so the final packet
can consume reasoning pack, cached replay, campaign summary, Alpamayo batch
summary, and current blockers. Produce `submission_dossier_v5.json/md` and a
`video_script.md` with timestamped narration.

#### Why

The project now has enough evidence that the bottleneck is presentation
coherence, not setup. A canonical final packet prevents the submission from
being a loose pile of artifacts.

#### Before -> After

- Before: V4 pack is strong, but final video/deck text still needs manual
  assembly.
- After: one command writes the final story, evidence links, claim boundaries,
  and 1-5 minute script.

#### Touch

- `src/driverx/pipeline/submission_dossier.py`: add V5 evidence inputs and
  script/write-up sections.
- `src/driverx/pipeline/submission_dossier_cli.py`: add args for reasoning
  pack, campaign, Alpamayo batch, cached replay, and V4 pack.
- `src/driverx/pipeline/submission_demo_pack.py`: only if V5 should reuse pack
  sections.
- `tests/test_submission_dossier.py`, `tests/test_submission_demo_pack.py`.
- `README.md`, `ARCHITECTURE.md`, `docs/progress.md`, `docs/HISTORY.md`,
  `blockers.md`.

#### Inspect

- `tickets/TASK-082/artifacts/submission-pack-v4-live-carlasame-v3/submission_demo_pack.json`
- `src/driverx/pipeline/submission_dossier.py`
- `docs/MEMORY.md` `MEM-0001`, `MEM-0007`

#### Signature Delta

```python
src/driverx/pipeline/submission_dossier.py / build_submission_dossier(run_dir: Path, *, demo_pack_path: Path | None = None, reasoning_pack_path: Path | None = None, campaign_summary_path: Path | None = None, alpamayo_batch_path: Path | None = None, cached_replay_path: Path | None = None, blockers_path: Path | None = None, progress_path: Path | None = None) -> dict[str, Any]
```

#### Type Sketch

```python
SubmissionDossierV5 = {
  "title": str,
  "thesis": str,
  "artifact_checklist": list[ArtifactRef],
  "video_script": list[{"time": str, "visual": str, "narration": str}],
  "slide_outline": list[{"title": str, "proof": str, "artifact": str}],
  "model_declarations": list[dict],
  "claim_boundaries": list[str],
  "open_blockers": list[str],
  "two_page_writeup": dict[str, str],
}
```

#### Typed Flow Example

`submission_demo_pack.json + reasoning_pack.json + campaign_summary.json + alpamayo_batch_summary.json + blockers.md`
-> `build-submission-dossier`
-> `submission_dossier_v5.md + video_script.md`
-> final deck/video editing uses those surfaces.

#### Execution Steps

1. Add V5 optional input fields and artifact normalization helpers.
2. Build a stable artifact checklist with exists/ignored/heavy labels.
3. Generate timestamped narration script from current best evidence.
4. Generate slide outline and two-page write-up draft.
5. Add tests for missing optional artifacts and current V4-only fallback.
6. Regenerate V5 dossier and update README/progress.

#### Recommendation

Keep the final packet Markdown/JSON-first. A rendered PPTX can be a follow-up,
but the repo needs a durable source of truth first.

#### Options Considered

- Hand-write final script in README: quick but brittle.
- Generate PPTX now: useful later, but risky before evidence stops changing.
- Dossier/script builder: best; testable and easy to refresh.

#### Blast Radius

- Submission/report generation only.
- No simulator/model behavior changes.

#### Risks

- The final story may overclaim closed-loop autonomy; claim-boundary table is a
  required output.
- Artifact paths can go stale; tests should use fixture evidence and current
  artifact existence checks.

### Acceptance Criteria

- [ ] AC-1: Dossier command writes JSON/Markdown plus `video_script.md`.
- [ ] AC-2: Artifact checklist includes live video, reasoning pack, Alpamayo comparison, replay/campaign/batch evidence when available, and blockers.
- [ ] AC-3: Claim-boundary table distinguishes scripted CARLA, cached replay, open-loop Alpamayo, stock Fail2Drive partial score, and future closed-loop work.
- [ ] AC-4: README/progress point at the V5 packet as the final source of truth.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_submission_dossier tests.test_submission_demo_pack`
- `PYTHONPATH=src python3 -m driverx build-submission-dossier --demo-pack tickets/TASK-082/artifacts/submission-pack-v4-live-carlasame-v3/submission_demo_pack.json --blockers blockers.md --progress docs/progress.md --run-id submission-dossier-v5`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Fully local.
- No GPU/CARLA needed unless refreshing upstream evidence first.

### Evidence

- Planned 2026-05-06 as the final consolidation ticket after current evidence
  train.
- Plan review: `docs/reviews/TASK-083-088-impl-plan-review.md`.

### Blockers

- None for V4-based dossier. Richer V5 quality improves if TASK-083 through
  TASK-086 land first.
