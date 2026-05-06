# TASK-095: Submission Scenario Browser And Demo Pack V6

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-090, TASK-093, TASK-094
- location: `src/driverx/pipeline`, `docs`, `tickets/TASK-095/artifacts`
- enter when: the catalog has quality-gated scenarios and policy evaluation packets
- leave when: the repo has a judge-facing static scenario browser, refreshed demo pack, and script framing the real contribution as OOD scenario generation plus minimal-shot VLA evaluation
- blockers: browser can be built from fake/local evidence; final hero video depends on TASK-093 live quality pass
- spawned follow-ups: final video/deck production ticket if the submission needs a rendered presentation file
- complexity: M

### Summary

Package the new contribution so it is obvious within one minute: DriverX is a
scenario forge for minimal-shot autonomy, with quality-gated CARLA OOD cases,
policy reasoning evidence, and realistic latency/model boundaries.

### Scope

- In scope: static HTML/Markdown scenario browser, refreshed dossier, video
  storyboard/script, quality evidence checklist, and current blocker summary.
- Out of scope: custom frontend app server, PowerPoint export, or new simulator
  behavior implementation.

### Gap Analysis

- Current state: V5 dossier exists but leads with setup-heavy evidence and
  includes videos the user no longer trusts.
- Production expectation: the submission should show scenario generation,
  suite management, quality gates, and VLA reaction evidence with a clear
  minimal-shot thesis.
- Missing gaps: browser over cataloged scenarios, quality-passed hero selection,
  "what we generated" explanation, and refreshed claim boundaries after the
  road-frame fix.
- Recommendation: build a static browser and V6 dossier from the catalog rather
  than hand-curating links in prose.

### Plan

#### Change

Add a report/browser builder that consumes scenario catalog and policy
evaluation outputs, then writes `scenario_browser.html`,
`submission_dossier_v6.md`, and `video_script_v6.md`.

#### Why

The project needs a coherent artifact that sells the simulator contribution,
not another pile of setup logs.

#### Before -> After

- Before: evidence is scattered across tickets and includes questionable old
  videos.
- After: the demo pack highlights only quality-passed or explicitly-labeled
  failure evidence and explains the generator/evaluation loop.

#### Touch

- `src/driverx/pipeline/submission_scenario_browser.py`: new static browser.
- `src/driverx/pipeline/submission_pack.py`: V6 sections and catalog inputs.
- `src/driverx/scenarios/reports.py`: reusable card/summary helpers.
- `tests/test_submission_scenario_browser.py`.
- `README.md`, `ARCHITECTURE.md`, `docs/progress.md`, `docs/HISTORY.md`.

#### Inspect

- `src/driverx/pipeline/submission_pack.py`
- `tickets/TASK-087/artifacts/submission-dossier-v5-live/submission_dossier.md`
- `tickets/TASK-084/artifacts/task84-reasoning-pack/reasoning_video_pack.html`
- `docs/prd.md`

#### Signature Delta

```python
build_submission_scenario_browser(catalog: ScenarioCatalog, evaluations: list[ScenarioPolicyEvaluation], output_dir: Path) -> SubmissionBrowserOutputs
build_submission_dossier_v6(inputs: SubmissionDossierInputs, output_dir: Path) -> dict[str, Path]
```

#### Type Sketch

```python
SubmissionBrowserOutputs = {
  "browser_html": str,
  "dossier_md": str,
  "video_script_md": str,
  "hero_scenarios": list[str],
  "failure_cases": list[str],
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example

`scenario_catalog.json + policy_evaluation_campaign.json`
-> `build-submission-scenario-browser`
-> browser cards with video/reasoning/quality
-> V6 dossier
-> final 1-5 minute video script.

#### Execution Steps

1. Add static browser renderer with cards for scenario, environment, behavior,
   quality checks, video, and policy reasoning.
2. Update submission pack generator to lead with the scenario forge thesis.
3. Ensure old off-road evidence is not promoted unless marked as failed/legacy.
4. Add tests for HTML/report generation.
5. Run full pre-push gate and attach QA/review artifacts.

#### Recommendation

Use static HTML and Markdown. It is enough for judges and avoids spending the
next day on frontend infrastructure.

#### Options Considered

- Build a full web app: high polish but unnecessary.
- Keep Markdown only: usable but weaker for navigating many generated cases.
- Static browser plus dossier: best balance for submission speed and clarity.

#### Blast Radius

- Low: reporting-only outputs.

#### Risks

- If TASK-093 has no live quality-passed video, browser must still render but
  prominently show the video blocker and use local/fake evidence as secondary.

### Acceptance Criteria

- [x] AC-1: Browser shows generated scenario cards with tags, quality checks,
  video links, policy evidence, and promotion status.
- [x] AC-2: V6 dossier leads with randomized OOD scenario generation and
  minimal-shot policy evaluation, not setup.
- [x] AC-3: Video script selects a hero only if a strict quality-passed promoted
  case exists; otherwise it explicitly says no hero is selected yet.
- [x] AC-4: Claim boundaries remain explicit for Alpamayo open-loop reasoning
  versus closed-loop CARLA execution.

### Verification

- `PYTHONPATH=src python3 -m unittest tests.test_submission_scenario_browser`
- `PYTHONPATH=src python3 -m driverx build-submission-scenario-browser --catalog artifacts/scenario-catalog/scenario_catalog.json --run-id task95-browser`
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness

- Fully local once TASK-090/TASK-093/TASK-094 artifacts exist.
- Can render partial/browser blocker states without live CARLA/GPU.

### Evidence

- Planned 2026-05-06 as the packaging step for the simulator-contribution
  milestone.
- Plan review: `docs/reviews/TASK-089-095-impl-plan-review.md`.
- Implementation review: `docs/reviews/TASK-089-095-implementation-review.md`.
- Implemented static scenario browser, V6 dossier, and V6 video script builder
  in `src/driverx/pipeline/submission_scenario_browser.py`.
- Review follow-up made hero selection require manual promotion plus strict
  `quality_status=passed`, video evidence, and road-alignment proof; current
  browser correctly has no hero scenario while the rendering host is blocked.
- Second review follow-up made the browser and V6 dossier show policy evidence
  as status counts rather than a raw completed-evaluation counter: passed `0`,
  planned `9`, blocked `18`, local decision artifacts `0`. Cards now expose
  `quality_status` and `promotion` for auditability.
- Focused tests passed:
  `PYTHONPATH=src python3 -m unittest tests.test_submission_scenario_browser tests.test_policy_evaluation_campaign tests.test_cli`.
- Generated V6 submission evidence:
  `tickets/TASK-095/artifacts/submission-browser-v11/scenario_browser.html`,
  `tickets/TASK-095/artifacts/submission-browser-v11/submission_dossier_v6.md`,
  and `tickets/TASK-095/artifacts/submission-browser-v11/video_script_v6.md`.

### Blockers

- Final hero content is limited by the current remote CARLA Vulkan blocker and
  by missing Alpamayo packages for several cataloged video cases; the browser
  labels those as planned/blocked evidence rather than completed closed-loop
  VLA proof.
