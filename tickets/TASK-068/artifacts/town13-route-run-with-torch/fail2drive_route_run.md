# Fail2Drive Route Run

- status: `blocked`
- exit_code: `None`
- duration_s: `300.561921`
- stdout: `/workspace/0xDriver/tickets/TASK-068/artifacts/town13-route-run-with-torch/logs/fail2drive_route.stdout.log`
- stderr: `/workspace/0xDriver/tickets/TASK-068/artifacts/town13-route-run-with-torch/logs/fail2drive_route.stderr.log`

## Command

```bash
CARLA_HOST='host.docker.internal' CARLA_PORT='2000' DRIVERX_METHOD_NAME='DriverXRouteSmoke' FAIL2DRIVE_ROOT='/workspace/fail2drive' LIVE_VISU='1' REPETITION='0' SAVE_PATH='/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/visualizations' SCENARIO_RUNNER_ROOT='/workspace/fail2drive/scenario_runner' TOWN='Town13' VIZ_PATH='/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/visualizations/Generalization_PedestriansOnRoad_1088/rgb'
python /workspace/fail2drive/leaderboard/leaderboard/leaderboard_evaluator_local.py --routes /workspace/fail2drive/fail2drive_split/Generalization_PedestriansOnRoad_1088.xml --repetitions 1 --track MAP --checkpoint /workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/Generalization_PedestriansOnRoad_1088_res.json --debug-checkpoint /workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/Generalization_PedestriansOnRoad_1088_debug.txt --timeout 900 --agent /workspace/fail2drive/team_code/viz_path_agent.py --host host.docker.internal --port 2000
```

## Expected Outputs

| label | exists | size_bytes | path |
|---|---:|---:|---|
| `result` | `True` | `361` | `/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/Generalization_PedestriansOnRoad_1088_res.json` |
| `debug` | `False` | `None` | `/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/Generalization_PedestriansOnRoad_1088_debug.txt` |
| `save_path` | `True` | `None` | `/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/visualizations` |
| `rgb_folder` | `True` | `None` | `/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/visualizations/Generalization_PedestriansOnRoad_1088/rgb` |
| `video` | `False` | `None` | `/workspace/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/Generalization_PedestriansOnRoad_1088.mp4` |

## Blockers

- Fail2Drive route command timed out.