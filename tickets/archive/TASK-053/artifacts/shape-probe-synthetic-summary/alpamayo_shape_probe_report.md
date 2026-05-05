# Alpamayo Shape Probe Report

- model_id: `nvidia/Alpamayo-1.5-10B`
- status: `shape_observed`
- blocked: `False`
- inference_state: `shape_observed`
- latency_ms: `96673.62`
- vram_peak_mb: `24478.66`

## Input Shapes

- `camera_indices`: `[4]`
- `ego_future_rot`: `[1, 1, 64, 3, 3]`
- `ego_future_xyz`: `[1, 1, 64, 3]`
- `ego_history_rot`: `[1, 1, 16, 3, 3]`
- `ego_history_xyz`: `[1, 1, 16, 3]`
- `image_frames`: `[4, 4, 3, 384, 448]`
- `tokenized_data`: `{'input_ids': [1, 2894], 'attention_mask': [1, 2894], 'pixel_values': [10752, 1536], 'image_grid_thw': [16, 3]}`

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
Dataset load failed; falling back to synthetic shape probe input.
Traceback (most recent call last):
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 402, in [REDACTED]
    response.raise_for_status()
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/requests/models.py", line 1026, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 403 Client Error: Forbidden for url: https://huggingface.co/api/datasets/nvidia/PhysicalAI-Autonomous-Vehicles/refs

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/workspace/0xdriver-artifacts/alpamayo-shape-probe/task53-shape-probe-synthetic-20260505T165013Z/shape_probe.py", line 143, in <module>
    data = load_physical_aiavdataset(clip_id, t0_us=t0_us)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/alpamayo1.5/src/alpamayo1_5/load_physical_aiavdataset.py", line 71, in load_physical_aiavdataset
    avdi = physical_ai_av.PhysicalAIAVDatasetInterface()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/physical_ai_av/dataset.py", line 53, in __init__
    super().__init__(
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/physical_ai_av/utils/[REDACTED].py", line 74, in __init__
    for branch in self.api.list_repo_refs(
                  ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 114, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/huggingface_hub/hf_api.py", line 3251, in list_repo_refs
    [REDACTED](response)
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 419, in [REDACTED]
    raise _format(GatedRepoError, message, response) from e
huggingface_hub.errors.GatedRepoError: 403 Client Error. (Request ID: Root=1-69fa1fef-65dc7ff33c550ae147890187;4753666c-33ea-4fbc-be14-c3f5cc13edb5)

Cannot access gated repo for url https://huggingface.co/api/datasets/nvidia/PhysicalAI-Autonomous-Vehicles/refs.
Access to dataset nvidia/PhysicalAI-Autonomous-Vehicles is restricted a
```