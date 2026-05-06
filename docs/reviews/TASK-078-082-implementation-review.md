# TASK-078..TASK-082 Implementation Review

## Verdict

- work_type: `backend`, `runtime-evidence`, `video-evidence`, `docs`
- rubrics_used: `code-quality`, `evidence-quality`, `integration-readiness`,
  `video-quality`
- overall_score: `4.2`
- overall_threshold: `4.0`
- verdict: `pass`
- rerun_required: `false`
- evidence_quality: `pass`
- integration_readiness: `pass`
- traceability: `pass`
- freshness: `pass`

## Search Scope

- Tickets:
  `tickets/TASK-078/ticket.md`, `tickets/TASK-079/ticket.md`,
  `tickets/TASK-080/ticket.md`, `tickets/TASK-081/ticket.md`,
  `tickets/TASK-082/ticket.md`
- Code:
  `src/driverx/simulators/carla_ood_demo.py`,
  `src/driverx/assets/carla_mapping.py`,
  `src/driverx/assets/pipeline.py`,
  `src/driverx/policies/alpamayo_ood_package.py`,
  `src/driverx/policies/alpamayo_ood_package_cli.py`,
  `src/driverx/pipeline/submission_demo_pack.py`,
  `src/driverx/cli.py`
- Tests:
  `tests/test_carla_ood_demo.py`, `tests/test_carla_asset_mapping.py`,
  `tests/test_alpamayo_ood_package.py`, plus focused Alpamayo/evidence tests
  listed in the QA report.
- Evidence:
  `tickets/TASK-078/artifacts/task78-live-ood-capture-v3/carla_ood_demo.md`,
  `tickets/TASK-079/artifacts/task79-live-ood-video/ood_video_evidence.md`,
  `tickets/TASK-080/artifacts/task80-live-same-scene-materialized-v2/alpamayo_tensor_manifest.md`,
  `tickets/TASK-081/artifacts/task81-live-same-scene-comparison/alpamayo_ood_comparison.md`,
  `tickets/TASK-082/artifacts/submission-pack-v4-live-carlasame-v3/submission_demo_pack.md`,
  `tickets/TASK-082/artifacts/qa/TASK-078-082-qa-report.md`
- Invariants checked:
  `MEM-0007`, `MEM-0016`, `MEM-0020`, `MEM-0021`

## Findings

No blocking findings.

- low / high confidence / code-quality:
  `src/driverx/pipeline/submission_demo_pack.py` is now close to 1k lines and
  the pre-push large-file warning flags it. This is not new enough to block the
  ticket, but the next pack iteration should split storyboard narration,
  artifact-map shaping, and markdown rendering into smaller modules.
- low / high confidence / evidence-quality:
  The Alpamayo same-scene package intentionally duplicates one live ego RGB
  stream across three camera slots. The ticket, docs, and package notes disclose
  this clearly, so the evidence is acceptable for open-loop reasoning proof, but
  it must not be presented as calibrated multi-camera autonomy.

## Rubric Sections

### Code Quality

- score: `4.1`
- threshold: `4.0`
- pass: `true`
- dimension_scores:
  - modularity-reusability: `4.0`
  - bloatability: `3.7`
  - readability: `4.0`
  - boundary-clarity: `4.2`
  - error-handling: `4.2`
  - maintainability: `4.0`
- rationale:
  The OOD package builder is a focused policy-boundary module with a small CLI
  registration, tests, and explicit validation. The CARLA runner checkpoint
  path improves failure recovery after killed runs. The stock blueprint mapping
  fix is localized and documented. The main caveat is the already-large
  submission demo pack module.

### Evidence Quality

- score: `4.4`
- threshold: `4.0`
- pass: `true`
- dimension_scores:
  - sufficiency: `4.4`
  - reproducibility: `4.2`
  - traceability: `4.5`
  - consistency: `4.4`
  - inspectability: `4.2`
  - autonomy-readiness: `4.3`
- rationale:
  Every important claim maps to concrete JSON/Markdown artifacts. The QA report
  records focused tests, full pre-push output, ffprobe duration/size, and secret
  scan results. Claim boundaries are repeated in ticket docs, demo-pack output,
  and package notes.

### Integration Readiness

- score: `4.1`
- threshold: `4.0`
- pass: `true`
- dimension_scores:
  - integration-safety: `4.1`
  - contract-correctness: `4.1`
  - dependency-readiness: `4.0`
  - coupling-risk: `4.0`
  - merge-readiness: `4.2`
- rationale:
  The live CARLA path, Alpamayo remote evidence, and V4 pack are integrated
  without claiming stock Fail2Drive scoring or closed-loop VLA control. Open
  runtime blockers remain in `blockers.md` and are outside this ticket train.

### Video Quality

- score: `4.0`
- threshold: `3.5`
- pass: `true`
- dimension_scores:
  - legibility: `4.0`
  - coverage: `4.0`
  - pacing: `4.0`
  - faithfulness: `4.1`
  - verification-value: `4.1`
- rationale:
  The 24s MP4 is long enough to inspect the generated OOD setup and overlays,
  and `source_kind=live_carla` plus claim labels prevent fixture/live confusion.
  It is verification evidence for a scripted DriverX scene, not stock
  Fail2Drive score proof.

## Hard Gates

- Tests: pass.
- Pre-push gate: pass.
- Secret scan: pass for live credential values.
- Heavy artifact policy: pass; MP4 and PNG outputs are ignored by git.

## Next Action

Advance this batch. Continue next with either TASK-060 full stock Fail2Drive
score on a graphics-capable Linux CARLA host or a TASK-083-style bridge that
turns Alpamayo trajectory intent into a conservative closed-loop CARLA follower
for the scripted OOD scene.
