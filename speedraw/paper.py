"""Procedural paper background: subtle grain + soft vignette, cached per size."""

from __future__ import annotations

from functools import lru_cache
from typing import Tuple

import numpy as np
from PIL import Image

BACKGROUND = (252, 252, 250)


@lru_cache(maxsize=4)
def get_paper(size: Tuple[int, int]) -> Image.Image:
    w, h = size
    rng = np.random.default_rng(20260812)  # deterministic across runs

    base = np.empty((h, w, 3), dtype=np.float32)
    base[:, :] = BACKGROUND

    # coarse fiber blotches: low-res noise scaled up smoothly
    coarse = rng.normal(0.0, 2.6, (max(2, h // 24), max(2, w // 24)))
    coarse_img = Image.fromarray(
        np.clip(coarse * 8 + 128, 0, 255).astype(np.uint8)
    ).resize((w, h), Image.BILINEAR)
    coarse_f = (np.asarray(coarse_img, dtype=np.float32) - 128.0) / 8.0

    # fine grain
    fine = rng.normal(0.0, 1.5, (h, w)).astype(np.float32)

    grain = (coarse_f + fine)[..., None]
    base += grain

    # soft vignette: corners ~3% darker
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xx / w - 0.5) * 2
    ny = (yy / h - 0.5) * 2
    vign = 1.0 - 0.035 * np.clip(nx * nx + ny * ny - 0.25, 0, None)
    base *= vign[..., None]

    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")
