"""Recordable Environment Studio pack for OODrive judges."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from driverx.core.artifacts import prepare_run_dir


REQUIRED_CLAIM_BOUNDARIES = [
    "closed_loop_vla_control=false",
    "real_time_vla_control=false",
    "sampled_open_loop_reasoning=true",
    "time_warped_offline_demo=true",
]


def build_environment_demo_pack(
    *,
    environment_summary_path: Path,
    output_root: Path,
    run_id: str,
    submission_pack_path: Path | None = None,
    hero_video_path: Path | None = None,
) -> dict[str, Any]:
    """Build a static, screen-recordable Environment Studio demo pack."""

    summary = _load_json(environment_summary_path)
    pack_dir = prepare_run_dir(output_root, run_id)
    recipes = _recipes(summary)
    cards = [_recipe_card(recipe) for recipe in recipes]
    claim_boundaries = list(REQUIRED_CLAIM_BOUNDARIES)
    command_transcript = _commands(environment_summary_path, submission_pack_path, hero_video_path)
    manifest = {
        "pack_id": pack_dir.name,
        "product_name": "OODrive",
        "headline": (
            "Environment Studio turns one minimal-shot stress-test prompt into "
            "CARLA-ready environment variants with weather, traffic, assets, "
            "road-local placements, and policy pressure labels."
        ),
        "environment_summary_path": str(environment_summary_path),
        "submission_pack": _linked_file(submission_pack_path),
        "hero_video": _linked_file(hero_video_path),
        "family_count": len(set(str(item) for item in summary.get("families", []))),
        "asset_request_count": len(list(summary.get("asset_requests", []))),
        "recipe_count": len(recipes),
        "families": [str(item) for item in list(summary.get("families", []))],
        "tags": [str(item) for item in list(summary.get("tags", []))],
        "cards": cards,
        "claim_boundaries": claim_boundaries,
        "command_transcript": command_transcript,
        "sections": [
            {
                "id": "generation",
                "title": "Randomized Environment Generation",
                "body": f"{len(recipes)} deterministic recipes across {len(set(card['family'] for card in cards))} families.",
            },
            {
                "id": "carla",
                "title": "CARLA-Ready Controls",
                "body": "Each recipe exposes weather, lighting, traffic pressure, stock proxy assets, collision boxes, and road-local placement hints.",
            },
            {
                "id": "minimal_shot",
                "title": "Minimal-Shot Pressure",
                "body": "Each environment states the policy pressure it creates, so the evaluator can test generalization rather than memorized routes.",
            },
            {
                "id": "evidence",
                "title": "Evidence Linkage",
                "body": "The page links generated environments to the hero CARLA/reasoning proof and the final submission pack when those files are available.",
            },
        ],
    }
    outputs = _write_pack(pack_dir, manifest)
    return {**manifest, **outputs, "pack_dir": str(pack_dir)}


def render_environment_demo_html(pack: dict[str, Any]) -> str:
    """Render an app-like static Environment Studio page."""

    cards = "".join(_card_html(card) for card in list(pack.get("cards", [])))
    families = "".join(
        f"<button class='chip' data-family='{_esc(family)}'>{_esc(family)}</button>"
        for family in list(pack.get("families", []))
    )
    sections = "".join(
        f"<section><h2>{_esc(section.get('title'))}</h2><p>{_esc(section.get('body'))}</p></section>"
        for section in list(pack.get("sections", []))
    )
    claims = "".join(f"<li><code>{_esc(claim)}</code></li>" for claim in list(pack.get("claim_boundaries", [])))
    hero = _linked_file_text(pack.get("hero_video"))
    submission = _linked_file_text(pack.get("submission_pack"))
    commands = "\n".join(str(command) for command in list(pack.get("command_transcript", [])))
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>OODrive Environment Studio</title>"
        "<style>"
        ":root{color-scheme:light;--ink:#17202a;--muted:#526170;--line:#d7e0ea;--panel:#f6f8fb;--accent:#0b6b5b;--risk:#a33b22}"
        "*{box-sizing:border-box}body{margin:0;font-family:Inter,Arial,sans-serif;color:var(--ink);background:#fff;line-height:1.45}"
        "header{padding:28px 32px 20px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#f8fbff,#fff)}"
        "main{padding:24px 32px 36px}.kicker{font-size:12px;font-weight:700;text-transform:uppercase;color:var(--accent);letter-spacing:.04em}"
        "h1{font-size:36px;line-height:1.05;margin:8px 0 10px;letter-spacing:0}p{margin:0;color:var(--muted)}"
        ".stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:18px;max-width:920px}"
        ".stat{border:1px solid var(--line);background:#fff;padding:12px;border-radius:8px}.stat strong{display:block;font-size:24px;color:var(--ink)}"
        ".filters{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0}.chip{border:1px solid var(--line);background:#fff;border-radius:999px;padding:7px 10px;color:var(--ink)}"
        ".grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.card{border:1px solid var(--line);border-radius:8px;padding:14px;background:#fff;min-height:300px}"
        ".card h2{font-size:18px;margin:0 0 4px}.family{color:var(--accent);font-weight:700}.pressure{margin:10px 0;padding:10px;border-left:3px solid var(--risk);background:#fff7f4;color:#452116}"
        ".kv{display:grid;grid-template-columns:96px 1fr;gap:5px;font-size:13px;margin:8px 0}.kv b{color:var(--muted)}"
        "table{width:100%;border-collapse:collapse;font-size:12px;margin-top:10px}td,th{border:1px solid var(--line);padding:6px;text-align:left;vertical-align:top}th{background:var(--panel)}"
        ".links,.claims,.commands{margin-top:24px;padding:16px;border:1px solid var(--line);border-radius:8px;background:var(--panel)}"
        "code,pre{background:#edf2f7;border-radius:4px}code{padding:2px 4px}pre{white-space:pre-wrap;padding:12px;overflow:auto}"
        "@media(max-width:900px){.grid,.stats{grid-template-columns:1fr}.card{min-height:auto}h1{font-size:30px}}"
        "</style></head><body>"
        "<header>"
        "<div class='kicker'>OODrive Environment Studio</div>"
        f"<h1>{_esc(pack.get('headline'))}</h1>"
        "<p>Record this page to show judges randomized simulation environments, not just a finished video.</p>"
        "<div class='stats'>"
        f"<div class='stat'><strong>{int(pack.get('family_count',0))}</strong><span>families</span></div>"
        f"<div class='stat'><strong>{int(pack.get('recipe_count',0))}</strong><span>recipes</span></div>"
        f"<div class='stat'><strong>{int(pack.get('asset_request_count',0))}</strong><span>asset requests</span></div>"
        f"<div class='stat'><strong>{len(pack.get('claim_boundaries',[]))}</strong><span>claim labels</span></div>"
        "</div></header><main>"
        f"{sections}<div class='filters'>{families}</div><div class='grid'>{cards}</div>"
        f"<div class='links'><h2>Proof Links</h2><p>Hero video: <code>{_esc(hero)}</code></p><p>Submission pack: <code>{_esc(submission)}</code></p></div>"
        f"<div class='claims'><h2>Claim Boundaries</h2><ul>{claims}</ul></div>"
        f"<div class='commands'><h2>Demo Commands</h2><pre>{_esc(commands)}</pre></div>"
        "</main></body></html>"
    )


def render_environment_demo_storyboard(pack: dict[str, Any]) -> str:
    commands = list(pack.get("command_transcript", []))
    return "\n".join(
        [
            "# OODrive Environment Studio Demo Storyboard",
            "",
            "Target length: 1-5 minutes.",
            "",
            "1. Open with the challenge fit: OODrive creates CARLA simulation environments for minimal-shot driving tests.",
            "2. Run or show the generate command and call out seed, severity, count, and families.",
            f"   `{commands[0] if commands else 'oodrive generate-envs ...'}`",
            "3. Open `index.html` and show the first row of environment cards.",
            "4. Zoom one card and point to weather, traffic, asset proxy, collision box, and road-local placement.",
            "5. Jump to the proof links: generated environments connect to the hero CARLA video and submission pack.",
            "6. End on claim boundaries: sampled open-loop Alpamayo reasoning, time-warped demo, no real-time closed-loop VLA claim.",
            "",
        ]
    )


def _write_pack(pack_dir: Path, manifest: dict[str, Any]) -> dict[str, str]:
    manifest_path = pack_dir / "environment_demo_manifest.json"
    html_path = pack_dir / "index.html"
    commands_path = pack_dir / "commands.sh"
    storyboard_path = pack_dir / "video_storyboard.md"
    manifest["artifacts"] = {
        "environment_demo_manifest_path": str(manifest_path),
        "environment_demo_index_path": str(html_path),
        "environment_demo_commands_path": str(commands_path),
        "environment_demo_storyboard_path": str(storyboard_path),
    }
    manifest["video_storyboard_path"] = str(storyboard_path)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    html_path.write_text(render_environment_demo_html(manifest), encoding="utf-8")
    commands_path.write_text(_commands_sh(manifest), encoding="utf-8")
    storyboard_path.write_text(render_environment_demo_storyboard(manifest), encoding="utf-8")
    return dict(manifest["artifacts"])


def _commands_sh(pack: dict[str, Any]) -> str:
    lines = ["#!/usr/bin/env bash", "set -euo pipefail", ""]
    for command in list(pack.get("command_transcript", [])):
        lines.append(str(command))
    return "\n".join(lines) + "\n"


def _commands(
    environment_summary_path: Path,
    submission_pack_path: Path | None,
    hero_video_path: Path | None,
) -> list[str]:
    commands = [
        "PYTHONPATH=src python3 -m oodrive generate-envs --severity 4 --count 6 --seed 31 --run-id task135-env-demo-v1",
        f"PYTHONPATH=src python3 -m oodrive export-env-demo --environment-summary {environment_summary_path}",
    ]
    if submission_pack_path is not None:
        commands[-1] += f" --submission-pack {submission_pack_path}"
    if hero_video_path is not None:
        commands[-1] += f" --hero-video {hero_video_path}"
    commands.append(
        "PYTHONPATH=src python3 -m oodrive score-env-demo "
        f"--environment-summary {environment_summary_path} --demo-manifest <environment_demo_manifest.json> --metric-only"
    )
    return commands


def _card_html(card: dict[str, Any]) -> str:
    assets = "".join(
        "<tr>"
        f"<td>{_esc(asset.get('asset_id'))}</td>"
        f"<td>{_esc(asset.get('role'))}</td>"
        f"<td><code>{_esc(asset.get('blueprint_hint'))}</code></td>"
        f"<td>{_esc(asset.get('placement'))}</td>"
        "</tr>"
        for asset in list(card.get("assets", []))
    )
    return (
        f"<article class='card' data-family='{_esc(card.get('family'))}'>"
        f"<div class='family'>{_esc(card.get('family'))}</div>"
        f"<h2>{_esc(card.get('template_id'))}</h2>"
        f"<p>{_esc(card.get('tags'))}</p>"
        f"<div class='pressure'>{_esc(card.get('expected_policy_pressure'))}</div>"
        f"<div class='kv'><b>weather</b><span>{_esc(card.get('weather'))}</span><b>traffic</b><span>{_esc(card.get('traffic'))}</span></div>"
        "<table><tr><th>asset</th><th>role</th><th>CARLA proxy</th><th>placement</th></tr>"
        f"{assets}</table></article>"
    )


def _recipe_card(recipe: dict[str, Any]) -> dict[str, Any]:
    return {
        "recipe_id": str(recipe.get("recipe_id", "")),
        "template_id": str(recipe.get("template_id", "")),
        "family": str(recipe.get("family", "")),
        "severity": int(_first_float(recipe.get("severity"))),
        "tags": ", ".join(str(tag) for tag in list(recipe.get("tags", []))[:8]),
        "weather": _compact_mapping(recipe.get("weather")),
        "traffic": _compact_mapping(recipe.get("traffic")),
        "expected_policy_pressure": str(recipe.get("expected_policy_pressure", "")),
        "assets": [
            {
                "asset_id": str(asset.get("asset_id", "")),
                "role": str(asset.get("role", "")),
                "blueprint_hint": str(asset.get("blueprint_hint", "")),
                "placement": _compact_mapping(asset.get("base_placement")),
                "collision_proxy": _compact_mapping(asset.get("collision_proxy")),
            }
            for asset in _list_of_mappings(recipe.get("assets"))
        ],
    }


def _linked_file(path: Path | None) -> dict[str, str]:
    if path is None:
        return {"path": "", "status": "missing"}
    return {"path": str(path), "status": "local_file" if path.exists() else "missing"}


def _linked_file_text(value: object) -> str:
    if isinstance(value, dict):
        path = value.get("path") or ""
        status = value.get("status") or "missing"
        return f"{path} ({status})"
    return ""


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, dict) else {}


def _recipes(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return _list_of_mappings(summary.get("recipes"))


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in value] if isinstance(value, list) and all(isinstance(item, dict) for item in value) else []


def _compact_mapping(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    parts = [f"{key}={item}" for key, item in list(value.items())[:4]]
    return ", ".join(parts)


def _first_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


__all__ = [
    "REQUIRED_CLAIM_BOUNDARIES",
    "build_environment_demo_pack",
    "render_environment_demo_html",
    "render_environment_demo_storyboard",
]
