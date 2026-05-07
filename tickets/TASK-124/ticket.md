# TASK-124: Flagship OODrive Final Evidence Pack

## Status
- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-120, TASK-121, TASK-122, TASK-123
- location: `src/driverx/pipeline`, `tickets/TASK-124/artifacts`, `artifacts/exported`
- enter when: flagship capture, Alpamayo predictions, and replay evidence exist
- leave when: final demo video, write-up, browser pack, and artifact map foreground the flagship OODrive contribution
- blockers: waiting for TASK-121 through TASK-123 evidence
- spawned follow-ups: none
- complexity: M

### Summary

Refresh the final submission around one high-quality, realistic flagship OOD
scenario. The final artifact should show the scenario generator, CARLA run,
RAG retrieval, Alpamayo reasoning, planned path, actual path, risk timeline, and
claim boundaries in one coherent story.

### Plan

#### Change

Build a V9 final pack from TASK-120 through TASK-123 artifacts and replace the
current broad V8 emphasis with a flagship case-study emphasis.

#### Acceptance Criteria

- [ ] AC-1: Final video is 1-5 minutes and uses the flagship scenario.
- [ ] AC-2: Overlay shows risk, retrieved memory, model reasoning, planned path,
  and actual path.
- [ ] AC-3: Dossier explains what is novel and what remains open.
- [ ] AC-4: Claim boundaries distinguish closed-loop CARLA baseline,
  time-warped Alpamayo replay, and no real-time VLA control unless proved.

### Verification

- Rendered local MP4 exists and has duration metadata.
- Final pack JSON/Markdown/HTML generated.
- Review and `bash scripts/pre_push_check.sh`.

### Blockers

- TASK-121 through TASK-123 evidence.
