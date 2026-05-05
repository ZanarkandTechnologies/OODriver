"""Materialize DriverX/CARLA capture packages into Alpamayo tensor contracts."""

from __future__ import annotations

import json
import struct
from importlib import import_module
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

EXPECTED_FRAMES_PER_CAMERA = 4
EXPECTED_HISTORY_STEPS = 16


@dataclass(frozen=True)
class AlpamayoMaterializedFrame:
    camera_index: int
    frame_index: int
    original_path: str
    resolved_path: str
    width: int | None
    height: int | None
    file_width: int | None = None
    file_height: int | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "camera_index": self.camera_index,
            "frame_index": self.frame_index,
            "original_path": self.original_path,
            "resolved_path": self.resolved_path,
            "width": self.width,
            "height": self.height,
            "file_width": self.file_width,
            "file_height": self.file_height,
        }


@dataclass(frozen=True)
class AlpamayoTensorManifest:
    frame_name: str
    source_package: str
    image_root: str | None
    camera_indices: list[int]
    image_frames_shape: list[int | None]
    camera_indices_shape: list[int]
    ego_history_xyz_shape: list[int]
    ego_history_rot_shape: list[int]
    materialized_frames: list[AlpamayoMaterializedFrame]
    nav_text: str | None = None
    memory_context_count: int = 0
    torch_ready: bool = False
    validation_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "frame_name": self.frame_name,
            "source_package": self.source_package,
            "image_root": self.image_root,
            "camera_indices": self.camera_indices,
            "image_frames_shape": self.image_frames_shape,
            "camera_indices_shape": self.camera_indices_shape,
            "ego_history_xyz_shape": self.ego_history_xyz_shape,
            "ego_history_rot_shape": self.ego_history_rot_shape,
            "materialized_frames": [frame.to_jsonable() for frame in self.materialized_frames],
            "nav_text": self.nav_text,
            "memory_context_count": self.memory_context_count,
            "torch_ready": self.torch_ready,
            "validation_errors": self.validation_errors,
            "warnings": self.warnings,
            "torch_loader_contract": _torch_loader_contract(self),
        }


def materialize_alpamayo_input(
    package_path: Path,
    image_root: Path | None = None,
) -> AlpamayoTensorManifest:
    """Validate a DriverX Alpamayo package and compute torch-ready shapes.

    The local materializer intentionally avoids importing torch. It proves the
    file/layout contract that the remote GPU runner will load into tensors.
    """

    package_path = package_path.expanduser()
    payload = json.loads(package_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Alpamayo input package must be a JSON object: {package_path}")

    errors: list[str] = []
    warnings: list[str] = []
    frame_name = str(payload.get("frame_name") or package_path.stem)
    camera_windows = _list_of_dicts(payload.get("camera_windows"), "camera_windows", errors)
    camera_indices = _camera_indices(payload.get("camera_indices"), errors)
    if camera_windows and camera_indices and len(camera_windows) != len(camera_indices):
        errors.append(
            f"camera_indices length {len(camera_indices)} does not match camera_windows length {len(camera_windows)}."
        )

    materialized_frames: list[AlpamayoMaterializedFrame] = []
    frame_counts: set[int] = set()
    dimensions: set[tuple[int, int]] = set()
    for window_index, window in enumerate(camera_windows):
        camera_index = _int_value(window.get("camera_index"), f"camera_windows[{window_index}].camera_index", errors)
        if (
            camera_index is not None
            and window_index < len(camera_indices)
            and camera_index != camera_indices[window_index]
        ):
            errors.append(
                f"camera_windows[{window_index}].camera_index {camera_index} does not match camera_indices[{window_index}] {camera_indices[window_index]}."
            )
        frames = _list_of_dicts(
            window.get("frames"),
            f"camera_windows[{window_index}].frames",
            errors,
        )
        frame_counts.add(len(frames))
        for fallback_frame_index, frame in enumerate(frames):
            frame_index = _optional_int(frame.get("frame_index"))
            original_path = str(frame.get("path") or frame.get("source_name") or "")
            if not original_path:
                errors.append(
                    f"camera_windows[{window_index}].frames[{fallback_frame_index}] is missing path/source_name."
                )
            resolved = _resolve_image_path(original_path, package_path, image_root)
            width = _optional_int(frame.get("width"))
            height = _optional_int(frame.get("height"))
            file_size = _read_png_size(resolved) if resolved.exists() else None
            if not resolved.exists():
                errors.append(f"Image path does not exist: {original_path}")
            elif file_size is None:
                warnings.append(f"Image path is not a readable PNG header: {resolved}")
            else:
                file_width, file_height = file_size
                if width is not None and height is not None and (width, height) != file_size:
                    errors.append(
                        f"Image metadata {width}x{height} does not match PNG header {file_width}x{file_height}: {original_path}"
                    )
                width = width if width is not None else file_width
                height = height if height is not None else file_height
            if width is not None and height is not None:
                dimensions.add((width, height))
            materialized_frames.append(
                AlpamayoMaterializedFrame(
                    camera_index=camera_index if camera_index is not None else -1,
                    frame_index=frame_index if frame_index is not None else fallback_frame_index,
                    original_path=original_path,
                    resolved_path=str(resolved),
                    width=width,
                    height=height,
                    file_width=file_size[0] if file_size else None,
                    file_height=file_size[1] if file_size else None,
                )
            )

    if frame_counts and frame_counts != {EXPECTED_FRAMES_PER_CAMERA}:
        errors.append(
            f"Expected {EXPECTED_FRAMES_PER_CAMERA} frames per camera; observed {sorted(frame_counts)}."
        )
    if len(dimensions) > 1:
        errors.append(f"All image frames must share one H/W; observed {sorted(dimensions)}.")
    camera_count = len(camera_windows)
    frame_count = next(iter(frame_counts)) if len(frame_counts) == 1 else None
    height = next(iter(dimensions))[1] if len(dimensions) == 1 else None
    width = next(iter(dimensions))[0] if len(dimensions) == 1 else None

    ego_history_xyz_shape = [1, 1, *_nested_shape(payload.get("ego_history_xyz"))]
    ego_history_rot_shape = [1, 1, *_nested_shape(payload.get("ego_history_rot"))]
    _validate_history_shape(
        ego_history_xyz_shape,
        [1, 1, EXPECTED_HISTORY_STEPS, 3],
        "ego_history_xyz",
        errors,
    )
    _validate_history_shape(
        ego_history_rot_shape,
        [1, 1, EXPECTED_HISTORY_STEPS, 3, 3],
        "ego_history_rot",
        errors,
    )

    memory_context = payload.get("memory_context")
    memory_context_count = len(memory_context) if isinstance(memory_context, list) else 0
    if memory_context is not None and not isinstance(memory_context, list):
        warnings.append("memory_context is present but is not a list; it will not be used.")

    return AlpamayoTensorManifest(
        frame_name=frame_name,
        source_package=str(package_path),
        image_root=str(image_root.expanduser()) if image_root is not None else None,
        camera_indices=camera_indices,
        image_frames_shape=[camera_count, frame_count, 3, height, width],
        camera_indices_shape=[len(camera_indices)],
        ego_history_xyz_shape=ego_history_xyz_shape,
        ego_history_rot_shape=ego_history_rot_shape,
        materialized_frames=materialized_frames,
        nav_text=payload.get("nav_text") if isinstance(payload.get("nav_text"), str) else None,
        memory_context_count=memory_context_count,
        torch_ready=not errors,
        validation_errors=errors,
        warnings=warnings,
    )


def load_alpamayo_torch_tensors(
    package_path: Path,
    image_root: Path | None = None,
    *,
    device: str | None = None,
) -> dict[str, Any]:
    """Load a validated Alpamayo package into torch tensors.

    This helper is lazy so local DriverX tests do not require torch. It is
    intended for the remote Alpamayo runner, where torch and Pillow already
    exist beside the model runtime.
    """

    try:
        torch = import_module("torch")
    except ImportError as exc:
        raise ImportError(
            "torch is required to load Alpamayo tensors; run this helper inside the remote Alpamayo environment."
        ) from exc
    try:
        image_module = import_module("PIL.Image")
    except ImportError as exc:
        raise ImportError("Pillow is required to load Alpamayo PNG frames.") from exc

    manifest = materialize_alpamayo_input(package_path, image_root=image_root)
    if manifest.validation_errors:
        raise ValueError(
            "Cannot load Alpamayo tensors from invalid package: "
            + "; ".join(manifest.validation_errors)
        )
    payload = json.loads(package_path.expanduser().read_text(encoding="utf-8"))
    frame_count = manifest.image_frames_shape[1]
    if not isinstance(frame_count, int):
        raise ValueError("Cannot load tensors when frame count is unknown.")
    camera_tensors: list[Any] = []
    for camera_offset in range(len(manifest.camera_indices)):
        start = camera_offset * frame_count
        frames = manifest.materialized_frames[start : start + frame_count]
        camera_tensors.append(
            torch.stack(
                [
                    _load_rgb_chw_tensor(torch, image_module, Path(frame.resolved_path))
                    for frame in frames
                ]
            )
        )
    tensors = {
        "image_frames": torch.stack(camera_tensors),
        "camera_indices": torch.tensor(manifest.camera_indices, dtype=torch.long),
        "ego_history_xyz": torch.tensor(payload["ego_history_xyz"], dtype=torch.float32).reshape(
            1,
            1,
            EXPECTED_HISTORY_STEPS,
            3,
        ),
        "ego_history_rot": torch.tensor(payload["ego_history_rot"], dtype=torch.float32).reshape(
            1,
            1,
            EXPECTED_HISTORY_STEPS,
            3,
            3,
        ),
        "manifest": manifest.to_jsonable(),
    }
    if device is not None:
        for key in ("image_frames", "camera_indices", "ego_history_xyz", "ego_history_rot"):
            tensors[key] = tensors[key].to(device)
    return tensors


def write_alpamayo_tensor_materialization(
    run_dir: Path,
    manifest: AlpamayoTensorManifest,
) -> dict[str, Any]:
    """Write JSON/Markdown materialization artifacts."""

    run_dir.mkdir(parents=True, exist_ok=True)
    payload = manifest.to_jsonable()
    json_path = run_dir / "alpamayo_tensor_manifest.json"
    report_path = run_dir / "alpamayo_tensor_manifest.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    return {
        **payload,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def _list_of_dicts(value: Any, name: str, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"{name} must be a list.")
        return []
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if isinstance(item, dict):
            result.append(item)
        else:
            errors.append(f"{name}[{index}] must be an object.")
    return result


def _camera_indices(value: Any, errors: list[str]) -> list[int]:
    if not isinstance(value, list):
        errors.append("camera_indices must be a list.")
        return []
    indices: list[int] = []
    for index, item in enumerate(value):
        item_int = _int_value(item, f"camera_indices[{index}]", errors)
        if item_int is not None:
            indices.append(item_int)
    return indices


def _int_value(value: Any, name: str, errors: list[str]) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{name} must be an integer.")
        return None
    return value


def _optional_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _resolve_image_path(path_text: str, package_path: Path, image_root: Path | None) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    candidates: list[Path] = []
    if image_root is not None:
        root = image_root.expanduser()
        candidates.append(root / path)
        candidates.append(root / path.name)
    candidates.append(package_path.parent / path)
    candidates.append(Path.cwd() / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0] if candidates else path


def _read_png_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) < 24 or not header.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    chunk_type = header[12:16]
    if chunk_type != b"IHDR":
        return None
    width, height = struct.unpack(">II", header[16:24])
    return int(width), int(height)


def _load_rgb_chw_tensor(torch: Any, image_module: Any, path: Path) -> Any:
    image = image_module.open(path).convert("RGB")
    width, height = image.size
    raw = image.tobytes()
    if hasattr(torch, "frombuffer"):
        tensor = torch.frombuffer(raw, dtype=torch.uint8)
    else:
        tensor = torch.ByteTensor(torch.ByteStorage.from_buffer(raw))
    return tensor.reshape(height, width, 3).permute(2, 0, 1).to(dtype=torch.float32) / 255.0


def _nested_shape(value: Any) -> list[int]:
    shape: list[int] = []
    current = value
    while isinstance(current, list):
        shape.append(len(current))
        if not current:
            break
        current = current[0]
    return shape


def _validate_history_shape(
    observed: list[int],
    expected: list[int],
    name: str,
    errors: list[str],
) -> None:
    if observed != expected:
        errors.append(f"{name} shape {observed} does not match expected {expected}.")


def _torch_loader_contract(manifest: AlpamayoTensorManifest) -> dict[str, Any]:
    return {
        "image_frames": {
            "shape": manifest.image_frames_shape,
            "dtype": "torch.float32",
            "layout": "[num_cameras, num_frames, channels, height, width]",
            "normalization": "RGB pixels converted to float32 in [0, 1]",
            "loader_note": "Use driverx.policies.load_alpamayo_torch_tensors(...) in the remote Alpamayo environment.",
        },
        "camera_indices": {
            "shape": manifest.camera_indices_shape,
            "dtype": "torch.long",
            "values": manifest.camera_indices,
        },
        "ego_history_xyz": {
            "shape": manifest.ego_history_xyz_shape,
            "dtype": "torch.float32",
        },
        "ego_history_rot": {
            "shape": manifest.ego_history_rot_shape,
            "dtype": "torch.float32",
        },
        "message_context": {
            "nav_text": manifest.nav_text,
            "memory_context_count": manifest.memory_context_count,
            "rule": "DriverX memory is prompt-side context only; it must not alter Alpamayo weights.",
        },
    }


def _markdown(payload: dict[str, Any]) -> str:
    errors = payload["validation_errors"]
    warnings = payload["warnings"]
    lines = [
        "# Alpamayo Tensor Manifest",
        "",
        f"- frame_name: `{payload['frame_name']}`",
        f"- torch_ready: `{payload['torch_ready']}`",
        f"- image_frames: `{payload['image_frames_shape']}`",
        f"- camera_indices: `{payload['camera_indices']}`",
        f"- ego_history_xyz: `{payload['ego_history_xyz_shape']}`",
        f"- ego_history_rot: `{payload['ego_history_rot_shape']}`",
        f"- memory_context_count: `{payload['memory_context_count']}`",
        "",
        "## Validation Errors",
        "",
    ]
    lines.extend([f"- {error}" for error in errors] or ["- none"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {warning}" for warning in warnings] or ["- none"])
    lines.extend(["", "## Camera Frames", ""])
    for frame in payload["materialized_frames"]:
        lines.append(
            f"- camera `{frame['camera_index']}` frame `{frame['frame_index']}`: `{frame['resolved_path']}`"
        )
    lines.extend(
        [
            "",
            "## Remote Loader Contract",
            "",
            "The remote runner should load PNGs as RGB, stack them as `[N, 4, 3, H, W]`, ",
            "create `camera_indices` as `torch.long`, and wrap ego history as `[1, 1, 16, ...]`.",
            "",
        ]
    )
    return "\n".join(lines)


__all__ = [
    "AlpamayoMaterializedFrame",
    "AlpamayoTensorManifest",
    "load_alpamayo_torch_tensors",
    "materialize_alpamayo_input",
    "write_alpamayo_tensor_materialization",
]
