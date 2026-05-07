# Review: Scenario Generator CLI Ticket Plan

Reviewed at: 2026-05-07 17:12 +0800

## Scope

- `docs/specs/scenario-generator-cli-v1.md`
- `tickets/TASK-114/ticket.md`
- `tickets/TASK-115/ticket.md`
- `tickets/TASK-116/ticket.md`
- `tickets/TASK-117/ticket.md`
- `tickets/TASK-118/ticket.md`

## Rubrics

### Spec Contract

- Score: 4.2 / 5.0
- Threshold: 4.0
- Verdict: pass
- Notes:
  - The ticket batch maps directly to the PRD's scenario generation,
    curation, closed-loop run, Alpamayo evaluation, replay, and export jobs.
  - The CLI-first decision is explicit and does not discard the future app or
    Codex skill wrapper.
  - Each ticket has observable artifacts and command-level proof.

### Implementation Plan

- Score: 4.1 / 5.0
- Threshold: 4.0
- Verdict: pass
- Notes:
  - File maps and signature deltas are concrete enough for build handoff.
  - The batch has a safe dependency-light first proof before live CARLA and
    Alpamayo work.
  - Runtime blockers are contained as manifest/blocker artifacts, not reasons
    to stop unrelated CLI work.

## Findings

- No blocking findings.
- Minor caveat: TASK-116 and TASK-117 are intentionally ambitious. Their local
  proof paths must pass even when live RunPod/CARLA or Alpamayo access fails.

## Readiness Call

Ready for implementation in order:

1. TASK-114
2. TASK-115
3. TASK-116
4. TASK-117
5. TASK-118

If time compresses, TASK-114 + TASK-115 + TASK-118 can still produce a coherent
CLI product demo using existing V8 evidence; TASK-116/TASK-117 add the higher
signal closed-loop and Alpamayo contribution.
