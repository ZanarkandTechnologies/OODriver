# TASK-041: DriverX Route Video Assembler

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-033, TASK-034, TASK-036
- location: `src/driverx/simulators`, `src/driverx/cli.py`, tests
- enter when: Fail2Drive route-video evidence is blocked by a missing external
  `tools/generate_video.py`
- leave when: DriverX can plan and optionally run an ffmpeg assembly command for
  a Fail2Drive RGB frame folder
- blockers: live assembly still needs RGB frames from a route run and `ffmpeg`
- spawned follow-ups: none
- complexity: M

## Summary

Remove the hard dependency on Fail2Drive's missing video helper by adding a
DriverX-owned route-video assembler. The assembler should be safe by default:
write a plan and blockers locally, and only invoke `ffmpeg` when explicitly
asked.

## Acceptance Criteria

- [x] RGB frame folders are scanned deterministically.
- [x] Missing folder, missing frames, and missing `ffmpeg` are reported as
  blockers.
- [x] CLI writes JSON/Markdown evidence and supports explicit live execution.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_route_video_assembly`
- `PYTHONPATH=src python3 -m driverx assemble-route-video --rgb-folder artifacts/runs/task36-suite-1b/recipes/000_generated-base-animals-0076-visual-noise-000/fail2drive_outputs/visualizations/Base_Animals_0076/rgb --output-root artifacts/runs --run-id task41-video-assembly`

## Evidence

- Code: `src/driverx/simulators/route_video_assembly.py`
- CLI: `python -m driverx assemble-route-video`
- Local report: `artifacts/runs/task41-video-assembly/route_video_assembly.md`
- Review: `tickets/TASK-041/artifacts/review/20260505T194200-review.json`

## Blockers

- Live video assembly still needs the route runner to create the RGB frame
  folder. Current evidence reports that folder as missing.
