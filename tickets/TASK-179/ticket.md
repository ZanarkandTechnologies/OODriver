# TASK-179: Codex Skill For OpenSCENARIO-To-CARLA Workflow

## Status
- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-174, TASK-175, TASK-176, TASK-177, TASK-178
- location: `/Users/kenjipcx/coding-harness/Codexter/skills`, `docs`, `tests`, `tickets/TASK-179`
- enter when: OODrive has CLI validation/run surfaces, but Codex still lacks a workflow skill for authoring ASAM OpenSCENARIO 2.0 and using OODrive to configure CARLA.
- leave when: a Codex skill teaches an agent to author `.osc`/sidecar files, call OODrive validation/run commands, configure CARLA/ScenarioRunner/custom assets/maps through CLI, and collect evidence without relying on an internal OODrive prompt resolver.
- blockers: skill can be local workflow-only first; live CARLA/ScenarioRunner proof depends on TASK-174/TASK-175 runtimes.
- spawned follow-ups: optional MCP wrapper after TASK-178 tool manifest exists.
- complexity: M
- assignee: generalPurpose

### Description
Make Codex/the coding harness the generator. The agent writes ASAM OpenSCENARIO 2.0 files and sidecars from the user's prompt, then uses OODrive CLI tools to validate, configure CARLA, run ScenarioRunner, and gather proof.

### Goal
Replace the rejected `oodrive resolve-prompt` idea with a durable agent workflow skill: "author standard scenario files, then use OODrive as the validator/runner/evidence layer."

### Integration Decision
Do not put prompt-to-scenario intelligence inside OODrive. Codex can reason over the prompt and write DSL files. OODrive should expose small tools: validate `.osc`, run `.osc`, package/probe assets/maps, index artifacts, and score visual proof.

### Plan

#### Change
Create an `oodrive-carla-scenario` Codex skill that guides agents through prompt -> OpenSCENARIO 2.0/sidecar -> OODrive validation -> CARLA/ScenarioRunner execution -> evidence.

#### Why
The user wants a harness-operated simulator product. Skills are the right place for flexible authoring workflows; CLI commands are the right place for deterministic validation and execution.

#### Before -> After
- Before: proposed `resolve-prompt` command tried to make OODrive infer too much.
- After: Codex skill owns authoring; OODrive CLI owns validation, CARLA setup, execution, and scoring.

#### Touch
- `/Users/kenjipcx/coding-harness/Codexter/skills/oodrive-carla-scenario/SKILL.md` new skill.
- optional `references/osc2-authoring.md` only if concise examples would bloat `SKILL.md`.
- `tickets/TASK-179/artifacts/review/...` planning/build review artifacts.
- `README.md` only after skill is usable.

#### Inspect
- `/Users/kenjipcx/coding-harness/Codexter/skills/skill-creator/SKILL.md`
- `tickets/TASK-175/ticket.md`
- `tickets/TASK-178/ticket.md`
- `src/driverx/scenarios/studio_product_cli.py`

#### Signature Delta
- Skill trigger: user asks Codex to create/run a CARLA scenario from a prompt using OODrive/OpenSCENARIO.
- Skill workflow output: `scenario.osc`, `scenario_sidecar.json`, validation report, run result, media/evidence links.
- OODrive CLI dependencies: `validate-osc2`, `run-osc2`, `carla-control`, `prepare-map-import`, `package-asset`, `tools-manifest`, `artifacts-list`, `score-visual-fidelity`.

#### Type Sketch
```python
AgentAuthoredScenarioBundle = {
  "scenario_osc_path": str,
  "sidecar_path": str,
  "validation_command": str,
  "run_command": str,
  "evidence_paths": list[str],
  "claim_boundaries": list[str],
}
```

#### Typed Flow Example
User: "wet roadwork, object blocks lane, scooter cuts in" -> Codex skill drafts `scenario.osc` plus sidecar -> runs `oodrive validate-osc2 --osc2 scenario.osc --sidecar scenario_sidecar.json` -> if valid, runs `oodrive run-osc2` or records ScenarioRunner blocker -> indexes artifacts and visual score.

#### Execution Steps
1. Create a compact skill with trigger conditions, 5-8 step workflow, decision branches, gotchas, judgment questions, and outcome contract.
2. Include minimal OpenSCENARIO authoring pattern examples without trying to document the whole ASAM language.
3. Teach the skill to prefer OODrive CLI validation/run/probe commands over internal generation.
4. Add fixture prompt and expected artifact checklist.
5. Validate skill shape against `skill-creator` first-load contract.

#### Recommendation
Build this skill after TASK-175's validation command exists, or build a draft skill now that references the planned commands. The final skill should not depend on `resolve-prompt`.

#### Options Considered
- `oodrive resolve-prompt`: rejected; it puts intelligence in the CLI.
- Agent freehands `.osc` with no OODrive validation: too brittle.
- Codex skill plus OODrive validator/runner: recommended.

#### Blast Radius
Low in OODrive code; moderate in Codex workflow. The skill can evolve without changing simulator internals.

#### Risks
- Skill may over-document OpenSCENARIO and bloat context; keep examples minimal and rely on validation.
- If TASK-175 commands do not exist yet, the skill must label them as prerequisites or use command stubs.

### Acceptance Criteria
- [x] AC-1: A Codex skill exists for OODrive CARLA/OpenSCENARIO scenario authoring.
- [x] AC-2: Skill workflow makes Codex author `.osc` and sidecar files directly from a user prompt.
- [x] AC-3: Skill instructs agents to use OODrive CLI for validation, execution, CARLA probing, artifact indexing, and visual scoring.
- [x] AC-4: Skill explicitly avoids `oodrive resolve-prompt` or any internal prompt compiler dependency.
- [x] AC-5: Skill outcome contract lists concrete artifacts: `scenario.osc`, sidecar, validation report, run result/blocker, media/evidence paths.

### Verification
- Read the skill once and confirm it satisfies the skill-creator first-load contract.
- Run the skill manually on a fixture prompt after TASK-175 exists:
  - `PYTHONPATH=src python3 -m oodrive validate-osc2 --osc2 <scenario.osc> --sidecar <scenario_sidecar.json>`
  - `PYTHONPATH=src python3 -m oodrive run-osc2 --osc2 <scenario.osc> --scenario-runner-root <path>`
- `bash scripts/pre_push_check.sh` only if repo code/docs changed.

### Evidence
- Skill path
- Fixture `scenario.osc`
- Fixture sidecar
- Validation report
- Run result or precise blocker
- Review artifact
- Build evidence: skill created at `/Users/kenjipcx/coding-harness/Codexter/skills/oodrive-carla-scenario/SKILL.md`
- Skill workflow uses `oodrive tools-manifest`, `validate-osc2`, `scenario-runner-package`, `run-osc2`, custom map/asset probe commands, `artifacts-list`, and `score-visual-fidelity`.
- Build review: `tickets/TASK-174/artifacts/review/task174-180-impl-review.json`
