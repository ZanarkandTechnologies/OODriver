# Route Video Assembly

- status: `passed`
- rgb_folder: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/visualizations/Generalization_PedestriansOnRoad_1088/rgb`
- output_video: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-068/artifacts/town13-route-run-with-torch/Generalization_PedestriansOnRoad_1088_partial.mp4`
- frame_count: `10`
- ffmpeg_path: `/opt/homebrew/bin/ffmpeg`

## Command

```bash
/opt/homebrew/bin/ffmpeg -y -framerate 10 -pattern_type glob -i /Users/kenjipcx/SOTA/0xDriver/tickets/TASK-060/artifacts/town13-video-plan/fail2drive_outputs/visualizations/Generalization_PedestriansOnRoad_1088/rgb/*.jpg -c:v libx264 -pix_fmt yuv420p /Users/kenjipcx/SOTA/0xDriver/tickets/TASK-068/artifacts/town13-route-run-with-torch/Generalization_PedestriansOnRoad_1088_partial.mp4
```

## Blockers

- none