# TASK-107 Final Demo Review

- work_type: `demo-quality`, `video-quality`, `evidence-quality`
- verdict: `pass`
- overall_score: `4.0 / 5.0`
- threshold: `4.0`
- rerun_required: `false`
- evidence_quality: `pass`
- integration_readiness: `pass`
- traceability: `pass`
- freshness: `pass`

## Search Scope

- Ticket: `tickets/TASK-107/ticket.md`
- Builder: `scripts/build_final_demo_video.sh`
- Manifest: `tickets/TASK-107/artifacts/final_demo_manifest.json`
- Packet: `tickets/TASK-107/artifacts/final_demo_packet.md`
- Inputs: `artifacts/exported/task102_high_fidelity_hero_v6_full.mp4`
- Output: `artifacts/exported/final_sota_demo_draft_v1.mp4`

## Findings

No blocking findings.

The draft video is intentionally simple, but it satisfies the submission-safety
goal: it is 124 seconds, combines explanatory cards with the full 84s CARLA
hero clip, and names the open-loop/official-score limitations instead of hiding
them. The generated MP4 remains under ignored `artifacts/exported/`, while the
tracked manifest records path, duration, size, beats, and claim boundaries.

## Score Rationale

This is a strong final-submission draft, not a polished cinematic cut. It passes
because it is reproducible, short enough for the 1-5 minute requirement, and
grounded in the current evidence pack. It is not a 5.0 because it lacks
voiceover, model reasoning screenshots, and a final public upload URL.

## Verification

- `scripts/build_final_demo_video.sh`
- `ffprobe`: duration `124.0s`, size `21126921` bytes
- `python3 -m json.tool tickets/TASK-107/artifacts/final_demo_manifest.json`
- `bash -n scripts/build_final_demo_video.sh`
- `bash scripts/pre_push_check.sh`

## Next Action

Use `artifacts/exported/final_sota_demo_draft_v1.mp4` as the first final demo
cut, then optionally replace the title cards with narration/slide captures if
time allows.
