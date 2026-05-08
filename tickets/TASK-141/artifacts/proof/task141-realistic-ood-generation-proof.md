# TASK-141 Realistic OOD Generation Proof

## Result

OODrive generated a deadline-friendly proof packet for realistic bad-path OOD scenarios.

- Source prompt families: `4`
- Generated candidates: `16`
- Queued scenarios: `16`
- Hard-case CARLA placement dry run: `1`
- Live CARLA claim: `false`
- Closed-loop VLA claim: `false`

## Prompt Families

1. Static object appears in the ego lane on a wet urban road; ego must brake to a full stop before contact.
2. Open road hole or trench appears ahead; ego must swerve around it and recover forward motion.
3. Accident debris or rolling object crosses into the ego path; ego must slow, create lateral clearance, then resume.
4. Compound blocked road: moving object crosses first, center lane is blocked, easy detour has a trench; ego must stop, replan, find alternate route, slow through, and recover.

## Generated Artifacts

- Scenario DB: `artifacts/runs/task141-realistic-ood-generation-v1/scenario_studio_db.json`
- Queue Markdown: `artifacts/runs/task141-realistic-ood-generation-v1/scenario_dataset_queue.md`
- Queue JSON: `artifacts/runs/task141-realistic-ood-generation-v1/scenario_dataset_queue.json`
- Compile batch: `artifacts/runs/task141-realistic-ood-generation-v1/compile/scenario_studio_batch.json`
- Gallery: `artifacts/runs/task141-realistic-ood-generation-v1/compile/scenario_studio_gallery.md`

## Representative Scenario IDs

- Static blocker: `studio-0041-static-object-appears-in-the-ego-lane-on-a-wet-u-v00`
- Road hole/trench: `studio-0045-open-road-hole-or-trench-appears-ahead-ego-must--v00`
- Rolling object/debris: `studio-0049-accident-debris-or-rolling-object-crosses-into-t-v00`
- Compound obstacle detour: `studio-0056-compound-blocked-road-moving-object-crosses-firs-v00`

## CARLA-Ready Placement Proof

The compound case was converted into a CARLA placement dry-run manifest:

- Run manifest: `artifacts/runs/task141-realistic-ood-generation-v1/runs/task141-compound-placement-proof/run_manifest.json`
- Placement report: `artifacts/runs/task141-realistic-ood-generation-v1/placements/task141-compound-placement-proof/carla_placement_plan.md`
- Placement plan: `artifacts/runs/task141-realistic-ood-generation-v1/placements/task141-compound-placement-proof/carla_placement_plan.json`
- Placement trace: `artifacts/runs/task141-realistic-ood-generation-v1/runs/task141-compound-placement-proof/placement_trace.json`

Dry-run details:

- scenario: `studio-0056-compound-blocked-road-moving-object-crosses-firs-v00`
- runtime: `carla-placement-dry-run`
- policy: `carla-scripted-ood-demo`
- object proxy blueprint: `static.prop.dirtdebris01`
- behavior samples: `25`

## Judge-Facing Framing

Use this proof as:

> "OODrive can generate realistic rare-event driving scenarios from short natural-language prompts, compile them into a scenario queue, and emit CARLA-ready placement plans. The current proof is generated and dry-run placed locally; live CARLA rendering and open-loop Alpamayo reasoning are separate evidence lanes."

Do not use it as:

> "The model is driving closed-loop in CARLA."

## Claim Boundaries

- `scenario_generation_ai_assisted=true`
- `scenario_generation_ai_provider=codex-template`
- `network_llm_call=false`
- `carla_placement_plan=true`
- `objects_placed_in_carla=false_dry_run`
- `closed_loop_vla_control=false`
- `real_time_vla_control=false`
