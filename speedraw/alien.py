"""The alien narrator: thick white line art acting on a black stage.

Frontal pose, built for close-up storytelling: huge eyes with gaze, squint
and blinks; emotive antennae; brow ridges; a viseme-driven mouth; long
three-fingered hands. While it talks the hands gesticulate continuously,
driven by the loudness of the narration (``emphasis``), so the limbs move
WITH the words — and named gestures land on top at the beats.

All geometry hangs off ``s`` so the camera can redraw the figure at any
zoom and stay razor sharp.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from PIL import ImageDraw

from .actor import _ease, _line, _smooth

Point = Tuple[float, float]

# ---- monochrome palette ----------------------------------------------------
LINE = (243, 246, 250)            # the white ink everything is drawn with
CORE = (7, 9, 13)                 # matches the stage: interiors stay black

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
_POSES: Dict[str, Tuple[float, float, float, float, float]] = {
    "idle":        (0.10, 0.12, 0.10, 0.12, 0.25),
    # conversational base while talking: forearms up, palms open to camera
    "conv":        (0.44, -1.05, 0.44, -1.20, 0.55),
    "open_arms":   (0.85, 0.55, 0.85, 0.55, 1.0),
    "point_left":  (1.62, 0.05, 0.10, 0.10, 0.0),
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


def head_extent(s: float) -> float:
    """Distance from head center to the top of the antennae (framing)."""
    return 92 * s


def _rot_ellipse(cx: float, cy: float, rx: float, ry: float,
                 ang: float, n: int = 44) -> List[Point]:
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        ex, ey = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + ex * ca - ey * sa, cy + ex * sa + ey * ca))
    return pts


def _ring(d: ImageDraw.ImageDraw, cx, cy, rx, ry, w) -> None:
    """White ellipse outline with a black core (line-art shape)."""
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=LINE)
    d.ellipse([cx - rx + w, cy - ry + w, cx + rx - w, cy + ry - w], fill=CORE)


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
    emphasis: float = 0.0,     # 0..1 narration loudness right now
    blink_seed: float = 0.7,
) -> Point:
    """Draw the narrator; returns the head-top anchor point."""
    head_dy, sh_drop, perk = _EMO_POSE.get(emotion, _EMO_POSE["neutral"])
    head_dy *= s
    sh_drop *= s

    e = _ease(act_t, act_dur) if gesture else 0.0
    pose = _POSES.get(gesture or "idle", _POSES["idle"])
    # while talking the resting pose is conversational: hands up, moving
    base = _POSES["conv"] if talking else _POSES["idle"]
    aL1 = base[0] + (pose[0] - base[0]) * e
    aL2 = base[1] + (pose[1] - base[1]) * e
    aR1 = base[2] + (pose[2] - base[2]) * e
    aR2 = base[3] + (pose[3] - base[3]) * e
    spread = base[4] + (pose[4] - base[4]) * e

    # speech-driven gesticulation: loud words push the hands outward and
    # bounce the forearms, alternating arms so it never looks mirrored
    if talking:
        conv_w = 1.0 - e            # fades while a named gesture holds
        beatL = math.sin(2 * math.pi * 1.9 * t)
        beatR = math.sin(2 * math.pi * 2.3 * t + 1.9)
        amp = (0.10 + 0.55 * emphasis) * conv_w
        aL1 += amp * 0.35 * beatL
        aL2 += amp * beatL
        aR1 += amp * 0.35 * beatR
        aR2 += amp * beatR
        spread = min(1.0, spread + 0.5 * emphasis * conv_w)
        head_dy -= 2.6 * s * emphasis          # emphasis nod
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
    lean += 0.03 * emphasis * math.sin(2 * math.pi * 0.9 * t)

    breath = 1.4 * s * math.sin(2 * math.pi * t / 3.4)
    bob = 1.6 * s * math.sin(2 * math.pi * t / 2.9)
    sway = 3.0 * s * math.sin(2 * math.pi * t / 5.7)   # weight shift

    # ---- skeleton ---------------------------------------------------------
    hip_y = ground_y - 74 * s
    hx0 = x + sway * 0.4
    sh_y = ground_y - 152 * s + sh_drop + breath * 0.5 + bob * 0.3
    sh_c = (hx0 + math.sin(lean) * (hip_y - sh_y) + sway * 0.3, sh_y)
    head_c = (sh_c[0] + math.sin(lean) * 44 * s + sway * 0.25,
              sh_y - 44 * s + head_dy + bob * 0.5)
    hrx, hry = 38 * s, 46 * s

    W = max(2, round(4.6 * s))          # the thick white line weight
    Wt = max(2, round(3.6 * s))         # thinner accents

    # ---- legs & feet ------------------------------------------------------
    for side in (-1, 1):
        top = (hx0 + side * 12 * s, hip_y)
        knee = (hx0 + side * 14 * s + sway * 0.2 * side, ground_y - 38 * s)
        ankle = (x + side * 15 * s, ground_y - 6 * s)
        _line(d, [top, knee, ankle], LINE, W)
        _line(d, [(ankle[0] - side * 3 * s, ground_y - 3 * s),
                  (ankle[0] + side * 12 * s, ground_y - 2 * s)], LINE, W)

    # ---- torso: slim outlined vessel --------------------------------------
    swu, sww = 21 * s, 15 * s
    waist_y = (sh_c[1] + hip_y) / 2
    outline = [(sh_c[0] - swu, sh_c[1] - 4 * s),
               (sh_c[0] + swu, sh_c[1] - 4 * s),
               (hx0 + sww * 0.75, waist_y),
               (hx0 + sww, hip_y + 6 * s),
               (hx0 - sww, hip_y + 6 * s),
               (hx0 - sww * 0.75, waist_y)]
    d.polygon(outline, fill=LINE)
    inner = [(sh_c[0] - swu + W, sh_c[1] - 4 * s + W),
             (sh_c[0] + swu - W, sh_c[1] - 4 * s + W),
             (hx0 + (sww * 0.75 - W), waist_y),
             (hx0 + sww - W, hip_y + 6 * s - W),
             (hx0 - sww + W, hip_y + 6 * s - W),
             (hx0 - (sww * 0.75 - W), waist_y)]
    d.polygon(inner, fill=CORE)

    # ---- arms with three long fingers ------------------------------------
    A1, A2 = 44 * s, 40 * s

    def arm(side: float, a1: float, a2: float) -> Point:
        o = (sh_c[0] + side * 19 * s, sh_c[1] + 2 * s)
        el = (o[0] + side * math.sin(a1) * A1, o[1] + math.cos(a1) * A1)
        hd = (el[0] + side * math.sin(a1 + a2) * A2,
              el[1] + math.cos(a1 + a2) * A2)
        _line(d, [o, el, hd], LINE, W)
        # hand: three fingers fanned along the forearm direction
        fdir = math.atan2(hd[1] - el[1], side * (hd[0] - el[0]))
        fan = 0.20 + 0.5 * spread
        for fi in (-1, 0, 1):
            fa = fdir + fi * fan
            fl = (12 + 2.5 * (fi == 0)) * s
            tip = (hd[0] + side * math.cos(fa) * fl, hd[1] + math.sin(fa) * fl)
            _line(d, [hd, tip], LINE, Wt)
        return hd

    handL = arm(-1.0, aL1, aL2)
    handR = arm(1.0, aR1, aR2)

    # ---- neck -------------------------------------------------------------
    _line(d, [(head_c[0], head_c[1] + hry * 0.8), (sh_c[0], sh_c[1] + 2 * s)],
          LINE, W)

    # ---- antennae ---------------------------------------------------------
    for side in (-1, 1):
        bx = head_c[0] + side * 15 * s
        by = head_c[1] - hry * 0.86
        wig_f = 1.3 if (emotion in ("excited", "surprised")) else 0.45
        wob = math.sin(2 * math.pi * (t * wig_f + side * 0.3)) * (1 + emphasis)
        tipx = bx + side * (10 + 12 * (1 - perk)) * s + wob * 2.5 * s
        tipy = by - (30 * max(0.15, perk) + 6) * s + (18 * s if perk < 0 else 0)
        midx = bx + side * 4 * s
        midy = by - 18 * s * max(0.3, perk + 0.3)
        _line(d, [(bx, by), (midx, midy), (tipx, tipy)], LINE, Wt)
        r = 4.4 * s
        _ring(d, tipx, tipy, r, r, max(2, round(2.2 * s)))

    # ---- head: thick white ring, black core -------------------------------
    _ring_w = max(2, round(5.2 * s))
    d.ellipse([head_c[0] - hrx, head_c[1] - hry,
               head_c[0] + hrx, head_c[1] + hry], fill=LINE)
    d.ellipse([head_c[0] - hrx + _ring_w, head_c[1] - hry + _ring_w,
               head_c[0] + hrx - _ring_w, head_c[1] + hry - _ring_w],
              fill=CORE)

    _draw_alien_face(d, head_c, hrx, hry, emotion, t, talking, mouth, gaze,
                     s, blink_seed)

    # hands that touch the face render over it
    if gesture in ("think", "facepalm") and e > 0.7:
        hd = handR
        d.ellipse([hd[0] - 5 * s, hd[1] - 5 * s, hd[0] + 5 * s, hd[1] + 5 * s],
                  fill=CORE, outline=LINE, width=Wt)

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


def _draw_alien_face(d, head_c, hrx, hry, emotion, t, talking, mouth, gaze,
                     s, blink_seed) -> None:
    hx, hy = head_c
    gx, gy = gaze
    eye_y = hy - 4 * s
    eye_dx = 17 * s
    Wt = max(2, round(3.2 * s))

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
        if openness <= 0.12:    # blink: a white line
            _line(d, [(ex - erx * 0.8, eye_y + side * 0),
                      (ex + erx * 0.8, eye_y)], LINE, Wt)
            continue
        # solid white almond, black pupil follows the gaze, white catch
        d.polygon(_rot_ellipse(ex, eye_y, erx, ery, tilt), fill=LINE)
        px = ex + gx * 4.5 * s
        py = eye_y + gy * 5 * s + 0.5 * s
        d.polygon(_rot_ellipse(px, py, erx * 0.42, ery * 0.5, tilt), fill=CORE)
        r1 = 1.9 * s
        d.ellipse([px - side * 2 * s - r1, py - ery * 0.2 - r1,
                   px - side * 2 * s + r1, py - ery * 0.2 + r1], fill=LINE)

    # brow ridges carry most of the expression
    lift, inner, outer = _ALIEN_BROWS.get(emotion, _ALIEN_BROWS["neutral"])
    for side in (-1, 1):
        ex = hx + side * eye_dx
        by = eye_y - lift * s
        pts = [(ex - side * 9 * s, by + inner * s),
               (ex, by - 2 * s),
               (ex + side * 9 * s, by + outer * s)]
        _line(d, pts, LINE, Wt)

    # tiny nostrils
    for side in (-1, 1):
        d.ellipse([hx + side * 3.2 * s - 1.2 * s, hy + 16 * s - 1.2 * s,
                   hx + side * 3.2 * s + 1.2 * s, hy + 16 * s + 1.2 * s],
                  fill=LINE)

    # ---- mouth: viseme-driven when talking, emotional curve otherwise -----
    my = hy + 27 * s
    if talking:
        if mouth is not None:
            open01, shape01 = mouth
        else:
            open01 = abs(math.sin(2 * math.pi * 3.1 * t))
            shape01 = 0.4
        bias = -1.0 if emotion in ("happy", "excited", "love") else (
            1.0 if emotion in ("sad", "scared") else 0.0)
        if open01 < 0.09:
            _line(d, [(hx - 6.5 * s, my + bias * 2 * s),
                      (hx, my + bias * 0.4 * s),
                      (hx + 6.5 * s, my + bias * 2 * s)], LINE, Wt)
        else:
            mw = (5.5 + 6.5 * shape01) * s
            oh = (1.6 + 15.0 * open01) * s * (1.0 - 0.42 * shape01)
            d.ellipse([hx - mw, my - oh / 2, hx + mw, my + oh / 2],
                      fill=CORE, outline=LINE, width=Wt)
            if oh > 9 * s:      # wide open: a hint of tongue, in line art
                d.arc([hx - mw * 0.55, my + oh * 0.02, hx + mw * 0.55,
                       my + oh * 0.6], 200, 340, fill=LINE,
                      width=max(1, round(2 * s)))
        return
    mw = 9 * s
    if emotion in ("happy", "excited", "love"):
        d.arc([hx - mw, my - 6 * s, hx + mw, my + 4 * s], 15, 165,
              fill=LINE, width=Wt)
    elif emotion == "sad":
        d.arc([hx - mw, my - 1 * s, hx + mw, my + 9 * s], 195, 345,
              fill=LINE, width=Wt)
    elif emotion == "angry":
        _line(d, [(hx - mw * 0.75, my + 1.5 * s), (hx + mw * 0.75, my)],
              LINE, Wt)
    elif emotion in ("surprised", "scared"):
        r = 4.5 * s
        _ring(d, hx, my, r * 0.8, r, max(1, round(2 * s)))
    else:
        _line(d, [(hx - 5 * s, my + 0.5 * s), (hx + 5 * s, my + 0.5 * s)],
              LINE, Wt)
