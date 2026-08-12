"""Prop library for story mode: named scene objects rendered as SVG snippets.

Each prop kind maps to a hand-drawn-style SVG fragment (reusing the demo
drawing helpers) positioned at (x, y) where y is the prop's BASE (ground
contact) unless noted. A ``motion`` name maps to a data-anim string.
"""

from __future__ import annotations

import math
from typing import List, Optional

from .demo_content import (
    BLUE, BROWN, GRAY, GREEN, INK, RED, SUN,
    _cloud, _el, _flower, _grass, _hatch, _lobed, _rays, _shadow, _wavy_circle,
)

MOTIONS = {
    "none": "",
    "drift_left": "drift:-14,0",
    "drift_right": "drift:14,0",
    "rise": "drift:4,-30,140",
    "fall_loop": "drift:-10,55,70",
    "bounce": "bounce:52,0.75",
    "spin": "spin:5",
    "sway": "sway:6",
    "float": "float:9",
    "pulse": "pulse:0.10",
}


def _wrap_anim(parts: List[str], anim: str) -> List[str]:
    """Tag every element of a prop with the same motion (last tag wins over
    any built-in per-element animation)."""
    return [p.replace("/>", f' data-anim="{anim}"/>') for p in parts]


def prop_svg(kind: str, x: float, y: float, scale: float = 1.0,
             motion: str = "none") -> List[str]:
    s = max(0.2, scale)
    anim = MOTIONS.get(motion, "")
    k = kind.lower().strip()
    fn = _PROPS.get(k)
    if fn is None:
        return []
    parts = fn(x, y, s)
    return _wrap_anim(parts, anim) if anim else parts


# --- sky ------------------------------------------------------------------

def _p_sun(x, y, s):
    r = 62 * s
    out = [
        _el(_wavy_circle(x, y, r, bumps=9, amp=2.6), SUN, 7, fill=SUN),
        _el(_wavy_circle(x, y, r * 0.76, bumps=8, amp=1.8), SUN, 3),
        _el(f"M {x-0.3*r:.0f},{y-0.15*r:.0f} C {x-0.2*r:.0f},{y-0.28*r:.0f} "
            f"{x-0.06*r:.0f},{y-0.28*r:.0f} {x+0.02*r:.0f},{y-0.15*r:.0f} "
            f"M {x+0.3*r:.0f},{y-0.15*r:.0f} C {x+0.2*r:.0f},{y-0.28*r:.0f} "
            f"{x+0.06*r:.0f},{y-0.28*r:.0f} {x-0.02*r:.0f},{y-0.15*r:.0f}".replace("+-", "-"),
            INK, 4),
        _el(f"M {x-0.35*r:.0f},{y+0.25*r:.0f} C {x-0.1*r:.0f},{y+0.5*r:.0f} "
            f"{x+0.1*r:.0f},{y+0.5*r:.0f} {x+0.35*r:.0f},{y+0.22*r:.0f}", INK, 4),
    ]
    out += _rays(x, y, r * 1.22, r * 1.8, 10, SUN, 4, phase=0.3, anim="spin:16")
    return out


def _p_moon(x, y, s):
    r = 52 * s
    return [
        _el(_wavy_circle(x, y, r, bumps=8, amp=2), GRAY, 6),
        _el(_wavy_circle(x - r * 0.28, y - r * 0.2, r * 0.16, bumps=5, amp=0.8), GRAY, 3),
        _el(_wavy_circle(x + r * 0.25, y + r * 0.25, r * 0.11, bumps=5, amp=0.6), GRAY, 3),
    ]


def _p_star(x, y, s):
    r = 16 * s
    pts = []
    for i in range(11):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(f"{x + rr * math.cos(a):.0f},{y + rr * math.sin(a):.0f}")
    return [_el("M " + " L ".join(pts) + " Z", SUN, 4)]


def _p_cloud(x, y, s):
    return [
        _el(_cloud(x, y, 0.8 * s), GRAY, 5),
        _el(_hatch(x - 60 * s, y + 26 * s, 110 * s, 14 * s, 5), GRAY, 3),
    ]


def _p_rain(x, y, s):
    drops = " ".join(
        f"M {x + dx * s},{y + dy * s} C {x + dx * s - 4},{y + dy * s + 14} "
        f"{x + dx * s - 8},{y + dy * s + 24} {x + dx * s - 10},{y + dy * s + 36}"
        for dx, dy in ((-50, 45), (-6, 55), (38, 47), (16, 30)))
    return [
        _el(_cloud(x, y, 0.6 * s), BLUE, 5),
        _el(drops, BLUE, 4, anim="drift:-12,50,62"),
    ]


# --- landscape ------------------------------------------------------------

def _p_tree(x, y, s):
    return [
        _el(f"M {x-26*s:.0f},{y:.0f} C {x-22*s:.0f},{y-46*s:.0f} {x-28*s:.0f},{y-96*s:.0f} {x-10*s:.0f},{y-134*s:.0f} "
            f"M {x+26*s:.0f},{y:.0f} C {x+22*s:.0f},{y-48*s:.0f} {x+28*s:.0f},{y-92*s:.0f} {x+10*s:.0f},{y-132*s:.0f}",
            BROWN, 6),
        _el(_lobed(x, y - 188 * s, 92 * s, 68 * s, lobes=7, depth=0.18), GREEN, 6, fill=GREEN),
        _el(_hatch(x - 74 * s, y - 158 * s, 60 * s, 32 * s, 5), GREEN, 3),
    ]


def _p_bush(x, y, s):
    return [
        _el(_lobed(x, y - 26 * s, 52 * s, 30 * s, lobes=5, depth=0.2), GREEN, 4, fill=GREEN),
        _el(_hatch(x - 26 * s, y - 28 * s, 44 * s, 20 * s, 4), GREEN, 3),
    ]


def _p_mountain(x, y, s):
    return [
        _el(f"M {x-190*s:.0f},{y:.0f} C {x-120*s:.0f},{y-140*s:.0f} {x-70*s:.0f},{y-190*s:.0f} {x-30*s:.0f},{y-210*s:.0f} "
            f"C {x+30*s:.0f},{y-180*s:.0f} {x+110*s:.0f},{y-80*s:.0f} {x+180*s:.0f},{y:.0f}", INK, 6),
        _el(f"M {x-64*s:.0f},{y-168*s:.0f} L {x-44*s:.0f},{y-182*s:.0f} L {x-26*s:.0f},{y-168*s:.0f} "
            f"L {x-8*s:.0f},{y-186*s:.0f} L {x+12*s:.0f},{y-168*s:.0f}", GRAY, 4),
    ]


def _p_flower(x, y, s):
    return _flower(x, y - 34 * s, s, RED)


def _p_grass(x, y, s):
    return [_grass(x, y)]


def _p_rock(x, y, s):
    return [
        _el(_lobed(x, y - 16 * s, 34 * s, 18 * s, lobes=4, depth=0.12), GRAY, 5),
        _el(_hatch(x - 18 * s, y - 20 * s, 30 * s, 14 * s, 3), GRAY, 3),
    ]


# --- built ---------------------------------------------------------------

def _p_house(x, y, s):
    w, h = 150 * s, 110 * s
    return [
        _el(f"M {x-w/2:.0f},{y:.0f} L {x-w/2:.0f},{y-h:.0f} L {x+w/2:.0f},{y-h:.0f} L {x+w/2:.0f},{y:.0f} Z", INK, 6, fill="#cbb98f"),
        _el(f"M {x-w/2-16*s:.0f},{y-h:.0f} L {x:.0f},{y-h-64*s:.0f} L {x+w/2+16*s:.0f},{y-h:.0f} Z", RED, 6, fill=RED),
        _el(f"M {x-18*s:.0f},{y:.0f} L {x-18*s:.0f},{y-56*s:.0f} C {x-18*s:.0f},{y-64*s:.0f} "
            f"{x+18*s:.0f},{y-64*s:.0f} {x+18*s:.0f},{y-56*s:.0f} L {x+18*s:.0f},{y:.0f}", BROWN, 5),
        _el(_wavy_circle(x - w * 0.28, y - h * 0.62, 17 * s, bumps=6, amp=1) +
            f" M {x-w*0.28-17*s:.0f},{y-h*0.62:.0f} L {x-w*0.28+17*s:.0f},{y-h*0.62:.0f}"
            f" M {x-w*0.28:.0f},{y-h*0.62-17*s:.0f} L {x-w*0.28:.0f},{y-h*0.62+17*s:.0f}", BLUE, 3),
        _el(f"M {x+w*0.34:.0f},{y-h-30*s:.0f} L {x+w*0.34:.0f},{y-h-58*s:.0f} "
            f"L {x+w*0.2:.0f},{y-h-58*s:.0f} L {x+w*0.2:.0f},{y-h-42*s:.0f}", GRAY, 4),
    ]


def _p_bench(x, y, s):
    w = 110 * s
    return [
        _el(f"M {x-w/2:.0f},{y-34*s:.0f} L {x+w/2:.0f},{y-34*s:.0f} "
            f"M {x-w/2:.0f},{y-52*s:.0f} L {x+w/2:.0f},{y-52*s:.0f}", BROWN, 5),
        _el(f"M {x-w/2+10*s:.0f},{y:.0f} L {x-w/2+10*s:.0f},{y-52*s:.0f} "
            f"M {x+w/2-10*s:.0f},{y:.0f} L {x+w/2-10*s:.0f},{y-52*s:.0f}", BROWN, 5),
    ]


def _p_car(x, y, s):
    w = 150 * s
    return [
        _el(f"M {x-w/2:.0f},{y-16*s:.0f} C {x-w/2:.0f},{y-44*s:.0f} {x-w*0.3:.0f},{y-50*s:.0f} {x-w*0.22:.0f},{y-52*s:.0f} "
            f"L {x-w*0.12:.0f},{y-76*s:.0f} C {x:.0f},{y-84*s:.0f} {x+w*0.2:.0f},{y-80*s:.0f} {x+w*0.26:.0f},{y-54*s:.0f} "
            f"C {x+w*0.44:.0f},{y-48*s:.0f} {x+w/2:.0f},{y-38*s:.0f} {x+w/2:.0f},{y-16*s:.0f} Z", RED, 6, fill=RED),
        _el(f"M {x-w*0.08:.0f},{y-56*s:.0f} L {x-w*0.06:.0f},{y-72*s:.0f} L {x+w*0.14:.0f},{y-70*s:.0f} L {x+w*0.16:.0f},{y-56*s:.0f}", BLUE, 3),
        _el(_wavy_circle(x - w * 0.28, y - 8 * s, 17 * s, bumps=6, amp=1) +
            f" M {x-w*0.28-9*s:.0f},{y-8*s:.0f} L {x-w*0.28+9*s:.0f},{y-8*s:.0f}", INK, 4, anim="spin:1.4"),
        _el(_wavy_circle(x + w * 0.3, y - 8 * s, 17 * s, bumps=6, amp=1) +
            f" M {x+w*0.3-9*s:.0f},{y-8*s:.0f} L {x+w*0.3+9*s:.0f},{y-8*s:.0f}", INK, 4, anim="spin:1.4"),
    ]


# --- playthings -----------------------------------------------------------

def _p_ball(x, y, s):
    r = 26 * s
    return [
        _el(_wavy_circle(x, y - r, r, bumps=7, amp=1.2), RED, 5, fill=RED),
        _el(f"M {x-r:.0f},{y-r:.0f} C {x-r*0.3:.0f},{y-r-10*s:.0f} {x+r*0.3:.0f},{y-r+10*s:.0f} {x+r:.0f},{y-r:.0f}", RED, 3),
    ]


def _p_balloon(x, y, s):
    r = 30 * s
    top = y - 120 * s
    return [
        _el(_wavy_circle(x, top, r, bumps=7, amp=1.2), RED, 5, fill=RED),
        _el(f"M {x-6*s:.0f},{top+r:.0f} L {x+6*s:.0f},{top+r:.0f} L {x:.0f},{top+r+9*s:.0f} Z", RED, 3),
        _el(f"M {x:.0f},{top+r+9*s:.0f} C {x+10*s:.0f},{top+r+45*s:.0f} {x-10*s:.0f},{y-30*s:.0f} {x:.0f},{y:.0f}", GRAY, 3),
    ]


def _p_bird(x, y, s):
    return [_el(
        f"M {x-22*s:.0f},{y:.0f} Q {x-10*s:.0f},{y-14*s:.0f} {x:.0f},{y:.0f} "
        f"Q {x+10*s:.0f},{y-14*s:.0f} {x+22*s:.0f},{y:.0f}", INK, 4)]


def _p_kite(x, y, s):
    top = y - 150 * s
    return [
        _el(f"M {x:.0f},{top:.0f} L {x+34*s:.0f},{top+44*s:.0f} L {x:.0f},{top+96*s:.0f} "
            f"L {x-34*s:.0f},{top+44*s:.0f} Z", RED, 4, fill=RED),
        _el(f"M {x:.0f},{top:.0f} L {x:.0f},{top+96*s:.0f} "
            f"M {x-34*s:.0f},{top+44*s:.0f} L {x+34*s:.0f},{top+44*s:.0f}", RED, 4),
        _el(f"M {x:.0f},{top+96*s:.0f} C {x-14*s:.0f},{top+130*s:.0f} {x+14*s:.0f},{y-40*s:.0f} {x:.0f},{y:.0f}", GRAY, 3),
    ]


# --- creatures & extras ---------------------------------------------------

def _p_cat(x, y, s):
    return [
        _el(f"M {x-40*s:.0f},{y:.0f} C {x-46*s:.0f},{y-34*s:.0f} {x-30*s:.0f},{y-52*s:.0f} "
            f"{x-6*s:.0f},{y-52*s:.0f} C {x+18*s:.0f},{y-52*s:.0f} {x+34*s:.0f},{y-36*s:.0f} "
            f"{x+34*s:.0f},{y-14*s:.0f} C {x+34*s:.0f},{y-5*s:.0f} {x+30*s:.0f},{y:.0f} "
            f"{x+24*s:.0f},{y:.0f} Z", GRAY, 5, fill=GRAY),
        _el(_wavy_circle(x - 26 * s, y - 62 * s, 17 * s, bumps=6, amp=1), GRAY, 5, fill=GRAY),
        _el(f"M {x-40*s:.0f},{y-72*s:.0f} L {x-36*s:.0f},{y-88*s:.0f} L {x-27*s:.0f},{y-75*s:.0f} Z "
            f"M {x-19*s:.0f},{y-76*s:.0f} L {x-13*s:.0f},{y-90*s:.0f} L {x-7*s:.0f},{y-74*s:.0f} Z",
            GRAY, 4, fill=GRAY),
        _el(f"M {x+32*s:.0f},{y-10*s:.0f} C {x+52*s:.0f},{y-20*s:.0f} {x+56*s:.0f},{y-44*s:.0f} "
            f"{x+44*s:.0f},{y-56*s:.0f}", GRAY, 5, anim="sway:9"),
        _el(f"M {x-33*s:.0f},{y-60*s:.0f} L {x-30*s:.0f},{y-59*s:.0f} "
            f"M {x-21*s:.0f},{y-60*s:.0f} L {x-18*s:.0f},{y-59*s:.0f} "
            f"M {x-27*s:.0f},{y-54*s:.0f} C {x-25*s:.0f},{y-52*s:.0f} {x-23*s:.0f},{y-52*s:.0f} {x-21*s:.0f},{y-54*s:.0f} "
            f"M {x-42*s:.0f},{y-55*s:.0f} L {x-52*s:.0f},{y-56*s:.0f} M {x-42*s:.0f},{y-51*s:.0f} L {x-52*s:.0f},{y-50*s:.0f}",
            INK, 3),
    ]


def _p_dog(x, y, s):
    return [
        _el(f"M {x-44*s:.0f},{y:.0f} C {x-52*s:.0f},{y-30*s:.0f} {x-40*s:.0f},{y-48*s:.0f} "
            f"{x-8*s:.0f},{y-50*s:.0f} C {x+26*s:.0f},{y-52*s:.0f} {x+44*s:.0f},{y-36*s:.0f} "
            f"{x+42*s:.0f},{y-12*s:.0f} C {x+41*s:.0f},{y-4*s:.0f} {x+36*s:.0f},{y:.0f} {x+30*s:.0f},{y:.0f} Z",
            BROWN, 5, fill=BROWN),
        _el(f"M {x-40*s:.0f},{y:.0f} L {x-40*s:.0f},{y-18*s:.0f} M {x-24*s:.0f},{y:.0f} L {x-24*s:.0f},{y-16*s:.0f} "
            f"M {x+16*s:.0f},{y:.0f} L {x+16*s:.0f},{y-14*s:.0f} M {x+32*s:.0f},{y:.0f} L {x+32*s:.0f},{y-12*s:.0f}",
            BROWN, 5),
        _el(f"M {x-64*s:.0f},{y-58*s:.0f} C {x-64*s:.0f},{y-72*s:.0f} {x-52*s:.0f},{y-78*s:.0f} "
            f"{x-40*s:.0f},{y-74*s:.0f} C {x-28*s:.0f},{y-72*s:.0f} {x-24*s:.0f},{y-62*s:.0f} "
            f"{x-30*s:.0f},{y-50*s:.0f} C {x-40*s:.0f},{y-42*s:.0f} {x-58*s:.0f},{y-46*s:.0f} "
            f"{x-64*s:.0f},{y-58*s:.0f} Z", BROWN, 5, fill=BROWN),
        _el(f"M {x-62*s:.0f},{y-70*s:.0f} C {x-70*s:.0f},{y-62*s:.0f} {x-70*s:.0f},{y-50*s:.0f} "
            f"{x-62*s:.0f},{y-46*s:.0f}", BROWN, 4),
        _el(f"M {x-58*s:.0f},{y-62*s:.0f} L {x-55*s:.0f},{y-61*s:.0f} M {x-66*s:.0f},{y-55*s:.0f} "
            f"C {x-64*s:.0f},{y-52*s:.0f} {x-61*s:.0f},{y-52*s:.0f} {x-60*s:.0f},{y-54*s:.0f}", INK, 3),
        _el(f"M {x+40*s:.0f},{y-24*s:.0f} C {x+56*s:.0f},{y-34*s:.0f} {x+60*s:.0f},{y-50*s:.0f} "
            f"{x+52*s:.0f},{y-58*s:.0f}", BROWN, 5, anim="sway:12"),
    ]


def _p_butterfly(x, y, s):
    return [
        _el(f"M {x:.0f},{y:.0f} C {x-26*s:.0f},{y-22*s:.0f} {x-34*s:.0f},{y+2*s:.0f} "
            f"{x-4*s:.0f},{y+8*s:.0f} Z "
            f"M {x:.0f},{y:.0f} C {x+26*s:.0f},{y-22*s:.0f} {x+34*s:.0f},{y+2*s:.0f} "
            f"{x+4*s:.0f},{y+8*s:.0f} Z", "#6c3c9e", 4, fill="#6c3c9e"),
        _el(f"M {x-2*s:.0f},{y-2*s:.0f} C {x-2*s:.0f},{y+6*s:.0f} {x+2*s:.0f},{y+10*s:.0f} "
            f"{x:.0f},{y+14*s:.0f} M {x-1*s:.0f},{y-3*s:.0f} L {x-6*s:.0f},{y-12*s:.0f} "
            f"M {x+1*s:.0f},{y-3*s:.0f} L {x+6*s:.0f},{y-12*s:.0f}", INK, 3),
    ]


def _p_bicycle(x, y, s):
    r = 26 * s
    return [
        _el(_wavy_circle(x - 44 * s, y - r, r, bumps=8, amp=1) +
            f" M {x-44*s-r*0.6:.0f},{y-r:.0f} L {x-44*s+r*0.6:.0f},{y-r:.0f}"
            f" M {x-44*s:.0f},{y-r-r*0.6:.0f} L {x-44*s:.0f},{y-r+r*0.6:.0f}",
            INK, 4, anim="spin:1.6"),
        _el(_wavy_circle(x + 44 * s, y - r, r, bumps=8, amp=1) +
            f" M {x+44*s-r*0.6:.0f},{y-r:.0f} L {x+44*s+r*0.6:.0f},{y-r:.0f}"
            f" M {x+44*s:.0f},{y-r-r*0.6:.0f} L {x+44*s:.0f},{y-r+r*0.6:.0f}",
            INK, 4, anim="spin:1.6"),
        _el(f"M {x-44*s:.0f},{y-r:.0f} L {x-12*s:.0f},{y-52*s:.0f} L {x+30*s:.0f},{y-52*s:.0f} "
            f"L {x+44*s:.0f},{y-r:.0f} M {x-12*s:.0f},{y-52*s:.0f} L {x+8*s:.0f},{y-r:.0f} "
            f"L {x-44*s:.0f},{y-r:.0f}", RED, 4),
        _el(f"M {x+30*s:.0f},{y-52*s:.0f} L {x+38*s:.0f},{y-72*s:.0f} "
            f"M {x+30*s:.0f},{y-72*s:.0f} L {x+46*s:.0f},{y-72*s:.0f} "
            f"M {x-12*s:.0f},{y-52*s:.0f} L {x-16*s:.0f},{y-66*s:.0f} "
            f"M {x-24*s:.0f},{y-66*s:.0f} L {x-8*s:.0f},{y-66*s:.0f}", INK, 4),
    ]


def _p_campfire(x, y, s):
    return [
        _el(f"M {x-34*s:.0f},{y-4*s:.0f} L {x+34*s:.0f},{y-14*s:.0f} "
            f"M {x-34*s:.0f},{y-14*s:.0f} L {x+34*s:.0f},{y-4*s:.0f}", BROWN, 6),
        _el(f"M {x-14*s:.0f},{y-14*s:.0f} C {x-24*s:.0f},{y-38*s:.0f} {x-10*s:.0f},{y-46*s:.0f} "
            f"{x-8*s:.0f},{y-62*s:.0f} C {x+4*s:.0f},{y-50*s:.0f} {x+20*s:.0f},{y-44*s:.0f} "
            f"{x+14*s:.0f},{y-24*s:.0f} C {x+11*s:.0f},{y-15*s:.0f} {x+4*s:.0f},{y-12*s:.0f} "
            f"{x-2*s:.0f},{y-12*s:.0f} Z", SUN, 5, fill=SUN, anim="sway:7"),
        _el(f"M {x-4*s:.0f},{y-14*s:.0f} C {x-8*s:.0f},{y-26*s:.0f} {x-2*s:.0f},{y-32*s:.0f} "
            f"{x:.0f},{y-40*s:.0f} C {x+6*s:.0f},{y-30*s:.0f} {x+8*s:.0f},{y-24*s:.0f} "
            f"{x+2*s:.0f},{y-15*s:.0f} Z", RED, 4, fill=RED, anim="sway:9"),
    ]


def _p_streetlamp(x, y, s):
    return [
        _el(f"M {x:.0f},{y:.0f} L {x:.0f},{y-180*s:.0f} C {x:.0f},{y-206*s:.0f} "
            f"{x+22*s:.0f},{y-210*s:.0f} {x+38*s:.0f},{y-206*s:.0f}", INK, 5),
        _el(f"M {x-14*s:.0f},{y:.0f} L {x+14*s:.0f},{y:.0f}", INK, 5),
        _el(_wavy_circle(x + 44 * s, y - 198 * s, 13 * s, bumps=6, amp=0.8),
            SUN, 4, fill=SUN),
    ]


def _p_fence(x, y, s):
    w = 120 * s
    posts = " ".join(
        f"M {x + dx * s:.0f},{y:.0f} L {x + dx * s:.0f},{y - 46 * s:.0f}"
        for dx in (-110, -55, 0, 55, 110))
    return [
        _el(posts, BROWN, 5),
        _el(f"M {x-w:.0f},{y-16*s:.0f} C {x:.0f},{y-22*s:.0f} {x+w:.0f},{y-16*s:.0f} {x+w:.0f},{y-16*s:.0f} "
            f"M {x-w:.0f},{y-34*s:.0f} C {x:.0f},{y-40*s:.0f} {x+w:.0f},{y-34*s:.0f} {x+w:.0f},{y-34*s:.0f}",
            BROWN, 4),
    ]


def _p_boat(x, y, s):
    return [
        _el(f"M {x-64*s:.0f},{y-24*s:.0f} L {x+64*s:.0f},{y-24*s:.0f} "
            f"L {x+40*s:.0f},{y:.0f} L {x-40*s:.0f},{y:.0f} Z", BROWN, 5, fill=BROWN),
        _el(f"M {x:.0f},{y-24*s:.0f} L {x:.0f},{y-98*s:.0f}", INK, 4),
        _el(f"M {x+4*s:.0f},{y-94*s:.0f} C {x+34*s:.0f},{y-80*s:.0f} {x+40*s:.0f},{y-52*s:.0f} "
            f"{x+6*s:.0f},{y-34*s:.0f} Z", "#d8dde4", 4, fill="#b9c4cf"),
        _el(f"M {x-84*s:.0f},{y+6*s:.0f} C {x-58*s:.0f},{y-2*s:.0f} {x-30*s:.0f},{y+8*s:.0f} {x-4*s:.0f},{y+2*s:.0f} "
            f"M {x+8*s:.0f},{y+8*s:.0f} C {x+34*s:.0f},{y:.0f} {x+60*s:.0f},{y+10*s:.0f} {x+86*s:.0f},{y+4*s:.0f}",
            BLUE, 4, anim="float:4"),
    ]


_PROPS = {
    "sun": _p_sun, "moon": _p_moon, "star": _p_star, "cloud": _p_cloud,
    "rain": _p_rain, "tree": _p_tree, "bush": _p_bush, "mountain": _p_mountain,
    "flower": _p_flower, "grass": _p_grass, "rock": _p_rock, "house": _p_house,
    "bench": _p_bench, "car": _p_car, "ball": _p_ball, "balloon": _p_balloon,
    "bird": _p_bird, "kite": _p_kite, "cat": _p_cat, "dog": _p_dog,
    "butterfly": _p_butterfly, "bicycle": _p_bicycle, "campfire": _p_campfire,
    "streetlamp": _p_streetlamp, "fence": _p_fence, "boat": _p_boat,
}

PROP_KINDS = sorted(_PROPS.keys())

# soft ground-shadow half-widths (px at scale 1) for sun-aware shadows
PROP_SHADOW_W = {
    "tree": 95, "bush": 52, "house": 105, "bench": 60, "car": 80, "ball": 26,
    "rock": 34, "flower": 16, "cat": 44, "dog": 52, "bicycle": 72,
    "campfire": 36, "streetlamp": 22, "boat": 70, "fence": 0, "grass": 0,
}
