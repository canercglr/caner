"""Title card: the topic title is 'written' on screen with a left-to-right wipe."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

from .animator import BACKGROUND

_TITLE_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
_LABEL_FONTS = [
    "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _load_font(size: int, candidates=None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in candidates or _TITLE_FONTS:
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
    ink = (35, 43, 56, 255)

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
    # underline flourish: a gentle hand-drawn swash with a small tail
    yy = y + 14
    d.line([(cw * 0.32 + i, yy + 4 * (1 - abs(i / (cw * 0.18) - 1)))
            for i in range(0, int(cw * 0.36), 8)],
           fill=(184, 69, 60, 255), width=max(3, ch // 130), joint="curve")
    return layer


def make_label_layer(text: str, canvas: Tuple[int, int]) -> Tuple[Image.Image, Tuple[int, int, int, int]]:
    """Small caption layer centered near the bottom of the canvas."""
    cw, ch = canvas
    size = max(22, ch // 15)
    font = _load_font(size, _LABEL_FONTS)
    layer = Image.new("RGBA", canvas, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    tw = d.textlength(text, font=font)
    x = (cw - tw) // 2
    y = int(ch * 0.905) - size
    d.text((x, y), text, font=font, fill=(35, 43, 56, 255))
    # short accent dashes flanking the caption
    my = y + size * 0.62
    acc = (184, 69, 60, 255)
    d.line([(x - 46, my), (x - 18, my)], fill=acc, width=3)
    d.line([(x + tw + 18, my), (x + tw + 46, my)], fill=acc, width=3)
    bbox = layer.getbbox() or (0, 0, cw, ch)
    return layer, bbox


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
