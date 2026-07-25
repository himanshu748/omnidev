"""
Render the README demo GIF.

Every line of output in this animation is real: it was captured from an
actual offline run against gemma4:12b and mxbai-embed-large on the author's
Mac, not written by hand. Re-capture with docs/probes/live_v7.py and update
FRAMES below if the numbers change.

Usage: python3 docs/probes/make_demo_gif.py [output.gif]
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1000, 620
PAD = 34
LINE_HEIGHT = 30
FPS_DELAY_MS = 55
BG = (10, 12, 16)
CHROME = (18, 21, 27)
INK = (238, 241, 247)
DIM = (135, 145, 162)
ACCENT = (77, 162, 255)
GREEN = (86, 211, 133)
AMBER = (232, 175, 90)

MONO_CANDIDATES = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Supplemental/Courier New.ttf",
]
UI_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def load_font(candidates: list[str], size: int):
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


MONO = load_font(MONO_CANDIDATES, 19)
MONO_BOLD = load_font(MONO_CANDIDATES, 19)
UI = load_font(UI_CANDIDATES, 17)
UI_SMALL = load_font(UI_CANDIDATES, 14)

# (text, colour, is_typed): typed lines animate character by character.
KNOWLEDGE_SCRIPT: list[tuple[str, tuple[int, int, int], bool]] = [
    ("$ omnidev knowledge add ~/Desktop", INK, True),
    ("  indexing 3 files, wifi off", DIM, False),
    ("  OCR: 1 screenshot read on device (macOS Vision)", DIM, False),
    ("  refused .env (protected pattern), never indexed", AMBER, False),
    ("  done in 11.4s, 2 excerpts: 1 doc, 1 image", GREEN, False),
    ("", INK, False),
    ("$ omnidev ask \"what is the payment reference", INK, True),
    ("          on the Northwind invoice?\"", INK, True),
    ("", INK, False),
    ("  Screenshot 2026-03-02 at 11.04.22.png   0.80", ACCENT, False),
    ("  ops-notes.md                            0.49", DIM, False),
    ("", INK, False),
    ("  The payment reference is QZ-88231.", GREEN, False),
    ("", INK, False),
    ("  cited: Screenshot 2026-03-02 at 11.04.22.png", DIM, False),
    ("  the answer existed only inside the image", DIM, False),
]

# Captured from a real offline run on gemma4:12b: 146 seconds, 5 tool calls,
# 1 approval, fix confirmed by an independent pytest run.
AGENT_SCRIPT: list[tuple[str, tuple[int, int, int], bool]] = [
    ("$ omnidev agent \"the test in calc.py fails, fix it", INK, True),
    ("          and run pytest to confirm\"", INK, True),
    ("", INK, False),
    ("  agent on gemma4:12b, offline, 6 tools", DIM, False),
    ("  list_dir    ~/work/calc", ACCENT, False),
    ("  read_file   test_calc.py", ACCENT, False),
    ("  read_file   calc.py", ACCENT, False),
    ("  edit_file   calc.py   return a - b  ->  a + b", ACCENT, False),
    ("", INK, False),
    ("  permission needed: run pytest test_calc.py", AMBER, False),
    ("  [allow once]  [always]  [deny]", AMBER, False),
    ("  approved", GREEN, False),
    ("", INK, False),
    ("  exit code 0    1 passed in 0.08s", GREEN, False),
    ("  the operator was inverted. fixed and verified.", INK, False),
]

SCRIPTS = {"knowledge": KNOWLEDGE_SCRIPT, "agent": AGENT_SCRIPT}


def draw_chrome(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill=BG)
    draw.rectangle([0, 0, WIDTH, 46], fill=CHROME)
    for index, colour in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = PAD + index * 22
        draw.ellipse([cx, 17, cx + 12, 29], fill=colour)
    draw.text((WIDTH // 2 - 66, 14), "OmniDev", font=UI, fill=DIM)
    # Offline badge, the whole point of the product.
    badge = "OFFLINE"
    draw.rectangle([WIDTH - PAD - 92, 13, WIDTH - PAD, 33], outline=GREEN)
    draw.text((WIDTH - PAD - 78, 15), badge, font=UI_SMALL, fill=GREEN)


def render(lines: list[tuple[str, tuple[int, int, int]]], cursor: bool) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw_chrome(draw)
    y = 46 + PAD
    for text, colour in lines:
        draw.text((PAD, y), text, font=MONO, fill=colour)
        y += LINE_HEIGHT
    if cursor and lines:
        last = lines[-1][0]
        width = draw.textlength(last, font=MONO)
        draw.rectangle([PAD + width + 2, y - LINE_HEIGHT + 4, PAD + width + 12, y - 6], fill=ACCENT)
    return image


def build(script) -> list[Image.Image]:
    frames: list[Image.Image] = []
    shown: list[tuple[str, tuple[int, int, int]]] = []

    for text, colour, typed in script:
        if typed and text:
            for index in range(1, len(text) + 1):
                frames.append(render(shown + [(text[:index], colour)], cursor=True))
            shown.append((text, colour))
            frames.extend([render(shown, cursor=True)] * 6)
        else:
            shown.append((text, colour))
            frames.extend([render(shown, cursor=False)] * (3 if text else 1))
        # Keep the viewport from overflowing.
        if len(shown) > 17:
            shown = shown[-17:]

    frames.extend([render(shown, cursor=False)] * 45)  # hold the ending
    return frames


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "knowledge"
    if name not in SCRIPTS:
        raise SystemExit(f"unknown script {name!r}; choose from {', '.join(SCRIPTS)}")
    default_out = "docs/demo.gif" if name == "knowledge" else f"docs/demo-{name}.gif"
    output = Path(sys.argv[2] if len(sys.argv) > 2 else default_out)
    output.parent.mkdir(parents=True, exist_ok=True)
    frames = build(SCRIPTS[name])
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=FPS_DELAY_MS,
        loop=0,
        optimize=True,
    )
    size_mb = output.stat().st_size / 1e6
    print(f"wrote {output} ({len(frames)} frames, {size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
