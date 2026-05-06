# TASK-107: Final Demo Video And Submission Upload Packet

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-102, TASK-103, TASK-104, TASK-105, TASK-106
- location: `tickets/TASK-107/artifacts`, `artifacts/exported`, `docs`
- enter when: TASK-106 final pack is `submission_ready` and the selected TASK-102 MP4 is locally exported
- leave when: a 1-5 minute final demo video/deck packet exists with the simulator contribution, Alpamayo reasoning evidence, one understood failure case, and upload checklist
- blockers: none for local assembly; external hosting/upload remains a human-side final step
- spawned follow-ups: none before submission unless upload hosting becomes explicit
- complexity: M

### Summary

Turn the now-ready evidence pack into the final judge-facing presentation
surface. TASK-106 proves the evidence matrix; this ticket creates the crisp
demo packet humans can actually submit: final video/deck assembly inputs,
voiceover/script timing, exported media manifest, model declarations, and upload
checklist.

### Scope

- In scope: final storyboard, video assembly plan, optional ffmpeg/remotion
  assembly from the 84s CARLA MP4 and static evidence cards, final artifact
  manifest, upload checklist, and one-page "what to submit" handoff.
- Out of scope: new simulator features, new Alpamayo runs, official Fail2Drive
  scoring, public hosting credentials, and committing generated MP4s.

### Goal

Make the final submission feel like a coherent product/research demo rather
than a pile of logs.

### Acceptance Criteria

- [x] AC-1: Final demo packet references the local exported hero MP4 at
  `artifacts/exported/task102_high_fidelity_hero_v6_full.mp4`.
- [x] AC-2: The 1-5 minute script/storyboard includes Scenario Studio,
  generated CARLA OOD evidence, Alpamayo+memory reasoning, Fail2Drive linkage,
  and one understood failure case.
- [x] AC-3: A final upload checklist names exactly which repo docs, artifacts,
  model declarations, and video/deck files to include.
- [x] AC-4: If a rendered final MP4 is produced, it stays under ignored
  `artifacts/exported/` and is referenced from a tracked manifest only.

### Build Plan

1. Read the TASK-106 final pack and current video script.
2. Create a compact storyboard with scene timing and exact evidence references.
3. Produce an upload packet manifest with local paths and claim boundaries.
4. If ffmpeg inputs are sufficient, render a simple final demo MP4 from title
   cards plus the exported CARLA clip; otherwise leave a render-ready manifest.
5. Run tests/JSON validation and review the packet against evidence and video
   quality rubrics.

### Evidence

- `tickets/TASK-107/artifacts/final_demo_packet.md`
- `tickets/TASK-107/artifacts/final_demo_manifest.json`
- `tickets/TASK-107/artifacts/review/task107-final-demo-review.md`
- `scripts/build_final_demo_video.sh`
- Draft rendered MP4 (ignored): `artifacts/exported/final_sota_demo_draft_v1.mp4`
- Verification: `ffprobe` duration `124.0s`, size `21126921` bytes.

### Blockers

- None locally. Public hosting/upload is intentionally left to the human-facing
  submission step.
