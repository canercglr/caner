"""Color & light atmosphere for story shots.

Each shot carries a ``mood`` (day / golden_hour / sunset / night / overcast)
that colors the whole frame three ways:

1. a **sky wash** — a soft vertical gradient painted onto the baked scenery
   background, like a watercolor wash over the paper;
2. a per-frame **color grade** — a cheap tint blend (plus a saturation trim
   for gloomy moods) applied after the camera crop;
3. **light glows** — warm radial halos behind lamp heads and campfires when
   the scene is dark enough for them to read.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Tuple

from PIL import Image, ImageEnhance

# mood -> (wash_rgb, wash_alpha, wash_depth,
#          grade_rgb, grade_alpha, saturation, brightness)
# wash_depth is how far down the canvas the sky gradient reaches (0-1).
MOODS = {
    "day":         ((188, 208, 232), 0.10, 0.42, None, 0.0, 1.0, 1.0),
    "golden_hour": ((246, 190, 118), 0.16, 0.60, (244, 186, 120), 0.085, 1.06, 1.0),
    "sunset":      ((238, 148, 116), 0.20, 0.72, (212, 130, 140), 0.11, 1.04, 0.97),
    "night":       ((42, 52, 96), 0.40, 1.00, (48, 56, 104), 0.26, 0.78, 0.85),
    "overcast":    ((176, 181, 189), 0.13, 0.60, (172, 176, 184), 0.09, 0.80, 0.96),
}

# how much longer/softer ground shadows get per mood
SHADOW_STRETCH = {"day": 1.0, "golden_hour": 1.7, "sunset": 1.9,
                  "night": 0.6, "overcast": 0.0}


def apply_sky_wash(bg: Image.Image, mood: str) -> None:
    """Paint the mood's sky gradient onto the baked background, in place."""
    rgb, alpha, depth, *_ = MOODS.get(mood, MOODS["day"])
    if alpha <= 0:
        return
    w, h = bg.size
    grad = _sky_gradient((w, h), rgb, alpha, depth)
    bg.paste(Image.new("RGB", (w, h), rgb), (0, 0), grad)


@lru_cache(maxsize=8)
def _sky_gradient(size: Tuple[int, int], rgb, alpha: float, depth: float) -> Image.Image:
    w, h = size
    col = Image.new("L", (1, h))
    px = col.load()
    reach = max(1, int(h * depth))
    for y in range(h):
        if y >= reach:
            px[0, y] = 0
        else:
            k = 1.0 - y / reach
            px[0, y] = int(255 * alpha * (k * k * (3 - 2 * k)))
    return col.resize((w, h))


@lru_cache(maxsize=8)
def _grade_layer(size: Tuple[int, int], rgb) -> Image.Image:
    return Image.new("RGB", size, rgb)


def grade_frame(frame: Image.Image, mood: str) -> Image.Image:
    """Fast per-frame color grade: tint blend + saturation/brightness trim."""
    spec = MOODS.get(mood, MOODS["day"])
    _, _, _, grade_rgb, grade_alpha, sat, bright = spec
    if grade_rgb is not None and grade_alpha > 0:
        frame = Image.blend(frame, _grade_layer(frame.size, grade_rgb), grade_alpha)
    if abs(sat - 1.0) > 0.01:
        frame = ImageEnhance.Color(frame).enhance(sat)
    if abs(bright - 1.0) > 0.01:
        frame = ImageEnhance.Brightness(frame).enhance(bright)
    return frame


@lru_cache(maxsize=4)
def _glow_sprite(radius: int, rgb) -> Image.Image:
    """Radial warm halo as an RGBA sprite (premultiplied look via alpha)."""
    d = radius * 2
    spr = Image.new("RGBA", (d, d), rgb + (0,))
    px = spr.load()
    for yy in range(d):
        for xx in range(d):
            r = math.hypot(xx - radius, yy - radius) / radius
            if r < 1.0:
                k = (1.0 - r)
                px[xx, yy] = rgb + (int(185 * k * k),)
    return spr


def add_light_glows(bg: Image.Image, props, mood: str, sx: float, sy: float) -> None:
    """Halos behind streetlamps and campfires on dark moods, in place."""
    if mood not in ("night", "sunset"):
        return
    strength = 1.0 if mood == "night" else 0.55
    for p in props:
        if p.kind == "streetlamp":
            cx = (p.x + 44 * p.scale) * sx
            cy = (p.y - 198 * p.scale) * sy
            radius = int(66 * p.scale * sx * strength)
        elif p.kind == "campfire":
            cx = p.x * sx
            cy = (p.y - 34 * p.scale) * sy
            radius = int(78 * p.scale * sx * strength)
        else:
            continue
        if radius < 8:
            continue
        spr = _glow_sprite(radius, (255, 199, 92))
        bg.paste(spr, (int(cx - radius), int(cy - radius)), spr)
