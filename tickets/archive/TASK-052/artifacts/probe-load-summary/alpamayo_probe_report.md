# Alpamayo Probe Report

- model_id: `nvidia/Alpamayo-1.5-10B`
- status: `auth_blocked`
- blocked: `True`
- model_load_state: `failed`
- latency_ms: `38709.03`
- vram_peak_mb: `0.0`

## Blockers

- Hugging Face or model access was rejected.

## Artifacts

| artifact | present | bytes |
|---|---:|---:|
| `alpamayo_probe.json` | `True` | `1465` |
| `gpu_snapshot.txt` | `True` | `66` |
| `package_versions.json` | `True` | `150` |
| `package_versions.txt` | `True` | `2115` |
| `memory_usage.json` | `True` | `212` |
| `probe.log` | `True` | `21279` |

## Expected Adapter Schema

- status: `unverified_adapter_stub`
- trajectory target: `20 x 2` waypoints for 5 seconds at 4 Hz when available
- TASK-039 must replace this with observed input/output shape evidence before live CARLA control.

## Redacted Excerpt

```text
Alpamayo1_5 load failed; trying transformers auto fallback.
Traceback (most recent call last):
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 402, in [REDACTED]
    response.raise_for_status()
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/requests/models.py", line 1026, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 403 Client Error: Forbidden for url: https://huggingface.co/nvidia/Cosmos-Reason2-8B/resolve/main/config.json

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/transformers/utils/hub.py", line 479, in cached_files
    [REDACTED](
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 114, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1007, in [REDACTED]
    return _[REDACTED](
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1114, in _[REDACTED]
    _raise_on_head_call_error(head_call_error, force_download, local_files_only)
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1655, in _raise_on_head_call_error
    raise head_call_error
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1543, in _get_metadata_or_catch_error
    metadata = get_[REDACTED](
               ^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 114, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1460, in get_[REDACTED]
    r = _request_wrapper(
        ^^^^^^^^^^^^^^^^^
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 283, in _request_wrapper
    response = _request_wrapper(
               ^^^^^^^^^^^^^^^^^
  File "/workspa
```
