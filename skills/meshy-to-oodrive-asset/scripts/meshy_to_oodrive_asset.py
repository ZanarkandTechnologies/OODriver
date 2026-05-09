#!/usr/bin/env python3
"""Generate Meshy assets and emit OODrive external manifests.

This helper intentionally lives in a repo-local Codex skill instead of OODrive
core: API keys and provider billing stay agent-side, while OODrive consumes the
resulting provider-neutral manifest.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_ROOT = "https://api.meshy.ai"
DEFAULT_FORMATS = ("glb", "fbx", "obj")


def main() -> int:
    args = _parse_args()
    key = _load_api_key(args.env_file)
    run_dir = Path(args.output_root).expanduser() / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    requests = _load_asset_requests(args)
    manifests: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for index, request in enumerate(requests):
        asset_dir = run_dir / _slug(request["asset_id"])
        asset_dir.mkdir(parents=True, exist_ok=True)
        try:
            manifest = _generate_one_asset(
                key,
                request,
                asset_dir,
                workflow=args.workflow,
                formats=tuple(args.format),
                poll_interval_s=args.poll_interval_s,
                timeout_s=args.timeout_s,
            )
            (asset_dir / "asset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            manifests.append(manifest)
        except Exception as exc:
            failures.append({"asset_id": request.get("asset_id", f"asset-{index}"), "error": str(exc)})
            if not args.continue_on_error:
                raise
    batch = {
        "schema_version": "oodrive.meshy_asset_batch.v1",
        "provider": "meshy",
        "workflow": args.workflow,
        "asset_count": len(manifests),
        "failure_count": len(failures),
        "asset_manifests": manifests,
        "failures": failures,
        "claim_boundaries": [
            "custom_mesh_generated=true" if manifests else "custom_mesh_generated=false",
            "carla_blueprint_registered=false_until_oodrive_probe_passes",
            "spawned_in_carla=false_until_oodrive_spawn_custom_asset_passes",
        ],
    }
    manifest_path = run_dir / "asset_manifests.json"
    report_path = run_dir / "asset_report.md"
    manifest_path.write_text(json.dumps(batch, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(batch), encoding="utf-8")
    print(json.dumps({"manifest_path": str(manifest_path), "report_path": str(report_path), **batch}, indent=2))
    return 0 if not failures else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-json", type=Path, help="JSON list of OODrive asset request objects.")
    parser.add_argument("--asset-id", help="Single asset id when --assets-json is omitted.")
    parser.add_argument("--prompt", help="Single asset prompt when --assets-json is omitted.")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--length", type=float, default=2.0)
    parser.add_argument("--width", type=float, default=1.0)
    parser.add_argument("--height", type=float, default=1.0)
    parser.add_argument("--env-file", type=Path, default=Path("my.env"))
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/runs"))
    parser.add_argument("--run-id", default="meshy-oodrive-assets")
    parser.add_argument("--workflow", choices=["text-to-3d", "text-image-to-3d"], default="text-to-3d")
    parser.add_argument("--format", action="append", choices=["glb", "fbx", "obj", "stl", "usdz", "3mf"])
    parser.add_argument("--poll-interval-s", type=float, default=10.0)
    parser.add_argument("--timeout-s", type=float, default=900.0)
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()
    args.format = list(dict.fromkeys(args.format or list(DEFAULT_FORMATS)))
    return args


def _load_api_key(env_file: Path) -> str:
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip() and key.strip() not in os.environ:
                os.environ[key.strip()] = value.strip().strip("'\"")
    key = os.environ.get("MESHY_API_KEY", "").strip()
    if not key:
        raise RuntimeError("MESHY_API_KEY is required in environment or --env-file.")
    return key


def _load_asset_requests(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.assets_json:
        payload = json.loads(args.assets_json.read_text(encoding="utf-8"))
        items = payload.get("asset_requests", payload.get("asset_manifests", payload)) if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            raise ValueError("--assets-json must contain a list, asset_requests, or asset_manifests.")
        return [_normalize_request(dict(item)) for item in items]
    if not args.asset_id or not args.prompt:
        raise ValueError("Pass --assets-json or both --asset-id and --prompt.")
    return [
        _normalize_request(
            {
                "asset_id": args.asset_id,
                "prompt": args.prompt,
                "semantic_tags": list(args.tag),
                "dimensions_m": {"length": args.length, "width": args.width, "height": args.height},
                "collision_proxy": {"kind": "box", "length": args.length, "width": args.width, "height": args.height},
                "intended_placement": {"surface": "road", "relative_to": "lane_center", "x_m": 25.0, "y_m": 0.0},
            }
        )
    ]


def _normalize_request(payload: dict[str, Any]) -> dict[str, Any]:
    asset_id = str(payload.get("asset_id", "")).strip()
    prompt = str(payload.get("prompt", "")).strip()
    if not asset_id or not prompt:
        raise ValueError("Each asset request needs asset_id and prompt.")
    dims = dict(payload.get("dimensions_m", {}))
    dims = {key: float(dims.get(key, 1.0)) for key in ("length", "width", "height")}
    proxy = dict(payload.get("collision_proxy", {})) or {"kind": "box", **dims}
    placement = dict(payload.get("intended_placement", {})) or {"surface": "road", "relative_to": "lane_center", "x_m": 25.0, "y_m": 0.0}
    return {
        "asset_id": asset_id,
        "prompt": prompt,
        "semantic_tags": [str(tag) for tag in list(payload.get("semantic_tags", []))],
        "dimensions_m": dims,
        "collision_proxy": proxy,
        "intended_placement": placement,
        "license": str(payload.get("license", "meshy-generated-for-oodrive-demo")),
        "source_recipe_id": payload.get("source_recipe_id"),
    }


def _generate_one_asset(
    key: str,
    request: dict[str, Any],
    asset_dir: Path,
    *,
    workflow: str,
    formats: tuple[str, ...],
    poll_interval_s: float,
    timeout_s: float,
) -> dict[str, Any]:
    if workflow == "text-image-to-3d":
        image_task = _create_text_to_image(key, request["prompt"])
        image_result = _poll_task(key, f"/openapi/v1/text-to-image/{image_task}", poll_interval_s, timeout_s)
        image_to_3d_task = _create_image_to_3d(key, image_task, formats)
        model_result = _poll_task(key, f"/openapi/v1/image-to-3d/{image_to_3d_task}", poll_interval_s, timeout_s)
        task_ids = {"text_to_image": image_task, "image_to_3d": image_to_3d_task}
        image_urls = image_result.get("image_urls", [])
    else:
        preview_task = _create_text_to_3d_preview(key, request["prompt"])
        preview_result = _poll_task(key, f"/openapi/v2/text-to-3d/{preview_task}", poll_interval_s, timeout_s)
        refine_task = _create_text_to_3d_refine(key, preview_task, formats)
        model_result = _poll_task(key, f"/openapi/v2/text-to-3d/{refine_task}", poll_interval_s, timeout_s)
        task_ids = {"text_to_3d_preview": preview_task, "text_to_3d_refine": refine_task}
        image_urls = []
        (asset_dir / "preview_task.json").write_text(json.dumps(preview_result, indent=2), encoding="utf-8")
    (asset_dir / "model_task.json").write_text(json.dumps(model_result, indent=2), encoding="utf-8")
    model_urls = dict(model_result.get("model_urls", {}))
    downloaded = _download_model_urls(model_urls, asset_dir, formats)
    thumbnail_path = _download_optional(model_result.get("thumbnail_url"), asset_dir / "thumbnail.png")
    primary_path = downloaded.get("glb") or next(iter(downloaded.values()), None)
    if primary_path is None:
        raise RuntimeError(f"Meshy task succeeded but no requested model formats were returned for {request['asset_id']}.")
    alternate = {fmt: str(path) for fmt, path in downloaded.items() if path != primary_path}
    return {
        "asset_id": request["asset_id"],
        "provider": "external_manifest",
        "status": "generated",
        "prompt": request["prompt"],
        "semantic_tags": request["semantic_tags"],
        "dimensions_m": request["dimensions_m"],
        "collision_proxy": request["collision_proxy"],
        "intended_placement": request["intended_placement"],
        "license": request["license"],
        "source_recipe_id": request.get("source_recipe_id"),
        "local_path": str(primary_path),
        "external_uri": model_urls.get("glb") or next(iter(model_urls.values()), None),
        "setup_guidance": "Run OODrive package/probe/spawn steps before claiming CARLA custom asset proof.",
        "metadata": {
            "provider": "meshy",
            "workflow": workflow,
            "meshy_task_ids": task_ids,
            "thumbnail_path": str(thumbnail_path) if thumbnail_path else None,
            "alternate_formats": alternate,
            "image_urls": image_urls,
            "custom_mesh_generated": True,
            "carla_blueprint_registered": False,
            "spawned_in_carla": False,
            "claim_boundaries": [
                "custom_mesh_generated=true",
                "carla_blueprint_registered=false_until_oodrive_probe_passes",
                "spawned_in_carla=false_until_oodrive_spawn_custom_asset_passes",
            ],
        },
    }


def _create_text_to_3d_preview(key: str, prompt: str) -> str:
    payload = {
        "mode": "preview",
        "prompt": prompt,
        "model_type": "lowpoly",
        "ai_model": "latest",
        "should_remesh": False,
        "moderation": True,
    }
    response = _request_json("POST", "/openapi/v2/text-to-3d", key, payload)
    return _task_id(response)


def _create_text_to_3d_refine(key: str, preview_task_id: str, formats: tuple[str, ...]) -> str:
    payload = {
        "mode": "refine",
        "preview_task_id": preview_task_id,
        "target_formats": list(formats),
        "auto_size": True,
        "origin_at": "bottom",
        "enable_pbr": True,
    }
    response = _request_json("POST", "/openapi/v2/text-to-3d", key, payload)
    return _task_id(response)


def _create_text_to_image(key: str, prompt: str) -> str:
    payload = {"ai_model": "nano-banana-pro", "prompt": prompt, "generate_multi_view": True}
    response = _request_json("POST", "/openapi/v1/text-to-image", key, payload)
    return _task_id(response)


def _create_image_to_3d(key: str, image_task_id: str, formats: tuple[str, ...]) -> str:
    payload = {
        "input_task_id": image_task_id,
        "model_type": "lowpoly",
        "ai_model": "latest",
        "should_texture": True,
        "enable_pbr": True,
        "target_formats": list(formats),
        "auto_size": True,
        "origin_at": "bottom",
        "moderation": True,
    }
    response = _request_json("POST", "/openapi/v1/image-to-3d", key, payload)
    return _task_id(response)


def _poll_task(key: str, path: str, poll_interval_s: float, timeout_s: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_s
    last_status = "UNKNOWN"
    while time.monotonic() < deadline:
        payload = _request_json("GET", path, key)
        status = str(payload.get("status", "")).upper()
        last_status = status or last_status
        if status == "SUCCEEDED":
            return payload
        if status in {"FAILED", "CANCELED", "CANCELLED"}:
            raise RuntimeError(f"Meshy task failed at {path}: {payload.get('task_error') or payload}")
        time.sleep(poll_interval_s)
    raise TimeoutError(f"Timed out waiting for Meshy task {path}; last status={last_status}.")


def _request_json(method: str, path: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        urllib.parse.urljoin(API_ROOT, path),
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Meshy HTTP {exc.code} for {method} {path}: {body}") from exc
    decoded = json.loads(body)
    if not isinstance(decoded, dict):
        raise RuntimeError(f"Meshy returned non-object response for {method} {path}: {decoded!r}")
    return decoded


def _task_id(payload: dict[str, Any]) -> str:
    value = payload.get("result") or payload.get("id")
    if not value:
        raise RuntimeError(f"Meshy response did not contain task id: {payload}")
    return str(value)


def _download_model_urls(model_urls: dict[str, Any], asset_dir: Path, formats: tuple[str, ...]) -> dict[str, Path]:
    downloaded: dict[str, Path] = {}
    for fmt in formats:
        url = model_urls.get(fmt)
        if not isinstance(url, str) or not url:
            continue
        path = asset_dir / f"model.{fmt}"
        _download(url, path)
        downloaded[fmt] = path
    return downloaded


def _download_optional(url: Any, path: Path) -> Path | None:
    if not isinstance(url, str) or not url:
        return None
    _download(url, path)
    return path


def _download(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "OODrive-Meshy-Skill/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        path.write_bytes(response.read())


def _markdown(batch: dict[str, Any]) -> str:
    lines = [
        "# Meshy OODrive Asset Batch",
        "",
        f"- workflow: `{batch.get('workflow')}`",
        f"- assets: `{batch.get('asset_count')}`",
        f"- failures: `{batch.get('failure_count')}`",
        "",
    ]
    for manifest in list(batch.get("asset_manifests", [])):
        lines.extend(
            [
                f"## {manifest.get('asset_id')}",
                "",
                f"- prompt: {manifest.get('prompt')}",
                f"- local_path: `{manifest.get('local_path')}`",
                f"- tags: `{', '.join(list(manifest.get('semantic_tags', [])))}`",
                "- CARLA status: `carla_blueprint_registered=false` until OODrive probe passes.",
                "",
            ]
        )
    if batch.get("failures"):
        lines.extend(["## Failures", ""])
        for failure in list(batch.get("failures", [])):
            lines.append(f"- `{failure.get('asset_id')}`: {failure.get('error')}")
    return "\n".join(lines) + "\n"


def _slug(value: str) -> str:
    safe = [char.lower() if char.isalnum() else "-" for char in value.strip()]
    return "-".join("".join(safe).split("-")) or "asset"


if __name__ == "__main__":
    raise SystemExit(main())
