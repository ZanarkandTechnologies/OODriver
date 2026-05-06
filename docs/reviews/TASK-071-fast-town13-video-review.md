# TASK-071 Review: Fast Town13 Route Video Evidence Runner

## Verdict

- overall_score: 4.1 / 5.0
- threshold: 4.0
- verdict: pass
- rerun_required: false
- reviewed_at: 2026-05-06 11:40 +0800

## Scope Reviewed

- `tickets/TASK-071/ticket.md`
- `src/driverx/simulators/route_video_assembly.py`
- `src/driverx/simulators/fail2drive_route_runner.py`
- `src/driverx/simulators/fail2drive_route_runner_cli.py`
- `src/driverx/pipeline/route_evidence.py`
- `src/driverx/pipeline/submission_demo_pack.py`
- `tests/test_route_video_assembly.py`
- `tests/test_fail2drive_route_runner.py`
- `tests/test_submission_demo_pack.py`
- `tickets/TASK-071/artifacts/town13-early-route-evidence/run_evidence.md`
- `tickets/TASK-070/artifacts/submission-pack-v2-final/submission_demo_pack.md`

## Rubric Scores

| family | score | threshold | pass |
|---|---:|---:|---|
| code-quality | 4.1 | 4.0 | yes |
| integration-readiness | 4.0 | 4.0 | yes |
| evidence-quality | 4.2 | 4.0 | yes |
| video-quality | 3.6 | 3.5 | yes |

## Findings

- No blocking findings.
- Minor caveat: the video is intentionally short at 0.5s / 5 frames. It is enough to prove fresh Town13 CARLA/F2D visual output, but not enough to claim route behavior quality or full route completion. The ticket and submission pack now label that boundary explicitly.

## Evidence Checked

- Focused tests passed:
  `PYTHONPATH=src python3 -m unittest tests.test_route_video_assembly tests.test_fail2drive_route_runner tests.test_route_evidence tests.test_submission_demo_pack`
- Full gate passed:
  `bash scripts/pre_push_check.sh` with 292 tests.
- MP4 probe:
  `ffprobe` reports H.264, 1920x1080, 10fps, 5 frames, 0.5s, 507730 bytes.
- Visual spot-check:
  first frame shows a CARLA third-person route view in Town13-style residential road geometry.
- Artifact policy:
  `.mp4` and RGB frame directories remain ignored; tracked artifacts are compact JSON/Markdown/log evidence only.

## Rationale

The implementation is localized: frame watching lives with route-video assembly,
the Fail2Drive runner owns process streaming and early-stop behavior, and route
evidence suppresses stale Docker-ffmpeg blockers only when a separate video
artifact exists. The CLI flags are explicit and preserve existing route-run
defaults.

The main risk is not code correctness but interpretation. TASK-071 produces
partial video evidence, not a full scored route. That boundary is now repeated
in the ticket, blocker ledger, progress doc, route evidence, and regenerated
demo pack.

## Next Action

Advance TASK-071. Keep TASK-060 open for the long-run scored route attempt and
TASK-069/TASK-061 open for route-aligned Alpamayo capture once a route can run
long enough.
