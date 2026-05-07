# Review: Scenario Generator CLI Ticket Plan

Reviewed at: 2026-05-07 17:21 +0800

## Scope

- `docs/specs/scenario-generator-cli-v1.md`
- `tickets/TASK-114/ticket.md`
- `tickets/TASK-115/ticket.md`
- `tickets/TASK-116/ticket.md`
- `tickets/TASK-117/ticket.md`
- `tickets/TASK-118/ticket.md`
- `tickets/TASK-119/ticket.md`

## Rubrics

### Spec Contract

- Score: 4.2 / 5.0
- Threshold: 4.0
- Verdict: pass
- Notes:
  - The ticket batch maps directly to the PRD's scenario generation,
    curation, closed-loop run, Alpamayo evaluation, replay, and export jobs.
  - The CLI database decision is explicit and separates deterministic durable
    state from Codex's AI-generation/operator role.
  - Each ticket has observable artifacts and command-level proof.

### Implementation Plan

- Score: 4.1 / 5.0
- Threshold: 4.0
- Verdict: pass
- Notes:
  - File maps and signature deltas are concrete enough for build handoff.
  - The batch has a safe dependency-light first proof before live CARLA,
    Alpamayo, and Codex skill work.
  - Runtime blockers are contained as manifest/blocker artifacts, not reasons
    to stop unrelated CLI work.

## Findings

- No blocking findings.
- Minor caveat: TASK-116 and TASK-117 are intentionally ambitious. Their local
  proof paths must pass even when live RunPod/CARLA or Alpamayo access fails.
- Minor caveat: TASK-119 should remain blocked until TASK-114/TASK-115 stabilize
  the DB command contract.

## Readiness Call

Ready for implementation in order:

1. TASK-114
2. TASK-115
3. TASK-116
4. TASK-117
5. TASK-118
6. TASK-119

If time compresses, TASK-114 + TASK-115 + TASK-118 can still produce a coherent
CLI product demo using existing V8 evidence; TASK-116/TASK-117 add the higher
signal closed-loop and Alpamayo contribution; TASK-119 adds the Codex operator
wrapper after the database layer stops moving.
