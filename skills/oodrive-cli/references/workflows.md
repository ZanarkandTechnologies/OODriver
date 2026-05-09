# OODrive Workflow Variants

## Live RunPod CARLA

1. Verify SSH and repo path.
2. Check CARLA process and smoke-connect before running scenarios.
3. Sync only the needed source/fixtures if the remote repo is not git-clean.
4. Run validation locally/remotely before live execution.
5. Capture screenshots/video and pull media back to the local workspace.
6. Show local absolute media links in the final answer.

## Fail2Drive Scenario Authoring

1. Run `f2d-catalog`.
2. Write a route spec or route XML.
3. Run `f2d-write-route --validate` or `f2d-validate-route`.
4. Dry-run `f2d-run-route`; keep the default OODrive capture agent for video evidence.
5. Live-run only after CARLA is reachable and route validation passes.
6. Attach `f2d-reason`.
7. Export `f2d-demo-video` or a snapshot/contact sheet.

## Submission Evidence

1. Prefer bad-path scenarios over happy paths.
2. Ensure frame/time/source provenance is visible.
3. Include at least three reasoning snippets and three memory/RAG callouts when claiming reasoning proof.
4. Score with the relevant `score-*` command.
5. State exactly which evidence is live, cached, fake, dry-run, or blocked.
