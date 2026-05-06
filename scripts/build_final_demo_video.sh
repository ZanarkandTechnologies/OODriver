#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HERO_VIDEO="${1:-$ROOT_DIR/artifacts/exported/task102_high_fidelity_hero_v6_full.mp4}"
OUTPUT_VIDEO="${2:-$ROOT_DIR/artifacts/exported/final_sota_demo_draft_v1.mp4}"
FPS="${DRIVERX_DEMO_FPS:-5}"
WIDTH="${DRIVERX_DEMO_WIDTH:-1280}"
HEIGHT="${DRIVERX_DEMO_HEIGHT:-720}"
FONT="${DRIVERX_DEMO_FONT:-}"

if [[ ! -f "$HERO_VIDEO" ]]; then
  echo "Missing hero video: $HERO_VIDEO" >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required to build the final demo video" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_VIDEO")"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/driverx-demo.XXXXXX")"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

make_card() {
  local name="$1"
  local seconds="$2"
  local text="$3"
  local image_file="$TMP_DIR/$name.png"
  local out_file="$TMP_DIR/$name.mp4"
  CARD_TEXT="$text" CARD_IMAGE="$image_file" CARD_FONT="$FONT" CARD_WIDTH="$WIDTH" CARD_HEIGHT="$HEIGHT" \
    python3 - <<'PY'
import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

width = int(os.environ["CARD_WIDTH"])
height = int(os.environ["CARD_HEIGHT"])
text = os.environ["CARD_TEXT"]
candidate_fonts = [
    Path(os.environ["CARD_FONT"]) if os.environ["CARD_FONT"] else None,
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    Path("/System/Library/Fonts/SFNS.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
]
font_path = next((path for path in candidate_fonts if path and path.exists()), None)
if font_path is None:
    title_font = ImageFont.load_default(size=52)
    body_font = ImageFont.load_default(size=36)
    small_font = ImageFont.load_default(size=24)
else:
    title_font = ImageFont.truetype(str(font_path), 52)
    body_font = ImageFont.truetype(str(font_path), 36)
    small_font = ImageFont.truetype(str(font_path), 24)
image = Image.new("RGB", (width, height), "#101418")
draw = ImageDraw.Draw(image)

draw.rectangle((0, 0, width, 84), fill="#1b2a32")
draw.text((56, 28), "0xDriver Scenario Studio", font=small_font, fill="#9fd3c7")

lines = []
for raw_line in text.splitlines():
    if raw_line.strip():
        lines.extend(textwrap.wrap(raw_line, width=54) or [""])
    else:
        lines.append("")

y = 180
for idx, line in enumerate(lines):
    font = title_font if idx == 0 else body_font
    bbox = draw.textbbox((0, 0), line, font=font)
    x = (width - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), line, font=font, fill="#f4f7f5")
    y += 70 if idx == 0 else 52

draw.rectangle((56, height - 86, width - 56, height - 84), fill="#5eead4")
draw.text((56, height - 58), "SoTA Commission I / minimal-shot autonomy evidence packet", font=small_font, fill="#9fb1aa")
image.save(os.environ["CARD_IMAGE"])
PY
  ffmpeg -hide_banner -loglevel error -y \
    -loop 1 -framerate "$FPS" -t "$seconds" -i "$image_file" \
    -vf "fps=${FPS},format=yuv420p" \
    -an -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$out_file"
}

make_card "00-title" 7 "0xDriver\nMinimal-shot autonomy stress testing\nRandomized OOD scenarios for frozen reasoning VLAs"
make_card "01-studio" 8 "Scenario Studio\n10 prompts -> 20 curated OOD candidates\nBehaviors, environments, assets, memory queries, and quality gates"

ffmpeg -hide_banner -loglevel error -y \
  -i "$HERO_VIDEO" \
  -vf "scale=${WIDTH}:${HEIGHT}:force_original_aspect_ratio=decrease,pad=${WIDTH}:${HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps=${FPS}" \
  -an -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$TMP_DIR/02-hero.mp4"

make_card "03-vla" 9 "Frozen Alpamayo + retrieved safety memory\n3 open-loop OOD comparisons\n2 reasoning traces changed without fine-tuning"
make_card "04-failure" 9 "Understood limitation\nThe current VLA proof is open-loop and slow\nIt reasons over generated scenes but does not steer CARLA in real time"
make_card "05-submit" 7 "Contribution\nA simulator data engine for making long-tail cases,\nrunning evidence gates, and preserving failures as minimal-shot memory"

cat > "$TMP_DIR/concat.txt" <<EOF
file '$TMP_DIR/00-title.mp4'
file '$TMP_DIR/01-studio.mp4'
file '$TMP_DIR/02-hero.mp4'
file '$TMP_DIR/03-vla.mp4'
file '$TMP_DIR/04-failure.mp4'
file '$TMP_DIR/05-submit.mp4'
EOF

ffmpeg -hide_banner -loglevel error -y \
  -f concat -safe 0 -i "$TMP_DIR/concat.txt" \
  -c copy "$OUTPUT_VIDEO"

echo "$OUTPUT_VIDEO"
