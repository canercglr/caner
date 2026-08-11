"""Render speed-drawing frames: progressively reveal SVG strokes with a hand,
then bring parts of the finished drawing to life.

Motion system
-------------
Any SVG element may carry a ``data-anim`` attribute. Once the scene's drawing
completes, tagged elements start moving while the caption is written:

- ``float[:amp]``          gentle vertical bobbing (bubbles, clouds, boats)
- ``drift:dx,dy[,wrap]``   continuous motion in px/s; with ``wrap`` the element
                           snaps back after travelling that many px (rain,
                           rising bubbles, conveyor items)
- ``spin[:period]``        slow rotation about its own center (gears, rays)
- ``sway[:deg]``           pendulum sway about its base (plants, trees, flames)
- ``pulse[:amp]``          gentle scale beat about its center (sun, hearts)

A procedural walking actor is available as a custom element::

    <walker x="200" y="560" to-x="900" scale="1" stroke="#222"/>

It is drawn standing (the hand traces it like any stroke), then walks from
``x`` to ``to-x`` with swinging arms and legs. ``y`` is the ground level.
"""

from __future__ import annotations

import bisect
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw
from svgpathtools import parse_path

from .hand import get_hand_image

Point = Tuple[float, float]

BACKGROUND = (252, 252, 250)


# ---------------------------------------------------------------------------
# Animation specs
# ---------------------------------------------------------------------------


@dataclass
class AnimSpec:
    kind: str                       # float | drift | spin | sway | pulse | walker
    params: Tuple[float, ...] = ()
    pivot: Point = (0.0, 0.0)       # set after parsing, from the group bbox
    phase: float = 0.0
    walker: Optional["WalkerSpec"] = None


@dataclass
class WalkerSpec:
    x: float          # canvas coords
    y: float          # ground level (feet)
    to_x: float
    scale: float      # canvas-space size multiplier
    color: Tuple[int, int, int]
    width: int


@dataclass
class Stroke:
    points: List[Point]           # dense polyline, canvas coordinates
    cum_len: List[float]          # cumulative length, cum_len[0] == 0
    color: Tuple[int, int, int]
    width: int
    anim: Optional[AnimSpec] = None

    @property
    def length(self) -> float:
        return self.cum_len[-1]


def _parse_anim(value: Optional[str]) -> Optional[AnimSpec]:
    if not value:
        return None
    head, _, rest = value.strip().partition(":")
    kind = head.strip().lower()
    nums: List[float] = []
    for tok in rest.split(","):
        tok = tok.strip()
        if tok:
            try:
                nums.append(float(tok))
            except ValueError:
                pass
    if kind == "float":
        return AnimSpec("float", (nums[0] if nums else 10.0,))
    if kind == "drift":
        if len(nums) < 2:
            return None
        wrap = nums[2] if len(nums) > 2 else 0.0
        return AnimSpec("drift", (nums[0], nums[1], wrap))
    if kind == "spin":
        return AnimSpec("spin", (nums[0] if nums else 6.0,))
    if kind == "sway":
        return AnimSpec("sway", (nums[0] if nums else 4.0,))
    if kind == "pulse":
        return AnimSpec("pulse", (nums[0] if nums else 0.06,))
    return None


def _anim_offset(anim: AnimSpec, t: float):
    """Return an affine transform fn for time t (seconds since motion start)."""
    k = anim.kind
    px, py = anim.pivot
    if k == "float":
        amp = anim.params[0]
        dy = amp * math.sin(2 * math.pi * t / 2.6 + anim.phase)
        return lambda x, y: (x, y + dy)
    if k == "drift":
        dx, dy, wrap = anim.params
        speed = math.hypot(dx, dy)
        if wrap > 0 and speed > 0:
            travelled = (speed * t) % wrap
            ox, oy = dx / speed * travelled, dy / speed * travelled
        else:
            ox, oy = dx * t, dy * t
        return lambda x, y: (x + ox, y + oy)
    if k == "spin":
        period = max(0.5, anim.params[0])
        a = 2 * math.pi * t / period
        ca, sa = math.cos(a), math.sin(a)
        return lambda x, y: (px + (x - px) * ca - (y - py) * sa,
                             py + (x - px) * sa + (y - py) * ca)
    if k == "sway":
        amp = math.radians(anim.params[0])
        a = amp * math.sin(2 * math.pi * t / 2.9 + anim.phase)
        ca, sa = math.cos(a), math.sin(a)
        return lambda x, y: (px + (x - px) * ca - (y - py) * sa,
                             py + (x - px) * sa + (y - py) * ca)
    if k == "pulse":
        amp = anim.params[0]
        s = 1.0 + amp * math.sin(2 * math.pi * t / 2.2 + anim.phase)
        return lambda x, y: (px + (x - px) * s, py + (y - py) * s)
    return lambda x, y: (x, y)


# ---------------------------------------------------------------------------
# SVG parsing
# ---------------------------------------------------------------------------

_TAG_RE = re.compile(
    r"<(path|line|circle|ellipse|rect|polyline|walker)\b([^>]*?)/?>",
    re.IGNORECASE | re.DOTALL,
)
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
    """Parse an SVG into ordered, densely sampled strokes in canvas coords."""
    vx, vy, vw, vh = _viewbox(svg_text)
    cw, ch = canvas
    scale = min(cw / vw, ch / vh)
    ox = (cw - vw * scale) / 2 - vx * scale
    oy = (ch - vh * scale) / 2 - vy * scale

    strokes: List[Stroke] = []
    for m in _TAG_RE.finditer(svg_text):
        tag = m.group(1).lower()
        attrs = dict(_ATTR_RE.findall(m.group(2)))

        if tag == "walker":
            strokes.extend(_walker_strokes(attrs, scale, ox, oy))
            continue

        d = _shape_to_path_d(tag, attrs)
        if not d:
            continue
        color = _parse_color(attrs.get("stroke")) or (17, 17, 17)
        try:
            width = max(2, round(float(attrs.get("stroke-width", 5)) * scale))
        except ValueError:
            width = 5
        anim = _parse_anim(attrs.get("data-anim"))
        try:
            path = parse_path(d)
        except Exception:
            continue

        group: List[Stroke] = []
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
            pts = _wobble(pts, seed=len(strokes) + len(group))
            cum = [0.0]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                cum.append(cum[-1] + math.hypot(x1 - x0, y1 - y0))
            if cum[-1] < 1.0:
                continue
            group.append(Stroke(points=pts, cum_len=cum, color=color,
                                width=width, anim=anim))

        if anim is not None and group:
            _set_group_pivot(anim, group, seed=len(strokes))
        strokes.extend(group)
    return strokes


def _set_group_pivot(anim: AnimSpec, group: List[Stroke], seed: int) -> None:
    xs = [p[0] for s in group for p in s.points]
    ys = [p[1] for s in group for p in s.points]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if anim.kind == "sway":
        anim.pivot = ((x0 + x1) / 2, y1)      # swing about the base
    else:
        anim.pivot = ((x0 + x1) / 2, (y0 + y1) / 2)
    anim.phase = (seed * 1.7) % (2 * math.pi)


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
# Walking actor
# ---------------------------------------------------------------------------


def _walker_spec(attrs: dict, scale: float, ox: float, oy: float) -> Optional[WalkerSpec]:
    def f(name: str, default: Optional[float] = None) -> Optional[float]:
        v = attrs.get(name)
        if v is None:
            return default
        try:
            return float(v)
        except ValueError:
            return default

    x, y = f("x"), f("y")
    if x is None or y is None:
        return None
    to_x = f("to-x", x)
    sc = f("scale", 1.0) or 1.0
    color = _parse_color(attrs.get("stroke")) or (17, 17, 17)
    return WalkerSpec(
        x=x * scale + ox,
        y=y * scale + oy,
        to_x=to_x * scale + ox,
        scale=sc * scale,
        color=color,
        width=max(3, round(6 * sc * scale)),
    )


def _walker_pose(spec: WalkerSpec, t: Optional[float], progress: float) -> List[List[Point]]:
    """Return the walker's polylines. t=None -> standing pose."""
    s = spec.scale
    X = spec.x + (spec.to_x - spec.x) * progress
    Y = spec.y
    facing = 1.0 if spec.to_x >= spec.x else -1.0

    if t is None:
        swing = 0.0
        bob = 0.0
        w = 0.0
    else:
        w = 2 * math.pi * 1.7 * t          # step cycle
        swing = math.sin(w)
        bob = 2.5 * s * abs(math.cos(w))

    hip = (X, Y - 92 * s - bob)
    shoulder = (X + facing * 2 * s, Y - 148 * s - bob)
    head_c = (X + facing * 5 * s, Y - 172 * s - bob)
    head_r = 23 * s

    def limb(origin: Point, l1: float, l2: float, a1: float, a2: float) -> List[Point]:
        """Two-segment limb; angles measured from straight down, + = forward."""
        jx = origin[0] + facing * math.sin(a1) * l1
        jy = origin[1] + math.cos(a1) * l1
        ex = jx + facing * math.sin(a1 + a2) * l2
        ey = jy + math.cos(a1 + a2) * l2
        return [origin, (jx, jy), (ex, ey)]

    if t is None:
        legs = [limb(hip, 48 * s, 46 * s, 0.14, 0.0),
                limb(hip, 48 * s, 46 * s, -0.14, 0.0)]
        arms = [limb(shoulder, 40 * s, 34 * s, 0.30, 0.10),
                limb(shoulder, 40 * s, 34 * s, -0.30, -0.10)]
    else:
        amp = 0.55
        legs = []
        for ph in (0.0, math.pi):
            a1 = amp * math.sin(w + ph)
            # knee bends while the leg swings forward
            a2 = -0.85 * max(0.0, math.sin(w + ph - math.pi / 2))
            legs.append(limb(hip, 48 * s, 46 * s, a1, a2))
        arms = []
        for ph in (math.pi, 0.0):   # arms opposite to same-side legs
            a1 = 0.7 * amp * math.sin(w + ph)
            arms.append(limb(shoulder, 40 * s, 34 * s, a1, 0.35))

    # head circle as a polyline
    head = [(head_c[0] + head_r * math.cos(2 * math.pi * i / 28),
             head_c[1] + head_r * math.sin(2 * math.pi * i / 28)) for i in range(29)]
    smile = [(head_c[0] + facing * (-6 + 12 * i / 6) * s,
              head_c[1] + 9 * s + 2.5 * s * math.sin(math.pi * i / 6)) for i in range(7)]
    spine = [shoulder, hip]
    neck = [(head_c[0], head_c[1] + head_r), shoulder]

    return [head, smile, neck, spine, arms[0], arms[1], legs[0], legs[1]]


def _walker_strokes(attrs: dict, scale: float, ox: float, oy: float) -> List[Stroke]:
    """Standing-pose strokes so the hand can draw the figure."""
    spec = _walker_spec(attrs, scale, ox, oy)
    if spec is None:
        return []
    anim = AnimSpec("walker", walker=spec)
    out: List[Stroke] = []
    for line in _walker_pose(spec, None, 0.0):
        if len(line) < 2:
            continue
        # densify for smooth partial reveal
        pts: List[Point] = []
        for (x0, y0), (x1, y1) in zip(line, line[1:]):
            seg = max(2, int(math.hypot(x1 - x0, y1 - y0) / 4))
            for i in range(seg):
                t = i / seg
                pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
        pts.append(line[-1])
        cum = [0.0]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            cum.append(cum[-1] + math.hypot(x1 - x0, y1 - y0))
        if cum[-1] < 1.0:
            continue
        out.append(Stroke(points=pts, cum_len=cum, color=spec.color,
                          width=spec.width, anim=anim))
    return out


def _draw_walker(draw: ImageDraw.ImageDraw, spec: WalkerSpec, t: float, progress: float) -> None:
    for line in _walker_pose(spec, t, progress):
        if len(line) >= 2:
            draw.line(line, fill=spec.color, width=spec.width, joint="curve")
            r = spec.width / 2
            for px, py in (line[0], line[-1]):
                draw.ellipse([px - r, py - r, px + r, py + r], fill=spec.color)


# ---------------------------------------------------------------------------
# Frame rendering
# ---------------------------------------------------------------------------


def _draw_stroke_upto(draw: ImageDraw.ImageDraw, stroke: Stroke, upto: float,
                      transform=None) -> Optional[Point]:
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
        i = bisect.bisect_right(cum, upto) - 1
        i = max(0, min(i, len(pts) - 2))
        seg_len = cum[i + 1] - cum[i]
        t = 0.0 if seg_len <= 0 else (upto - cum[i]) / seg_len
        x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t
        y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
        segment = pts[: i + 1] + [(x, y)]
        seg_cum = cum[: i + 1] + [upto]
        tip = (x, y)
    if transform is not None:
        segment = [transform(x, y) for x, y in segment]
        tip = segment[-1]
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

    def __init__(self, canvas: Tuple[int, int], fps: int, motion: bool = True):
        self.canvas = canvas
        self.fps = fps
        self.motion = motion
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
        if not self.motion:
            for s in strokes:
                if s.anim is not None and s.anim.kind != "walker":
                    s.anim = None
        total_len = sum(s.length for s in strokes)
        total_frames = max(1, round(duration * self.fps))

        label_layer = label_bbox = None
        label_frames = 0
        if label:
            from .textcard import make_label_layer

            draw_fraction = min(draw_fraction, 0.62)
            label_layer, label_bbox = make_label_layer(label, self.canvas)
            label_frames = max(1, round(total_frames * 0.14))
        draw_frames = max(1, min(total_frames, round(total_frames * draw_fraction)))
        anim_seconds = max(1e-6, (total_frames - draw_frames) / self.fps)

        start_cum = [0.0]
        for s in strokes:
            start_cum.append(start_cum[-1] + s.length)

        # Static strokes get baked into a base image once fully drawn, so each
        # frame only re-draws the in-progress stroke and the moving elements.
        base = Image.new("RGB", self.canvas, BACKGROUND)
        baked = [False] * len(strokes)

        idx = start_index
        for f in range(total_frames):
            if total_len > 0 and f < draw_frames:
                revealed = total_len * (f + 1) / draw_frames
            else:
                revealed = total_len
            t_anim = max(0.0, (f - draw_frames + 1)) / self.fps if self.motion else 0.0
            progress = min(1.0, t_anim / anim_seconds)

            base_draw = ImageDraw.Draw(base)
            for i, s in enumerate(strokes):
                if (not baked[i] and s.anim is None
                        and revealed >= start_cum[i] + s.length - 1e-6):
                    _draw_stroke_upto(base_draw, s, s.length)
                    baked[i] = True

            frame = base.copy()
            d = ImageDraw.Draw(frame)
            tip: Optional[Point] = None
            transforms: Dict[int, object] = {}
            walkers_drawn: set = set()

            for i, s in enumerate(strokes):
                rev = revealed - start_cum[i]
                if rev <= 0 or baked[i]:
                    continue
                anim = s.anim
                if rev < s.length - 1e-6:
                    tip = _draw_stroke_upto(d, s, rev)
                elif anim is None:
                    pass  # baked above
                elif anim.kind == "walker":
                    if t_anim > 0:
                        if id(anim) not in walkers_drawn:
                            _draw_walker(d, anim.walker, t_anim, progress)
                            walkers_drawn.add(id(anim))
                    else:
                        _draw_stroke_upto(d, s, s.length)
                else:
                    if t_anim > 0:
                        key = id(anim)
                        if key not in transforms:
                            transforms[key] = _anim_offset(anim, t_anim)
                        _draw_stroke_upto(d, s, s.length, transform=transforms[key])
                    else:
                        _draw_stroke_upto(d, s, s.length)

            drawing_done = f >= draw_frames - 1 or revealed >= total_len

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
