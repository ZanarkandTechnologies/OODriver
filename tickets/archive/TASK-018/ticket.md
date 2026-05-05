# TASK-018: Generated Bench2Drive Route Pack Export

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-007, TASK-011, TASK-015
- location: `src/driverx/simulators`, CLI, tests, docs
- enter when: generated scenario recipes need a SimLingo/Bench2Drive execution surface
- leave when: recipes export to stock-compatible Bench2Drive route XML plus DriverX OOD overlay artifacts
- blockers: live custom actor injection still requires a future runtime runner around SimLingo/CARLA
- spawned follow-ups: live H100 route execution, companion actor injector
- complexity: M

### Summary
Export generated OOD recipes into a route pack that SimLingo can consume without
modifying upstream scenario classes. The XML remains stock Bench2Drive route XML,
while a sidecar overlay records the generated object, behavior, memory, and
expected failure intent for DriverX.

### Acceptance Criteria
- [x] Resolve each recipe's source route XML from `recipe.route_path` and an optional route root.
- [x] Write per-recipe route XML and a merged Bench2Drive route suite XML.
- [x] Write per-recipe overlay JSON preserving mutation, actors, environment,
  memory query, behavior id, and compatibility notes.
- [x] Optionally write a SimLingo command plan pointing at the merged route suite.
- [x] Add CLI entrypoint for route pack export.
- [x] Add unit and CLI tests without requiring CARLA or SimLingo.
- [x] Run `bash scripts/pre_push_check.sh`.

### Evidence
- Scenario forge:
  `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/scenario-forge/scenario_recipes.json`
- Route pack report:
  `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/bench2drive_route_pack.md`
- Route suite XML:
  `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/bench2drive_routes/generated_routes.xml`
- DriverX overlays:
  `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/driverx_overlays/000_generated-base-animals-0076-occlusion-000.json`
  `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/driverx_overlays/001_generated-generalization-customobstacles-1028-visual-noise-001.json`
- SimLingo plan:
  `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/simlingo_command_plan.json`
- Fixture route-pack proof: `num_routes=2`, merged route ids `0076` and
  `1028`, two per-route XML files, two sidecar overlays, and an absolute
  SimLingo `--routes=.../generated_routes.xml` command.
- Focused tests:
  `PYTHONPATH=src python3 -m unittest tests.test_bench2drive_route_export tests.test_cli`
- External Fail2Drive smoke:
  `tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/external-fail2drive/route-pack/bench2drive_route_pack.md`
  exported real routes `Base_Animals_0075.xml` and `Base_Animals_0076.xml`
  from `../external/fail2drive` with route ids `75` and `76`.
- Local gate: `bash scripts/pre_push_check.sh` passed with `125` tests.
- Review:
  `docs/reviews/TASK-018-bench2drive-route-pack-review.md`
