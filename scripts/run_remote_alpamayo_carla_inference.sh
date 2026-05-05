#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ] || [ "${2:-}" = "" ]; then
  echo "usage: $0 local-alpamayo-package.json user@host [local-output-dir]" >&2
  exit 2
fi

PACKAGE_PATH="$1"
REMOTE="$2"
ENV_FILE="${DRIVERX_ENV_FILE:-.env}"
if [ -f "${ENV_FILE}" ]; then
  set -a
  # shellcheck disable=SC1090
  . "${ENV_FILE}"
  set +a
fi

RUN_ID="${RUN_ID:-alpamayo-carla-live-$(date -u +%Y%m%dT%H%M%SZ)}"
REMOTE_ROOT="${REMOTE_ROOT:-/workspace/0xdriver-artifacts/alpamayo-carla-live/$RUN_ID}"
LOCAL_OUTPUT="${3:-${LOCAL_OUTPUT:-artifacts/remote/alpamayo-carla-live/$RUN_ID}}"
MODEL_ID="${ALPAMAYO_REPO_ID:-nvidia/Alpamayo-1.5-10B}"
PYTHON_BIN="${PYTHON_BIN:-/workspace/alpamayo1.5/a1_5_venv/bin/python}"
ALPAMAYO_NUM_TRAJ_SAMPLES="${ALPAMAYO_NUM_TRAJ_SAMPLES:-1}"
ALPAMAYO_MAX_GENERATION_LENGTH="${ALPAMAYO_MAX_GENERATION_LENGTH:-256}"
ALPAMAYO_ATTN_IMPLEMENTATION="${ALPAMAYO_ATTN_IMPLEMENTATION:-eager}"
REMOTE_CACHE_ROOT="${REMOTE_CACHE_ROOT:-/workspace/.cache/driverx}"
SSH_OPTIONS="${GPU_SSH_OPTS:-${SSH_OPTS:-}}"
SSH_RSH="ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new"

STAGING_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "${STAGING_DIR}"
}
trap cleanup EXIT

mkdir -p "${STAGING_DIR}/input/images"
python3 - "$PACKAGE_PATH" "${STAGING_DIR}/input/package.json" "${STAGING_DIR}/input/images" <<'PY'
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

source = Path(sys.argv[1]).expanduser()
target = Path(sys.argv[2])
image_dir = Path(sys.argv[3])
payload = json.loads(source.read_text(encoding="utf-8"))
package_parent = source.parent
seen: set[str] = set()
for window in payload.get("camera_windows", []):
    camera_index = int(window.get("camera_index", len(seen)))
    for frame in window.get("frames", []):
        original = str(frame.get("path") or frame.get("source_name") or "")
        path = Path(original).expanduser()
        if not path.is_absolute():
            candidates = [package_parent / path, Path.cwd() / path]
            path = next((candidate for candidate in candidates if candidate.exists()), candidates[-1])
        if not path.exists():
            raise FileNotFoundError(f"Image path does not exist: {original}")
        frame_index = int(frame.get("frame_index", 0))
        name = f"camera_{camera_index}_frame_{frame_index:03d}{path.suffix or '.png'}"
        while name in seen:
            name = f"camera_{camera_index}_frame_{frame_index:03d}_{len(seen)}{path.suffix or '.png'}"
        seen.add(name)
        shutil.copy2(path, image_dir / name)
        frame["path"] = f"images/{name}"
target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY

ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new "$REMOTE" "mkdir -p '$REMOTE_ROOT/input' '$REMOTE_CACHE_ROOT'"
COPYFILE_DISABLE=1 tar --no-xattrs --no-mac-metadata -C "${STAGING_DIR}/input" -cf - . | ssh ${SSH_OPTIONS} "$REMOTE" "tar --no-same-owner -C '$REMOTE_ROOT/input' -xf -"

if [ -n "${HF_TOKEN:-}" ]; then
  printf '%s' "$HF_TOKEN" | ssh ${SSH_OPTIONS} "$REMOTE" "cat > '$REMOTE_ROOT/.hf_token' && chmod 600 '$REMOTE_ROOT/.hf_token'"
fi

ssh ${SSH_OPTIONS} "$REMOTE" "cat > '$REMOTE_ROOT/carla_inference.py'" <<'PY'
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


def jsonable(value: Any, *, max_items: int = 4096) -> Any:
    if hasattr(value, "detach"):
        tensor = value.detach().cpu()
        if getattr(tensor, "numel", lambda: max_items + 1)() <= max_items:
            return tensor.tolist()
        return {"shape": list(tensor.shape), "truncated": True}
    if isinstance(value, dict):
        return {str(key): jsonable(item, max_items=max_items) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item, max_items=max_items) for item in list(value)[:64]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def first_text(value: Any) -> str:
    if isinstance(value, str):
        return value[:1000]
    if isinstance(value, dict):
        for key in ("cot", "answer", "reasoning"):
            if key in value:
                return first_text(value[key])
    if isinstance(value, (list, tuple)):
        current = value
        while isinstance(current, (list, tuple)) and current:
            current = current[0]
        return str(current)[:1000]
    if hasattr(value, "detach"):
        return first_text(jsonable(value, max_items=64))
    return str(value)[:1000]


def load_rgb_chw(torch: Any, image_module: Any, path: Path) -> Any:
    image = image_module.open(path).convert("RGB")
    width, height = image.size
    raw = image.tobytes()
    if hasattr(torch, "frombuffer"):
        tensor = torch.frombuffer(raw, dtype=torch.uint8).clone()
    else:
        tensor = torch.ByteTensor(torch.ByteStorage.from_buffer(raw))
    return tensor.reshape(height, width, 3).permute(2, 0, 1)


remote_root = Path(os.environ["REMOTE_ROOT"])
input_root = remote_root / "input"
model_id = os.environ["MODEL_ID"]
num_traj_samples = int(os.environ["ALPAMAYO_NUM_TRAJ_SAMPLES"])
max_generation_length = int(os.environ["ALPAMAYO_MAX_GENERATION_LENGTH"])
attn_implementation = os.environ.get("ALPAMAYO_ATTN_IMPLEMENTATION", "eager").strip() or "eager"
token_file = remote_root / ".hf_token"
if token_file.exists():
    os.environ["HF_TOKEN"] = token_file.read_text(encoding="utf-8").strip()

log_lines: list[str] = []
prediction: dict[str, Any] = {
    "model_id": model_id,
    "run_id": remote_root.name,
    "inference_state": "not_started",
    "attn_implementation": attn_implementation,
    "num_traj_samples": num_traj_samples,
}
memory: dict[str, Any] = {}

code, gpu_snapshot = run(
    [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,memory.used,compute_cap",
        "--format=csv,noheader",
    ]
)
(remote_root / "gpu_snapshot.txt").write_text(gpu_snapshot, encoding="utf-8")
prediction["nvidia_smi_exit_code"] = code

code, freeze = run([os.environ.get("PYTHON_BIN", "python3"), "-m", "pip", "freeze"])
(remote_root / "package_versions.json").write_text(
    json.dumps({"pip_freeze_exit_code": code, "python": os.environ.get("PYTHON_BIN", "python3")}, indent=2),
    encoding="utf-8",
)

started = time.perf_counter()
try:
    import torch
    from PIL import Image
    from alpamayo1_5 import helper
    from alpamayo1_5.models.alpamayo1_5 import Alpamayo1_5

    payload = json.loads((input_root / "package.json").read_text(encoding="utf-8"))
    camera_tensors = []
    for window in payload["camera_windows"]:
        frames = []
        for frame in window["frames"]:
            frames.append(load_rgb_chw(torch, Image, input_root / frame["path"]))
        camera_tensors.append(torch.stack(frames))
    image_frames = torch.stack(camera_tensors)
    camera_indices = torch.tensor(payload["camera_indices"], dtype=torch.long)
    ego_history_xyz = torch.tensor(payload["ego_history_xyz"], dtype=torch.float32).reshape(1, 1, 16, 3)
    ego_history_rot = torch.tensor(payload["ego_history_rot"], dtype=torch.float32).reshape(1, 1, 16, 3, 3)
    input_shapes = {
        "image_frames": shape_of(image_frames),
        "camera_indices": shape_of(camera_indices),
        "ego_history_xyz": shape_of(ego_history_xyz),
        "ego_history_rot": shape_of(ego_history_rot),
    }

    prediction["inference_state"] = "loading_model"
    load_kwargs: dict[str, Any] = {"dtype": torch.bfloat16}
    if os.environ.get("HF_TOKEN"):
        load_kwargs["token"] = os.environ["HF_TOKEN"]
    if attn_implementation not in {"default", "none"}:
        load_kwargs["attn_implementation"] = attn_implementation
    model = Alpamayo1_5.from_pretrained(model_id, **load_kwargs).to("cuda")
    processor = helper.get_processor(model.tokenizer)
    messages = helper.create_message(
        frames=image_frames.flatten(0, 1),
        camera_indices=camera_indices,
    )
    tokenized = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=False,
        continue_final_message=True,
        return_dict=True,
        return_tensors="pt",
    )
    model_inputs = helper.to_device(
        {
            "tokenized_data": tokenized,
            "ego_history_xyz": ego_history_xyz,
            "ego_history_rot": ego_history_rot,
        },
        "cuda",
    )
    input_shapes["tokenized_data"] = shape_of(model_inputs["tokenized_data"])

    prediction["inference_state"] = "running_inference"
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
    prediction["input_shapes"] = input_shapes
    prediction["output_shapes"] = {
        "pred_xyz": shape_of(pred_xyz),
        "pred_rot": shape_of(pred_rot),
        **({f"extra.{key}": shape_of(value) for key, value in extra.items()} if isinstance(extra, dict) else {}),
    }
    prediction["pred_xyz"] = pred_xyz.detach().float().cpu().tolist()
    prediction["pred_rot"] = pred_rot.detach().float().cpu().tolist()
    prediction["extra"] = jsonable(extra, max_items=512)
    prediction["cot_summary"] = first_text(extra)
    prediction["inference_state"] = "completed"
except Exception as exc:
    prediction["inference_state"] = "failed"
    prediction["error"] = f"{type(exc).__name__}: {exc}"
    log_lines.append(traceback.format_exc())
finally:
    prediction["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)

try:
    import torch

    if torch.cuda.is_available():
        device = torch.cuda.current_device()
        memory["vram_peak_mb"] = round(torch.cuda.max_memory_allocated(device) / 1024 / 1024, 2)
        prediction["vram_peak_mb"] = memory["vram_peak_mb"]
except Exception:
    pass

(remote_root / "memory_usage.json").write_text(json.dumps(memory, indent=2), encoding="utf-8")
(remote_root / "alpamayo_live_prediction.json").write_text(json.dumps(prediction, indent=2), encoding="utf-8")
(remote_root / "alpamayo_live.log").write_text(redact("\n".join(log_lines)), encoding="utf-8")
if token_file.exists():
    token_file.unlink()
PY

ssh ${SSH_OPTIONS} "$REMOTE" "PATH=\"\$HOME/.local/bin:\$PATH\" REMOTE_ROOT='$REMOTE_ROOT' MODEL_ID='$MODEL_ID' ALPAMAYO_NUM_TRAJ_SAMPLES='$ALPAMAYO_NUM_TRAJ_SAMPLES' ALPAMAYO_MAX_GENERATION_LENGTH='$ALPAMAYO_MAX_GENERATION_LENGTH' ALPAMAYO_ATTN_IMPLEMENTATION='$ALPAMAYO_ATTN_IMPLEMENTATION' PYTHON_BIN='$PYTHON_BIN' XDG_CACHE_HOME='$REMOTE_CACHE_ROOT' UV_CACHE_DIR='$REMOTE_CACHE_ROOT/uv' HF_HOME='$REMOTE_CACHE_ROOT/huggingface' TRANSFORMERS_CACHE='$REMOTE_CACHE_ROOT/huggingface' HF_HUB_CACHE='$REMOTE_CACHE_ROOT/huggingface/hub' '$PYTHON_BIN' '$REMOTE_ROOT/carla_inference.py'; status=\$?; rm -f '$REMOTE_ROOT/.hf_token'; exit \$status"

mkdir -p "$LOCAL_OUTPUT"
rsync -rltz --prune-empty-dirs \
  -e "${SSH_RSH}" \
  --no-owner \
  --no-group \
  --include='*/' \
  --include='alpamayo_live_prediction.json' \
  --include='alpamayo_live.log' \
  --include='memory_usage.json' \
  --include='gpu_snapshot.txt' \
  --include='package_versions.json' \
  --exclude='*' \
  "$REMOTE:${REMOTE_ROOT%/}/" \
  "$LOCAL_OUTPUT/" || {
    echo "rsync pullback failed; falling back to ssh tar stream." >&2
    ssh ${SSH_OPTIONS} "$REMOTE" "cd '$REMOTE_ROOT' && files=''; for f in alpamayo_live_prediction.json alpamayo_live.log memory_usage.json gpu_snapshot.txt package_versions.json; do if [ -e \"\$f\" ]; then files=\"\$files \$f\"; fi; done; if [ -n \"\$files\" ]; then tar -cf - \$files; fi" \
      | tar -xf - -C "$LOCAL_OUTPUT" || true
  }

if [ -s "$LOCAL_OUTPUT/alpamayo_live_prediction.json" ]; then
  PYTHONPATH="${PYTHONPATH:-src}" python3 -m driverx run-alpamayo-live \
    --package "$PACKAGE_PATH" \
    --prediction-json "$LOCAL_OUTPUT/alpamayo_live_prediction.json" \
    --model-id "$MODEL_ID" \
    --output-root "$(dirname "$LOCAL_OUTPUT")" \
    --run-id "$(basename "$LOCAL_OUTPUT")-summary" || true
fi
