"""Alien narrator pipeline: one acted monologue on a black stage.

The figure is redrawn from vectors every frame at the camera's exact zoom,
so closeups stay razor sharp — no crop-and-upscale. Camera framing glides
between wide / medium / closeup per beat with a gentle handheld drift;
speech is lip-synced from the audio envelope plus letter-level visemes,
and the narrator's voice is pitch-shifted up for an alien timbre.
"""

from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

from .alien import draw_alien, head_center_y, head_extent
from .alien_story import AlienStory
from .assembler import build_video
from .pipeline import DEFAULT_MODEL, log
from .story_pipeline import AUDIO_RATE, _mouth_track, _shot_audio, _to_std_wav, TimedEvent
from .textcard import _TITLE_FONTS, _load_font
from .voiceover import synthesize

BG = (7, 9, 13)                 # matches alien.CORE — pure monochrome stage
STAGE_GLOW = (24, 26, 30)
GROUND_GLOW = (18, 20, 23)
STAR = (105, 110, 120)
TITLE_INK = (232, 236, 240)

GROUND_W = 620.0            # world ground line y
ALIEN_X = 640.0
ALIEN_S = 1.6               # world scale: ~370px tall in the wide framing
SS = 2                      # supersample factor

# stars fixed in world space (x, y, r, phase); drawn with 0.5x parallax
_STARS = [(97 * i % 1280, (211 * i * i + 60 * i) % 400 + 20,
           1.0 + (i % 3) * 0.7, i * 0.77) for i in range(1, 42)]


@dataclass
class BeatTrack:
    beat: object
    start: float
    dur: float
    wav: Optional[Path] = None
    mouth: Optional[List[Tuple[float, float]]] = None


def _alienize_voice(wav_path: Path, factor: float = 1.16) -> None:
    """Pitch the narration up without changing duration (alien timbre)."""
    ffmpeg = shutil.which("ffmpeg")
    tmp = wav_path.with_suffix(".alien.wav")
    subprocess.run(
        [ffmpeg, "-y", "-i", str(wav_path),
         "-af", f"asetrate={AUDIO_RATE * factor:.0f},"
                f"atempo={1 / factor:.6f},aresample={AUDIO_RATE}",
         "-ar", str(AUDIO_RATE), "-ac", "1", "-c:a", "pcm_s16le", str(tmp)],
        capture_output=True)
    if tmp.exists() and tmp.stat().st_size > 44:
        tmp.replace(wav_path)


@lru_cache(maxsize=1)
def _radial_base(n: int = 384) -> Image.Image:
    """One soft radial falloff, resized per use (smooth at any zoom)."""
    m = Image.new("L", (n, n), 0)
    px = m.load()
    c = (n - 1) / 2
    for yy in range(n):
        for xx in range(n):
            r = math.hypot((xx - c) / c, (yy - c) / c)
            if r < 1.0:
                k = 1.0 - r
                px[xx, yy] = int(255 * k * k)
    return m


def _radial(w: int, h: int, alpha: int) -> Image.Image:
    m = _radial_base().resize((max(2, w), max(2, h)))
    if alpha >= 255:
        return m
    return m.point(lambda v: v * alpha // 255)


def _stage(canvas: Tuple[int, int], cam: Tuple[float, float, float],
           t: float) -> Image.Image:
    """Black stage: starfield (0.5x parallax), spotlight cone, floor glow."""
    cw, ch = canvas
    kx, ky = cw / 1280.0, ch / 720.0
    cx, cy, z = cam
    frame = Image.new("RGB", canvas, BG)
    d = ImageDraw.Draw(frame)

    def w2s(wx: float, wy: float, par: float = 1.0):
        zp = 1.0 + (z - 1.0) * par
        cxp = 640 + (cx - 640) * par
        cyp = 360 + (cy - 360) * par
        return (cw / 2 + (wx - cxp) * zp * kx,
                ch / 2 + (wy - cyp) * zp * ky)

    for sxw, syw, r, phs in _STARS:
        px, py = w2s(sxw, syw, 0.5)
        if -4 < px < cw + 4 and -4 < py < ch + 4:
            tw = 0.55 + 0.45 * math.sin(2 * math.pi * (t * 0.13 + phs))
            col = tuple(int(c * tw) for c in STAR)
            rr = r * (1.0 + (z - 1.0) * 0.25)
            d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=col)

    # spotlight pool centered on the alien, floor glow at its feet
    ax, ay = w2s(ALIEN_X, head_center_y(GROUND_W, ALIEN_S) + 60)
    sw, sh = int(860 * z * kx), int(780 * z * ky)
    spot = _radial(sw, sh, 255)
    lay = Image.new("RGB", spot.size, STAGE_GLOW)
    frame.paste(lay, (int(ax - sw / 2), int(ay - sh / 2)), spot)
    gx, gy = w2s(ALIEN_X, GROUND_W)
    gw, gh = int(600 * z * kx), int(92 * z * ky)
    gm = _radial(gw, gh, 210)
    glay = Image.new("RGB", gm.size, GROUND_GLOW)
    frame.paste(glay, (int(gx - gw / 2), int(gy - gh / 2)), gm)
    return frame


# framing -> (zoom, world focus y offset from head center; 0 = head)
def _framing_target(kind: str, prog: float) -> Tuple[float, float]:
    head = head_center_y(GROUND_W, ALIEN_S)
    mid = head * 0.45 + GROUND_W * 0.55
    if kind == "wide":
        return 1.0, (head + GROUND_W) / 2 - 40
    if kind == "closeup":
        return 2.5, head + 16
    if kind == "push_in":
        return 1.5 + 0.85 * prog, head + 30 - 16 * prog
    if kind == "pull_back":
        return 2.3 - 1.3 * prog, head + 14 + 56 * prog
    return 1.8, mid          # medium


def _head_safe_cy(cy: float, z: float) -> float:
    """Clamp the camera so the head AND antennae always stay in frame."""
    top = head_center_y(GROUND_W, ALIEN_S) - head_extent(ALIEN_S)
    return min(cy, top + (360.0 - 14.0) / max(z, 1e-6))


_GAZE_FOR_GESTURE = {"point_left": (-0.8, -0.1), "point_right": (0.8, -0.1),
                     "point_up": (0.3, -0.9), "think": (0.55, -0.6),
                     "facepalm": (0.0, 0.6), "bow": (0.0, 0.5)}


def run_alien_pipeline(
    topic: str,
    output: Path,
    *,
    model: str = DEFAULT_MODEL,
    tts_engine: str = "auto",
    voice: Optional[str] = None,
    canvas: Tuple[int, int] = (1280, 720),
    fps: int = 30,
    demo: bool = False,
    title_card: bool = True,
    music: bool = True,
    music_volume: float = 0.16,
    workdir: Optional[Path] = None,
    keep_workdir: bool = False,
) -> Path:
    if demo:
        from .alien_story import DEMO_ALIEN_STORY

        story: AlienStory = DEMO_ALIEN_STORY
        log("demo mode: using the bundled alien monologue (no API calls)")
    else:
        import anthropic

        from .alien_story import generate_alien_story

        client = anthropic.Anthropic()
        log(f"writing alien monologue for {topic!r} with {model} ...")
        story = generate_alien_story(client, topic, model)
    log(f'monologue ready: "{story.title}" — {len(story.beats)} beats')

    tmp_created = workdir is None
    workdir = workdir or Path(tempfile.mkdtemp(prefix="speedraw_alien_"))
    workdir.mkdir(parents=True, exist_ok=True)
    frames_dir = workdir / "frames"
    frames_dir.mkdir(exist_ok=True)

    cw, ch = canvas
    ky = ch / 720.0

    try:
        # ---- synthesize narration per beat, alienize, lip-sync ------------
        from .voiceover import resolve_edge_voice

        narr_voice = voice or "en"
        tracks: List[BeatTrack] = []
        t0 = 2.2 if title_card else 0.9
        t = t0
        for bi, beat in enumerate(story.beats):
            wav = workdir / f"beat_{bi:02d}.wav"
            words = workdir / f"beat_{bi:02d}.words.json"
            dur = synthesize(beat.text, wav, engine=tts_engine,
                             voice=narr_voice, emotion=beat.emotion,
                             words_out=words)
            _to_std_wav(wav)
            _alienize_voice(wav)
            bt = BeatTrack(beat=beat, start=t, dur=dur + 0.55, wav=wav)
            bt.mouth = _mouth_track(wav, fps, words)
            tracks.append(bt)
            t += bt.dur
        total_seconds = t + 1.8
        total_frames = int(round(total_seconds * fps))
        log(f"performance: {total_seconds:.1f}s, {total_frames} frames")

        # ---- title overlay -------------------------------------------------
        title_font = _load_font(max(28, round(58 * ky)), _TITLE_FONTS)

        # ---- render --------------------------------------------------------
        head_y = head_center_y(GROUND_W, ALIEN_S)
        cam = [640.0, (head_y + GROUND_W) / 2, 1.12]
        energy = 0.0            # smoothed narration loudness (drives limbs)
        for f in range(total_frames):
            tt = f / fps

            # current beat (if any)
            cur: Optional[BeatTrack] = None
            prog = 0.0
            for bt in tracks:
                if bt.start <= tt < bt.start + bt.dur:
                    cur = bt
                    prog = (tt - bt.start) / bt.dur
                    break

            if cur is not None:
                tz, tfy = _framing_target(cur.beat.camera, prog)
            elif tt < t0:       # intro: settle into a medium shot
                tz, tfy = _framing_target("medium", 0.0)
            else:               # outro: drift wide
                tz, tfy = _framing_target("wide", 1.0)

            # handheld drift + glide
            tcx = 640 + 7 * math.sin(2 * math.pi * tt * 0.037)
            tcy = tfy + 5 * math.sin(2 * math.pi * tt * 0.049)
            k = min(1.0, 2.6 / fps)
            cam[0] += (tcx - cam[0]) * k
            cam[1] += (tcy - cam[1]) * k
            cam[2] += (tz - cam[2]) * k
            cam[1] = _head_safe_cy(cam[1], cam[2])
            cx, cy, z = cam

            frame = _stage(canvas, (cx, cy, z), tt)

            # acting state
            emotion = "neutral"
            gesture = None
            act_t = act_dur = 1.0
            talking = False
            mo = None
            if cur is not None:
                emotion = cur.beat.emotion
                g1 = cur.beat.gesture
                g2 = getattr(cur.beat, "gesture2", "none") or "none"
                bt_t = tt - cur.start
                if g2 != "none":
                    # two acted gestures: one per half of the beat
                    half = cur.dur * 0.5
                    if bt_t < half:
                        gesture = None if g1 == "none" else g1
                        act_t, act_dur = bt_t, half
                    else:
                        gesture = g2
                        act_t, act_dur = bt_t - half, cur.dur - half
                elif g1 != "none":
                    gesture = g1
                    act_t, act_dur = bt_t, cur.dur
                talking = tt < cur.start + cur.dur - 0.4
                fi = int(bt_t * fps)
                if cur.mouth and 0 <= fi < len(cur.mouth):
                    mo = cur.mouth[fi]
            elif tt < t0:
                emotion = "happy"

            # smoothed loudness: fast attack, slow decay — the limbs and
            # head ride this so movement follows the words
            cur_open = mo[0] if (mo and talking) else 0.0
            energy = max(energy * 0.86, min(1.0, cur_open * 1.25))

            gz = _GAZE_FOR_GESTURE.get(gesture or "", None)
            if gz is None:
                gz = (0.30 * math.sin(2 * math.pi * tt * 0.043),
                      0.18 * math.sin(2 * math.pi * tt * 0.031 + 1.3))

            # alien drawn at the camera's exact zoom: always sharp
            px = cw / 2 + (ALIEN_X - cx) * z * (cw / 1280.0)
            pg = ch / 2 + (GROUND_W - cy) * z * ky
            layer = Image.new("RGBA", (cw * SS, ch * SS), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            draw_alien(ld, px * SS, pg * SS, ALIEN_S * z * ky * SS,
                       emotion=emotion, gesture=gesture, act_t=act_t,
                       act_dur=act_dur, talking=talking, mouth=mo,
                       gaze=gz, t=tt, emphasis=energy)
            layer = layer.resize(canvas, Image.LANCZOS)
            frame.paste(layer, (0, 0), layer)

            # title fade in/out over the intro
            if title_card and tt < t0:
                a = min(1.0, tt / 0.6) * min(1.0, max(0.0, (t0 - tt) / 0.6))
                if a > 0.01:
                    ov = Image.new("RGBA", canvas, (0, 0, 0, 0))
                    od = ImageDraw.Draw(ov)
                    tw_ = od.textlength(story.title, font=title_font)
                    od.text(((cw - tw_) / 2, ch * 0.10), story.title,
                            font=title_font,
                            fill=TITLE_INK + (int(255 * a),))
                    frame = Image.alpha_composite(
                        frame.convert("RGBA"), ov).convert("RGB")

            # gentle fade to black at the very end
            if f > total_frames - int(1.0 * fps):
                a = (total_frames - f) / (1.0 * fps)
                frame = Image.eval(frame, lambda v: int(v * a)) if a < 1 else frame

            frame.save(frames_dir / f"{f:06d}.png")
            if f % (fps * 8) == 0:
                log(f"rendered {f}/{total_frames} frames")

        # ---- audio + music -------------------------------------------------
        full_wav = workdir / "narration.wav"
        _shot_audio(full_wav, tracks, total_frames / fps)

        music_wav = None
        if music:
            from .music import compose_music

            log("composing background music ...")
            music_wav = compose_music(total_frames / fps, workdir / "music.wav")

        log(f"encoding video ({total_frames} frames @ {fps}fps) ...")
        build_video(frames_dir, [full_wav], output, fps, workdir,
                    music=music_wav, music_volume=music_volume)
        log(f"done: {output}")
        return output
    finally:
        if tmp_created and not keep_workdir:
            shutil.rmtree(workdir, ignore_errors=True)
        elif keep_workdir:
            log(f"working files kept in {workdir}")
