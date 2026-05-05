# Fail2Drive Video Smoke Plan

- dry_run: `True`
- route_path: `/workspace/fail2drive/fail2drive_split/Generalization_PedestriansOnRoad_1088.xml`
- agent_path: `/workspace/fail2drive/team_code/viz_path_agent.py`
- cwd: `/workspace/fail2drive`
- blockers: `2`

## Route Command

```bash
CARLA_HOST='host.docker.internal' CARLA_PORT='2000' DRIVERX_METHOD_NAME='DriverXRouteSmoke' FAIL2DRIVE_ROOT='/workspace/fail2drive' LIVE_VISU='1' REPETITION='0' SAVE_PATH='/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/visualizations' SCENARIO_RUNNER_ROOT='/workspace/fail2drive/scenario_runner' TOWN='Town13' VIZ_PATH='/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/visualizations/Generalization_PedestriansOnRoad_1088/rgb'
python /workspace/fail2drive/leaderboard/leaderboard/leaderboard_evaluator_local.py --routes /workspace/fail2drive/fail2drive_split/Generalization_PedestriansOnRoad_1088.xml --repetitions 1 --track MAP --checkpoint /workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/Generalization_PedestriansOnRoad_1088_res.json --debug-checkpoint /workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/Generalization_PedestriansOnRoad_1088_debug.txt --timeout 900 --agent /workspace/fail2drive/team_code/viz_path_agent.py --host host.docker.internal --port 2000
```

## Video Command

```bash
python /workspace/fail2drive/tools/generate_video.py -f /workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/visualizations/Generalization_PedestriansOnRoad_1088/rgb -o /workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/Generalization_PedestriansOnRoad_1088.mp4
```

## Expected Outputs

- result: `/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/Generalization_PedestriansOnRoad_1088_res.json`
- debug: `/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/Generalization_PedestriansOnRoad_1088_debug.txt`
- save_path: `/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/visualizations`
- rgb_folder: `/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/visualizations/Generalization_PedestriansOnRoad_1088/rgb`
- video: `/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/Generalization_PedestriansOnRoad_1088.mp4`

## Live Blockers

- Fail2Drive video tool not found: /workspace/fail2drive/tools/generate_video.py
- RGB folder does not exist yet; run the route command with SAVE_PATH before generating video: /workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/visualizations/Generalization_PedestriansOnRoad_1088/rgb
