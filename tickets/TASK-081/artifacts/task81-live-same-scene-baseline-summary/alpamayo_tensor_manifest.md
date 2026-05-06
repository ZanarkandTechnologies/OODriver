# Alpamayo Tensor Manifest

- frame_name: `driverx_ood_generated-base-animals-0076-regional-driving-behavior-000`
- torch_ready: `True`
- image_frames: `[3, 4, 3, 360, 640]`
- camera_indices: `[0, 1, 2]`
- ego_history_xyz: `[1, 1, 16, 3]`
- ego_history_rot: `[1, 1, 16, 3, 3]`
- memory_context_count: `0`

## Validation Errors

- none

## Warnings

- none

## Camera Frames

- camera `0` frame `0`: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb/frame_000025.png`
- camera `0` frame `1`: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb/frame_000026.png`
- camera `0` frame `2`: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb/frame_000027.png`
- camera `0` frame `3`: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb/frame_000028.png`
- camera `1` frame `0`: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb/frame_000025.png`
- camera `1` frame `1`: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb/frame_000026.png`
- camera `1` frame `2`: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb/frame_000027.png`
- camera `1` frame `3`: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb/frame_000028.png`
- camera `2` frame `0`: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb/frame_000025.png`
- camera `2` frame `1`: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb/frame_000026.png`
- camera `2` frame `2`: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb/frame_000027.png`
- camera `2` frame `3`: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-078/artifacts/task78-live-ood-capture-v3/rgb/frame_000028.png`

## Remote Loader Contract

The remote runner should load PNGs as RGB, stack them as `[N, 4, 3, H, W]`,
create `camera_indices` as `torch.long`, and wrap ego history as `[1, 1, 16, ...]`.
