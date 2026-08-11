"""Canned script + drawings for offline testing (no API key required).

The demo illustrations are built procedurally so they can be genuinely
detailed (hatching, serrated leaves, bumpy clouds, wavy rays) while staying
readable in source form. Element order == drawing order on screen.
"""

from __future__ import annotations

import math
from typing import List

from .script_gen import Scene, VideoScript

INK = "#222"
SUN = "#d37c1b"
GREEN = "#278243"
BLUE = "#1a6fb0"
RED = "#c0392b"
GRAY = "#6e6e6e"
BROWN = "#7a4a22"


def _el(d: str, stroke: str = INK, width: int = 6, anim: str = "") -> str:
    a = f' data-anim="{anim}"' if anim else ""
    return f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width}"{a}/>'


def _wavy_circle(cx: float, cy: float, r: float, bumps: int = 12, amp: float = 4) -> str:
    """Closed, slightly lumpy circle as a polyline path."""
    pts = []
    for i in range(bumps * 6 + 1):
        a = 2 * math.pi * i / (bumps * 6)
        rr = r + amp * math.sin(a * bumps + cx * 0.13)
        pts.append(f"{cx + rr * math.cos(a):.0f},{cy + rr * math.sin(a):.0f}")
    return "M " + " L ".join(pts) + " Z"


def _hatch(x: float, y: float, w: float, h: float, n: int, slant: float = 0.55) -> str:
    """n parallel shading strokes inside a box; one path, pen lifts between."""
    parts = []
    for i in range(n):
        t = (i + 0.5) / n
        x0 = x + t * w
        parts.append(f"M {x0:.0f},{y:.0f} L {x0 - h * slant:.0f},{y + h:.0f}")
    return " ".join(parts)


def _cloud(cx: float, cy: float, s: float = 1.0) -> str:
    """Puffy cloud outline made of arcs."""
    b = [(-95, 12, 34), (-45, -26, 40), (18, -34, 42), (72, -8, 34), (96, 22, 26)]
    pts = []
    for i in range(121):
        a = math.pi * 2 * i / 120
        best = 0.0
        for bx, by, br in b:
            d = br + 6 - math.hypot(math.cos(a) * 110 - bx, math.sin(a) * 55 - by) * 0.55
            best = max(best, d)
        rr = 58 + best * 0.9 + 3 * math.sin(a * 9)
        pts.append(f"{cx + s * rr * math.cos(a) * 1.55:.0f},{cy + s * rr * math.sin(a) * 0.8:.0f}")
    return "M " + " L ".join(pts) + " Z"


def _rays(cx: float, cy: float, r0: float, r1: float, n: int, color: str,
          width: int = 5, phase: float = 0.0, anim: str = "") -> List[str]:
    parts = []
    for i in range(n):
        a = 2 * math.pi * i / n + phase
        x0, y0 = cx + r0 * math.cos(a), cy + r0 * math.sin(a)
        x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
        mx = (x0 + x1) / 2 + 9 * math.cos(a + math.pi / 2)
        my = (y0 + y1) / 2 + 9 * math.sin(a + math.pi / 2)
        parts.append(f"M {x0:.0f},{y0:.0f} Q {mx:.0f},{my:.0f} {x1:.0f},{y1:.0f}")
    # one path with pen lifts, so the rays animate as a single group
    return [_el(" ".join(parts), color, width, anim=anim)]


def _arrow(x0, y0, x1, y1, color, width=7, bend=30) -> List[str]:
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    mx, my = (x0 + x1) / 2 + nx * bend, (y0 + y1) / 2 + ny * bend
    ux, uy = (x1 - mx) / max(1, math.hypot(x1 - mx, y1 - my)), (y1 - my) / max(1, math.hypot(x1 - mx, y1 - my))
    h = 26
    h1 = (x1 - ux * h + nx * h * 0.6, y1 - uy * h + ny * h * 0.6)
    h2 = (x1 - ux * h - nx * h * 0.6, y1 - uy * h - ny * h * 0.6)
    return [
        _el(f"M {x0:.0f},{y0:.0f} Q {mx:.0f},{my:.0f} {x1:.0f},{y1:.0f}", color, width),
        _el(f"M {x1:.0f},{y1:.0f} L {h1[0]:.0f},{h1[1]:.0f} M {x1:.0f},{y1:.0f} L {h2[0]:.0f},{h2[1]:.0f}",
            color, width),
    ]


def _bird(cx, cy, s=1.0) -> str:
    return _el(f"M {cx - 22 * s:.0f},{cy:.0f} Q {cx - 10 * s:.0f},{cy - 14 * s:.0f} {cx:.0f},{cy:.0f} "
               f"Q {cx + 10 * s:.0f},{cy - 14 * s:.0f} {cx + 22 * s:.0f},{cy:.0f}", INK, 4)


def _grass(cx, cy) -> str:
    return _el(f"M {cx - 14:.0f},{cy:.0f} L {cx - 8:.0f},{cy - 18:.0f} "
               f"M {cx - 2:.0f},{cy:.0f} L {cx:.0f},{cy - 24:.0f} "
               f"M {cx + 10:.0f},{cy:.0f} L {cx + 14:.0f},{cy - 16:.0f}", GREEN, 4)


def _sparkle(cx, cy, r=14, color=SUN) -> str:
    return _el(f"M {cx - r},{cy} L {cx + r},{cy} M {cx},{cy - r} L {cx},{cy + r}", color, 4)


def _serrated_leaf(cx: float, cy: float, length: float, width: float,
                   tilt_deg: float = 0.0) -> str:
    """Serrated leaf outline: base at the bottom, tip at the top."""
    a = math.radians(tilt_deg)
    ca, sa = math.cos(a), math.sin(a)

    def T(x, y):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)

    pts = []
    n = 46
    for side in (1, -1):
        rng = range(n + 1) if side == 1 else range(n, -1, -1)
        for i in rng:
            t = i / n
            y = length / 2 - t * length
            base_w = width * math.sin(math.pi * min(1, t * 1.06)) ** 0.8
            serr = 10 * (1 if i % 2 else -0.2) * math.sin(math.pi * t) ** 0.5
            x, yy = T(side * (base_w + serr), y)
            pts.append(f"{x:.0f},{yy:.0f}")
    return "M " + " L ".join(pts) + " Z"


def _leaf_veins(cx, cy, length, width, tilt_deg=0.0, n=6) -> List[str]:
    a = math.radians(tilt_deg)
    ca, sa = math.cos(a), math.sin(a)

    def T(x, y):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)

    out = []
    p0, p1 = T(0, length / 2), T(0, -length / 2)
    out.append(_el(f"M {p0[0]:.0f},{p0[1]:.0f} L {p1[0]:.0f},{p1[1]:.0f}", GREEN, 5))
    for i in range(1, n + 1):
        t = i / (n + 1)
        y = length / 2 - t * length
        w = width * math.sin(math.pi * min(1, t * 1.06)) ** 0.8 * 0.82
        for side in (1, -1):
            s0, s1, s2 = T(0, y), T(side * w * 0.6, y - w * 0.28), T(side * w, y - w * 0.5)
            out.append(_el(
                f"M {s0[0]:.0f},{s0[1]:.0f} Q {s1[0]:.0f},{s1[1]:.0f} {s2[0]:.0f},{s2[1]:.0f}",
                GREEN, 3))
    return out


# ---------------------------------------------------------------------------
# Scene 1 — landscape: sun, clouds, birds, hills, tree, sprout
# ---------------------------------------------------------------------------

def _scene1() -> str:
    e: List[str] = []
    # sun with face, rays, inner shading
    e.append(_el(_wavy_circle(240, 185, 85, bumps=10, amp=3.5), SUN, 8))
    e.append(_el("M 206,163 C 212,155 222,155 228,163", INK, 5))
    e.append(_el("M 252,163 C 258,155 268,155 274,163", INK, 5))
    e.append(_el("M 204,205 C 222,228 258,228 276,203", INK, 5))
    e += _rays(240, 185, 103, 148, 10, SUN, 5, phase=0.31, anim="spin:16")
    # clouds drift, birds glide
    e.append(_el(_cloud(660, 120, 0.9), GRAY, 6, anim="drift:9,0"))
    e.append(_el(_hatch(590, 148, 130, 18, 5), GRAY, 3, anim="drift:9,0"))
    e.append(_el(_cloud(1130, 95, 0.55), GRAY, 6, anim="drift:-6,0"))
    e.append(_el(_hatch(1090, 112, 76, 12, 4), GRAY, 3, anim="drift:-6,0"))
    e.append(_el(f"M 768,84 Q 780,70 790,84 Q 800,70 812,84 "
                 f"M 834,60 Q 843,49 852,60 Q 861,49 870,60 "
                 f"M 894,100 Q 901,91 908,100 Q 915,91 922,100",
                 INK, 4, anim="drift:16,-3"))
    # hills and ground
    e.append(_el("M 84,520 C 250,438 420,440 560,502 C 612,525 676,525 728,502 "
                 "C 872,440 1040,444 1196,512", INK, 7))
    e.append(_el("M 84,598 C 400,566 900,572 1196,596", INK, 6))
    e.append(_el(_hatch(150, 540, 180, 40, 6), GRAY, 3))
    e.append(_el(_hatch(800, 535, 160, 40, 5), GRAY, 3))
    # tree: trunk, bark, foliage, shading, apples
    e.append(_el("M 985,592 C 990,540 982,480 1002,438 M 1042,592 C 1036,540 1046,485 1022,440 "
                 "M 1002,438 C 992,410 980,395 962,382 M 1022,440 C 1036,408 1052,394 1072,380", BROWN, 7))
    e.append(_el("M 998,560 C 1004,548 1004,536 1000,524 M 1024,555 C 1018,540 1020,528 1026,514", BROWN, 3))
    e.append(_el(_wavy_circle(1016, 315, 118, bumps=14, amp=9), GREEN, 7))
    e.append(_el(_hatch(920, 350, 80, 46, 5), GREEN, 3))
    e += [_el(_wavy_circle(x, y, 13, bumps=6, amp=1.2), RED, 5)
          for x, y in ((966, 300), (1060, 282), (1022, 360))]
    # sprout in a soil mound, light beams reaching it
    e.append(_el("M 380,586 C 402,566 458,566 480,586", BROWN, 6))
    # stem + leaves as one group so the sprout sways about its base
    e.append(_el("M 430,574 C 428,548 430,522 429,500 "
                 "M 429,530 C 400,526 386,506 380,482 C 408,486 424,502 429,530 Z "
                 "M 429,512 C 458,508 472,488 478,464 C 450,468 434,484 429,512 Z",
                 GREEN, 6, anim="sway:7"))
    e.append(_el(_hatch(396, 578, 70, 14, 4), BROWN, 3))
    e += _arrow(330, 262, 408, 440, SUN, 5, bend=40)
    # grass tufts
    e += [_grass(320, 590), _grass(580, 585), _grass(770, 588), _grass(1140, 590)]
    return _svg(e)


# ---------------------------------------------------------------------------
# Scene 2 — serrated leaf with veins + sun / CO2 cloud / rain inputs
# ---------------------------------------------------------------------------

def _scene2() -> str:
    e: List[str] = []
    # central leaf with stem and roots
    e.append(_el(_serrated_leaf(645, 360, 360, 165), GREEN, 7))
    e += _leaf_veins(645, 360, 360, 165)
    e.append(_el("M 645,540 C 643,562 645,578 644,592", GREEN, 6))
    e.append(_el("M 644,592 C 620,596 600,590 585,596 M 644,592 C 668,598 688,592 704,598 "
                 "M 644,592 C 640,596 636,596 632,599", BROWN, 4))
    # ground line + soil shading
    e.append(_el("M 90,588 C 320,578 560,582 700,586 C 880,590 1050,584 1190,588", INK, 5))
    e.append(_el(_hatch(520, 592, 260, 8, 8), BROWN, 3))
    # sun + its arrow
    e.append(_el(_wavy_circle(195, 150, 62, bumps=9, amp=3), SUN, 7))
    e += _rays(195, 150, 76, 108, 8, SUN, 4, phase=0.2, anim="spin:14")
    e += _arrow(285, 225, 520, 300, SUN, 6, bend=36)
    # CO2 cloud + bobbing molecules + arrow
    e.append(_el(_cloud(1075, 150, 0.78), GRAY, 6, anim="float:6"))
    e += [_el(_wavy_circle(x, y, r, bumps=5, amp=1), GRAY, 4, anim=f"float:{a}")
          for x, y, r, a in ((995, 235, 14, 8), (958, 274, 10, 11), (930, 306, 7, 9))]
    e += _arrow(990, 255, 790, 330, GRAY, 6, bend=-32)
    # rain cloud + falling rain + arrow into the roots
    e.append(_el(_cloud(255, 445, 0.62), BLUE, 6))
    e.append(_el(" ".join(
        f"M {x},{y} C {x - 4},{y + 14} {x - 8},{y + 24} {x - 10},{y + 36}"
        for x, y in ((205, 495), (248, 505), (292, 498), (270, 480))),
        BLUE, 4, anim="drift:-14,52,64"))
    e += _arrow(330, 520, 560, 575, BLUE, 6, bend=24)
    return _svg(e)


# ---------------------------------------------------------------------------
# Scene 3 — leaf factory: sugar + oxygen + breathing stick figure
# ---------------------------------------------------------------------------

def _scene3() -> str:
    e: List[str] = []
    # leaf tilted like a little factory, with chimney
    e.append(_el(_serrated_leaf(330, 400, 300, 140, tilt_deg=-14), GREEN, 7))
    e += _leaf_veins(330, 400, 300, 140, tilt_deg=-14, n=5)
    e.append(_el("M 350,262 L 360,215 L 402,224 L 396,252", BROWN, 6))
    # oxygen bubbles rising from the chimney
    e += [_el(_wavy_circle(x, y, r, bumps=5, amp=1), BLUE, 5, anim=a)
          for x, y, r, a in ((392, 185, 18, "drift:8,-26,95"),
                             (430, 138, 14, "drift:10,-30,110"),
                             (474, 102, 11, "drift:12,-24,90"),
                             (524, 76, 8, "float:9"))]
    # arrow to the sugar crystal
    e += _arrow(478, 400, 640, 396, INK, 7, bend=-18)
    # sugar: hexagon with inner facets and sparkles
    hexpts = [(760 + 74 * math.cos(math.radians(60 * i - 30)),
               392 + 74 * math.sin(math.radians(60 * i - 30))) for i in range(6)]
    e.append(_el("M " + " L ".join(f"{x:.0f},{y:.0f}" for x, y in hexpts) + " Z", RED, 7))
    e.append(_el(" ".join(f"M 760,392 L {x:.0f},{y:.0f}" for x, y in hexpts[::2]), RED, 4))
    e.append(_el("M 676,302 L 700,302 M 688,290 L 688,314", SUN, 4, anim="pulse:0.35"))
    e.append(_el("M 827,300 L 857,300 M 842,285 L 842,315", SUN, 4, anim="pulse:0.30"))
    e.append(_el("M 841,470 L 863,470 M 852,459 L 852,481", SUN, 4, anim="pulse:0.40"))
    # energy bolt above the sugar
    e.append(_el("M 780,232 L 756,282 L 778,282 L 748,338", SUN, 6, anim="pulse:0.10"))
    # ground + grass first, then someone strolls in to enjoy the oxygen
    e.append(_el("M 120,565 C 400,552 800,556 1170,562", INK, 5))
    e += [_grass(240, 560), _grass(700, 558), _grass(1150, 560)]
    e.append('<walker x="1120" y="558" to-x="920" scale="0.95" stroke="#222"/>')
    # breath swirls drifting near the walker's path
    e.append(_el("M 800,190 C 828,180 848,186 862,200 C 848,208 832,206 822,198", BLUE, 4, anim="float:8"))
    e.append(_el("M 812,238 C 838,230 856,234 868,246", BLUE, 4, anim="float:11"))
    return _svg(e)


def _svg(elements: List[str]) -> str:
    body = "\n  ".join(elements)
    return ('<svg viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg">\n  '
            f"{body}\n</svg>")


DEMO_SCRIPT = VideoScript(
    title="How Photosynthesis Works",
    scenes=[
        Scene(
            label="Powered by the Sun",
            narration=(
                "Every plant on Earth is powered by the same giant engine: the sun. "
                "Sunlight streams down carrying the energy that starts everything."
            ),
            visual_description=(
                "A smiling sun with wavy rays over a landscape: shaded clouds, birds, "
                "rolling hills, an apple tree, and a small sprout catching a sunbeam."
            ),
        ),
        Scene(
            label="Three Ingredients",
            narration=(
                "A leaf collects three simple ingredients. It soaks up sunlight from "
                "above, pulls in carbon dioxide from the air, and drinks water "
                "brought up from the roots."
            ),
            visual_description=(
                "A large serrated leaf with detailed veins and roots; a sun, a CO2 "
                "cloud with drifting molecules, and a rain cloud each sending an "
                "arrow into the leaf."
            ),
        ),
        Scene(
            label="Sugar and Oxygen",
            narration=(
                "Inside the leaf, those ingredients are transformed into sugar the "
                "plant uses as food, and oxygen is released into the air. That "
                "oxygen is what you are breathing right now."
            ),
            visual_description=(
                "A leaf-factory with a chimney releasing oxygen bubbles, an arrow to "
                "a faceted sugar crystal with sparkles and an energy bolt, and a "
                "happy stick figure breathing in the oxygen."
            ),
        ),
    ],
)

DEMO_SVGS = [_scene1(), _scene2(), _scene3()]
