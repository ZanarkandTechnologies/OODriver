# Alpamayo Tensor Manifest

- frame_name: `carla_live_alpamayo_capture`
- torch_ready: `True`
- image_frames: `[3, 4, 3, 90, 160]`
- camera_indices: `[0, 1, 2]`
- ego_history_xyz: `[1, 1, 16, 3]`
- ego_history_rot: `[1, 1, 16, 3, 3]`
- memory_context_count: `0`

## Validation Errors

- none

## Warnings

- none

## Camera Frames

- camera `0` frame `0`: `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task51-live-alpamayo-capture/images/camera_0_frame_000.png`
- camera `0` frame `1`: `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task51-live-alpamayo-capture/images/camera_0_frame_001.png`
- camera `0` frame `2`: `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task51-live-alpamayo-capture/images/camera_0_frame_002.png`
- camera `0` frame `3`: `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task51-live-alpamayo-capture/images/camera_0_frame_003.png`
- camera `1` frame `0`: `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task51-live-alpamayo-capture/images/camera_1_frame_000.png`
- camera `1` frame `1`: `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task51-live-alpamayo-capture/images/camera_1_frame_001.png`
- camera `1` frame `2`: `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task51-live-alpamayo-capture/images/camera_1_frame_002.png`
- camera `1` frame `3`: `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task51-live-alpamayo-capture/images/camera_1_frame_003.png`
- camera `2` frame `0`: `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task51-live-alpamayo-capture/images/camera_2_frame_000.png`
- camera `2` frame `1`: `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task51-live-alpamayo-capture/images/camera_2_frame_001.png`
- camera `2` frame `2`: `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task51-live-alpamayo-capture/images/camera_2_frame_002.png`
- camera `2` frame `3`: `/Users/kenjipcx/SOTA/0xDriver/artifacts/runs/task51-live-alpamayo-capture/images/camera_2_frame_003.png`

## Remote Loader Contract

The remote runner should load PNGs as RGB, stack them as `[N, 4, 3, H, W]`, 
create `camera_indices` as `torch.long`, and wrap ego history as `[1, 1, 16, ...]`.
