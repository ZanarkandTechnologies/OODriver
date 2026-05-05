# Fail2Drive Video Smoke Plan

- dry_run: `True`
- route_path: `/workspace/fail2drive/scenario_runner/srunner/data/routes_town10.xml`
- agent_path: `/workspace/fail2drive/team_code/viz_path_agent.py`
- cwd: `/workspace/fail2drive`
- blockers: `2`

## Route Command

```bash
CARLA_HOST='host.docker.internal' CARLA_PORT='2000' DRIVERX_METHOD_NAME='DriverXRouteSmoke' FAIL2DRIVE_ROOT='/workspace/fail2drive' LIVE_VISU='1' REPETITION='0' SAVE_PATH='/workspace/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/visualizations' SCENARIO_RUNNER_ROOT='/workspace/fail2drive/scenario_runner' TOWN='Town10HD_Opt' VIZ_PATH='/workspace/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/visualizations/routes_town10/rgb'
python /workspace/fail2drive/leaderboard/leaderboard/leaderboard_evaluator_local.py --routes /workspace/fail2drive/scenario_runner/srunner/data/routes_town10.xml --repetitions 1 --track MAP --checkpoint /workspace/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/routes_town10_res.json --debug-checkpoint /workspace/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/routes_town10_debug.txt --timeout 300 --agent /workspace/fail2drive/team_code/viz_path_agent.py --host host.docker.internal --port 2000
```

## Video Command

```bash
python /workspace/fail2drive/tools/generate_video.py -f /workspace/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/visualizations/routes_town10/rgb -o /workspace/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/routes_town10.mp4
```

## Expected Outputs

- result: `/workspace/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/routes_town10_res.json`
- debug: `/workspace/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/routes_town10_debug.txt`
- save_path: `/workspace/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/visualizations`
- rgb_folder: `/workspace/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/visualizations/routes_town10/rgb`
- video: `/workspace/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/routes_town10.mp4`

## Live Blockers

- Fail2Drive video tool not found: /workspace/fail2drive/tools/generate_video.py
- RGB folder does not exist yet; run the route command with SAVE_PATH before generating video: /workspace/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/visualizations/routes_town10/rgb
