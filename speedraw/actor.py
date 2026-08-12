"""Stick-figure actor for story mode: poses, emotions, gestures, speech.

Coordinates are canvas pixels. An actor stands on ``ground_y`` with total
height ~200*scale. Emotions change the face AND the posture; a badge above
the head (!, ?, heart, anger mark, sweat drop, sparkles) sells the feeling.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw

from .textcard import _LABEL_FONTS, _load_font

Point = Tuple[float, float]

EMOTIONS = ("neutral", "happy", "sad", "angry", "surprised", "scared",
            "excited", "love")
GESTURES = ("wave", "jump", "point_left", "point_right", "dance", "nod",
            "shake", "clap", "bow", "shrug", "facepalm", "think", "cry",
            "laugh", "cheer", "sit")


def _smooth(k: float) -> float:
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def _ease(act_t: float, act_dur: float, ramp: float = 0.35,
          overshoot: float = 0.12) -> float:
    """0->1->0 envelope: smooth ease in, overshoot-settle hold, ease out.

    The hold phase starts with a small damped oscillation past 1.0 so poses
    snap into place with follow-through instead of stopping dead.
    """
    if act_dur <= 2 * ramp:
        return math.sin(math.pi * min(1.0, act_t / max(act_dur, 1e-3)))
    if act_t < ramp:
        return _smooth(act_t / ramp)
    if act_t > act_dur - ramp:
        return _smooth(max(0.0, (act_dur - act_t) / ramp))
    if overshoot:
        dt = act_t - ramp
        return 1.0 + overshoot * math.exp(-4.0 * dt) * math.sin(2 * math.pi * 1.5 * dt)
    return 1.0


def _jump_phases(act_t: float, s: float) -> Tuple[float, float, float]:
    """Anticipation -> flight -> landing. Returns (jump_dy, hip_crouch, sy).

    sy is the vertical body-stretch factor: squash while crouching and on
    landing, stretch while moving fast through the air.
    """
    if act_t < 0.16:
        k = _smooth(act_t / 0.16)
        return 0.0, 12 * s * k, 1.0 - 0.10 * k
    if act_t < 0.86:
        u = (act_t - 0.16) / 0.70
        return (-64 * s * math.sin(math.pi * u), 0.0,
                1.0 + 0.11 * abs(math.cos(math.pi * u)))
    v = min(1.0, (act_t - 0.86) / 0.24)
    return 0.0, 0.0, 1.0 - 0.16 * math.sin(math.pi * v)


def body_stretch(activity: str, act_t: float, act_dur: float) -> Tuple[float, float]:
    """(sx, sy) squash & stretch factors about the ground anchor.

    Volume-preserving: sx = 1/sy, so squashing down widens the body.
    """
    sy = 1.0
    if activity == "jump":
        sy = _jump_phases(act_t, 1.0)[2]
    elif activity == "walk":
        sy = 1.0 + 0.028 - 0.05 * abs(math.cos(2 * math.pi * 1.8 * act_t))
    elif activity == "run":
        sy = 1.0 + 0.04 - 0.08 * abs(math.cos(2 * math.pi * 2.6 * act_t))
    elif activity == "cheer":
        sy = 1.0 + 0.05 * abs(math.sin(2 * math.pi * 2.2 * act_t))
    elif activity == "dance":
        sy = 1.0 + 0.035 * math.sin(2 * math.pi * 1.62 * act_t)
    return (1.0 / sy, sy)

# posture per emotion: (head_dy, lean, arm_base) — arm_base is the resting
# arm angle from straight down (positive = away from body)
_POSTURE = {
    "neutral":   (0.0, 0.00, 0.16),
    "happy":     (-2.0, 0.00, 0.30),
    "sad":       (10.0, 0.10, 0.06),
    "angry":     (2.0, -0.10, 0.34),
    "surprised": (-4.0, -0.04, 0.42),
    "scared":    (2.0, 0.14, 0.55),
    "excited":   (-4.0, 0.00, 0.45),
    "love":      (-2.0, 0.04, 0.22),
}


SKIN = (243, 205, 171)
SHOE = (58, 62, 74)
PANTS = (76, 84, 102)
SHADOW = (224, 222, 214)


@dataclass
class ActorVisual:
    color: Tuple[int, int, int]                 # outline / limb ink
    scale: float
    shirt: Optional[Tuple[int, int, int]] = None
    hair: str = "spiky"                          # spiky | curly | flat | bun
    hair_color: Tuple[int, int, int] = (64, 50, 42)


def _capsule(d: ImageDraw.ImageDraw, a: Point, b: Point, r: float, fill,
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


def _cir(d: ImageDraw.ImageDraw, c: Point, r: float, color, width: int) -> None:
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=color, width=width)


def _dot(d: ImageDraw.ImageDraw, c: Point, r: float, color) -> None:
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=color)


def _line(d: ImageDraw.ImageDraw, pts: List[Point], color, width: int) -> None:
    d.line(pts, fill=color, width=width, joint="curve")
    r = width / 2
    for p in (pts[0], pts[-1]):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)


def draw_actor(
    d: ImageDraw.ImageDraw,
    x: float,
    ground_y: float,
    vis: ActorVisual,
    facing: float = 1.0,
    emotion: str = "neutral",
    t: float = 0.0,             # global time, drives idle bob / blink / cycles
    activity: str = "idle",     # idle | walk | run | any GESTURES entry
    act_t: float = 0.0,         # time within the activity
    act_dur: float = 1.5,       # planned duration of the activity
    talking: bool = False,
    mouth: Optional[Tuple[float, float]] = None,  # lip-sync (open, shape) 0-1
    vel: float = 0.0,           # horizontal velocity px/s (drives hair lag)
    settle: float = 0.0,        # damped follow-through lean after stopping
    gaze: Optional[float] = None,   # -1..1 world-space look direction
    blink_seed: float = 0.0,    # desyncs blink timing between actors
) -> Point:
    """Draw the actor; returns the head-top anchor (for badges/bubbles)."""
    s = vis.scale
    color = vis.color
    W = max(3, round(7 * s))

    head_dy, lean, arm_base = _POSTURE.get(emotion, _POSTURE["neutral"])
    head_dy *= s
    e = _ease(act_t, act_dur)

    bob = 2.2 * s * math.sin(2 * math.pi * t / 2.8)
    jump_dy = 0.0
    hip_drop = 0.0
    body_lean = lean + settle   # forward lean in rad (positive = toward facing)
    w = 2 * math.pi * 1.8 * act_t
    wr = 2 * math.pi * 2.6 * act_t

    if activity == "jump":
        jump_dy, crouch, _ = _jump_phases(act_t, s)
        hip_drop += crouch
        bob = 0.0
    elif activity == "walk":
        bob = 2.5 * s * abs(math.cos(w))
    elif activity == "run":
        bob = 3.6 * s * abs(math.cos(wr))
        body_lean += 0.22
    elif activity == "cheer":
        jump_dy = -10 * s * abs(math.sin(2 * math.pi * 2.2 * act_t))
    elif activity == "sit":
        hip_drop = 34 * s * e
    elif activity == "bow":
        body_lean += 0.85 * e
    elif activity == "laugh":
        body_lean -= 0.34 * e
        bob = 1.8 * s * math.sin(2 * math.pi * 5 * act_t)
    elif activity == "cry":
        head_dy += 7 * s

    # chibi proportions: the head is ~40% of total height, limbs short
    Y = ground_y + jump_dy
    hip = (x, Y - 55 * s + hip_drop + bob * 0.4)
    bvx, bvy = facing * math.sin(body_lean), -math.cos(body_lean)
    shoulder = (hip[0] + bvx * 36 * s, hip[1] + bvy * 36 * s + bob * 0.6)
    if activity == "cry":
        shoulder = (shoulder[0] + 1.6 * s * math.sin(2 * math.pi * 7 * act_t), shoulder[1])
    head_c = [shoulder[0] + bvx * 30 * s + facing * 4 * s * math.cos(body_lean),
              shoulder[1] + bvy * 30 * s + head_dy]
    if activity == "nod":
        head_c[1] += 6 * s * abs(math.sin(2 * math.pi * 1.9 * act_t)) * e
    elif activity == "shake":
        head_c[0] += 7 * s * math.sin(2 * math.pi * 2.4 * act_t) * e
    head_c = (head_c[0], head_c[1])
    head_r = 31 * s

    def limb(origin: Point, l1: float, l2: float, a1: float, a2: float,
             face_mult: float = 1.0) -> List[Point]:
        f = facing * face_mult
        jx = origin[0] + f * math.sin(a1) * l1
        jy = origin[1] + math.cos(a1) * l1
        ex = jx + f * math.sin(a1 + a2) * l2
        ey = jy + math.cos(a1 + a2) * l2
        return [origin, (jx, jy), (ex, ey)]

    extras: List = []           # drawn after the body (marks, dots)

    # ---- legs -------------------------------------------------------------
    L1, L2 = 30 * s, 26 * s
    if activity == "walk":
        legs = []
        for ph in (0.0, math.pi):
            a1 = 0.55 * math.sin(w + ph)
            a2 = -0.85 * max(0.0, math.sin(w + ph - math.pi / 2))
            legs.append(limb(hip, L1, L2, a1, a2))
    elif activity == "run":
        legs = []
        for ph in (0.0, math.pi):
            a1 = 0.85 * math.sin(wr + ph) + 0.1
            a2 = -1.35 * max(0.0, math.sin(wr + ph - math.pi / 2))
            legs.append(limb(hip, L1, L2, a1, a2))
    elif activity == "jump":
        if act_t < 0.16:        # anticipation crouch: knees bend
            tuck = 0.42 * _smooth(act_t / 0.16)
        elif act_t < 0.86:      # airborne tuck
            tuck = 0.5 * math.sin(math.pi * (act_t - 0.16) / 0.70)
        else:                   # landing: absorb with bent knees
            tuck = 0.30 * math.sin(math.pi * min(1.0, (act_t - 0.86) / 0.24))
        legs = [limb(hip, L1, L2, 0.3 * tuck + 0.1, -1.4 * tuck),
                limb(hip, L1, L2, -0.3 * tuck - 0.1, -1.2 * tuck)]
    elif activity == "dance":
        k = math.sin(w * 0.9)
        legs = [limb(hip, L1, L2, 0.28 * k + 0.12, -0.4 * max(0.0, k)),
                limb(hip, L1, L2, -0.28 * k - 0.12, -0.4 * max(0.0, -k))]
    elif activity == "sit":
        fold = e
        legs = [limb(hip, L1, L2, 1.9 * fold + 0.13 * (1 - fold), -2.4 * fold),
                limb(hip, L1 * 0.98, L2, 1.74 * fold - 0.13 * (1 - fold), -2.2 * fold)]
    else:
        legs = [limb(hip, L1, L2, 0.13, 0.0), limb(hip, L1, L2, -0.13, 0.0)]

    # ---- arms -------------------------------------------------------------
    A1, A2 = 26 * s, 22 * s
    if activity == "walk":
        arms = [limb(shoulder, A1, A2, 0.7 * 0.55 * math.sin(w + math.pi), 0.35),
                limb(shoulder, A1, A2, 0.7 * 0.55 * math.sin(w), 0.35)]
    elif activity == "run":
        arms = [limb(shoulder, A1, A2, 0.7 * math.sin(wr + math.pi), 1.0),
                limb(shoulder, A1, A2, 0.7 * math.sin(wr), 1.0)]
    elif activity == "wave":
        wavea = math.pi - 0.5 + 0.45 * math.sin(2 * math.pi * 2.2 * act_t)
        arms = [limb(shoulder, A1, A2, arm_base, 0.2, -1.0),
                limb(shoulder, A1 * 1.15, A2 * 1.15, math.pi * 0.68,
                     wavea - math.pi * 0.68)]
    elif activity == "jump":
        if act_t < 0.16:        # wind-up: arms swing behind for momentum
            k = _smooth(act_t / 0.16)
            arms = [limb(shoulder, A1, A2, -0.55 * k + 0.1, -0.2 * k, -1.0),
                    limb(shoulder, A1, A2, -0.55 * k + 0.1, -0.2 * k)]
        else:                   # airborne / landing: arms flung up-and-out
            up = math.pi * 0.60   # clears the big chibi head
            arms = [limb(shoulder, A1, A2, up, 0.35, -1.0),
                    limb(shoulder, A1, A2, up, 0.35)]
    elif activity == "idle" and emotion == "excited":
        up = math.pi * 0.60
        arms = [limb(shoulder, A1, A2, up, 0.35, -1.0),
                limb(shoulder, A1, A2, up, 0.35)]
    elif activity in ("point_left", "point_right"):
        pdir = 1.0 if activity == "point_right" else -1.0
        pa = min(1.0, act_t / 0.35) * math.pi / 2
        arms = [limb(shoulder, A1, A2, arm_base, 0.15, -pdir * facing),
                limb(shoulder, A1, A2 * 1.05, pa, 0.0, pdir * facing)]
    elif activity == "dance":
        k = math.sin(w * 0.9)
        arms = [limb(shoulder, A1, A2, math.pi * 0.6 + 0.5 * k, 0.6, -1.0),
                limb(shoulder, A1, A2, math.pi * 0.6 - 0.5 * k, 0.6)]
    elif activity == "clap":
        gap = 0.38 * max(0.0, math.sin(2 * math.pi * 3.2 * act_t))
        arms = [limb(shoulder, A1, A2, 1.35 - gap, -0.5),
                limb(shoulder, A1 * 0.97, A2, 1.35 + gap, -0.5)]
        if gap < 0.08 and act_t > 0.2:
            hx = (arms[0][-1][0] + arms[1][-1][0]) / 2
            hy = (arms[0][-1][1] + arms[1][-1][1]) / 2
            for a in (-0.7, 0.0, 0.7):
                extras.append(("line", [(hx + facing * 12 * s * math.cos(a),
                                         hy - 12 * s * math.sin(a) - 4 * s),
                                        (hx + facing * 23 * s * math.cos(a),
                                         hy - 23 * s * math.sin(a) - 6 * s)],
                               (217, 144, 43), max(2, round(2.6 * s))))
    elif activity == "bow":
        arms = [limb(shoulder, A1, A2, 0.10, 0.05, -1.0),
                limb(shoulder, A1, A2, 0.10, 0.05)]
    elif activity == "shrug":
        k = e
        arms = [limb(shoulder, A1, A2, 0.45 * k, 2.3 * k, -1.0),
                limb(shoulder, A1, A2, 0.45 * k, 2.3 * k)]
    elif activity == "facepalm":
        # longer reach so the hand lands on the big chibi face
        arms = [limb(shoulder, A1, A2, arm_base * 0.4, 0.08, -1.0),
                limb(shoulder, A1 * 1.3, A2 * 1.45, 2.05 * e, 2.0 * e)]
        if e > 0.75:  # redraw the hand over the face (the head hides it)
            extras.append(("hand", arms[1][-1]))
    elif activity == "think":
        arms = [limb(shoulder, A1, A2, 0.35, -1.1, -1.0),
                limb(shoulder, A1 * 1.25, A2 * 1.4, 1.75 * e, 2.35 * e)]
        bx0, by0 = head_c[0] + facing * head_r * 1.4, head_c[1] - head_r * 1.2
        for i, rr in enumerate((3.0, 4.4, 6.0)):
            extras.append(("dotc", (bx0 + facing * i * 14 * s,
                                    by0 - i * 16 * s), rr * s, color))
    elif activity == "cry":
        # one hand wiping the eyes, the other hanging limp
        arms = [limb(shoulder, A1, A2, 0.14, 0.05, -1.0),
                limb(shoulder, A1 * 1.25, A2 * 1.4, 1.55 * e, 2.45 * e)]
        if e > 0.75:
            extras.append(("hand", arms[1][-1]))
    elif activity == "laugh":
        # one hand on the belly, the other flung up
        arms = [limb(shoulder, A1, A2, 0.42, -1.15),
                limb(shoulder, A1, A2, 2.25, 0.3, -1.0)]
        hx0 = head_c[0] + facing * head_r * 1.9
        hy0 = head_c[1] - 6 * s - 12 * s * (act_t % 0.8)
        for i in range(3):
            extras.append(("arc", (hx0 + facing * i * 17 * s, hy0 - i * 11 * s),
                           (9 - i * 1.5) * s, color))
    elif activity == "cheer":
        k = math.sin(2 * math.pi * 2.2 * act_t)
        arms = [limb(shoulder, A1, A2, math.pi * 0.60 + 0.15 * k, 0.25, -1.0),
                limb(shoulder, A1, A2, math.pi * 0.60 - 0.15 * k, 0.25)]
    elif activity == "sit":
        arms = [limb(shoulder, A1, A2, 0.55 * e + arm_base * (1 - e), -0.9 * e, -1.0),
                limb(shoulder, A1, A2, 0.6 * e + arm_base * (1 - e), -0.95 * e)]
    elif emotion == "sad":
        arms = [limb(shoulder, A1, A2, 0.12, 0.06, -1.0),
                limb(shoulder, A1, A2, 0.12, 0.06)]
    elif emotion == "scared":
        arms = [limb(shoulder, A1, A2, math.pi * 0.55, 0.8, -1.0),
                limb(shoulder, A1, A2, math.pi * 0.55, 0.8)]
    else:
        arms = [limb(shoulder, A1, A2, arm_base, 0.12, -1.0),
                limb(shoulder, A1, A2, arm_base, 0.12)]

    # ---- draw the doodle body ---------------------------------------------
    # ground shadow (shrinks when airborne)
    shrink = max(0.5, 1.0 - abs(jump_dy) / (110 * s))
    rx, ry = 42 * s * shrink, 8 * s * shrink
    d.ellipse([x - rx, ground_y + 5 * s - ry, x + rx, ground_y + 5 * s + ry],
              fill=SHADOW)

    # legs in trousers + shoes
    for limb_pts in legs:
        _line(d, limb_pts, PANTS, W + round(3 * s))
        fx_, fy_ = limb_pts[-1]
        # shoe: small ellipse nudged toward the walking direction
        d.ellipse([fx_ - 9 * s + facing * 5 * s, fy_ - 6 * s,
                   fx_ + 12 * s + facing * 5 * s, fy_ + 6 * s], fill=SHOE)

    # torso: shirt-coloured bean from below the neck to the hip
    shirt = vis.shirt or color
    t0 = (shoulder[0] + bvx * 7 * s, shoulder[1] + bvy * 7 * s)
    _capsule(d, t0, hip, 20 * s, shirt, color, max(2, round(2.6 * s)))
    # a couple of crease strokes keep it doodly
    _line(d, [(hip[0] - 8 * s, hip[1] - 16 * s), (hip[0] + 2 * s, hip[1] - 12 * s)],
          _mix_c(shirt, (0, 0, 0), 0.25), max(2, round(2 * s)))

    # arms: darker sleeves so they read against the shirt, skin hands
    sleeve = _mix_c(shirt, (0, 0, 0), 0.32)
    for limb_pts in arms:
        _line(d, limb_pts, sleeve, W + round(1 * s))
        hx_, hy_ = limb_pts[-1]
        d.ellipse([hx_ - 6.5 * s, hy_ - 6.5 * s, hx_ + 6.5 * s, hy_ + 6.5 * s],
                  fill=SKIN, outline=color, width=max(2, round(1.8 * s)))

    # neck + head (skin-filled) + hair
    _line(d, [(head_c[0] - bvx * head_r, head_c[1] - bvy * head_r), shoulder],
          color, W)
    d.ellipse([head_c[0] - head_r, head_c[1] - head_r,
               head_c[0] + head_r, head_c[1] + head_r], fill=SKIN)
    _cir(d, head_c, head_r, color, W)
    hv = max(-1.0, min(1.0, vel / 430.0)) + 0.35 * settle * facing
    _draw_hair(d, head_c, head_r, facing, vis.hair, vis.hair_color, s, hv, t)

    for ex in extras:
        if ex[0] == "line":
            _line(d, ex[1], ex[2], ex[3])
        elif ex[0] == "dotc":
            _cir(d, ex[1], ex[2], ex[3], max(2, round(2.2 * s)))
        elif ex[0] == "arc":
            c, r = ex[1], ex[2]
            d.arc([c[0] - r, c[1] - r, c[0] + r, c[1] + r], 200, 340,
                  fill=ex[3], width=max(2, round(2.4 * s)))

    _draw_face(d, head_c, head_r, facing, emotion, t, activity, talking, color, s,
               mouth=mouth, gaze=gaze, blink_seed=blink_seed)
    for ex in extras:
        if ex[0] == "hand":     # hands resting ON the face draw over it
            hx_, hy_ = ex[1]
            d.ellipse([hx_ - 7 * s, hy_ - 7 * s, hx_ + 7 * s, hy_ + 7 * s],
                      fill=SKIN, outline=color, width=max(2, round(1.8 * s)))
    _draw_badge(d, (head_c[0], head_c[1] - head_r), emotion, t, s)
    return (head_c[0], head_c[1] - head_r)


def _mix_c(a: Tuple[int, int, int], b: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def _draw_hair(d: ImageDraw.ImageDraw, head_c: Point, head_r: float,
               facing: float, style: str, hair_color, s: float,
               hv: float = 0.0, t: float = 0.0) -> None:
    """hv is the follow-through drag (-1..1): hair trails opposite to motion
    and keeps swaying gently at rest so it never looks glued on."""
    hx, hy = head_c
    ow = max(2, round(2.2 * s))
    drag = -hv * 9 * s + 1.1 * s * math.sin(2 * math.pi * t / 2.1)
    if style == "curly":
        for i in range(6):
            a = math.pi + (i + 0.5) * math.pi / 6   # across the top arc
            lift = max(0.0, -math.sin(a))           # top curls trail the most
            cx = hx + (head_r * 0.95) * math.cos(a) + drag * 0.55 * lift
            cy = hy + (head_r * 0.95) * math.sin(a)
            r = (7.5 - abs(i - 2.5)) * s + 3 * s
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=hair_color)
    elif style == "flat":
        d.chord([hx - head_r, hy - head_r, hx + head_r, hy + head_r],
                195, 345, fill=hair_color)
        for i in range(3):
            x0 = hx - head_r * 0.5 + i * head_r * 0.42
            d.line([(x0, hy - head_r * 0.55),
                    (x0 + facing * 5 * s + drag * 0.6, hy - head_r * 0.9)],
                   fill=_mix_c(hair_color, (0, 0, 0), 0.3), width=ow)
    elif style == "bun":
        d.chord([hx - head_r, hy - head_r, hx + head_r, hy + head_r],
                190, 350, fill=hair_color)
        bx = hx - facing * head_r * 0.75 + drag * 0.8
        by = hy - head_r * 0.95 + abs(drag) * 0.15
        r = 10 * s
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=hair_color)
    else:  # spiky
        for i in range(5):
            a = math.pi + (i + 0.7) * math.pi / 6.2
            lift = max(0.0, -math.sin(a))
            bx = hx + head_r * 0.92 * math.cos(a)
            by = hy + head_r * 0.92 * math.sin(a)
            tipx = hx + head_r * 1.45 * math.cos(a) + facing * 3 * s + drag * lift
            tipy = hy + head_r * 1.45 * math.sin(a)
            wx, wy = -math.sin(a) * 7 * s, math.cos(a) * 7 * s
            d.polygon([(bx - wx, by - wy), (tipx, tipy), (bx + wx, by + wy)],
                      fill=hair_color)


# eyebrow spec per emotion: (lift in s-units, inner_drop, outer_drop)
# inner = toward the nose. Positive drop moves that end down.
_BROWS = {
    "neutral":   (14.5, 0.0, 0.0),
    "happy":     (16.5, 0.5, 1.5),
    "surprised": (19.0, 0.0, 1.0),
    "scared":    (18.0, -1.5, 2.0),
    "excited":   (17.5, 0.0, 1.5),
    "love":      (16.0, 1.0, 2.0),
}

PUPIL = (52, 58, 72)
SCLERA = (255, 255, 253)
BLUSH = (242, 186, 178)


def _eye_open(d, ex, ey, gaze, color, s, pupil_scale=1.0, lid=0.0):
    """Big chibi eye: white sclera, large gaze-following pupil, highlight.

    pupil_scale shrinks the pupil (shock/fear read as tiny pupils in big
    whites); lid > 0 drops a straight upper eyelid over the eye (drowsy,
    sad, unimpressed).
    """
    rx, ry = 7.6 * s, 8.6 * s
    ow = max(2, round(2.2 * s))
    d.ellipse([ex - rx, ey - ry, ex + rx, ey + ry], fill=SCLERA,
              outline=color, width=ow)
    px = ex + (gaze or 0.0) * 3.0 * s
    pr = 4.1 * s * pupil_scale
    py = ey + 0.8 * s
    d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=PUPIL)
    hr = max(1.0, 1.6 * s * pupil_scale)
    d.ellipse([px - pr * 0.35 - hr, py - pr * 0.45 - hr,
               px - pr * 0.35 + hr, py - pr * 0.45 + hr], fill=SCLERA)
    if lid > 0:
        ly = ey - ry + lid * 2 * ry
        d.rectangle([ex - rx, ey - ry - ow, ex + rx, ly], fill=SKIN)
        d.line([(ex - rx, ly), (ex + rx, ly)], fill=color, width=ow)


def _draw_brows(d, fx, eye_y, eye_dx, emotion, color, s, blink=False):
    ow = max(2, round(2.4 * s))
    if emotion == "angry":
        for side in (-1, 1):
            ex = fx + side * eye_dx
            _line(d, [(ex - 6 * s, eye_y - 15 * s + (2.5 * s if side < 0 else 0)),
                      (ex + 6 * s, eye_y - 11 * s - (2.5 * s if side < 0 else 0))][::side],
                  color, max(2, round(2.6 * s)))
        return
    if emotion == "sad":
        for side in (-1, 1):
            ex = fx + side * eye_dx
            _line(d, [(ex - side * 6 * s, eye_y - 14 * s), (ex + side * 5 * s, eye_y - 11 * s)],
                  color, max(2, round(2.2 * s)))
        return
    lift, inner, outer = _BROWS.get(emotion, _BROWS["neutral"])
    if blink:
        lift -= 2.0
    for side in (-1, 1):
        ex = fx + side * eye_dx
        by = eye_y - lift * s
        # three-point polyline reads as a hand-drawn brow arc
        pts = [(ex - side * 6.5 * s, by + inner * s),
               (ex, by - 1.4 * s),
               (ex + side * 6.5 * s, by + outer * s)]
        _line(d, pts, color, ow)


def _mouth_corner_bias(emotion):
    """Vertical corner offset while talking: smiles curl up, sadness down."""
    if emotion in ("happy", "excited", "love"):
        return -1.0
    if emotion in ("sad", "scared"):
        return 1.0
    return 0.0


def _draw_face(d, head_c, head_r, facing, emotion, t, activity, talking, color, s,
               mouth=None, gaze=None, blink_seed=0.0):
    fx = head_c[0] + facing * 5 * s
    fy = head_c[1]
    eye_dx = 11 * s
    eye_y = fy - 4 * s

    def blush():
        for side in (-1, 1):
            bx = fx + side * 15 * s
            d.ellipse([bx - 4.5 * s, fy + 7 * s, bx + 4.5 * s, fy + 11.5 * s],
                      fill=BLUSH)

    if activity == "cry":
        _draw_brows(d, fx, eye_y, eye_dx, "sad", color, s)
        for side in (-1, 1):
            ex = fx + side * eye_dx
            _line(d, [(ex - 5.5 * s, eye_y), (ex + 5.5 * s, eye_y)], color,
                  max(2, round(2.5 * s)))
            tl = (7 + 6 * abs(math.sin(2 * math.pi * 1.8 * t))) * s
            _line(d, [(ex, eye_y + 4 * s), (ex - side * 2 * s, eye_y + 4 * s + tl)],
                  (57, 114, 158), max(2, round(2.6 * s)))
        my = fy + 14 * s
        d.arc([fx - 8 * s, my, fx + 8 * s, my + 10 * s], 195, 345,
              fill=color, width=max(2, round(2.6 * s)))
        return
    if activity == "laugh":
        _draw_brows(d, fx, eye_y, eye_dx, "happy", color, s)
        blush()
        for side in (-1, 1):
            ex = fx + side * eye_dx
            d.arc([ex - 5.5 * s, eye_y - 5.5 * s, ex + 5.5 * s, eye_y + 4 * s],
                  200, 340, fill=color, width=max(2, round(2.6 * s)))
        oh = (9 + 3.5 * abs(math.sin(2 * math.pi * 4 * t))) * s
        d.ellipse([fx - 8 * s, fy + 8 * s, fx + 8 * s, fy + 8 * s + oh],
                  outline=color, width=max(2, round(2.6 * s)))
        return

    period = 3.1 + (blink_seed % 1.0) * 1.4
    blink = ((t + blink_seed) % period) < 0.13 and emotion not in ("surprised", "scared")

    for side in (-1, 1):
        ex = fx + side * eye_dx
        if blink:
            _line(d, [(ex - 5 * s, eye_y + 1 * s), (ex + 5 * s, eye_y + 1 * s)],
                  color, max(2, round(2.6 * s)))
        elif emotion == "surprised":
            _eye_open(d, ex, eye_y, gaze, color, s, pupil_scale=0.55)
        elif emotion == "scared":
            _eye_open(d, ex, eye_y, gaze, color, s, pupil_scale=0.45)
        elif emotion == "love":
            _heart(d, (ex, eye_y), 7.5 * s, (184, 69, 60))
        elif emotion == "happy" or emotion == "excited":
            d.arc([ex - 5.5 * s, eye_y - 5.5 * s, ex + 5.5 * s, eye_y + 4 * s],
                  200, 340, fill=color, width=max(2, round(2.6 * s)))
        elif emotion == "sad":
            _eye_open(d, ex, eye_y, gaze, color, s, lid=0.30)
        else:
            _eye_open(d, ex, eye_y, gaze, color, s)

    _draw_brows(d, fx, eye_y, eye_dx, emotion, color, s, blink=blink)
    if emotion in ("happy", "excited", "love") or talking:
        blush()

    my = fy + 14 * s
    mw = 8 * s
    if talking:
        if mouth is not None:
            open01, shape01 = mouth
        else:  # no audio track available — fall back to a talking rhythm
            open01 = abs(math.sin(2 * math.pi * 3.1 * t))
            shape01 = 0.4
        ow = max(2, round(2.4 * s))
        bias = _mouth_corner_bias(emotion)
        if open01 < 0.09:
            # between words / syllables: lips closed (curved by emotion)
            _line(d, [(fx - 5 * s, my + bias * 1.6 * s), (fx, my + bias * 0.2 * s),
                      (fx + 5 * s, my + bias * 1.6 * s)], color, ow)
        else:
            # loudness opens the mouth; high-frequency sounds widen and
            # flatten it (ee/ss), low-frequency vowels round it (ah/oh)
            mw2 = (4.5 + 5.0 * shape01) * s
            oh = (1.5 + 10.0 * open01) * s * (1.0 - 0.45 * shape01)
            if oh > 5.5 * s:  # wide open: show a dark mouth interior
                d.ellipse([fx - mw2, my - oh / 2, fx + mw2, my + oh / 2],
                          fill=(94, 52, 50), outline=color, width=ow)
            else:
                d.ellipse([fx - mw2, my - oh / 2, fx + mw2, my + oh / 2],
                          outline=color, width=ow)
            if bias:
                # corner ticks keep the emotion readable mid-speech
                for side in (-1, 1):
                    cx0 = fx + side * mw2
                    _line(d, [(cx0, my), (cx0 + side * 2.4 * s, my - bias * 2.6 * s)],
                          color, max(2, round(2 * s)))
        return
    if emotion in ("happy", "excited", "love"):
        d.arc([fx - mw, my - 6 * s, fx + mw, my + 6 * s], 15, 165,
              fill=color, width=max(2, round(2.8 * s)))
    elif emotion == "sad":
        d.arc([fx - mw, my, fx + mw, my + 12 * s], 195, 345,
              fill=color, width=max(2, round(2.8 * s)))
        # a small tear
        _line(d, [(fx - eye_dx - 3 * s, eye_y + 5 * s),
                  (fx - eye_dx - 4 * s, eye_y + 12 * s)], (57, 114, 158), max(2, round(2.2 * s)))
    elif emotion == "angry":
        _line(d, [(fx - mw * 0.8, my + 3 * s), (fx + mw * 0.8, my + 1 * s)], color,
              max(2, round(2.8 * s)))
    elif emotion == "surprised":
        _cir(d, (fx, my + 1 * s), 4.5 * s, color, max(2, round(2.4 * s)))
    elif emotion == "scared":
        pts = [(fx - mw * 0.8 + i * mw * 0.4, my + (2 * s if i % 2 else -1 * s))
               for i in range(5)]
        _line(d, pts, color, max(2, round(2.4 * s)))
    else:
        _line(d, [(fx - mw * 0.6, my + 1 * s), (fx + mw * 0.6, my + 1 * s)], color,
              max(2, round(2.4 * s)))


def _heart(d, c, r, color) -> None:
    x, y = c
    d.polygon([(x, y + r), (x - r, y - r * 0.2), (x - r * 0.5, y - r),
               (x, y - r * 0.35), (x + r * 0.5, y - r), (x + r, y - r * 0.2)],
              fill=color)


def _draw_badge(d, anchor, emotion, t, s) -> None:
    """Floating symbol above the head that sells the emotion."""
    x, y = anchor
    y -= 18 * s + 3 * s * math.sin(2 * math.pi * t / 1.6)
    ink = (40, 48, 63)
    if emotion == "surprised":
        _line(d, [(x, y - 22 * s), (x, y - 8 * s)], ink, max(3, round(3.5 * s)))
        _dot(d, (x, y), 2.6 * s, ink)
    elif emotion == "love":
        _heart(d, (x, y - 10 * s), 9 * s, (184, 69, 60))
    elif emotion == "angry":
        for a in (0.6, 1.2, 1.9, 2.5):
            x0 = x - 24 * s * math.cos(a)
            y0 = y - 6 * s - 16 * s * math.sin(a)
            _line(d, [(x0, y0), (x0 - 8 * s * math.cos(a), y0 - 8 * s * math.sin(a))],
                  (184, 69, 60), max(2, round(2.8 * s)))
    elif emotion == "scared":
        _line(d, [(x + 16 * s, y - 14 * s), (x + 13 * s, y - 4 * s)], (57, 114, 158),
              max(2, round(2.6 * s)))
    elif emotion == "excited":
        for dx, dy in ((-20, -12), (18, -16), (0, -26)):
            px, py = x + dx * s, y + dy * s
            _line(d, [(px - 4 * s, py), (px + 4 * s, py)], (217, 144, 43), max(2, round(2.4 * s)))
            _line(d, [(px, py - 4 * s), (px, py + 4 * s)], (217, 144, 43), max(2, round(2.4 * s)))


# ---------------------------------------------------------------------------
# Speech bubbles
# ---------------------------------------------------------------------------


def draw_speech_bubble(
    frame: Image.Image,
    head_anchor: Point,
    text: str,
    canvas: Tuple[int, int],
    scale: float = 1.0,
    age: float = 1.0,
) -> None:
    d = ImageDraw.Draw(frame)
    cw, ch = canvas
    size = max(16, round(26 * scale))
    font = _load_font(size, _LABEL_FONTS)

    # wrap text
    words = text.split()
    lines, line = [], ""
    maxw = int(cw * 0.34)
    for wd in words:
        trial = (line + " " + wd).strip()
        if d.textlength(trial, font=font) <= maxw or not line:
            line = trial
        else:
            lines.append(line)
            line = wd
    lines.append(line)
    tw = max(d.textlength(ln, font=font) for ln in lines)
    lh = round(size * 1.22)
    th = lh * len(lines)

    pad = round(16 * scale)
    bw, bh = tw + 2 * pad, th + 2 * pad
    p = min(1.0, age / 0.22)            # quick pop-in with a springy overshoot
    pop = _smooth(p) * (1.0 + 0.10 * math.sin(math.pi * p))
    bw, bh = bw * pop, bh * pop

    hx, hy = head_anchor
    side = 1 if hx < cw / 2 else -1     # bubble opens toward canvas center
    bx = hx + side * 30 - (0 if side > 0 else bw)
    by = hy - 46 - bh
    bx = max(12, min(bx, cw - bw - 12))
    by = max(10, by)

    ink = (40, 48, 63)
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=round(16 * pop) + 1,
                        fill=(255, 255, 253), outline=ink, width=3)
    # tail
    t0 = (hx + side * 26, by + bh - 2)
    d.polygon([t0, (t0[0] + side * 26, by + bh - 12 * pop), (hx + side * 8, hy - 34)],
              fill=(255, 255, 253), outline=ink)

    if p >= 1.0:
        ty = by + pad
        for ln in lines:
            lw = d.textlength(ln, font=font)
            d.text((bx + (bw - lw) / 2, ty), ln, font=font, fill=ink)
            ty += lh
