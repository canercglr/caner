"""Procedurally drawn hand-holding-a-marker overlay (no binary assets needed).

The pen tip sits at pixel (6, 6) of the returned RGBA image, so pasting the
image at (x - 6, y - 6) puts the tip exactly on the current drawing point.

A stylized cartoon hand grips a marker that points up-left at 45 degrees; the
forearm leaves toward the bottom-right. Drawn at 2x and downsampled for smooth
anti-aliased edges. Coordinates use a pen-local frame: ``p(t, s)`` is ``t`` px
from the tip along the barrel and ``s`` px sideways (positive = up-right).
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Tuple

from PIL import Image, ImageDraw

SKIN = (240, 200, 168, 255)
SKIN_DEEP = (221, 175, 138, 255)
OUTLINE = (110, 76, 52, 255)
MARKER_DARK = (45, 47, 55, 255)
MARKER_MID = (80, 84, 96, 255)
MARKER_TIP = (22, 22, 26, 255)
SLEEVE = (56, 94, 150, 255)
SLEEVE_DARK = (41, 71, 116, 255)

Pt = Tuple[float, float]

_COS45 = math.cos(math.radians(45))


def _p(t: float, s: float) -> Pt:
    """Pen-local frame -> image px. t: along barrel from tip, s: sideways."""
    return (6 + _COS45 * (t + s), 6 + _COS45 * (t - s))


def _capsule(d: ImageDraw.ImageDraw, a: Pt, b: Pt, r: float, fill,
             outline=None, ow: float = 0) -> None:
    def solid(radius, color):
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L * radius, dx / L * radius
        d.polygon([(ax + nx, ay + ny), (bx + nx, by + ny),
                   (bx - nx, by - ny), (ax - nx, ay - ny)], fill=color)
        d.ellipse([ax - radius, ay - radius, ax + radius, ay + radius], fill=color)
        d.ellipse([bx - radius, by - radius, bx + radius, by + radius], fill=color)

    if outline and ow:
        solid(r + ow, outline)
    solid(r, fill)


@lru_cache(maxsize=4)
def get_hand_image(scale: float = 1.0) -> Image.Image:
    S = 2  # supersampling
    w, h = 310, 330
    img = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def sp(pt: Pt) -> Pt:
        return (pt[0] * S, pt[1] * S)

    def cap(t0, s0, t1, s1, r, fill, ow=3):
        _capsule(d, sp(_p(t0, s0)), sp(_p(t1, s1)), r * S, fill, OUTLINE, ow * S)

    # ---- forearm / sleeve toward bottom-right ------------------------------
    elbow = (272 * S, 300 * S)
    wrist = sp(_p(158, 12))
    _capsule(d, wrist, elbow, 46 * S, SLEEVE, OUTLINE, 3 * S)

    # ---- palm mass (behind fingers, connects grip to wrist) ----------------
    cap(100, 38, 168, 20, 34, SKIN)

    # ---- marker ------------------------------------------------------------
    cap(30, 0, 148, 0, 12, MARKER_DARK, ow=2)                    # barrel
    cap(148, 0, 170, 0, 9, MARKER_MID, ow=2)                     # end cap
    d.polygon([sp((6, 6)), sp(_p(32, 12)), sp(_p(32, -12))], fill=MARKER_TIP)  # nib
    _capsule(d, sp(_p(45, 5)), sp(_p(135, 5)), 2.2 * S, (255, 255, 255, 70))  # sheen

    # ---- four fingers wrapping across the barrel ---------------------------
    for i, t in enumerate((92, 112, 132, 152)):
        taper = (13, 12.5, 12, 11)[i]
        cap(t, 34, t - 6, -22, taper, SKIN)
        # fingertip nail-side shading
        tip = sp(_p(t - 6, -22))
        rr = 6 * S
        d.ellipse([tip[0] - rr, tip[1] - rr, tip[0] + rr, tip[1] + rr], fill=SKIN_DEEP)

    # ---- thumb pressing along the near side toward the nib -----------------
    cap(128, 30, 70, 16, 13, SKIN_DEEP)

    img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return img


if __name__ == "__main__":
    im = get_hand_image()
    bg = Image.new("RGB", im.size, (250, 250, 248))
    bg.paste(im, (0, 0), im)
    bg.save("/tmp/hand_preview.png")
