#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OVERLAY_VIDEO="${1:-$ROOT_DIR/artifacts/exported/task111_reasoning_overlay_v1.mp4}"
OUTPUT_VIDEO="${2:-$ROOT_DIR/artifacts/exported/final_sota_demo_v8.mp4}"
FPS="${DRIVERX_DEMO_FPS:-15}"
WIDTH="${DRIVERX_DEMO_WIDTH:-1280}"
HEIGHT="${DRIVERX_DEMO_HEIGHT:-720}"

if [[ ! -f "$OVERLAY_VIDEO" ]]; then
  echo "Missing reasoning overlay video: $OVERLAY_VIDEO" >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required to build the paper demo video" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_VIDEO")"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/driverx-paper-demo.XXXXXX")"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

make_card() {
  local name="$1"
  local seconds="$2"
  local title="$3"
  local body="$4"
  local image_file="$TMP_DIR/$name.png"
  local out_file="$TMP_DIR/$name.mp4"
  CARD_TITLE="$title" CARD_BODY="$body" CARD_IMAGE="$image_file" CARD_WIDTH="$WIDTH" CARD_HEIGHT="$HEIGHT" \
    python3 - <<'PY'
import os
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

width = int(os.environ["CARD_WIDTH"])
height = int(os.environ["CARD_HEIGHT"])
title = os.environ["CARD_TITLE"]
body = os.environ["CARD_BODY"]
fonts = [
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
font_path = next((path for path in fonts if path.exists()), None)
if font_path:
    title_font = ImageFont.truetype(str(font_path), 54)
    body_font = ImageFont.truetype(str(font_path), 34)
    small_font = ImageFont.truetype(str(font_path), 24)
else:
    title_font = ImageFont.load_default(size=54)
    body_font = ImageFont.load_default(size=34)
    small_font = ImageFont.load_default(size=24)
image = Image.new("RGB", (width, height), "#0e1418")
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, width, 92), fill="#18242c")
draw.text((56, 30), "0xDriver Scenario Workbench", font=small_font, fill="#9ee5d5")
draw.text((72, 176), title, font=title_font, fill="#f8fbfa")
y = 270
for paragraph in body.split("\\n"):
    for line in textwrap.wrap(paragraph, width=60):
        draw.text((74, y), line, font=body_font, fill="#dce6e2")
        y += 46
    y += 18
draw.rectangle((72, height - 82, width - 72, height - 80), fill="#59d5c7")
draw.text((72, height - 54), "time-warped offline CARLA evidence / sampled open-loop Alpamayo reasoning", font=small_font, fill="#9fb2ac")
image.save(os.environ["CARD_IMAGE"])
PY
  ffmpeg -hide_banner -loglevel error -y \
    -loop 1 -framerate "$FPS" -t "$seconds" -i "$image_file" \
    -vf "fps=${FPS},format=yuv420p" \
    -an -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$out_file"
}

make_card "00-title" 8 "Minimal-shot autonomy needs a simulator flywheel" "Generate weird-but-plausible OOD cases.\\nRun them in CARLA.\\nShow what the VLA/RAG stack notices."
make_card "01-generate" 10 "Agentic Scenario Studio" "Deterministic agent loop proposes regional driving chaos, scores novelty, rejects duplicates, and queues the next CARLA runs."

ffmpeg -hide_banner -loglevel error -y \
  -i "$OVERLAY_VIDEO" \
  -vf "scale=${WIDTH}:${HEIGHT}:force_original_aspect_ratio=decrease,pad=${WIDTH}:${HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps=${FPS}" \
  -an -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$TMP_DIR/02-overlay.mp4"

make_card "03-curate" 11 "Evidence becomes memory" "Risk events, retrieved principles, and Alpamayo reasoning snapshots become reusable dataset rows for minimal-shot evaluation."
make_card "04-boundary" 11 "Honest current claim" "This is a time-warped offline demo.\\nAlpamayo is sampled open-loop.\\nReal-time VLA serving is the next phase."
make_card "05-close" 8 "Contribution" "A CARLA OOD scenario workbench for generating, testing, explaining, and curating long-tail autonomy cases."

cat > "$TMP_DIR/concat.txt" <<EOF
file '$TMP_DIR/00-title.mp4'
file '$TMP_DIR/01-generate.mp4'
file '$TMP_DIR/02-overlay.mp4'
file '$TMP_DIR/03-curate.mp4'
file '$TMP_DIR/04-boundary.mp4'
file '$TMP_DIR/05-close.mp4'
EOF

ffmpeg -hide_banner -loglevel error -y \
  -f concat -safe 0 -i "$TMP_DIR/concat.txt" \
  -c copy "$OUTPUT_VIDEO"

echo "$OUTPUT_VIDEO"
