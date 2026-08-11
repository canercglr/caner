"""Title card: the topic title is 'written' on screen with a left-to-right wipe."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

from .animator import BACKGROUND

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # older Pillow
        return ImageFont.load_default()


def _fit_title(title: str, canvas: Tuple[int, int]) -> Image.Image:
    """Render the title (word-wrapped, centered) onto a full-canvas RGBA layer."""
    cw, ch = canvas
    size = max(28, ch // 8)
    ink = (30, 35, 60, 255)

    while True:
        font = _load_font(size)
        words = title.split()
        lines, line = [], ""
        max_w = int(cw * 0.86)
        dummy = ImageDraw.Draw(Image.new("RGB", (8, 8)))
        for w in words:
            trial = (line + " " + w).strip()
            if dummy.textlength(trial, font=font) <= max_w or not line:
                line = trial
            else:
                lines.append(line)
                line = w
        lines.append(line)
        line_h = int(size * 1.25)
        total_h = line_h * len(lines)
        if total_h <= ch * 0.7 or size <= 28:
            break
        size = int(size * 0.85)

    layer = Image.new("RGBA", canvas, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = (ch - total_h) // 2
    for ln in lines:
        w = d.textlength(ln, font=font)
        d.text(((cw - w) // 2, y), ln, font=font, fill=ink)
        y += line_h
    # underline flourish
    d.line([(cw * 0.3, y + 10), (cw * 0.7, y + 10)], fill=(192, 57, 43, 255),
           width=max(3, ch // 120))
    return layer


def render_title_frames(
    title: str,
    duration: float,
    frames_dir: Path,
    start_index: int,
    canvas: Tuple[int, int],
    fps: int,
    animator,
) -> int:
    cw, ch = canvas
    layer = _fit_title(title, canvas)
    bbox = layer.getbbox() or (0, 0, cw, ch)
    x0, x1 = bbox[0], bbox[2]
    mid_y = (bbox[1] + bbox[3]) // 2

    total_frames = max(1, round(duration * fps))
    wipe_frames = max(1, int(total_frames * 0.7))

    idx = start_index
    for f in range(total_frames):
        frame = Image.new("RGB", canvas, BACKGROUND)
        if f < wipe_frames:
            reveal_x = x0 + int((x1 - x0) * (f + 1) / wipe_frames)
            mask = Image.new("L", canvas, 0)
            ImageDraw.Draw(mask).rectangle([0, 0, reveal_x, ch], fill=255)
            partial = Image.new("RGBA", canvas, (0, 0, 0, 0))
            partial.paste(layer, (0, 0), mask)
            frame.paste(partial, (0, 0), partial)
            animator.paste_hand(frame, (reveal_x, mid_y))
        else:
            frame.paste(layer, (0, 0), layer)
        frame.save(frames_dir / f"{idx:06d}.png")
        idx += 1
    return idx
