#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "usage: $0 user@host [local-output-dir]" >&2
  exit 2
fi

REMOTE="$1"
ENV_FILE="${DRIVERX_ENV_FILE:-.env}"
if [ -f "${ENV_FILE}" ]; then
  set -a
  # shellcheck disable=SC1090
  . "${ENV_FILE}"
  set +a
fi

RUN_ID="${RUN_ID:-alpamayo-shape-probe-$(date -u +%Y%m%dT%H%M%SZ)}"
REMOTE_ROOT="${REMOTE_ROOT:-/workspace/0xdriver-artifacts/alpamayo-shape-probe/$RUN_ID}"
LOCAL_OUTPUT="${2:-${LOCAL_OUTPUT:-artifacts/remote/alpamayo-shape-probe/$RUN_ID}}"
MODEL_ID="${ALPAMAYO_REPO_ID:-nvidia/Alpamayo-1.5-10B}"
PYTHON_BIN="${PYTHON_BIN:-/workspace/alpamayo1.5/a1_5_venv/bin/python}"
ALPAMAYO_CLIP_ID="${ALPAMAYO_CLIP_ID:-030c760c-ae38-49aa-9ad8-f5650a545d26}"
ALPAMAYO_T0_US="${ALPAMAYO_T0_US:-5100000}"
ALPAMAYO_NUM_TRAJ_SAMPLES="${ALPAMAYO_NUM_TRAJ_SAMPLES:-1}"
ALPAMAYO_MAX_GENERATION_LENGTH="${ALPAMAYO_MAX_GENERATION_LENGTH:-256}"
ALPAMAYO_ATTN_IMPLEMENTATION="${ALPAMAYO_ATTN_IMPLEMENTATION:-eager}"
ALPAMAYO_SHAPE_SOURCE="${ALPAMAYO_SHAPE_SOURCE:-auto}"
ALPAMAYO_SYNTHETIC_HEIGHT="${ALPAMAYO_SYNTHETIC_HEIGHT:-384}"
ALPAMAYO_SYNTHETIC_WIDTH="${ALPAMAYO_SYNTHETIC_WIDTH:-448}"
REMOTE_CACHE_ROOT="${REMOTE_CACHE_ROOT:-/workspace/.cache/driverx}"
SSH_OPTIONS="${GPU_SSH_OPTS:-${SSH_OPTS:-}}"
SSH_RSH="ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new"

ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new "$REMOTE" "mkdir -p '$REMOTE_ROOT' '$REMOTE_CACHE_ROOT'"

if [ -n "${HF_TOKEN:-}" ]; then
  printf '%s' "$HF_TOKEN" | ssh ${SSH_OPTIONS} "$REMOTE" "cat > '$REMOTE_ROOT/.hf_token' && chmod 600 '$REMOTE_ROOT/.hf_token'"
fi

ssh ${SSH_OPTIONS} "$REMOTE" "cat > '$REMOTE_ROOT/shape_probe.py'" <<'PY'
from __future__ import annotations

import json
import os
import subprocess
import time
import traceback
from pathlib import Path
from typing import Any


def run(command: list[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=45,
        )
        return completed.returncode, completed.stdout
    except Exception as exc:
        return 1, f"{type(exc).__name__}: {exc}"


def redact(text: str) -> str:
    token = os.environ.get("HF_TOKEN", "")
    if token:
        text = text.replace(token, "[REDACTED]")
    return text


def shape_of(value: Any) -> Any:
    shape = getattr(value, "shape", None)
    if shape is not None:
        return list(shape)
    if isinstance(value, dict):
        return {str(key): shape_of(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [len(value)]
    return None


def type_of(value: Any) -> str:
    if isinstance(value, dict):
        return "dict"
    if hasattr(value, "__class__"):
        return value.__class__.__name__
    return type(value).__name__


remote_root = Path(os.environ["REMOTE_ROOT"])
model_id = os.environ["MODEL_ID"]
clip_id = os.environ["ALPAMAYO_CLIP_ID"]
t0_us = int(os.environ["ALPAMAYO_T0_US"])
num_traj_samples = int(os.environ["ALPAMAYO_NUM_TRAJ_SAMPLES"])
max_generation_length = int(os.environ["ALPAMAYO_MAX_GENERATION_LENGTH"])
attn_implementation = os.environ.get("ALPAMAYO_ATTN_IMPLEMENTATION", "eager").strip() or "eager"
shape_source = os.environ.get("ALPAMAYO_SHAPE_SOURCE", "auto").strip() or "auto"
synthetic_height = int(os.environ.get("ALPAMAYO_SYNTHETIC_HEIGHT", "384"))
synthetic_width = int(os.environ.get("ALPAMAYO_SYNTHETIC_WIDTH", "448"))
token_file = remote_root / ".hf_token"
if token_file.exists():
    os.environ["HF_TOKEN"] = token_file.read_text(encoding="utf-8").strip()

log_lines: list[str] = []
probe: dict[str, Any] = {
    "model_id": model_id,
    "clip_id": clip_id,
    "t0_us": t0_us,
    "num_traj_samples": num_traj_samples,
    "max_generation_length": max_generation_length,
    "attn_implementation": attn_implementation,
    "shape_source": shape_source,
    "inference_state": "not_started",
}
memory: dict[str, Any] = {}
inventory: dict[str, Any] = {
    "entrypoint": "alpamayo1_5.test_inference equivalent",
    "data_loader": "load_physical_aiavdataset",
    "message_builder": "helper.create_message",
    "trajectory_method": "sample_trajectories_from_data_with_vlm_rollout",
}


def synthetic_data() -> dict[str, Any]:
    image_frames = torch.zeros(
        (4, 4, 3, synthetic_height, synthetic_width),
        dtype=torch.uint8,
    )
    camera_indices = torch.tensor([0, 1, 2, 6], dtype=torch.int64)
    ego_history_xyz = torch.zeros((1, 1, 16, 3), dtype=torch.float32)
    ego_history_rot = torch.eye(3, dtype=torch.float32).reshape(1, 1, 1, 3, 3).repeat(1, 1, 16, 1, 1)
    ego_future_xyz = torch.zeros((1, 1, 64, 3), dtype=torch.float32)
    ego_future_rot = torch.eye(3, dtype=torch.float32).reshape(1, 1, 1, 3, 3).repeat(1, 1, 64, 1, 1)
    relative_timestamps = torch.arange(4, dtype=torch.float32).reshape(1, 4).repeat(4, 1) * 0.1
    absolute_timestamps = torch.arange(4, dtype=torch.int64).reshape(1, 4).repeat(4, 1)
    return {
        "image_frames": image_frames,
        "camera_indices": camera_indices,
        "ego_history_xyz": ego_history_xyz,
        "ego_history_rot": ego_history_rot,
        "ego_future_xyz": ego_future_xyz,
        "ego_future_rot": ego_future_rot,
        "relative_timestamps": relative_timestamps,
        "absolute_timestamps": absolute_timestamps,
        "t0_us": t0_us,
        "clip_id": "synthetic_shape_probe",
    }

code, gpu_snapshot = run(
    [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,memory.used,compute_cap",
        "--format=csv,noheader",
    ]
)
(remote_root / "gpu_snapshot.txt").write_text(gpu_snapshot, encoding="utf-8")
probe["nvidia_smi_exit_code"] = code

code, freeze = run([os.environ.get("PYTHON_BIN", "python3"), "-m", "pip", "freeze"])
if code != 0:
    code, freeze = run(["uv", "pip", "freeze", "--python", os.environ.get("PYTHON_BIN", "python3")])
(remote_root / "package_versions.json").write_text(
    json.dumps({"pip_freeze_exit_code": code, "python": os.environ.get("PYTHON_BIN", "python3")}, indent=2),
    encoding="utf-8",
)

started = time.perf_counter()
try:
    import torch
    from alpamayo1_5 import helper
    from alpamayo1_5.load_physical_aiavdataset import load_physical_aiavdataset
    from alpamayo1_5.models.alpamayo1_5 import Alpamayo1_5

    probe["inference_state"] = "loading_dataset"
    if shape_source == "synthetic":
        data = synthetic_data()
        probe["shape_source_used"] = "synthetic"
    else:
        try:
            data = load_physical_aiavdataset(clip_id, t0_us=t0_us)
            probe["shape_source_used"] = "dataset"
        except Exception:
            if shape_source != "auto":
                raise
            log_lines.append("Dataset load failed; falling back to synthetic shape probe input.")
            log_lines.append(traceback.format_exc())
            data = synthetic_data()
            probe["shape_source_used"] = "synthetic_after_dataset_blocker"
    input_shapes = {
        "image_frames": shape_of(data.get("image_frames")),
        "camera_indices": shape_of(data.get("camera_indices")),
        "ego_history_xyz": shape_of(data.get("ego_history_xyz")),
        "ego_history_rot": shape_of(data.get("ego_history_rot")),
        "ego_future_xyz": shape_of(data.get("ego_future_xyz")),
        "ego_future_rot": shape_of(data.get("ego_future_rot")),
    }
    inventory["dataset_keys"] = sorted(str(key) for key in data.keys())
    messages = helper.create_message(
        frames=data["image_frames"].flatten(0, 1),
        camera_indices=data["camera_indices"],
    )

    probe["inference_state"] = "loading_model"
    load_kwargs: dict[str, Any] = {"dtype": torch.bfloat16}
    if os.environ.get("HF_TOKEN"):
        load_kwargs["token"] = os.environ["HF_TOKEN"]
    if attn_implementation not in {"default", "none"}:
        load_kwargs["attn_implementation"] = attn_implementation
    model = Alpamayo1_5.from_pretrained(model_id, **load_kwargs).to("cuda")
    processor = helper.get_processor(model.tokenizer)
    tokenized = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=False,
        continue_final_message=True,
        return_dict=True,
        return_tensors="pt",
    )
    model_inputs = {
        "tokenized_data": tokenized,
        "ego_history_xyz": data["ego_history_xyz"],
        "ego_history_rot": data["ego_history_rot"],
    }
    model_inputs = helper.to_device(model_inputs, "cuda")
    input_shapes["tokenized_data"] = shape_of(model_inputs["tokenized_data"])

    probe["inference_state"] = "running_inference"
    torch.cuda.manual_seed_all(42)
    with torch.autocast("cuda", dtype=torch.bfloat16):
        pred_xyz, pred_rot, extra = model.sample_trajectories_from_data_with_vlm_rollout(
            data=model_inputs,
            top_p=0.98,
            temperature=0.6,
            num_traj_samples=num_traj_samples,
            max_generation_length=max_generation_length,
            return_extra=True,
        )
    output_shapes = {
        "pred_xyz": shape_of(pred_xyz),
        "pred_rot": shape_of(pred_rot),
        "extra": shape_of(extra),
    }
    output_types = {
        "pred_xyz": type_of(pred_xyz),
        "pred_rot": type_of(pred_rot),
        "extra": type_of(extra),
    }
    if isinstance(extra, dict):
        output_shapes.update({f"extra.{key}": shape_of(value) for key, value in extra.items()})
        output_types.update({f"extra.{key}": type_of(value) for key, value in extra.items()})
        if "cot" in extra:
            probe["cot_excerpt"] = str(extra["cot"].reshape(-1)[0])[:500]
    probe["input_shapes"] = input_shapes
    probe["output_shapes"] = output_shapes
    probe["output_types"] = output_types
    probe["inference_state"] = "shape_observed"
except Exception as exc:
    probe["inference_state"] = "failed"
    probe["error"] = f"{type(exc).__name__}: {exc}"
    log_lines.append(traceback.format_exc())
finally:
    probe["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
    try:
        import torch

        if torch.cuda.is_available():
            device = torch.cuda.current_device()
            props = torch.cuda.get_device_properties(device)
            memory["torch"] = {
                "device_name": props.name,
                "compute_capability": f"{props.major}.{props.minor}",
                "total_memory_mb": round(props.total_memory / 1024 / 1024, 2),
                "allocated_mb": round(torch.cuda.memory_allocated(device) / 1024 / 1024, 2),
                "reserved_mb": round(torch.cuda.memory_reserved(device) / 1024 / 1024, 2),
                "vram_peak_mb": round(torch.cuda.max_memory_allocated(device) / 1024 / 1024, 2),
            }
    except Exception:
        pass

(remote_root / "entrypoint_inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
(remote_root / "memory_usage.json").write_text(json.dumps(memory, indent=2), encoding="utf-8")
(remote_root / "alpamayo_shape_probe.json").write_text(json.dumps(probe, indent=2), encoding="utf-8")
(remote_root / "shape_probe.log").write_text(redact("\n".join(log_lines)), encoding="utf-8")
PY

ssh ${SSH_OPTIONS} "$REMOTE" "PATH=\"\$HOME/.local/bin:\$PATH\" REMOTE_ROOT='$REMOTE_ROOT' MODEL_ID='$MODEL_ID' ALPAMAYO_CLIP_ID='$ALPAMAYO_CLIP_ID' ALPAMAYO_T0_US='$ALPAMAYO_T0_US' ALPAMAYO_NUM_TRAJ_SAMPLES='$ALPAMAYO_NUM_TRAJ_SAMPLES' ALPAMAYO_MAX_GENERATION_LENGTH='$ALPAMAYO_MAX_GENERATION_LENGTH' ALPAMAYO_ATTN_IMPLEMENTATION='$ALPAMAYO_ATTN_IMPLEMENTATION' ALPAMAYO_SHAPE_SOURCE='$ALPAMAYO_SHAPE_SOURCE' ALPAMAYO_SYNTHETIC_HEIGHT='$ALPAMAYO_SYNTHETIC_HEIGHT' ALPAMAYO_SYNTHETIC_WIDTH='$ALPAMAYO_SYNTHETIC_WIDTH' PYTHON_BIN='$PYTHON_BIN' UV_CACHE_DIR='$REMOTE_CACHE_ROOT/uv' TRANSFORMERS_CACHE='$REMOTE_CACHE_ROOT/huggingface' HF_HUB_CACHE='$REMOTE_CACHE_ROOT/huggingface/hub' '$PYTHON_BIN' '$REMOTE_ROOT/shape_probe.py'; rm -f '$REMOTE_ROOT/.hf_token'"

mkdir -p "$LOCAL_OUTPUT"
rsync -rltz --prune-empty-dirs \
  -e "${SSH_RSH}" \
  --no-owner \
  --no-group \
  --include='*/' \
  --include='alpamayo_shape_probe.json' \
  --include='entrypoint_inventory.json' \
  --include='gpu_snapshot.txt' \
  --include='package_versions.json' \
  --include='memory_usage.json' \
  --include='shape_probe.log' \
  --exclude='*' \
  "$REMOTE:${REMOTE_ROOT%/}/" \
  "$LOCAL_OUTPUT/" || {
    echo "rsync pullback failed; falling back to ssh tar stream." >&2
    ssh ${SSH_OPTIONS} "$REMOTE" "cd '$REMOTE_ROOT' && files=''; for f in alpamayo_shape_probe.json entrypoint_inventory.json gpu_snapshot.txt package_versions.json memory_usage.json shape_probe.log; do if [ -e \"\$f\" ]; then files=\"\$files \$f\"; fi; done; if [ -n \"\$files\" ]; then tar -cf - \$files; fi" \
      | tar -xf - -C "$LOCAL_OUTPUT" || true
  }

PYTHONPATH="${PYTHONPATH:-src}" python3 -m driverx probe-alpamayo-shapes \
  --artifact-root "$LOCAL_OUTPUT" \
  --model-id "$MODEL_ID" \
  --output-root "$(dirname "$LOCAL_OUTPUT")" \
  --run-id "$(basename "$LOCAL_OUTPUT")-summary"
