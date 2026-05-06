# TASK-094: Policy Evaluation Harness Over Quality-Gated Generated Scenarios

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-090, TASK-093
- location: `src/driverx/pipeline`, `src/driverx/policies`, `src/driverx/alpamayo`, tests, docs, `tickets/TASK-094/artifacts`
- enter when: quality-gated generated scenarios are cataloged and selectable
- leave when: DriverX can run policy evaluations over selected scenarios and clearly compare deterministic baseline, memory-guided baseline, cached Alpamayo open-loop, and live Alpamayo when available
- blockers: live Alpamayo comparison needs RunPod/remote GPU; local fake/offline evaluation does not
- spawned follow-ups: closed-loop controller improvement ticket if cached Alpamayo replay remains unstable
- complexity: M

### Summary

Move Alpamayo back into the story as measured policy evidence, not as the thing
we rely on to steer every CARLA tick. The harness should answer: "When the
generator creates a weird case, what does the latest VLA reason, what
trajectory does it propose, and does memory context change the decision?"

### Scope

- In scope: scenario-selection based evaluation, policy matrix over generated
  cases, reasoning capture, trajectory comparison, latency/VRAM reporting, and
  clear open-loop/cached-replay claim boundaries.
- Out of scope: real-time closed-loop Alpamayo driving, model fine-tuning, or
  CUDA optimization.

### Gap Analysis

- Current state: Alpamayo can run on captures and campaign cases, but the
  comparison is not integrated with quality-gated generated scenario selection.
- Production expectation: the simulator should generate OOD scenarios, then run
  policies through the same cases and collect interpretable evidence.
- Missing gaps: catalog selection input, consistent policy matrix, reasoning
  extraction per generated case, and explicit labels separating open-loop VLA
  evaluation from closed-loop CARLA driving.
- Recommendation: evaluate Alpamayo as an open-loop reasoning/action proposer
  first; only later harden cached replay if it becomes useful for the video.

### Plan

#### Change

Add a policy evaluation command that reads a scenario selection from the
catalog, locates captures/packages, runs available policy adapters, and writes
one comparison packet per case plus an aggregate report.

#### Why

The submission gets stronger when the generator and VLA are connected through a
single evidence loop.

#### Before -> After

- Before: generated scenario videos and Alpamayo reasoning exist as mostly
  separate artifacts.
- After: each promoted scenario can show generator recipe, video, policy
  reasoning, trajectory, memory delta, and latency in one report.

#### Touch

- `src/driverx/pipeline/policy_evaluation_campaign.py`: new evaluator.
- `src/driverx/policies/registry.py`: policy mode selection if missing.
- `src/driverx/alpamayo/*`: reuse existing live/offline adapters; add tolerant
  no-GPU blocker classification.
- `src/driverx/scenarios/catalog.py`: scenario selection input.
- `tests/test_policy_evaluation_campaign.py`.
- `README.md`, `ARCHITECTURE.md`, `docs/progress.md`.

#### Inspect

- `src/driverx/pipeline/alpamayo_ood_comparison.py`
- `src/driverx/pipeline/alpamayo_batch_comparison.py`
- `src/driverx/pipeline/rag_comparison.py`
- `src/driverx/policies/types.py`
- `tickets/TASK-086/artifacts/task86-plan-cache/alpamayo_ood_batch_summary.md`

#### Signature Delta

```python
run_policy_evaluation_campaign(config: PolicyEvaluationCampaignConfig) -> PolicyEvaluationCampaignSummary
evaluate_policy_on_scenario(record: ScenarioCatalogRecord, policy_modes: list[str]) -> ScenarioPolicyEvaluation
write_policy_evaluation_report(summary: PolicyEvaluationCampaignSummary, output_dir: Path) -> dict[str, Path]
```

#### Type Sketch

```python
ScenarioPolicyEvaluation = {
  "scenario_id": str,
  "quality_status": str,
  "policy_results": {
    "deterministic_baseline": PolicyEvidence,
    "memory_guided_baseline": PolicyEvidence,
    "alpamayo_open_loop": PolicyEvidence | None,
    "alpamayo_memory_open_loop": PolicyEvidence | None,
  },
  "claim_boundary": {"closed_loop_carla": bool, "open_loop_policy_evaluation": bool},
}
```

#### Typed Flow Example

`scenario_selection.json`
-> `run-policy-evaluation-campaign --policy deterministic --policy alpamayo-live`
-> per-case `policy_evaluation.json`
-> aggregate `policy_evaluation_campaign.md`
-> TASK-095 browser/demo pack.

#### Execution Steps

1. Add policy evaluation campaign config and summary schema.
2. Support local deterministic/mock/memory policies first.
3. Plug in existing Alpamayo live/offline adapter with actionable blocker
   reports when GPU/SSH/model is unavailable.
4. Add aggregate latency, reasoning snippet, trajectory delta, and memory-delta
   reporting.
5. Run one live Alpamayo pass on RunPod if available.

#### Recommendation

Do not block this ticket on live GPU. The harness should complete locally with
mock/offline policies and opportunistically attach Alpamayo proof when the
remote lane is alive.

#### Options Considered

- Make Alpamayo drive CARLA closed-loop now: too unstable and conflates control
  bugs with VLA reasoning.
- Only report images/VQA: too weak for an autonomy submission.
- Run open-loop trajectory/reasoning evaluation over generated cases: best; it
  is measurable, honest, and directly tied to minimal-shot behavior.

#### Blast Radius

- Moderate: mostly new pipeline and reports using existing adapters.

#### Risks

- Existing captures may not be road-aligned; only run on TASK-093
  quality-passed scenarios or label legacy evidence as partial.

### Acceptance Criteria

- [x] AC-1: Command evaluates a catalog scenario selection with at least two
  non-GPU policy modes locally.
- [x] AC-2: Report includes reasoning/decision summaries, trajectory deltas,
  latency, and memory/no-memory comparison where available.
- [x] AC-3: Alpamayo live mode is supported through existing remote adapter and
  produces either live evidence or an actionable blocker artifact.
- [x] AC-4: Reports clearly label open-loop policy evaluation versus closed-loop
  CARLA control.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_policy_evaluation_campaign`
- `PYTHONPATH=src python3 -m driverx run-policy-evaluation-campaign --selection artifacts/scenario-catalog/hero_selection.json --run-id task94-policy-eval`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Local policy modes are fully autonomous.
- Live Alpamayo depends on remote GPU availability; if blocked, continue and
  record `alpamayo_live_blocked` in the report.

### Evidence

- Planned 2026-05-06 to connect generated simulator cases to latest-VLA
  reasoning without overstating closed-loop autonomy.
- Plan review: `docs/reviews/TASK-089-095-impl-plan-review.md`.
- Implementation review: `docs/reviews/TASK-089-095-implementation-review.md`.
- Implemented `run-policy-evaluation-campaign` over Scenario Studio catalog
  records with deterministic baseline, memory-guided, and Alpamayo open-loop
  policy modes.
- Review follow-up made local policy modes write explicit decision artifacts
  only for quality-passed scenarios; legacy/open-loop records are now blocked
  or planned with actionable reasons instead of being counted as passed policy
  evaluations. The current evidence packet reports passed `0`, planned `9`,
  blocked `18`, and local decision artifacts `0`.
- Focused tests passed:
  `PYTHONPATH=src python3 -m unittest tests.test_policy_evaluation_campaign tests.test_scenario_catalog tests.test_cli`.
- Generated policy evaluation evidence:
  `tickets/TASK-094/artifacts/policy-evaluation-v6/policy_evaluation_campaign.md`.

### Blockers

- None for local build.
- Live Alpamayo requires the RunPod/remote GPU and HF cache to remain available;
  current campaign uses existing cached Alpamayo evidence and explicit planned
  statuses where package/reasoning artifacts are missing.

### Archive Note

Archived from the active board on 2026-05-07 02:55 +0800. This ticket is preserved as historical evidence and is superseded for final submission execution by TASK-101 through TASK-106. Do not treat this ticket as active sprint work unless it is explicitly reopened.
