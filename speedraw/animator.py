"""Render speed-drawing frames: progressively reveal SVG strokes with a hand."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw
from svgpathtools import parse_path

from .hand import get_hand_image

Point = Tuple[float, float]

BACKGROUND = (252, 252, 250)


@dataclass
class Stroke:
    points: List[Point]           # dense polyline, canvas coordinates
    cum_len: List[float]          # cumulative length at each point, cum_len[0] == 0
    color: Tuple[int, int, int]
    width: int

    @property
    def length(self) -> float:
        return self.cum_len[-1]


# ---------------------------------------------------------------------------
# SVG parsing
# ---------------------------------------------------------------------------

_TAG_RE = re.compile(r"<(path|line|circle|ellipse|rect|polyline)\b([^>]*?)/?>", re.IGNORECASE | re.DOTALL)
_ATTR_RE = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*"([^"]*)"')


def _parse_color(value: Optional[str]) -> Optional[Tuple[int, int, int]]:
    if not value:
        return None
    value = value.strip().lower()
    if value in ("none", "transparent"):
        return None
    named = {
        "black": (17, 17, 17), "red": (192, 57, 43), "blue": (26, 111, 176),
        "green": (39, 130, 67), "orange": (211, 124, 27), "gray": (110, 110, 110),
        "grey": (110, 110, 110), "brown": (120, 78, 40), "purple": (108, 60, 158),
        "yellow": (222, 178, 20),
    }
    if value in named:
        return named[value]
    m = re.match(r"#([0-9a-f]{3})$", value)
    if m:
        h = m.group(1)
        return tuple(int(c * 2, 16) for c in h)  # type: ignore[return-value]
    m = re.match(r"#([0-9a-f]{6})$", value)
    if m:
        h = m.group(1)
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    m = re.match(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$", value)
    if m:
        return tuple(min(255, int(g)) for g in m.groups())  # type: ignore[return-value]
    return (17, 17, 17)


def _shape_to_path_d(tag: str, attrs: dict) -> Optional[str]:
    """Convert basic SVG shapes to a path 'd' string."""
    def f(name: str, default: float = 0.0) -> float:
        try:
            return float(attrs.get(name, default))
        except ValueError:
            return default

    if tag == "path":
        return attrs.get("d")
    if tag == "line":
        return f"M {f('x1')},{f('y1')} L {f('x2')},{f('y2')}"
    if tag == "circle":
        cx, cy, r = f("cx"), f("cy"), f("r")
        if r <= 0:
            return None
        return (
            f"M {cx - r},{cy} "
            f"A {r},{r} 0 1 0 {cx + r},{cy} "
            f"A {r},{r} 0 1 0 {cx - r},{cy}"
        )
    if tag == "ellipse":
        cx, cy, rx, ry = f("cx"), f("cy"), f("rx"), f("ry")
        if rx <= 0 or ry <= 0:
            return None
        return (
            f"M {cx - rx},{cy} "
            f"A {rx},{ry} 0 1 0 {cx + rx},{cy} "
            f"A {rx},{ry} 0 1 0 {cx - rx},{cy}"
        )
    if tag == "rect":
        x, y, w, h = f("x"), f("y"), f("width"), f("height")
        if w <= 0 or h <= 0:
            return None
        return f"M {x},{y} L {x + w},{y} L {x + w},{y + h} L {x},{y + h} Z"
    if tag == "polyline":
        raw = attrs.get("points", "")
        nums = re.findall(r"-?\d*\.?\d+(?:e-?\d+)?", raw)
        if len(nums) < 4:
            return None
        pairs = [f"{nums[i]},{nums[i+1]}" for i in range(0, len(nums) - 1, 2)]
        return "M " + " L ".join(pairs)
    return None


def _viewbox(svg_text: str) -> Tuple[float, float, float, float]:
    m = re.search(r'viewBox\s*=\s*"([^"]+)"', svg_text)
    if m:
        nums = re.findall(r"-?\d*\.?\d+", m.group(1))
        if len(nums) == 4:
            x, y, w, h = (float(n) for n in nums)
            if w > 0 and h > 0:
                return x, y, w, h
    return 0.0, 0.0, 1280.0, 720.0


def parse_svg_strokes(svg_text: str, canvas: Tuple[int, int]) -> List[Stroke]:
    """Parse an SVG into ordered, densely sampled strokes in canvas coordinates."""
    vx, vy, vw, vh = _viewbox(svg_text)
    cw, ch = canvas
    scale = min(cw / vw, ch / vh)
    ox = (cw - vw * scale) / 2 - vx * scale
    oy = (ch - vh * scale) / 2 - vy * scale

    strokes: List[Stroke] = []
    for m in _TAG_RE.finditer(svg_text):
        tag = m.group(1).lower()
        attrs = dict(_ATTR_RE.findall(m.group(2)))
        d = _shape_to_path_d(tag, attrs)
        if not d:
            continue
        color = _parse_color(attrs.get("stroke")) or (17, 17, 17)
        try:
            width = max(2, round(float(attrs.get("stroke-width", 5)) * scale))
        except ValueError:
            width = 5
        try:
            path = parse_path(d)
        except Exception:
            continue

        # Each subpath (continuous run of segments) becomes one stroke, so the
        # pen lifts between disconnected parts instead of drawing a bridge.
        for sub in path.continuous_subpaths():
            try:
                sub_len = sub.length(error=1e-3)
            except Exception:
                continue
            if not sub_len or sub_len < 1e-6:
                continue
            n = max(12, min(600, int(sub_len * scale / 3)))
            pts: List[Point] = []
            for i in range(n + 1):
                z = sub.point(i / n)
                pts.append((z.real * scale + ox, z.imag * scale + oy))
            pts = _wobble(pts, seed=len(strokes))
            cum = [0.0]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                cum.append(cum[-1] + math.hypot(x1 - x0, y1 - y0))
            if cum[-1] < 1.0:
                continue
            strokes.append(Stroke(points=pts, cum_len=cum, color=color, width=width))
    return strokes


def _wobble(pts: List[Point], seed: int, amp: float = 1.6, wavelength: float = 70.0) -> List[Point]:
    """Displace points perpendicular to the path with smooth noise for a
    hand-drawn look. Deterministic per stroke so repeated runs match."""
    if len(pts) < 3:
        return pts
    phase = (seed * 2.399963) % (2 * math.pi)  # golden-angle spread per stroke
    out: List[Point] = [pts[0]]
    dist = 0.0
    for i in range(1, len(pts) - 1):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        seg = math.hypot(x1 - x0, y1 - y0)
        dist += seg
        dx, dy = pts[i + 1][0] - x0, pts[i + 1][1] - y0
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        # two sine octaves = organic wobble, fades at the ends of the stroke
        w = (math.sin(dist * 2 * math.pi / wavelength + phase)
             + 0.5 * math.sin(dist * 2 * math.pi / (wavelength * 0.37) + phase * 1.7))
        fade = min(1.0, i / 4, (len(pts) - 1 - i) / 4)
        off = amp * w * fade
        out.append((x1 + nx * off, y1 + ny * off))
    out.append(pts[-1])
    return out


# ---------------------------------------------------------------------------
# Frame rendering
# ---------------------------------------------------------------------------


def _draw_stroke_upto(draw: ImageDraw.ImageDraw, stroke: Stroke, upto: float) -> Optional[Point]:
    """Draw a stroke up to `upto` px of its length. Returns the pen tip point."""
    pts = stroke.points
    cum = stroke.cum_len
    if upto <= 0:
        return None
    if upto >= stroke.length:
        segment = pts
        seg_cum = cum
        tip = pts[-1]
    else:
        # find last fully-covered point, then interpolate the partial segment
        import bisect

        i = bisect.bisect_right(cum, upto) - 1
        i = max(0, min(i, len(pts) - 2))
        seg_len = cum[i + 1] - cum[i]
        t = 0.0 if seg_len <= 0 else (upto - cum[i]) / seg_len
        x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t
        y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
        segment = pts[: i + 1] + [(x, y)]
        seg_cum = cum[: i + 1] + [upto]
        tip = (x, y)
    if len(segment) >= 2:
        # draw in short chunks with a subtly varying width — marker pressure feel
        base_w = stroke.width
        step = 6
        for j in range(0, len(segment) - 1, step):
            chunk = segment[j : j + step + 1]
            mid = seg_cum[min(j + step // 2, len(seg_cum) - 1)]
            wv = base_w + round(0.9 * math.sin(mid / 34.0 + base_w))
            draw.line(chunk, fill=stroke.color, width=max(2, wv), joint="curve")
        r = base_w / 2
        for px, py in (segment[0], segment[-1]):
            draw.ellipse([px - r, py - r, px + r, py + r], fill=stroke.color)
    return tip


class SceneAnimator:
    """Writes the PNG frame sequence for one scene."""

    def __init__(self, canvas: Tuple[int, int], fps: int):
        self.canvas = canvas
        self.fps = fps
        scale = canvas[1] / 720
        self.hand = get_hand_image(scale=scale)
        self._hand_tip = max(1, int(6 * scale))  # pen-tip offset inside the hand image

    def render_scene(
        self,
        svg_text: str,
        duration: float,
        frames_dir: Path,
        start_index: int,
        label: Optional[str] = None,
        draw_fraction: float = 0.82,
    ) -> int:
        """Render one scene's frames. Returns the next free frame index."""
        strokes = parse_svg_strokes(svg_text, self.canvas)
        total_len = sum(s.length for s in strokes)
        total_frames = max(1, round(duration * self.fps))

        label_layer = label_bbox = None
        label_frames = 0
        if label:
            from .textcard import make_label_layer

            draw_fraction = min(draw_fraction, 0.70)
            label_layer, label_bbox = make_label_layer(label, self.canvas)
            label_frames = max(1, round(total_frames * 0.16))
        draw_frames = max(1, min(total_frames, round(total_frames * draw_fraction)))

        # Static base image rebuilt incrementally: completed strokes are baked in
        # so each frame only re-draws the one in-progress stroke.
        base = Image.new("RGB", self.canvas, BACKGROUND)
        baked = 0  # number of strokes fully drawn onto base

        idx = start_index
        for f in range(total_frames):
            if total_len > 0 and f < draw_frames:
                revealed = total_len * (f + 1) / draw_frames
            else:
                revealed = total_len

            # bake strokes that are now fully revealed
            remaining = revealed
            for s in strokes[:baked]:
                remaining -= s.length
            while baked < len(strokes) and remaining >= strokes[baked].length:
                d = ImageDraw.Draw(base)
                _draw_stroke_upto(d, strokes[baked], strokes[baked].length)
                remaining -= strokes[baked].length
                baked += 1

            frame = base.copy()
            tip: Optional[Point] = None
            if baked < len(strokes) and remaining > 0:
                d = ImageDraw.Draw(frame)
                tip = _draw_stroke_upto(d, strokes[baked], remaining)

            drawing_done = revealed >= total_len or baked >= len(strokes)

            # caption wipes in right after the drawing completes
            if label_layer is not None and f >= draw_frames:
                lf = f - draw_frames
                x0, x1 = label_bbox[0], label_bbox[2]
                mid_y = (label_bbox[1] + label_bbox[3]) // 2
                if lf < label_frames:
                    reveal_x = x0 + int((x1 - x0) * (lf + 1) / label_frames)
                    mask = Image.new("L", self.canvas, 0)
                    ImageDraw.Draw(mask).rectangle(
                        [0, 0, reveal_x, self.canvas[1]], fill=255
                    )
                    partial = Image.new("RGBA", self.canvas, (0, 0, 0, 0))
                    partial.paste(label_layer, (0, 0), mask)
                    frame.paste(partial, (0, 0), partial)
                    self.paste_hand(frame, (reveal_x, mid_y))
                    tip = None  # hand already placed at the caption
                else:
                    frame.paste(label_layer, (0, 0), label_layer)

            if tip is not None and not drawing_done:
                self.paste_hand(frame, tip)

            frame.save(frames_dir / f"{idx:06d}.png")
            idx += 1
        return idx

    def render_title(
        self, title: str, duration: float, frames_dir: Path, start_index: int
    ) -> int:
        """Render a title card where the title text wipes in with the hand."""
        from .textcard import render_title_frames

        return render_title_frames(
            title, duration, frames_dir, start_index, self.canvas, self.fps, self
        )

    def paste_hand(self, frame: Image.Image, tip: Point) -> None:
        x, y = int(tip[0]), int(tip[1])
        off = self._hand_tip
        frame.paste(self.hand, (x - off, y - off), self.hand)
