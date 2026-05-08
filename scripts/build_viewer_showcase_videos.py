#!/usr/bin/env python3
"""Build narrated viewer-facing showcase videos from current OODrive evidence."""

from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "viewer_showcase"
WORK = OUT / "_work"
SIZE = (1280, 720)
FPS = 15
VOICE = "Samantha"


@dataclass(frozen=True)
class Slide:
    title: str
    bullets: tuple[str, ...]
    narration: str
    duration_s: float = 7.0
    footer: str = "OODrive evidence showcase"


@dataclass(frozen=True)
class SourceClip:
    path: Path
    title: str
    caption: str
    start_s: float = 0.0
    duration_s: float = 10.0


@dataclass(frozen=True)
class ShowcaseVideo:
    file_stem: str
    title: str
    description: str
    slides: tuple[Slide, ...]
    clips: tuple[SourceClip, ...]


def main() -> int:
    require_tools()
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)

    manifest = load_project_manifest()
    videos = build_video_specs(manifest)
    rendered: list[dict[str, object]] = []
    for index, video in enumerate(videos, start=1):
        output = OUT / f"{index:02d}_{video.file_stem}.mp4"
        chapter_paths = render_showcase_video(video, index, output)
        rendered.append(
            {
                "title": video.title,
                "description": video.description,
                "path": str(output.relative_to(ROOT)),
                "chapters": [str(path.relative_to(ROOT)) for path in chapter_paths],
            }
        )

    full_output = OUT / "00_viewer_presentation_full.mp4"
    concat_videos([OUT / f"{index:02d}_{video.file_stem}.mp4" for index, video in enumerate(videos, start=1)], full_output)
    rendered.insert(
        0,
        {
            "title": "Full Viewer Presentation",
            "description": "All OODrive showcase chapters concatenated.",
            "path": str(full_output.relative_to(ROOT)),
        },
    )

    write_manifest(rendered, manifest)
    return 0


def require_tools() -> None:
    for tool in ("ffmpeg", "ffprobe", "say"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"Missing required tool: {tool}")


def load_project_manifest() -> dict[str, object]:
    manifest_path = (
        ROOT
        / "artifacts"
        / "runs"
        / "task128-oodrive-live-product"
        / "submission-packs"
        / "task135-submission-pack-with-env-demo"
        / "submission_manifest.json"
    )
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def build_video_specs(manifest: dict[str, object]) -> tuple[ShowcaseVideo, ...]:
    hero = ROOT / "artifacts" / "exported" / "task128_oodrive_live_product.mp4"
    reasoning = ROOT / "artifacts" / "exported" / "task111_reasoning_overlay_v1.mp4"
    timewarp = ROOT / "artifacts" / "exported" / "task112_hero_timewarp_3x.mp4"
    final_v8 = ROOT / "artifacts" / "exported" / "final_sota_demo_v8.mp4"
    high_fidelity = ROOT / "artifacts" / "exported" / "task102_high_fidelity_hero_v6_full.mp4"
    live_carla = (
        ROOT
        / "artifacts"
        / "runs"
        / "task141-runpod-carla-live-video"
        / "wet-malaysian-roadwork-scooter-cut-in-lane-debris-0041_ood.mp4"
    )
    stress = (
        ROOT
        / "artifacts"
        / "runs"
        / "task140-bad-path-stress-v3-lane-safe-001"
        / "bad_path_stress_demo.mp4"
    )

    unique = tuple(str(item) for item in manifest.get("unique_contributions", []) if isinstance(item, str))
    core_unique = unique[:4] or (
        "Minimal-prompt OOD scenario generation.",
        "CARLA placement and evidence capture.",
        "Alpamayo open-loop reasoning over simulator frames.",
        "RAG/memory callouts with honest claim boundaries.",
    )

    return (
        ShowcaseVideo(
            file_stem="cli_overview",
            title="CLI Overview",
            description="Explains the OODrive command surface and the generate-place-reason loop.",
            slides=(
                Slide(
                    title="OODrive CLI: the control plane",
                    bullets=(
                        "generate: prompt to scenario candidates",
                        "place: materialize a CARLA placement/run manifest",
                        "reason: attach Alpamayo and memory evidence",
                        "score/export: gate what becomes viewer-facing proof",
                    ),
                    narration=(
                        "OODrive is the command line control plane for this project. "
                        "The important loop is generate, place, reason, then score and export. "
                        "That turns a tiny prompt into a scenario database, a CARLA run, and a packaged evidence story."
                    ),
                ),
                Slide(
                    title="Novel contribution: evidence-first autonomy tooling",
                    bullets=core_unique,
                    narration=(
                        "The contribution is not just one simulator clip. It is an evidence harness for minimal shot autonomy: "
                        "generate rare cases, put them in CARLA, run or attach policy reasoning, and keep the limits visible."
                    ),
                ),
            ),
            clips=(
                SourceClip(hero, "Generate -> Place -> Reason", "Live CARLA placement plus fresh Alpamayo reasoning evidence.", 0, 15),
                SourceClip(final_v8, "Final submission packet", "Prior compact demo showing the project story and artifact chain.", 5, 12),
            ),
        ),
        ShowcaseVideo(
            file_stem="ood_scenario_generation",
            title="OOD Scenario Generation",
            description="Shows minimal-shot generation of weird but plausible navigation tasks.",
            slides=(
                Slide(
                    title="Minimal prompt, many stressors",
                    bullets=(
                        "Start with a short regional driving brief",
                        "Expand into weather, actors, props, and behavior pressure",
                        "Emit CARLA-ready placement plans with stock proxy assets",
                        "Keep generated 3D asset claims separate until import is proved",
                    ),
                    narration=(
                        "A minimal shot autonomy test should not need hundreds of handcrafted examples. "
                        "Here, a short brief expands into weather, objects, vehicles, pedestrians, and route pressure that CARLA can actually render."
                    ),
                ),
                Slide(
                    title="What viewers should notice",
                    bullets=(
                        "The scenario is weird but still road-plausible",
                        "Objects are placed in the simulator, not only described in text",
                        "The car has to respond to blockers, cut-ins, debris, and low visibility",
                        "Promotion is gated by video and quality scores",
                    ),
                    narration=(
                        "The goal is not random chaos. The goal is plausible long-tail driving: wet roads, roadside clutter, scooter cut-ins, "
                        "lane debris, and a navigation task that makes a model reveal what it understands."
                    ),
                ),
            ),
            clips=(
                SourceClip(live_carla, "Live CARLA generated scene", "RunPod/Kasm CARLA render of a Malaysian wet-roadwork OOD case.", 8, 18),
                SourceClip(high_fidelity, "High-fidelity hero pass", "Earlier hero capture used to refine viewer-visible OOD evidence.", 8, 14),
                SourceClip(stress, "Bad-path stress reel", "Local stress cases for blockers, swerves, and recovery behavior.", 0, 12),
            ),
        ),
        ShowcaseVideo(
            file_stem="rag_alpamayo_reasoning",
            title="RAG + Alpamayo Reasoning",
            description="Explains current memory retrieval, Alpamayo-in-CARLA evidence, and future reasoning direction.",
            slides=(
                Slide(
                    title="Alpamayo inside the CARLA evidence loop",
                    bullets=(
                        "CARLA produces frames and simulator-grounded tracks",
                        "Alpamayo reasons over captured frame packages",
                        "The current proof is open-loop sampled reasoning",
                        "Real-time VLA control remains an explicit next step",
                    ),
                    narration=(
                        "One unique piece here is the Alpamayo bridge into CARLA evidence. "
                        "Today the model reasons over captured simulator frames and emits trajectory intent. "
                        "That is real evidence, but it is not yet a claim of real-time closed-loop VLA driving."
                    ),
                ),
                Slide(
                    title="RAG today, memory tomorrow",
                    bullets=(
                        "Current backend: deterministic lexical and tag overlap retrieval",
                        "Retrieved memories become driving principles in the prompt context",
                        "Ledger artifacts make the retrieval auditable",
                        "Future work: embedding/vector memory and closed-loop adaptation",
                    ),
                    narration=(
                        "The memory system is deliberately auditable. It retrieves prior failure principles by lexical and tag overlap, "
                        "then shows what memory changed in the reasoning. A future version can replace that with vector retrieval without changing the evidence loop."
                    ),
                ),
            ),
            clips=(
                SourceClip(reasoning, "Reasoning overlay", "Risk, retrieved memory, and sampled VLA reasoning presented beside CARLA video.", 0, 18),
                SourceClip(timewarp, "Time-warped Alpamayo replay", "Offline replay format that makes trajectory intent visible without overstating real-time control.", 0, 16),
                SourceClip(hero, "Open-loop claim boundary", "TASK-128 evidence: generated, placed, reasoned, and labeled honestly.", 6, 10),
            ),
        ),
        ShowcaseVideo(
            file_stem="evidence_reel",
            title="Current Evidence Reel",
            description="A fast viewer reel of the most useful generated videos currently available.",
            slides=(
                Slide(
                    title="What evidence exists right now",
                    bullets=(
                        "Product loop video: OODrive generate/place/reason",
                        "Live CARLA generated scenario footage",
                        "Reasoning overlay with RAG callouts",
                        "Prior final submission and high-fidelity hero reels",
                    ),
                    narration=(
                        "This is the current evidence shelf. Some clips are live CARLA evidence, some are time-warped or overlay videos, "
                        "and the labels are part of the point: viewers can see both what works and what remains future work."
                    ),
                ),
            ),
            clips=(
                SourceClip(hero, "OODrive live product proof", "Prompt-generated CARLA placement plus Alpamayo reasoning attachment.", 0, 12),
                SourceClip(live_carla, "Live CARLA OOD video", "Generated wet-roadwork scene rendered in CARLA.", 25, 12),
                SourceClip(reasoning, "RAG and reasoning overlay", "Memory callouts and model reasoning over simulator evidence.", 4, 12),
                SourceClip(final_v8, "Final V8 summary", "Earlier concise submission narrative.", 10, 12),
                SourceClip(high_fidelity, "High-fidelity visual pass", "Longer hero footage for presentation context.", 20, 12),
            ),
        ),
    )


def render_showcase_video(video: ShowcaseVideo, index: int, output: Path) -> list[Path]:
    chapter_paths: list[Path] = []
    parts: list[Path] = []
    chapter_dir = WORK / f"{index:02d}_{video.file_stem}"
    if chapter_dir.exists():
        shutil.rmtree(chapter_dir)
    chapter_dir.mkdir(parents=True, exist_ok=True)

    for slide_index, slide in enumerate(video.slides, start=1):
        part = chapter_dir / f"slide_{slide_index:02d}.mp4"
        render_slide_video(slide, part, chapter_dir / f"slide_{slide_index:02d}.png", chapter_dir / f"slide_{slide_index:02d}.aiff")
        parts.append(part)
        chapter_paths.append(part)

    for clip_index, clip in enumerate(video.clips, start=1):
        if not clip.path.exists():
            continue
        intro = chapter_dir / f"clip_{clip_index:02d}_intro.mp4"
        render_slide_video(
            Slide(
                title=clip.title,
                bullets=(clip.caption,),
                narration=clip.caption,
                duration_s=4.0,
                footer=video.title,
            ),
            intro,
            chapter_dir / f"clip_{clip_index:02d}_intro.png",
            chapter_dir / f"clip_{clip_index:02d}_intro.aiff",
        )
        part = chapter_dir / f"clip_{clip_index:02d}.mp4"
        render_clip_segment(clip, part)
        parts.extend([intro, part])
        chapter_paths.extend([intro, part])

    concat_videos(parts, output)
    return chapter_paths


def render_slide_video(slide: Slide, output: Path, image_path: Path, audio_path: Path) -> None:
    draw_slide(slide, image_path)
    subprocess.run(["say", "-v", VOICE, "-o", str(audio_path), slide.narration], check=True)
    audio_duration = probe_duration(audio_path)
    duration = max(slide.duration_s, audio_duration + 0.5)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-framerate",
            str(FPS),
            "-t",
            f"{duration:.2f}",
            "-i",
            str(image_path),
            "-i",
            str(audio_path),
            "-f",
            "lavfi",
            "-t",
            f"{duration:.2f}",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-filter_complex",
            "[1:a][2:a]amix=inputs=2:duration=longest:dropout_transition=0[a]",
            "-map",
            "0:v",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            "-c:a",
            "aac",
            "-shortest",
            str(output),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def render_clip_segment(clip: SourceClip, output: Path) -> None:
    overlay_path = output.with_suffix(".overlay.png")
    draw_clip_overlay(clip, overlay_path)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{clip.start_s:.2f}",
            "-t",
            f"{clip.duration_s:.2f}",
            "-i",
            str(clip.path),
            "-loop",
            "1",
            "-t",
            f"{clip.duration_s:.2f}",
            "-i",
            str(overlay_path),
            "-f",
            "lavfi",
            "-t",
            f"{clip.duration_s:.2f}",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-filter_complex",
            (
                "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,"
                "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x0f1418,setsar=1[base];"
                "[base][1:v]overlay=0:0:format=auto[v]"
            ),
            "-map",
            "[v]",
            "-map",
            "2:a",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            "-c:a",
            "aac",
            "-shortest",
            str(output),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def draw_clip_overlay(clip: SourceClip, path: Path) -> None:
    image = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    title_font = load_font(34)
    caption_font = load_font(24)
    source_font = load_font(15)
    draw.rectangle((0, 0, 1280, 92), fill=(8, 16, 22, 194))
    draw.rectangle((0, 628, 1280, 720), fill=(8, 16, 22, 199))
    draw.text((46, 24), clip.title, font=title_font, fill=(245, 247, 240, 255))
    draw.text((46, 654), clip.caption, font=caption_font, fill=(220, 232, 222, 255))
    draw.text(
        (46, 690),
        f"source: {clip.path.relative_to(ROOT)}",
        font=source_font,
        fill=(159, 176, 168, 255),
    )
    image.save(path)


def draw_slide(slide: Slide, path: Path) -> None:
    image = Image.new("RGB", SIZE, "#101719")
    draw = ImageDraw.Draw(image)
    title_font = load_font(58)
    bullet_font = load_font(31)
    small_font = load_font(20)
    mono_font = load_font(23, mono=True)

    for y in range(SIZE[1]):
        shade = int(16 + (y / SIZE[1]) * 24)
        draw.line([(0, y), (SIZE[0], y)], fill=(shade, 26 + shade // 3, 28 + shade // 4))
    draw.rectangle((0, 0, 1280, 720), outline="#2c4f47", width=5)
    draw.rectangle((0, 0, 1280, 94), fill="#0b1114")
    draw.rectangle((0, 626, 1280, 720), fill="#0b1114")
    draw.rounded_rectangle((44, 120, 1236, 594), radius=18, fill="#142024", outline="#31554e", width=2)
    draw.text((54, 30), "0xDriver / OODrive", font=mono_font, fill="#9bd6c0")
    draw.text((54, 154), slide.title, font=title_font, fill="#f6f3e8")

    y = 258
    for bullet in slide.bullets:
        wrapped = wrap_text(bullet, 58)
        draw.text((80, y), "-", font=bullet_font, fill="#87d7b6")
        for line in wrapped:
            draw.text((118, y), line, font=bullet_font, fill="#e6eee7")
            y += 39
        y += 14

    draw.text((54, 652), slide.footer, font=small_font, fill="#9fb0a8")
    draw.text((54, 680), "Generated from local evidence artifacts. Claim boundaries preserved.", font=small_font, fill="#d1dacd")
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def concat_videos(parts: list[Path], output: Path) -> None:
    if not parts:
        raise ValueError(f"No parts to concatenate for {output}")
    inputs: list[str] = []
    concat_inputs: list[str] = []
    for index, part in enumerate(parts):
        inputs.extend(["-i", str(part)])
        concat_inputs.append(f"[{index}:v:0][{index}:a:0]")
    filter_graph = "".join(concat_inputs) + f"concat=n={len(parts)}:v=1:a=1[v][a]"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex",
            filter_graph,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            "-shortest",
            str(output),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def write_manifest(rendered: list[dict[str, object]], source_manifest: dict[str, object]) -> None:
    output = {
        "showcase_id": "viewer_showcase",
        "generated_from": "local OODrive evidence artifacts",
        "videos": rendered,
        "novel_contributions": source_manifest.get("unique_contributions", []),
        "claim_boundaries": [
            "Alpamayo evidence is sampled open-loop reasoning over captured CARLA frames.",
            "Current RAG backend is deterministic lexical/tag-overlap retrieval, not embedding/vector RAG.",
            "Real-time closed-loop VLA control remains future work unless a live control trace proves it.",
            "Stock proxy assets prove CARLA simulator placement, not arbitrary generated Unreal asset import.",
        ],
        "recommended_order": [
            "00_viewer_presentation_full.mp4",
            "01_cli_overview.mp4",
            "02_ood_scenario_generation.mp4",
            "03_rag_alpamayo_reasoning.mp4",
            "04_evidence_reel.mp4",
        ],
    }
    (OUT / "viewer_showcase_manifest.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    lines = [
        "# OODrive Viewer Showcase",
        "",
        "## Videos",
        "",
    ]
    for item in rendered:
        lines.append(f"- **{item['title']}**: `{item['path']}`")
        lines.append(f"  - {item['description']}")
    lines.extend(["", "## Novel Contributions", ""])
    for item in source_manifest.get("unique_contributions", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Honest Claim Boundaries", ""])
    for item in output["claim_boundaries"]:
        lines.append(f"- {item}")
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def load_font(size: int, *, mono: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(font_path(mono=mono)), size=size)


def font_path(*, mono: bool = False) -> Path:
    if mono:
        return Path("/System/Library/Fonts/SFNSMono.ttf")
    return Path("/System/Library/Fonts/Avenir.ttc")


def wrap_text(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=False) or [text]


if __name__ == "__main__":
    raise SystemExit(main())
