"""Procedurally drawn hand-holding-a-marker overlay (no binary assets needed).

The pen tip sits at pixel (6, 6) of the returned RGBA image, so pasting the
image at (x - 6, y - 6) puts the tip exactly on the current drawing point.
"""

from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageDraw

SKIN = (232, 190, 156, 255)
SKIN_SHADOW = (206, 160, 125, 255)
OUTLINE = (120, 85, 60, 255)
MARKER_BODY = (40, 40, 45, 255)
MARKER_CAP = (90, 90, 100, 255)
SLEEVE = (70, 110, 170, 255)


@lru_cache(maxsize=4)
def get_hand_image(scale: float = 1.0) -> Image.Image:
    w, h = 260, 300
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Marker running from the tip (6,6) down-right at ~40 degrees.
    d.polygon([(6, 6), (26, 14), (18, 32)], fill=MARKER_BODY)          # nib
    d.polygon([(20, 16), (96, 78), (76, 104), (10, 40)], fill=MARKER_BODY)  # barrel
    d.polygon([(96, 78), (120, 100), (100, 126), (76, 104)], fill=MARKER_CAP)  # butt

    # Fist gripping the marker.
    d.ellipse([52, 62, 172, 176], fill=SKIN, outline=OUTLINE, width=3)
    # Fingers wrapped over the barrel.
    for i in range(4):
        x0 = 48 + i * 24
        y0 = 58 + i * 16
        d.rounded_rectangle([x0, y0, x0 + 34, y0 + 26], radius=12,
                            fill=SKIN, outline=OUTLINE, width=2)
    # Thumb.
    d.ellipse([44, 96, 96, 140], fill=SKIN_SHADOW, outline=OUTLINE, width=2)

    # Wrist / sleeve trailing to bottom-right.
    d.polygon([(120, 150), (196, 128), (256, 208), (196, 288), (108, 200)], fill=SKIN)
    d.polygon([(176, 168), (256, 130), (260, 300), (150, 300)], fill=SLEEVE)

    if scale != 1.0:
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))),
                         Image.LANCZOS)
    return img
