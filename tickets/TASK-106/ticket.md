# TASK-106: Final SoTA Submission Pack V7

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-101, TASK-102, TASK-103, TASK-104, TASK-105
- location: `src/driverx/pipeline/submission_demo_pack.py`, `src/driverx/pipeline/submission_dossier.py`, `src/driverx/pipeline/submission_scenario_browser.py`, `tickets/TASK-106/artifacts`
- enter when: the final scenario matrix, high-fidelity video evidence, scenario studio batch, Alpamayo/RAG batch, and Fail2Drive extension report are available or precisely blocked
- leave when: final browser, dossier, video script, 2-page write-up draft, and submission artifact map are regenerated around the strongest evidence
- blockers: depends on upstream ticket evidence; can still ship with explicit blocked rows
- spawned follow-ups: none before submission
- complexity: M
- assignee: generalPurpose

### Summary

Package the actual submission. This ticket turns the evidence into a judge-facing
artifact: what we built, why it is minimal-shot, how randomized generation
works, how Alpamayo/RAG reacts, what failed, and what the prize money unlocks.

### Scope

- In scope: final scenario browser, final dossier, 1-5 minute video script,
  two-page write-up draft, model/data declarations, artifact map, blocker/future
  work section, and claim-boundary audit.
- Out of scope: new simulator/model features.

### Plan

#### Change

Regenerate V7 submission pack from the final evidence train.

#### Why

The project has enough pieces to be interesting, but judges need a clean story,
not a filesystem scavenger hunt.

#### Before -> After

- Before: V6 browser centers the first RunPod hero and early Alpamayo proof.
- After: V7 centers scenario generation, quality-gated CARLA evidence,
  Alpamayo+RAG comparison, Fail2Drive extension, and honest limitations.

#### Touch

- `src/driverx/pipeline/submission_demo_pack.py`
- `src/driverx/pipeline/submission_dossier.py`
- `src/driverx/pipeline/submission_scenario_browser.py`
- `tickets/TASK-106/artifacts/final_submission_pack_v7/`
- `README.md` if the final commands/mission need one last update.

#### Inspect

- TASK-101 matrix.
- TASK-102 video/evidence.
- TASK-103 studio batch.
- TASK-104 Alpamayo/RAG batch.
- TASK-105 Fail2Drive extension report.
- TASK-100 model declaration and latency/VRAM facts.

#### Signature Delta

```python
build_demo_pack(...,
  eval_matrix_path: Path | None,
  scenario_studio_path: Path | None,
  alpamayo_rag_batch_path: Path | None,
  fail2drive_extension_path: Path | None,
): dict[str, Any]

build_submission_scenario_browser(...): dict[str, Any]
```

#### Type Sketch

```python
SubmissionEvidenceRow = {
  "claim": str,
  "artifact": str | None,
  "status": "proved" | "partial" | "blocked",
  "why_it_matters": str,
  "claim_boundary": str,
}
```

#### Typed Flow Example

`TASK-101 matrix + TASK-104 batch + TASK-102 video`
-> `SubmissionEvidenceRow[]`
-> `scenario_browser.html`
-> `submission_dossier_v7.md`
-> `video_script_v7.md`
-> `writeup_2page_draft.md`.

#### Execution Steps

1. Collect upstream evidence paths and classify each claim as proved/partial/
   blocked.
2. Regenerate scenario browser with hero/support/failure sections.
3. Regenerate dossier and video script around the final thesis.
4. Draft the two-page write-up: motivation, architecture, what worked, what did
   not, prize-money next step.
5. Audit model/data declarations and non-commercial license notes.
6. Run QA/review and final pre-push gate.

#### Recommendation

Ship V7 even if one upstream ticket blocks. A clean, honest pack with one
excellent hero and several partial proofs is better than waiting for a perfect
closed-loop VLA stack.

#### Options Considered

- Keep adding features until deadline: risky and incoherent.
- Submit only the current V6 browser: safe but undersells the contribution.
- Recommended: freeze features after TASK-104/TASK-105, then package hard.

#### Blast Radius

Medium. Submission builders are large files and historically easy to overclaim;
review must challenge evidence status labels.

#### Risks

- Claim inflation. Mitigate with explicit `proved/partial/blocked` rows and
  review against MEM-0024/MEM-0028.

### Gap Analysis

Current artifacts are credible but scattered. A production submission needs a
single path through the evidence and a short video/deck narrative. This ticket
creates that final surface.

### Acceptance Criteria

- [ ] AC-1: V7 browser links hero video, Alpamayo/RAG evidence, scenario studio
  batch, and Fail2Drive extension report.
- [ ] AC-2: Dossier includes model declarations, hardware/latency facts, and
  no-fine-tuning claim.
- [ ] AC-3: Video script fits 1-5 minutes and includes at least one understood
  failure case.
- [ ] AC-4: Every major claim is labeled proved, partial, or blocked.

### Verification

- Focused submission-pack tests.
- Link-resolution test for browser artifacts.
- Secret/heavy-artifact scan.
- `bash scripts/pre_push_check.sh`
- Review with evidence-quality and demo/video-quality rubrics.

### Autonomy Readiness

- Inputs available after TASK-101 through TASK-105.
- Human gates: final subjective video/deck preference only; not needed to build
  the pack.
- Compute: local only.
- Stop condition: final pack generated and reviewed.

### Evidence

- `tickets/TASK-106/artifacts/final_submission_pack_v7/scenario_browser.html`
- `tickets/TASK-106/artifacts/final_submission_pack_v7/submission_dossier_v7.md`
- `tickets/TASK-106/artifacts/final_submission_pack_v7/video_script_v7.md`
- `tickets/TASK-106/artifacts/final_submission_pack_v7/writeup_2page_draft.md`

### Blockers

- Upstream evidence gaps become labeled `partial` or `blocked`; they should not
  stop packaging.
