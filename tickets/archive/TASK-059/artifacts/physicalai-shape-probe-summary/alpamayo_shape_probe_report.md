# Alpamayo Shape Probe Report

- model_id: `nvidia/Alpamayo-1.5-10B`
- status: `dataset_shape_observed`
- blocked: `False`
- inference_state: `shape_observed`
- shape_source_used: `dataset`
- clip_id: `030c760c-ae38-49aa-9ad8-f5650a545d26`
- t0_us: `5100000`
- latency_ms: `124987.44`
- vram_peak_mb: `24881.65`

## Input Shapes

- `camera_indices`: `[4]`
- `ego_future_rot`: `[1, 1, 64, 3, 3]`
- `ego_future_xyz`: `[1, 1, 64, 3]`
- `ego_history_rot`: `[1, 1, 16, 3, 3]`
- `ego_history_xyz`: `[1, 1, 16, 3]`
- `image_frames`: `[4, 4, 3, 1080, 1920]`
- `tokenized_data`: `{'input_ids': [1, 3086], 'attention_mask': [1, 3086], 'pixel_values': [11520, 1536], 'image_grid_thw': [16, 3]}`

## Output Shapes

- `extra`: `{'cot': [1, 1, 1], 'meta_action': [1, 1, 1], 'answer': [1, 1, 1]}`
- `extra.answer`: `[1, 1, 1]`
- `extra.cot`: `[1, 1, 1]`
- `extra.meta_action`: `[1, 1, 1]`
- `pred_rot`: `[1, 1, 1, 64, 3, 3]`
- `pred_xyz`: `[1, 1, 1, 64, 3]`

## Blockers

- none

## Redacted Excerpt

```text

NVIDIA RTX 6000 Ada Generation, 570.124.06, 49140 MiB, 2 MiB, 8.9

{"attn_implementation": "eager", "clip_id": "030c760c-ae38-49aa-9ad8-f5650a545d26", "cot_excerpt": "Nudge to the left to clear the construction equipment blocking the right side of our lane", "inference_state": "shape_observed", "input_shapes": {"camera_indices": [4], "ego_future_rot": [1, 1, 64, 3, 3], "ego_future_xyz": [1, 1, 64, 3], "ego_history_rot": [1, 1, 16, 3, 3], "ego_history_xyz": [1, 1, 16, 3], "image_frames": [4, 4, 3, 1080, 1920], "tokenized_data": {"attention_mask": [1, 3086], "image_grid_thw": [16, 3], "input_ids": [1, 3086], "pixel_values": [11520, 1536]}}, "latency_ms": 124987.44, "max_generation_length": 256, "model_id": "nvidia/Alpamayo-1.5-10B", "num_traj_samples": 1, "nvidia_smi_exit_code": 0, "output_shapes": {"extra": {"answer": [1, 1, 1], "cot": [1, 1, 1], "meta_action": [1, 1, 1]}, "extra.answer": [1, 1, 1], "extra.cot": [1, 1, 1], "extra.meta_action": [1, 1, 1], "pred_rot": [1, 1, 1, 64, 3, 3], "pred_xyz": [1, 1, 1, 64, 3]}, "output_types": {"extra": "dict", "extra.answer": "ndarray", "extra.cot": "ndarray", "extra.meta_action": "ndarray", "pred_rot": "Tensor", "pred_xyz": "Tensor"}, "shape_source": "dataset", "shape_source_used": "dataset", "t0_us": 5100000}
{"torch": {"allocated_mb": 21218.13, "compute_capability": "8.9", "device_name": "NVIDIA RTX 6000 Ada Generation", "reserved_mb": 25994.0, "total_memory_mb": 48519.94, "vram_peak_mb": 24881.65}}
{"data_loader": "load_physical_aiavdataset", "dataset_keys": ["absolute_timestamps", "camera_indices", "clip_id", "ego_future_rot", "ego_future_xyz", "ego_history_rot", "ego_history_xyz", "image_frames", "relative_timestamps", "t0_us"], "entrypoint": "alpamayo1_5.test_inference equivalent", "message_builder": "helper.create_message", "trajectory_method": "sample_trajectories_from_data_with_vlm_rollout"}
{"pip_freeze_exit_code": 0, "python": "/workspace/alpamayo1.5/a1_5_venv/bin/python"}
```