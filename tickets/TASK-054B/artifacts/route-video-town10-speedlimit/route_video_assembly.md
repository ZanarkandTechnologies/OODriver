# Route Video Assembly

- status: `passed`
- rgb_folder: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/visualizations/routes_town10/rgb`
- output_video: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/routes_town10.mp4`
- frame_count: `41`
- ffmpeg_path: `/opt/homebrew/bin/ffmpeg`

## Command

```bash
/opt/homebrew/bin/ffmpeg -y -framerate 10 -pattern_type glob -i /Users/kenjipcx/SOTA/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/visualizations/routes_town10/rgb/*.jpg -c:v libx264 -pix_fmt yuv420p /Users/kenjipcx/SOTA/0xDriver/tickets/TASK-054B/artifacts/docker-route-plan-town10-speedlimit/fail2drive_outputs/routes_town10.mp4
```

## Blockers

- none