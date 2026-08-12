"""Story mode pipeline: animated stick-figure stories with dialogue.

No speed-drawing here — each shot's scenery appears fully drawn, the world
moves (via the prop motion system), and actors walk, emote, gesture and speak
with lip-synced-ish mouths, speech bubbles, and per-actor TTS voices.
"""

from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

from .actor import ActorVisual, draw_actor, draw_speech_bubble
from .animator import BACKGROUND, SceneAnimator, _anim_offset, _draw_stroke_upto, parse_svg_strokes
from .assembler import build_video
from .pipeline import DEFAULT_MODEL, log
from .props import prop_svg
from .story import Story
from .voiceover import synthesize

GROUND_Y = 585
WALK_SPEED = 230.0          # px/s
AUDIO_RATE = 44100

ACTOR_COLORS = {
    "ink": (40, 48, 63),
    "blue": (57, 114, 158),
    "red": (184, 69, 60),
    "green": (47, 125, 79),
}

GESTURE_SECONDS = {"wave": 1.8, "jump": 1.1, "point_left": 1.5,
                   "point_right": 1.5, "dance": 2.4, "nod": 1.2, "shake": 1.4,
                   "clap": 2.0, "bow": 1.9, "shrug": 1.7, "facepalm": 1.9,
                   "think": 2.5, "cry": 2.7, "laugh": 2.3, "cheer": 2.1,
                   "sit": 2.8}
RUN_SPEED = 430.0           # px/s

VOICE_MAP = {
    "en": {"female": "en-US-AriaNeural", "male": "en-US-GuyNeural"},
    "tr": {"female": "tr-TR-EmelNeural", "male": "tr-TR-AhmetNeural"},
    "de": {"female": "de-DE-KatjaNeural", "male": "de-DE-ConradNeural"},
    "fr": {"female": "fr-FR-DeniseNeural", "male": "fr-FR-HenriNeural"},
    "es": {"female": "es-ES-ElviraNeural", "male": "es-ES-AlvaroNeural"},
    "it": {"female": "it-IT-ElsaNeural", "male": "it-IT-DiegoNeural"},
}


@dataclass
class TimedEvent:
    ev: object
    start: float
    dur: float
    x0: float = 0.0
    x1: float = 0.0
    wav: Optional[Path] = None
    mouth: Optional[List[Tuple[float, float]]] = None  # (open, shape) per frame


def _mouth_track(wav_path: Path, fps: int) -> List[Tuple[float, float]]:
    """Per-video-frame lip-sync track from the speech audio.

    Returns (open, shape) pairs: `open` is the normalized RMS loudness that
    drives how far the mouth opens; `shape` is the zero-crossing rate that
    separates round open vowels (low) from wide flat consonants (high).
    """
    import numpy as np

    with wave.open(str(wav_path), "rb") as w:
        rate = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    hop = max(1, int(rate / fps))
    n = max(1, len(x) // hop)
    opens, shapes = [], []
    for i in range(n):
        seg = x[i * hop:(i + 1) * hop]
        if seg.size == 0:
            break
        opens.append(float(np.sqrt(np.mean(seg * seg))))
        if seg.size > 1:
            shapes.append(float(np.mean(np.abs(np.diff(np.sign(seg))) / 2)))
        else:
            shapes.append(0.0)
    o = np.asarray(opens)
    z = np.asarray(shapes)
    ref = np.percentile(o[o > 0], 92) if (o > 0).any() else 1.0
    o = np.clip(o / max(ref, 1e-6), 0.0, 1.0)
    if o.size > 2:  # light smoothing so the mouth doesn't flicker at 30fps
        o = np.convolve(o, [0.2, 0.6, 0.2], "same")
    z = np.clip(z / 0.35, 0.0, 1.0)
    if float(o.max(initial=0.0)) < 0.05:
        # silent track (--tts none): fall back to a plausible syllable rhythm
        t = np.arange(o.size) / fps
        o = np.clip(0.5 + 0.5 * np.sin(2 * math.pi * 3.0 * t), 0, 1) * 0.8
        z = np.full_like(o, 0.4)
    return list(zip(o.tolist(), z.tolist()))


@dataclass
class ActorTrack:
    visual: ActorVisual
    x: float
    facing: float = 1.0
    emotion: str = "neutral"


def _to_std_wav(src: Path) -> None:
    """Re-encode any wav to 44100 Hz mono s16 in place."""
    ffmpeg = shutil.which("ffmpeg")
    tmp = src.with_suffix(".std.wav")
    subprocess.run([ffmpeg, "-y", "-i", str(src), "-ar", str(AUDIO_RATE),
                    "-ac", "1", "-c:a", "pcm_s16le", str(tmp)],
                   capture_output=True)
    tmp.replace(src)


def _shot_audio(path: Path, timed: List[TimedEvent], total_seconds: float) -> None:
    """Lay each say-event's wav at its start time over silence."""
    n_total = int(total_seconds * AUDIO_RATE)
    buf = bytearray(n_total * 2)
    for te in timed:
        if te.wav is None:
            continue
        with wave.open(str(te.wav), "rb") as w:
            data = w.readframes(w.getnframes())
        off = int(te.start * AUDIO_RATE) * 2
        end = min(len(buf), off + len(data))
        if off < len(buf):
            buf[off:end] = data[: end - off]
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(AUDIO_RATE)
        w.writeframes(bytes(buf))


def _resolve_actor_voice(gender: str, voice_pref: Optional[str], engine: str) -> str:
    lang = (voice_pref or "en").split("-")[0].lower()
    if voice_pref and "Neural" in voice_pref:
        return voice_pref
    m = VOICE_MAP.get(lang)
    if m:
        return m.get(gender, m["female"])
    return lang  # espeak-style language code fallback


def run_story_pipeline(
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
    workdir: Optional[Path] = None,
    keep_workdir: bool = False,
) -> Path:
    if demo:
        from .story import DEMO_STORY

        story: Story = DEMO_STORY
        log("demo mode: using the bundled story (no API calls)")
    else:
        import anthropic

        from .story import generate_story

        client = anthropic.Anthropic()
        log(f"writing story for {topic!r} with {model} ...")
        story = generate_story(client, topic, model)
    log(f'story ready: "{story.title}" — {len(story.shots)} shots, '
        f"{len(story.actors)} actors")

    tmp_created = workdir is None
    workdir = workdir or Path(tempfile.mkdtemp(prefix="speedraw_story_"))
    workdir.mkdir(parents=True, exist_ok=True)
    frames_dir = workdir / "frames"
    frames_dir.mkdir(exist_ok=True)

    sx = canvas[0] / 1280.0
    sy = canvas[1] / 720.0
    ground = GROUND_Y * sy

    try:
        tracks: Dict[str, ActorTrack] = {}
        voices: Dict[str, str] = {}
        for a in story.actors:
            tracks[a.id] = ActorTrack(
                visual=ActorVisual(color=ACTOR_COLORS.get(a.color, ACTOR_COLORS["ink"]),
                                   scale=0.92 * sy),
                x=a.start_x * sx,
                facing=1.0 if a.start_x < canvas[0] / 2 else -1.0,
            )
            voices[a.id] = _resolve_actor_voice(a.voice, voice, tts_engine)

        frame_idx = 0
        audio_files: List[Path] = []

        if title_card:
            animator = SceneAnimator(canvas, fps)
            log("rendering title card ...")
            frame_idx = animator.render_title(story.title, 2.4, frames_dir, frame_idx)
            silence = workdir / "audio_title.wav"
            _shot_audio(silence, [], frame_idx / fps)
            audio_files.append(silence)

        for si, shot in enumerate(story.shots, 1):
            # ---- plan the timeline (and synthesize speech) ----------------
            start_x = {aid: tr.x for aid, tr in tracks.items()}
            start_facing = {aid: tr.facing for aid, tr in tracks.items()}
            timed: List[TimedEvent] = []
            t = 0.6  # settle-in beat
            for ei, ev in enumerate(shot.events):
                tr = tracks.get(ev.actor)
                if tr is None:
                    continue
                te = TimedEvent(ev=ev, start=t, dur=1.0, x0=tr.x, x1=tr.x)
                if ev.action == "say":
                    wav = workdir / f"say_{si}_{ei}.wav"
                    dur = synthesize(ev.text or "...", wav, engine=tts_engine,
                                     voice=voices[ev.actor])
                    _to_std_wav(wav)
                    te.wav = wav
                    te.mouth = _mouth_track(wav, fps)
                    te.dur = dur + 0.45
                elif ev.action in ("walk", "run"):
                    speed = RUN_SPEED if ev.action == "run" else WALK_SPEED
                    te.x1 = (ev.to_x if ev.to_x is not None else tr.x / sx) * sx
                    te.dur = max(0.6, min(4.5, abs(te.x1 - te.x0) / (speed * sx)))
                    tr.x = te.x1
                    if abs(te.x1 - te.x0) > 8:
                        tr.facing = 1.0 if te.x1 > te.x0 else -1.0
                elif ev.action == "emote":
                    te.dur = 1.25
                elif ev.action == "gesture":
                    te.dur = GESTURE_SECONDS.get(ev.gesture or "wave", 1.5)
                elif ev.action == "wait":
                    te.dur = max(0.3, min(5.0, ev.seconds or 1.0))
                timed.append(te)
                t = te.start + te.dur
            shot_seconds = t + 1.0
            shot_frames = max(1, round(shot_seconds * fps))

            log(f"shot {si}/{len(story.shots)}: {len(timed)} events, "
                f"{shot_seconds:.1f}s")

            # ---- scenery: static baked once, moving parts per frame -------
            svg_parts: List[str] = []
            for p in shot.props:
                svg_parts.extend(prop_svg(p.kind, p.x, p.y, p.scale, p.motion))
            gline = (f'<path d="M 60,{GROUND_Y} C 380,{GROUND_Y - 9} '
                     f'900,{GROUND_Y + 7} 1220,{GROUND_Y - 4}" fill="none" '
                     f'stroke="#28303f" stroke-width="5"/>')
            svg = ('<svg viewBox="0 0 1280 720">' + gline + "".join(svg_parts)
                   + "</svg>")
            strokes = parse_svg_strokes(svg, canvas)
            bg = Image.new("RGB", canvas, BACKGROUND)
            bgd = ImageDraw.Draw(bg)
            moving = []
            for s in strokes:
                if s.anim is None:
                    _draw_stroke_upto(bgd, s, s.length)
                else:
                    moving.append(s)

            # ---- shot state: emotions & positions evolve over the timeline
            for f in range(shot_frames):
                tt = f / fps
                frame = bg.copy()
                d = ImageDraw.Draw(frame)

                transforms = {}
                for s in moving:
                    key = id(s.anim)
                    if key not in transforms:
                        transforms[key] = _anim_offset(s.anim, tt)
                    _draw_stroke_upto(d, s, s.length, transform=transforms[key])

                # actor states at time tt: replay the timeline up to this frame
                aids = list(tracks.keys())
                states = {
                    aid: {
                        "x": start_x[aid], "activity": "idle", "act_t": 0.0,
                        "act_dur": 1.5, "talking": False, "mouth": None,
                        "emotion": tracks[aid].emotion,
                        "facing": start_facing[aid], "bubble": None,
                    }
                    for aid in aids
                }
                for te in timed:
                    ev = te.ev
                    st = states.get(ev.actor)
                    if st is None:
                        continue
                    if ev.action in ("walk", "run") and tt >= te.start:
                        if tt >= te.start + te.dur:
                            st["x"] = te.x1
                        else:
                            k = (tt - te.start) / te.dur
                            st["x"] = te.x0 + (te.x1 - te.x0) * k
                        if abs(te.x1 - te.x0) > 8:
                            st["facing"] = 1.0 if te.x1 > te.x0 else -1.0
                    if ev.action in ("emote", "say") and tt >= te.start and ev.emotion:
                        st["emotion"] = ev.emotion
                    if te.start <= tt < te.start + te.dur:
                        if ev.action in ("walk", "run"):
                            st["activity"], st["act_t"] = ev.action, tt - te.start
                            st["act_dur"] = te.dur
                        elif ev.action == "gesture":
                            st["activity"] = ev.gesture or "wave"
                            st["act_t"] = tt - te.start
                            st["act_dur"] = te.dur
                        elif ev.action == "say":
                            fi = int((tt - te.start) * fps)
                            if te.mouth and 0 <= fi < len(te.mouth):
                                st["mouth"] = te.mouth[fi]
                            st["talking"] = tt < te.start + te.dur - 0.35
                            st["bubble"] = (ev.text, tt - te.start)

                bubbles = []
                order = sorted(aids, key=lambda a: states[a]["x"])
                for aid in order:
                    st = states[aid]
                    if st["talking"] and len(aids) > 1:
                        other = next(a for a in aids if a != aid)
                        dx = states[other]["x"] - st["x"]
                        if abs(dx) > 60:
                            st["facing"] = 1.0 if dx > 0 else -1.0
                    anchor = draw_actor(
                        d, st["x"], ground, tracks[aid].visual,
                        facing=st["facing"], emotion=st["emotion"], t=tt,
                        activity=st["activity"], act_t=st["act_t"],
                        act_dur=st["act_dur"], talking=st["talking"],
                        mouth=st["mouth"],
                    )
                    if st["bubble"]:
                        bubbles.append((anchor, st["bubble"]))

                for anchor, (text, age) in bubbles:
                    draw_speech_bubble(frame, anchor, text or "", canvas,
                                       scale=sy, age=age)

                frame.save(frames_dir / f"{frame_idx + f:06d}.png")

            # persist end-of-shot state
            for te in timed:
                if te.ev.action in ("emote", "say") and te.ev.emotion:
                    tracks[te.ev.actor].emotion = te.ev.emotion
            frame_idx += shot_frames

            shot_wav = workdir / f"shot_{si}.wav"
            _shot_audio(shot_wav, timed, shot_frames / fps)
            audio_files.append(shot_wav)

        log(f"encoding video ({frame_idx} frames @ {fps}fps) ...")
        build_video(frames_dir, audio_files, output, fps, workdir)
        log(f"done: {output}")
        return output
    finally:
        if tmp_created and not keep_workdir:
            shutil.rmtree(workdir, ignore_errors=True)
        elif keep_workdir:
            log(f"working files kept in {workdir}")
