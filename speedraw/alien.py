"""The alien narrator: a single expressive figure acting on a dark stage.

Frontal pose, built for close-up storytelling: huge glossy almond eyes with
gaze, squint and blinks; emotive antennae; brow ridges; a viseme-driven
mouth; long three-fingered hands and a library of acting gestures. All
geometry hangs off ``scale`` so the camera can redraw the figure at any
zoom and stay razor sharp.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from PIL import ImageDraw

from .actor import _capsule, _ease, _line, _mix_c, _smooth

Point = Tuple[float, float]

# ---- palette tuned for a black stage --------------------------------------
SKIN = (163, 199, 172)
SKIN_DARK = (52, 82, 64)          # outlines
SKIN_SHADE = (120, 158, 130)      # brow ridges / creases
BELLY = (188, 216, 191)
EYE_DARK = (16, 18, 26)
EYE_GLOW = (74, 146, 124)         # rim around the eyes
EYE_INNER = (44, 66, 96)          # faint galaxy sheen inside the eye
HIGHLIGHT = (235, 245, 250)
ANTENNA_TIP = (140, 230, 205)
MOUTH_IN = (26, 20, 30)
TONGUE = (154, 84, 96)

ALIEN_GESTURES = ("open_arms", "point_left", "point_right", "point_up",
                  "think", "shrug", "wave", "facepalm", "jazz_hands",
                  "clasp", "arms_cross", "recoil", "bow", "count")

# emotion -> (head_dy, shoulder_drop, antenna_perk)  perk: 1 up .. -1 droop
_EMO_POSE = {
    "neutral":   (0.0, 0.0, 0.25),
    "happy":     (-3.0, -1.0, 0.7),
    "sad":       (7.0, 5.0, -0.9),
    "angry":     (2.0, -2.0, 0.5),
    "surprised": (-5.0, -2.0, 1.0),
    "scared":    (3.0, 4.0, -0.4),
    "excited":   (-5.0, -2.5, 1.0),
    "love":      (-2.0, 0.0, 0.55),
    "curious":   (-2.0, -1.0, 0.85),
}

# gesture -> per-arm pose: (aL1, aL2, aR1, aR2, spread) angles from
# straight-down, positive = away from the body on each side; spread 0..1
# fans the fingers open
_POSES: Dict[str, Tuple[float, float, float, float, float]] = {
    "idle":        (0.10, 0.12, 0.10, 0.12, 0.25),
    "open_arms":   (0.85, 0.55, 0.85, 0.55, 1.0),
    "point_left":  (1.62, 0.05, 0.10, 0.10, 0.0),   # viewer-left arm extends
    "point_right": (0.10, 0.10, 1.62, 0.05, 0.0),
    "point_up":    (0.10, 0.10, 2.85, 0.25, 0.0),
    "think":       (0.12, 0.10, 1.35, 2.35, 0.15),
    "shrug":       (0.55, 2.10, 0.55, 2.10, 1.0),
    "wave":        (0.10, 0.12, 2.30, 0.55, 0.9),
    "facepalm":    (0.10, 0.10, 1.75, 2.35, 0.4),
    "jazz_hands":  (1.15, 1.30, 1.15, 1.30, 1.0),
    "clasp":       (0.42, -0.95, 0.42, -0.95, 0.0),
    "arms_cross":  (0.55, -1.55, 0.55, -1.55, 0.0),
    "recoil":      (1.30, 1.10, 1.30, 1.10, 1.0),
    "bow":         (0.35, 0.25, 0.35, 0.25, 0.2),
    "count":       (0.12, 0.10, 1.05, 1.95, 0.8),
}


def head_center_y(ground_y: float, s: float) -> float:
    """World-space y of the head center (camera framing hook)."""
    return ground_y - 196 * s


def _rot_ellipse(cx: float, cy: float, rx: float, ry: float,
                 ang: float, n: int = 40) -> List[Point]:
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        ex, ey = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + ex * ca - ey * sa, cy + ex * sa + ey * ca))
    return pts


def draw_alien(
    d: ImageDraw.ImageDraw,
    x: float,
    ground_y: float,
    s: float,
    emotion: str = "neutral",
    gesture: Optional[str] = None,
    act_t: float = 0.0,
    act_dur: float = 2.0,
    talking: bool = False,
    mouth: Optional[Tuple[float, float]] = None,
    gaze: Tuple[float, float] = (0.0, 0.0),   # -1..1 each axis
    t: float = 0.0,
    blink_seed: float = 0.7,
) -> Point:
    """Draw the narrator; returns the head-top anchor point."""
    head_dy, sh_drop, perk = _EMO_POSE.get(emotion, _EMO_POSE["neutral"])
    head_dy *= s
    sh_drop *= s

    e = _ease(act_t, act_dur) if gesture else 0.0
    pose = _POSES.get(gesture or "idle", _POSES["idle"])
    idle = _POSES["idle"]
    aL1 = idle[0] + (pose[0] - idle[0]) * e
    aL2 = idle[1] + (pose[1] - idle[1]) * e
    aR1 = idle[2] + (pose[2] - idle[2]) * e
    aR2 = idle[3] + (pose[3] - idle[3]) * e
    spread = idle[4] + (pose[4] - idle[4]) * e

    # animated gesture flourishes
    if gesture == "wave":
        aR2 += 0.4 * math.sin(2 * math.pi * 2.3 * act_t) * e
    elif gesture == "jazz_hands":
        wig = 0.13 * math.sin(2 * math.pi * 5.5 * act_t) * e
        aL1 += wig
        aR1 -= wig
    elif gesture == "count":
        aR2 += 0.12 * math.sin(2 * math.pi * 1.6 * act_t) * e
    elif gesture == "recoil":
        head_dy += 3 * s * e
    lean = 0.0
    if gesture == "bow":
        lean = 0.55 * e
    elif gesture == "recoil":
        lean = -0.28 * e

    breath = 1.4 * s * math.sin(2 * math.pi * t / 3.4)
    bob = 1.6 * s * math.sin(2 * math.pi * t / 2.9)

    # ---- skeleton ---------------------------------------------------------
    hip_y = ground_y - 74 * s
    sh_y = ground_y - 152 * s + sh_drop + breath * 0.5 + bob * 0.3
    bvx, bvy = math.sin(lean), -math.cos(lean)
    sh_c = (x + bvx * (hip_y - sh_y), sh_y) if lean else (x, sh_y)
    head_c = (sh_c[0] + bvx * 44 * s,
              sh_y - 44 * s + head_dy + bob * 0.5)
    hrx, hry = 38 * s, 46 * s

    lw = max(1, round(1.6 * s))

    # ---- legs & feet ------------------------------------------------------
    for side in (-1, 1):
        top = (x + side * 12 * s, hip_y)
        knee = (x + side * 14 * s, ground_y - 38 * s)
        ankle = (x + side * 15 * s, ground_y - 6 * s)
        _capsule(d, top, knee, 5.6 * s + lw, SKIN_DARK)
        _capsule(d, knee, ankle, 4.6 * s + lw, SKIN_DARK)
        _capsule(d, top, knee, 5.6 * s, SKIN)
        _capsule(d, knee, ankle, 4.6 * s, SKIN)
        _capsule(d, (ankle[0] - side * 2 * s, ground_y - 4 * s),
                 (ankle[0] + side * 12 * s, ground_y - 3 * s),
                 4.8 * s, SKIN, SKIN_DARK, lw)

    # ---- torso ------------------------------------------------------------
    def torso(extra: float, colr) -> None:
        swu, sww, swh = 21 * s + extra, 12 * s + extra, 16 * s + extra
        waist_y = (sh_c[1] + hip_y) / 2
        pts = [(sh_c[0] - swu, sh_c[1]), (sh_c[0] + swu, sh_c[1]),
               (x + sww, waist_y), (x + swh, hip_y),
               (x - swh, hip_y), (x - sww, waist_y)]
        d.polygon(pts, fill=colr)
        d.ellipse([sh_c[0] - swu, sh_c[1] - 7 * s - extra,
                   sh_c[0] + swu, sh_c[1] + 7 * s + extra], fill=colr)
        d.ellipse([x - swh, hip_y - 9 * s - extra, x + swh,
                   hip_y + 9 * s + extra], fill=colr)

    torso(lw, SKIN_DARK)
    torso(0, SKIN)
    d.ellipse([x - 11 * s, hip_y - 34 * s, x + 11 * s, hip_y + 2 * s],
              fill=BELLY)

    # ---- arms with three long fingers ------------------------------------
    A1, A2 = 44 * s, 40 * s

    def arm(side: float, a1: float, a2: float) -> Point:
        o = (sh_c[0] + side * 20 * s, sh_c[1] + 3 * s)
        el = (o[0] + side * math.sin(a1) * A1, o[1] + math.cos(a1) * A1)
        hd = (el[0] + side * math.sin(a1 + a2) * A2,
              el[1] + math.cos(a1 + a2) * A2)
        _capsule(d, o, el, 4.6 * s + lw, SKIN_DARK)
        _capsule(d, el, hd, 4.0 * s + lw, SKIN_DARK)
        _capsule(d, o, el, 4.6 * s, SKIN)
        _capsule(d, el, hd, 4.0 * s, SKIN)
        # hand: palm + three fingers fanned along the forearm direction
        fdir = math.atan2(hd[1] - el[1], side * (hd[0] - el[0]))
        d.ellipse([hd[0] - 4.6 * s - lw, hd[1] - 4.6 * s - lw,
                   hd[0] + 4.6 * s + lw, hd[1] + 4.6 * s + lw], fill=SKIN_DARK)
        d.ellipse([hd[0] - 4.6 * s, hd[1] - 4.6 * s,
                   hd[0] + 4.6 * s, hd[1] + 4.6 * s], fill=SKIN)
        fan = 0.18 + 0.5 * spread
        for fi in (-1, 0, 1):
            fa = fdir + fi * fan
            fl = (11 + 2 * (fi == 0)) * s
            tip = (hd[0] + side * math.cos(fa) * fl, hd[1] + math.sin(fa) * fl)
            _capsule(d, hd, tip, 1.9 * s + lw * 0.6, SKIN_DARK)
            _capsule(d, hd, tip, 1.9 * s, SKIN)
        return hd

    handL = arm(-1.0, aL1, aL2)
    handR = arm(1.0, aR1, aR2)

    # ---- neck -------------------------------------------------------------
    _capsule(d, (head_c[0], head_c[1] + hry * 0.75),
             (sh_c[0], sh_c[1] + 4 * s), 5.5 * s, SKIN, SKIN_DARK, lw)

    # ---- antennae (behind the head) ---------------------------------------
    for side in (-1, 1):
        bx = head_c[0] + side * 15 * s
        by = head_c[1] - hry * 0.86
        wob = math.sin(2 * math.pi * (t * (1.3 if emotion in ("excited",
                       "surprised") else 0.45) + side * 0.3))
        tipx = bx + side * (10 + 12 * (1 - perk)) * s + wob * 2.5 * s
        tipy = by - (30 * max(0.15, perk) + 6) * s + (18 * s if perk < 0 else 0)
        midx = bx + side * 4 * s
        midy = by - 18 * s * max(0.3, perk + 0.3)
        _line(d, [(bx, by), (midx, midy), (tipx, tipy)], SKIN_DARK,
              max(2, round(2.6 * s)))
        r = 4.6 * s
        d.ellipse([tipx - r - 1.5 * s, tipy - r - 1.5 * s,
                   tipx + r + 1.5 * s, tipy + r + 1.5 * s],
                  fill=_mix_c(ANTENNA_TIP, (10, 12, 16), 0.55))
        d.ellipse([tipx - r, tipy - r, tipx + r, tipy + r], fill=ANTENNA_TIP)

    # ---- head -------------------------------------------------------------
    d.ellipse([head_c[0] - hrx - lw, head_c[1] - hry - lw,
               head_c[0] + hrx + lw, head_c[1] + hry + lw], fill=SKIN_DARK)
    d.ellipse([head_c[0] - hrx, head_c[1] - hry,
               head_c[0] + hrx, head_c[1] + hry], fill=SKIN)

    _draw_alien_face(d, head_c, hrx, hry, emotion, gesture, t, talking,
                     mouth, gaze, s, blink_seed)

    # hands that touch the face render over it
    if gesture in ("think", "facepalm") and e > 0.7:
        for hd in (handR,):
            d.ellipse([hd[0] - 4.6 * s - lw, hd[1] - 4.6 * s - lw,
                       hd[0] + 4.6 * s + lw, hd[1] + 4.6 * s + lw],
                      fill=SKIN_DARK)
            d.ellipse([hd[0] - 4.6 * s, hd[1] - 4.6 * s,
                       hd[0] + 4.6 * s, hd[1] + 4.6 * s], fill=SKIN)

    return (head_c[0], head_c[1] - hry)


# eyebrow-ridge spec per emotion: (lift, inner_drop, outer_drop) in s units
_ALIEN_BROWS = {
    "neutral":   (30, 0.0, 0.0),
    "happy":     (33, 1.0, 2.0),
    "sad":       (31, -3.5, 2.5),
    "angry":     (28, 4.0, -2.0),
    "surprised": (37, 0.0, 1.0),
    "scared":    (35, -2.5, 2.0),
    "excited":   (35, 0.0, 1.5),
    "love":      (32, 1.5, 2.5),
    "curious":   (34, -1.0, 3.0),
}


def _draw_alien_face(d, head_c, hrx, hry, emotion, gesture, t, talking,
                     mouth, gaze, s, blink_seed) -> None:
    hx, hy = head_c
    gx, gy = gaze
    eye_y = hy - 4 * s
    eye_dx = 17 * s

    period = 3.3 + (blink_seed % 1.0) * 1.5
    blink01 = 1.0
    ph = (t + blink_seed) % period
    if ph < 0.14:  # eased blink: close then open
        blink01 = abs(math.cos(math.pi * ph / 0.14))
    squint = 0.0
    if emotion == "angry":
        squint = 0.30
    elif emotion == "happy":
        squint = 0.18
    elif emotion in ("surprised", "scared", "excited"):
        squint = -0.15          # wider
    openness = max(0.06, (1.0 - squint) * blink01)

    for side in (-1, 1):
        ex = hx + side * eye_dx + gx * 2.0 * s
        tilt = side * 0.42      # classic outward slant
        erx, ery = 12.5 * s, 19 * s * openness
        glow = _rot_ellipse(ex, eye_y, erx + 1.6 * s, ery + 1.6 * s, tilt)
        d.polygon(glow, fill=EYE_GLOW)
        d.polygon(_rot_ellipse(ex, eye_y, erx, ery, tilt), fill=EYE_DARK)
        if openness > 0.25:
            # galaxy sheen + gaze-following highlights
            ix = ex + gx * 4.5 * s
            iy = eye_y + gy * 5 * s
            d.polygon(_rot_ellipse(ix, iy, erx * 0.55, ery * 0.5, tilt),
                      fill=EYE_INNER)
            hlx = ix - side * 3 * s - 2 * s + gx * 1.5 * s
            hly = iy - ery * 0.35
            r1 = 3.4 * s
            d.ellipse([hlx - r1, hly - r1, hlx + r1, hly + r1], fill=HIGHLIGHT)
            r2 = 1.7 * s
            d.ellipse([hlx + 4 * s - r2, hly + 6 * s - r2,
                       hlx + 4 * s + r2, hly + 6 * s + r2], fill=HIGHLIGHT)

    # brow ridges: skin creases that carry most of the expression
    lift, inner, outer = _ALIEN_BROWS.get(emotion, _ALIEN_BROWS["neutral"])
    for side in (-1, 1):
        ex = hx + side * eye_dx
        by = eye_y - lift * s
        pts = [(ex - side * 9 * s, by + inner * s),
               (ex, by - 2 * s),
               (ex + side * 9 * s, by + outer * s)]
        _line(d, pts, SKIN_SHADE, max(2, round(2.8 * s)))

    # tiny nostrils
    for side in (-1, 1):
        d.ellipse([hx + side * 3.2 * s - 1.1 * s, hy + 16 * s - 1.1 * s,
                   hx + side * 3.2 * s + 1.1 * s, hy + 16 * s + 1.1 * s],
                  fill=SKIN_SHADE)

    # ---- mouth: viseme-driven when talking, emotional curve otherwise -----
    my = hy + 27 * s
    if talking:
        if mouth is not None:
            open01, shape01 = mouth
        else:
            open01 = abs(math.sin(2 * math.pi * 3.1 * t))
            shape01 = 0.4
        ow = max(1, round(2 * s))
        bias = -1.0 if emotion in ("happy", "excited", "love") else (
            1.0 if emotion in ("sad", "scared") else 0.0)
        if open01 < 0.09:
            _line(d, [(hx - 6.5 * s, my + bias * 2 * s),
                      (hx, my + bias * 0.4 * s),
                      (hx + 6.5 * s, my + bias * 2 * s)], SKIN_DARK, ow)
        else:
            mw = (5.5 + 6.5 * shape01) * s
            oh = (1.6 + 15.0 * open01) * s * (1.0 - 0.42 * shape01)
            d.ellipse([hx - mw, my - oh / 2, hx + mw, my + oh / 2],
                      fill=MOUTH_IN, outline=SKIN_DARK, width=ow)
            if oh > 9 * s:      # wide open: hint of a tongue
                d.chord([hx - mw * 0.6, my + oh * 0.05, hx + mw * 0.6,
                         my + oh * 0.62], 180, 360, fill=TONGUE)
        return
    mw = 9 * s
    if emotion in ("happy", "excited", "love"):
        d.arc([hx - mw, my - 6 * s, hx + mw, my + 4 * s], 15, 165,
              fill=SKIN_DARK, width=max(2, round(2.4 * s)))
    elif emotion == "sad":
        d.arc([hx - mw, my - 1 * s, hx + mw, my + 9 * s], 195, 345,
              fill=SKIN_DARK, width=max(2, round(2.4 * s)))
    elif emotion == "angry":
        _line(d, [(hx - mw * 0.75, my + 1.5 * s), (hx + mw * 0.75, my)],
              SKIN_DARK, max(2, round(2.4 * s)))
    elif emotion in ("surprised", "scared"):
        r = 4.5 * s
        d.ellipse([hx - r * 0.8, my - r, hx + r * 0.8, my + r],
                  fill=MOUTH_IN, outline=SKIN_DARK, width=max(1, round(2 * s)))
    else:
        _line(d, [(hx - 5 * s, my + 0.5 * s), (hx + 5 * s, my + 0.5 * s)],
              SKIN_DARK, max(2, round(2.2 * s)))
