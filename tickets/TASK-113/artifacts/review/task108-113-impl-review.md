# Review: TASK-108 Through TASK-113 Implementation Batch

Reviewed at: 2026-05-07 16:36 +0800

## Verdict

- Verdict: `pass`
- Overall score: `4.0 / 5.0`
- Threshold: `4.0`
- Rerun required: `false`

## Scope

- Tickets: TASK-108, TASK-109, TASK-110, TASK-111, TASK-112, TASK-113
- Code: `driverx.workbench`, `driverx.perception`, agentic scenario loop,
  video timewarp, reasoning overlay, V8 final submission pack, CLI extensions
- Evidence: TASK-108 through TASK-113 artifacts, final V8 demo video metadata,
  full pre-push gate
- Docs: `README.md`, `docs/HISTORY.md`, `docs/test-audit.md`, `blockers.md`

## Rubric Scores

| Rubric | Score | Pass | Notes |
| --- | ---: | --- | --- |
| code-quality | 4.0 | yes | New modules are additive and feature-owned. The largest caveat is that video/pipeline code necessarily shells out to ffmpeg, but failure paths are explicit. |
| evidence-quality | 4.1 | yes | Each major claim maps to JSON/Markdown artifacts and the full gate passes. Video files are ignored and referenced, not tracked. |
| integration-readiness | 4.0 | yes | CLI commands are registered, tests cover each new seam, and claim boundaries prevent closed-loop/realtime overclaiming. |
| video-quality | 3.7 | yes | The overlay finally makes risk/RAG/reasoning visible. Base CARLA footage remains visually rough, but the packet labels it as time-warped offline evidence. |
| user-intent-satisfaction | 4.1 | yes | The batch moves from setup tickets to the actual product/research contribution: scenario generation, risk explanation, RAG/VLA reasoning, and curation. |

## Findings

No blocking findings remain.

Resolved during review:

- `claim inflation / stale boundary`: V8 initially inherited
  `fast_ffmpeg_no_reasoning_overlay=true` from an older V7 boundary even though
  TASK-111 added reasoning overlays. The V8 claim-boundary merger now filters
  that stale boundary and the pack was regenerated.

## Evidence Checked

- `bash scripts/pre_push_check.sh` passed: `388` tests, `3` skips.
- V8 pack status:
  `tickets/TASK-113/artifacts/final-submission-pack-v8/final_submission_pack_v8.json`
  -> `submission_ready_with_claim_boundaries`.
- Reasoning overlay:
  `tickets/TASK-111/artifacts/reasoning-overlay-v1/reasoning_overlay_video.json`
  -> `status=passed`, `event_count=10`, `frame_count=420`.
- Timewarp:
  `tickets/TASK-112/artifacts/timewarp-v1/video_timewarp.json`
  -> `84.0s` source to `28.0s` presentation clip.
- Final paper demo video:
  `artifacts/exported/final_sota_demo_v8.mp4` -> `76.0s`, ignored by git.
- Test audit:
  `docs/test-audit.md` -> no exact duplicate test bodies found.

## Caveats

- Fresh longer CARLA source capture was not attempted because local CARLA port
  `127.0.0.1:2000` refused connection. The blocker is logged in `blockers.md`.
- The risk timeline uses simulator ground-truth tracks from the best available
  local live motorcycle-filtering capture because the TASK-102 evidence JSON
  references a track path that is not present locally.
- Alpamayo is still sampled open-loop reasoning and trajectory intent; there is
  no closed-loop VLA steering claim.
