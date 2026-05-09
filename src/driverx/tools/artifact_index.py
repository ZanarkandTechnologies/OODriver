"""Index recent OODrive artifacts for agent workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir


def build_artifact_index(output_root: Path, *, limit: int = 50) -> dict[str, Any]:
    files = sorted((path for path in output_root.rglob("*") if path.is_file()), key=lambda path: path.stat().st_mtime, reverse=True)
    entries = [_entry(path) for path in files[: max(1, limit)]]
    return {
        "schema_version": "oodrive.artifact_index.v1",
        "output_root": str(output_root),
        "artifact_count": len(entries),
        "artifacts": entries,
    }


def write_artifact_index(run_dir: Path, index: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "artifacts_index.json"
    report_path = run_dir / "artifacts_index.md"
    json_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(index), encoding="utf-8")
    return {**index, "json_path": str(json_path), "report_path": str(report_path)}


def build_and_write_artifact_index(output_root: Path, run_id: str, *, limit: int = 50) -> dict[str, Any]:
    run_dir = prepare_run_dir(output_root, run_id)
    return write_artifact_index(run_dir, build_artifact_index(output_root, limit=limit))


def _entry(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    kind = {
        ".json": "json",
        ".md": "report",
        ".mp4": "video",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".html": "html",
    }.get(suffix, "file")
    proof_level = "media" if kind in {"video", "image"} else "metadata"
    return {"path": str(path), "kind": kind, "proof_level": proof_level, "size_bytes": path.stat().st_size}


def _markdown(index: dict[str, Any]) -> str:
    lines = ["# OODrive Artifact Index", "", f"- artifacts: {index.get('artifact_count', 0)}", ""]
    for entry in list(index.get("artifacts", []))[:20]:
        if isinstance(entry, dict):
            lines.append(f"- `{entry.get('kind')}` {entry.get('path')}")
    return "\n".join(lines) + "\n"


__all__ = ["build_and_write_artifact_index", "build_artifact_index", "write_artifact_index"]
