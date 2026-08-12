"""Canned script + drawings for offline testing (no API key required).

The demo illustrations are built procedurally so they can be genuinely
detailed (hatching, serrated leaves, fences, flowers, molecules) while
staying readable in source form. Element order == drawing order on screen.
"""

from __future__ import annotations

import math
from typing import List

from .script_gen import Scene, VideoScript

# refined, slightly muted palette — reads as deliberate design, not defaults
INK = "#28303f"     # deep ink navy
SUN = "#d9902b"     # warm ochre
GREEN = "#2f7d4f"   # sage-leaning green
BLUE = "#39729e"    # slate blue
RED = "#b8453c"     # terracotta
GRAY = "#8b909a"    # cool gray
BROWN = "#7b5233"   # walnut


def _el(d: str, stroke: str = INK, width: int = 6, anim: str = "",
        fill: str = "") -> str:
    a = f' data-anim="{anim}"' if anim else ""
    f = f' data-fill="{fill}"' if fill else ""
    return f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width}"{a}{f}/>'


def _wavy_circle(cx: float, cy: float, r: float, bumps: int = 12, amp: float = 4) -> str:
    pts = []
    for i in range(bumps * 6 + 1):
        a = 2 * math.pi * i / (bumps * 6)
        rr = r + amp * math.sin(a * bumps + cx * 0.13)
        pts.append(f"{cx + rr * math.cos(a):.0f},{cy + rr * math.sin(a):.0f}")
    return "M " + " L ".join(pts) + " Z"


def _lobed(cx: float, cy: float, rx: float, ry: float, lobes: int = 7,
           depth: float = 0.16) -> str:
    """Scalloped foliage blob — reads as drawn leaf masses."""
    pts = []
    for i in range(lobes * 10 + 1):
        a = 2 * math.pi * i / (lobes * 10)
        k = 1 + depth * abs(math.sin(a * lobes / 2 + cx * 0.07))
        pts.append(f"{cx + rx * k * math.cos(a):.0f},{cy + ry * k * math.sin(a):.0f}")
    return "M " + " L ".join(pts) + " Z"


def _hatch(x: float, y: float, w: float, h: float, n: int, slant: float = 0.55) -> str:
    parts = []
    for i in range(n):
        t = (i + 0.5) / n
        x0 = x + t * w
        parts.append(f"M {x0:.0f},{y:.0f} L {x0 - h * slant:.0f},{y + h:.0f}")
    return " ".join(parts)


def _shadow(cx: float, y: float, w: float, n: int = 5) -> str:
    """Short horizontal contact-shadow dashes beneath an object."""
    parts = []
    for i in range(n):
        t = (i + 0.5) / n
        x0 = cx - w / 2 + t * w
        L = 14 * (1 - abs(2 * t - 1) * 0.55)
        parts.append(f"M {x0 - L / 2:.0f},{y:.0f} L {x0 + L / 2:.0f},{y:.0f}")
    return " ".join(parts)


def _cloud(cx: float, cy: float, s: float = 1.0) -> str:
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
        rr1 = r1 if i % 2 == 0 else r0 + (r1 - r0) * 0.55   # long/short alternation
        x0, y0 = cx + r0 * math.cos(a), cy + r0 * math.sin(a)
        x1, y1 = cx + rr1 * math.cos(a), cy + rr1 * math.sin(a)
        mx = (x0 + x1) / 2 + 8 * math.cos(a + math.pi / 2)
        my = (y0 + y1) / 2 + 8 * math.sin(a + math.pi / 2)
        parts.append(f"M {x0:.0f},{y0:.0f} Q {mx:.0f},{my:.0f} {x1:.0f},{y1:.0f}")
    return [_el(" ".join(parts), color, width, anim=anim)]


def _arrow(x0, y0, x1, y1, color, width=7, bend=30) -> List[str]:
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    mx, my = (x0 + x1) / 2 + nx * bend, (y0 + y1) / 2 + ny * bend
    hl = max(1, math.hypot(x1 - mx, y1 - my))
    ux, uy = (x1 - mx) / hl, (y1 - my) / hl
    h = 24
    h1 = (x1 - ux * h + nx * h * 0.55, y1 - uy * h + ny * h * 0.55)
    h2 = (x1 - ux * h - nx * h * 0.55, y1 - uy * h - ny * h * 0.55)
    return [
        _el(f"M {x0:.0f},{y0:.0f} Q {mx:.0f},{my:.0f} {x1:.0f},{y1:.0f}", color, width),
        _el(f"M {x1:.0f},{y1:.0f} L {h1[0]:.0f},{h1[1]:.0f} M {x1:.0f},{y1:.0f} L {h2[0]:.0f},{h2[1]:.0f}",
            color, width),
    ]


def _bird(cx, cy, s=1.0) -> str:
    return (f"M {cx - 22 * s:.0f},{cy:.0f} Q {cx - 10 * s:.0f},{cy - 14 * s:.0f} {cx:.0f},{cy:.0f} "
            f"Q {cx + 10 * s:.0f},{cy - 14 * s:.0f} {cx + 22 * s:.0f},{cy:.0f}")


def _grass(cx, cy) -> str:
    return _el(f"M {cx - 14:.0f},{cy:.0f} L {cx - 8:.0f},{cy - 18:.0f} "
               f"M {cx - 2:.0f},{cy:.0f} L {cx:.0f},{cy - 24:.0f} "
               f"M {cx + 10:.0f},{cy:.0f} L {cx + 14:.0f},{cy - 16:.0f}", GREEN, 4)


def _flower(cx: float, cy: float, s: float = 1.0, color: str = RED) -> List[str]:
    petals = []
    for i in range(5):
        a = 2 * math.pi * i / 5 - math.pi / 2
        px, py = cx + 13 * s * math.cos(a), cy + 13 * s * math.sin(a)
        n1 = a - 0.65
        n2 = a + 0.65
        petals.append(
            f"M {cx + 4 * s * math.cos(a):.0f},{cy + 4 * s * math.sin(a):.0f} "
            f"Q {cx + 17 * s * math.cos(n1):.0f},{cy + 17 * s * math.sin(n1):.0f} {px:.0f},{py:.0f} "
            f"Q {cx + 17 * s * math.cos(n2):.0f},{cy + 17 * s * math.sin(n2):.0f} "
            f"{cx + 4 * s * math.cos(a):.0f},{cy + 4 * s * math.sin(a):.0f}")
    return [
        _el(f"M {cx:.0f},{cy + 34 * s:.0f} C {cx - 2 * s:.0f},{cy + 22 * s:.0f} "
            f"{cx + 2 * s:.0f},{cy + 12 * s:.0f} {cx:.0f},{cy + 5 * s:.0f}", GREEN, 3),
        _el(" ".join(petals), color, 3, anim="sway:5"),
        _el(_wavy_circle(cx, cy, 4.5 * s, bumps=5, amp=0.6), SUN, 3),
    ]


def _serrated_leaf(cx: float, cy: float, length: float, width: float,
                   tilt_deg: float = 0.0) -> str:
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


def _leaf_shading(cx, cy, length, width, tilt_deg=0.0, n=7) -> str:
    """Fine hatch lines following the shaded (left) side of the leaf."""
    a = math.radians(tilt_deg)
    ca, sa = math.cos(a), math.sin(a)

    def T(x, y):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)

    parts = []
    for i in range(n):
        t = 0.28 + 0.5 * i / n
        y = length / 2 - t * length
        w = width * math.sin(math.pi * min(1, t * 1.06)) ** 0.8
        a0, a1 = T(-w * 0.92, y + 5), T(-w * 0.64, y - 9)
        parts.append(f"M {a0[0]:.0f},{a0[1]:.0f} L {a1[0]:.0f},{a1[1]:.0f}")
    return " ".join(parts)


def _molecule(cx: float, cy: float, s: float = 1.0) -> str:
    """O=C=O — reads as a CO2 molecule without any text."""
    parts = [
        _wavy_circle(cx - 34 * s, cy, 13 * s, bumps=5, amp=0.8),
        _wavy_circle(cx, cy, 17 * s, bumps=5, amp=0.9),
        _wavy_circle(cx + 34 * s, cy, 13 * s, bumps=5, amp=0.8),
        f"M {cx - 21 * s:.0f},{cy - 4 * s:.0f} L {cx - 15 * s:.0f},{cy - 4 * s:.0f} "
        f"M {cx - 21 * s:.0f},{cy + 4 * s:.0f} L {cx - 15 * s:.0f},{cy + 4 * s:.0f} "
        f"M {cx + 15 * s:.0f},{cy - 4 * s:.0f} L {cx + 21 * s:.0f},{cy - 4 * s:.0f} "
        f"M {cx + 15 * s:.0f},{cy + 4 * s:.0f} L {cx + 21 * s:.0f},{cy + 4 * s:.0f}",
    ]
    return " ".join(parts)


def _svg(elements: List[str]) -> str:
    body = "\n  ".join(elements)
    return ('<svg viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg">\n  '
            f"{body}\n</svg>")


# ---------------------------------------------------------------------------
# Scene 1 — landscape: sun, clouds, hills, fence, path, tree, sprout, flowers
# ---------------------------------------------------------------------------

def _scene1() -> str:
    e: List[str] = []
    # sun: double ring, calm face, alternating rays
    e.append(_el(_wavy_circle(225, 172, 84, bumps=10, amp=3), SUN, 8, fill=SUN))
    e.append(_el(_wavy_circle(225, 172, 66, bumps=9, amp=2), SUN, 3))
    e.append(_el("M 192,152 C 198,144 208,144 214,152", INK, 5))
    e.append(_el("M 238,152 C 244,144 254,144 260,152", INK, 5))
    e.append(_el("M 194,196 C 210,216 242,216 258,194", INK, 5))
    e += _rays(225, 172, 100, 150, 12, SUN, 4, phase=0.26, anim="spin:18")
    # clouds drift with their shading; birds glide
    e.append(_el(_cloud(680, 105, 0.85), GRAY, 5, anim="drift:9,0"))
    e.append(_el(_hatch(615, 132, 120, 16, 5), GRAY, 3, anim="drift:9,0"))
    e.append(_el(_cloud(1120, 85, 0.55), GRAY, 5, anim="drift:-6,0"))
    e.append(_el(_hatch(1082, 102, 72, 12, 4), GRAY, 3, anim="drift:-6,0"))
    e.append(_el(_bird(795, 82) + " " + _bird(858, 58, 0.8) + " " + _bird(912, 98, 0.6),
                 INK, 4, anim="drift:14,-3"))
    # hills, winding path, ground
    e.append(_el("M 84,516 C 250,436 420,438 560,498 C 612,521 676,521 728,498 "
                 "C 872,436 1040,440 1196,508", INK, 7))
    e.append(_el("M 84,598 C 400,566 900,572 1196,596", INK, 6))
    e.append(_el("M 596,596 C 622,558 640,532 652,512 M 676,596 C 688,560 698,534 706,514",
                 BROWN, 4))
    e.append(_el(_hatch(760, 522, 150, 34, 6), GRAY, 3))
    # fence along the left slope
    e.append(_el("M 120,540 L 122,586 M 190,534 L 192,582 M 260,532 L 262,580 M 330,536 L 332,584",
                 BROWN, 5))
    e.append(_el("M 112,552 C 186,544 260,542 340,548 M 112,570 C 186,562 260,560 340,566",
                 BROWN, 4))
    # apple tree: trunk with root flare and bark, lobed canopy, apples
    e.append(_el("M 980,594 C 986,544 978,486 1000,440 M 1046,594 C 1040,546 1050,490 1026,442 "
                 "M 1000,440 C 990,414 976,398 958,386 M 1026,442 C 1040,410 1056,396 1076,382 "
                 "M 980,594 C 968,600 958,602 946,604 M 1046,594 C 1058,600 1068,602 1080,604",
                 BROWN, 7))
    e.append(_el("M 996,560 C 1002,546 1002,534 998,522 M 1022,554 C 1016,540 1018,526 1024,514 "
                 "M 1008,500 C 1012,488 1010,478 1006,468", BROWN, 3))
    e.append(_el(_lobed(1014, 300, 118, 88, lobes=8, depth=0.18), GREEN, 7, fill=GREEN))
    e.append(_el(_lobed(942, 352, 52, 38, lobes=5, depth=0.2), GREEN, 4))
    e.append(_el(_lobed(1092, 348, 48, 36, lobes=5, depth=0.2), GREEN, 4))
    e.append(_el(_hatch(920, 342, 78, 42, 6), GREEN, 3))
    e += [_el(_wavy_circle(x, y, 12, bumps=6, amp=1.1), RED, 4, fill=RED)
          for x, y in ((968, 292), (1058, 272), (1022, 350))]
    e.append(_el(_shadow(1013, 610, 150, 6), GRAY, 3))
    # sprout in a soil mound, swaying, lit by a sunbeam
    e.append(_el("M 380,586 C 402,566 458,566 480,586", BROWN, 6))
    e.append(_el("M 430,574 C 428,548 430,522 429,500 "
                 "M 429,530 C 400,526 386,506 380,482 C 408,486 424,502 429,530 Z "
                 "M 429,512 C 458,508 472,488 478,464 C 450,468 434,484 429,512 Z",
                 GREEN, 6, anim="sway:7"))
    e.append(_el(_hatch(398, 578, 66, 13, 4), BROWN, 3))
    e.append(_el(_shadow(430, 598, 90, 4), GRAY, 3))
    e += _arrow(322, 250, 408, 442, SUN, 5, bend=38)
    # flowers and grass dress the foreground
    e += _flower(552, 552, 1.35, RED)
    e += _flower(856, 550, 1.15, BLUE)
    e += [_grass(300, 588), _grass(640, 590), _grass(944, 586), _grass(1150, 590)]
    return _svg(e)


# ---------------------------------------------------------------------------
# Scene 2 — serrated leaf with shading + sun / CO2 molecule / rain inputs
# ---------------------------------------------------------------------------

def _scene2() -> str:
    e: List[str] = []
    # central leaf: outline, veins, interior shading, dew drop
    e.append(_el(_serrated_leaf(645, 355, 370, 168), GREEN, 7, fill=GREEN))
    e += _leaf_veins(645, 355, 370, 168)
    e.append(_el(_leaf_shading(645, 355, 370, 168, n=8), GREEN, 3))
    e.append(_el("M 728,300 C 738,316 742,330 734,340 C 722,346 710,338 710,324 "
                 "C 712,314 720,306 728,300 Z M 722,318 C 720,324 722,330 726,332",
                 BLUE, 3))
    e.append(_el("M 645,540 C 643,562 645,578 644,592", GREEN, 6))
    e.append(_el("M 644,592 C 618,598 596,592 578,600 M 644,592 C 670,600 692,594 710,602 "
                 "M 644,592 C 636,600 630,606 626,612 M 610,596 C 600,602 594,608 590,614",
                 BROWN, 4))
    # ground line + soil shading + contact shadow
    e.append(_el("M 90,588 C 320,578 560,582 700,586 C 880,590 1050,584 1190,588", INK, 5))
    e.append(_el(_hatch(520, 592, 260, 9, 8), BROWN, 3))
    # sun + its arrow
    e.append(_el(_wavy_circle(192, 145, 60, bumps=9, amp=2.6), SUN, 7, fill=SUN))
    e.append(_el(_wavy_circle(192, 145, 46, bumps=8, amp=1.8), SUN, 3))
    e += _rays(192, 145, 74, 112, 10, SUN, 4, phase=0.2, anim="spin:15")
    e += _arrow(282, 222, 516, 298, SUN, 6, bend=36)
    # CO2: a real O=C=O molecule bobbing out of a cloud
    e.append(_el(_cloud(1078, 140, 0.75), GRAY, 5, anim="float:6"))
    e.append(_el(_molecule(990, 248, 1.0), GRAY, 4, anim="float:9"))
    e.append(_el(_molecule(918, 312, 0.7), GRAY, 3, anim="float:12"))
    e += _arrow(980, 272, 792, 336, GRAY, 6, bend=-30)
    # rain cloud, falling rain, puddle with ripples, arrow to the roots
    e.append(_el(_cloud(252, 442, 0.6), BLUE, 5))
    e.append(_el(" ".join(
        f"M {x},{y} C {x - 4},{y + 14} {x - 8},{y + 24} {x - 10},{y + 36}"
        for x, y in ((202, 492), (246, 502), (290, 495), (268, 477))),
        BLUE, 4, anim="drift:-14,52,64"))
    e.append(_el("M 176,566 C 210,556 268,556 300,566 C 268,576 210,576 176,566 Z "
                 "M 210,566 C 226,562 252,562 268,566", BLUE, 3))
    e += _arrow(322, 520, 560, 576, BLUE, 6, bend=22)
    return _svg(e)


# ---------------------------------------------------------------------------
# Scene 3 — leaf factory: sugar crystal + oxygen + a walker breathing it in
# ---------------------------------------------------------------------------

def _scene3() -> str:
    e: List[str] = []
    # leaf-factory: tilted leaf, veins, porthole window, chimney
    e.append(_el(_serrated_leaf(330, 395, 310, 145, tilt_deg=-14), GREEN, 7, fill=GREEN))
    e += _leaf_veins(330, 395, 310, 145, tilt_deg=-14, n=5)
    e.append(_el(_leaf_shading(330, 395, 310, 145, tilt_deg=-14, n=6), GREEN, 3))
    e.append(_el(_wavy_circle(296, 372, 34, bumps=7, amp=1.4), INK, 4))
    e.append(_el("M 262,372 L 330,372 M 296,338 L 296,406", INK, 3))
    e.append(_el("M 350,262 L 360,212 L 404,221 L 396,252", BROWN, 6))
    e.append(_el("M 356,236 L 398,244", BROWN, 3))
    # oxygen bubbles rising from the chimney
    e += [_el(_wavy_circle(x, y, r, bumps=5, amp=1), BLUE, 5, anim=a)
          for x, y, r, a in ((392, 182, 18, "drift:8,-26,95"),
                             (432, 136, 14, "drift:10,-30,110"),
                             (476, 100, 11, "drift:12,-24,90"),
                             (526, 74, 8, "float:9"))]
    # arrow to the sugar crystal
    e += _arrow(482, 398, 640, 394, INK, 7, bend=-16)
    # sugar: faceted crystal with interior shading and pulsing sparkles
    hexpts = [(760 + 74 * math.cos(math.radians(60 * i - 30)),
               390 + 74 * math.sin(math.radians(60 * i - 30))) for i in range(6)]
    e.append(_el("M " + " L ".join(f"{x:.0f},{y:.0f}" for x, y in hexpts) + " Z", RED, 7, fill=RED))
    e.append(_el(" ".join(f"M 760,390 L {x:.0f},{y:.0f}" for x, y in hexpts[::2]), RED, 4))
    e.append(_el(_hatch(712, 404, 44, 38, 5), RED, 3))
    e.append(_el(_shadow(760, 486, 120, 5), GRAY, 3))
    e.append(_el("M 676,300 L 700,300 M 688,288 L 688,312", SUN, 4, anim="pulse:0.35"))
    e.append(_el("M 827,298 L 857,298 M 842,283 L 842,313", SUN, 4, anim="pulse:0.30"))
    e.append(_el("M 841,468 L 863,468 M 852,457 L 852,479", SUN, 4, anim="pulse:0.40"))
    # energy bolt above the sugar
    e.append(_el("M 780,230 L 756,280 L 778,280 L 748,336", SUN, 6, anim="pulse:0.10"))
    # ground, bush, grass — then someone strolls in to enjoy the oxygen
    e.append(_el("M 120,565 C 400,552 800,556 1170,562", INK, 5))
    e.append(_el(_lobed(172, 534, 54, 32, lobes=5, depth=0.2), GREEN, 4))
    e.append(_el(_hatch(146, 532, 46, 20, 4), GREEN, 3))
    e += [_grass(560, 558), _grass(700, 558), _grass(1050, 560)]
    e.append(_el(_shadow(330, 580, 170, 6), GRAY, 3))
    e.append('<walker x="1120" y="558" to-x="920" scale="0.95" stroke="#28303f"/>')
    # breath swirls drifting near the walker's path
    e.append(_el("M 800,190 C 828,180 848,186 862,200 C 848,208 832,206 822,198", BLUE, 4, anim="float:8"))
    e.append(_el("M 812,238 C 838,230 856,234 868,246", BLUE, 4, anim="float:11"))
    return _svg(e)


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
                "A smiling sun with turning rays over a countryside: drifting shaded "
                "clouds, gliding birds, hills with a winding path and fence, an "
                "apple tree, flowers, and a swaying sprout caught in a sunbeam."
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
                "A large serrated leaf with veins, shading and a dew drop; a sun, "
                "CO2 molecules bobbing out of a cloud, and rain falling into a "
                "puddle, each sending an arrow into the leaf."
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
                "A leaf-factory with a porthole window and chimney releasing oxygen "
                "bubbles, an arrow to a shaded sugar crystal with sparkles and an "
                "energy bolt, and a figure strolling in to breathe the oxygen."
            ),
        ),
    ],
)

DEMO_SVGS = [_scene1(), _scene2(), _scene3()]
