# Alpamayo Probe Report

- model_id: `nvidia/Alpamayo-1.5-10B`
- status: `runtime_blocked`
- blocked: `True`
- model_load_state: `failed`
- latency_ms: `76654.29`
- vram_peak_mb: `0.0`

## Blockers

- ValueError: Unrecognized processing class in nvidia/Alpamayo-1.5-10B. Can't instantiate a processor, a tokenizer, an image processor or a feature extractor for this model. Make sure the repository contains the files of at least one of those processing classes.

## Artifacts

| artifact | present | bytes |
|---|---:|---:|
| `alpamayo_probe.json` | `True` | `1194` |
| `gpu_snapshot.txt` | `True` | `66` |
| `package_versions.json` | `True` | `150` |
| `package_versions.txt` | `True` | `2115` |
| `memory_usage.json` | `True` | `212` |
| `probe.log` | `True` | `5985` |

## Expected Adapter Schema

- status: `unverified_adapter_stub`
- trajectory target: `20 x 2` waypoints for 5 seconds at 4 Hz when available
- TASK-039 must replace this with observed input/output shape evidence before live CARLA control.

## Redacted Excerpt

```text
Alpamayo1_5 load failed; trying transformers auto fallback.
Traceback (most recent call last):
  File "/workspace/0xdriver-artifacts/alpamayo-probe/task52-runpod-load-after-cosmos-20260505T160041Z/probe.py", line 117, in <module>
    Alpamayo1_5.from_pretrained(
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/transformers/modeling_utils.py", line 277, in _wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4971, in from_pretrained
    model = cls(config, *model_args, **model_kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/alpamayo1.5/src/alpamayo1_5/models/alpamayo1_5.py", line 94, in __init__
    super().__init__(config, pretrained_modules, original_vocab_size, print_param_count=False)
  File "/workspace/alpamayo1.5/src/alpamayo1_5/models/base_model.py", line 302, in __init__
    super().__init__(config)
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/transformers/modeling_utils.py", line 2076, in __init__
    self.config._attn_implementation_internal = self._check_and_adjust_attn_implementation(
                                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/transformers/modeling_utils.py", line 2686, in _check_and_adjust_attn_implementation
    applicable_attn_implementation = self.get_correct_attn_implementation(
                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/transformers/modeling_utils.py", line 2725, in get_correct_attn_implementation
    raise e
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/transformers/modeling_utils.py", line 2722, in get_correct_attn_implementation
    self._sdpa_can_dispatch(is_init_check)
  File "/workspace/alpamayo1.5/a1_5_venv/lib/python3.12/site-packages/transformers/modeling_utils.py", line 2574, in _sdpa_can_dispatch
    raise ValueError(
ValueError: Alpamayo1_5 does not support an attention implementation through torch.nn.functional.scaled_dot_product_attention yet. Please request the support for this architecture: https://github.com/huggingface/transformers/issues/28005. If you believe this error is a bug
```
