"""End-to-end pipeline: topic -> script -> drawings -> voiceover -> video."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from .animator import SceneAnimator
from .assembler import build_video
from .script_gen import VideoScript
from .voiceover import synthesize, _write_silence

DEFAULT_MODEL = "claude-opus-5"
TITLE_SECONDS = 2.6
END_HOLD_SECONDS = 1.5


def log(msg: str) -> None:
    print(f"[speedraw] {msg}", file=sys.stderr, flush=True)


def run_pipeline(
    topic: str,
    output: Path,
    *,
    num_scenes: int = 4,
    model: str = DEFAULT_MODEL,
    tts_engine: str = "espeak",
    voice: str = "en-US",
    canvas: Tuple[int, int] = (1280, 720),
    fps: int = 30,
    demo: bool = False,
    title_card: bool = True,
    workdir: Optional[Path] = None,
    keep_workdir: bool = False,
) -> Path:
    if demo:
        from .demo_content import DEMO_SCRIPT, DEMO_SVGS

        script: VideoScript = DEMO_SCRIPT
        svgs = list(DEMO_SVGS)
        log("demo mode: using bundled script and drawings (no API calls)")
    else:
        import anthropic

        from .script_gen import generate_script
        from .svg_gen import generate_scene_svg

        client = anthropic.Anthropic()
        log(f"generating script for {topic!r} with {model} ...")
        script = generate_script(client, topic, num_scenes, model)
        log(f"script ready: \"{script.title}\" — {len(script.scenes)} scenes")
        svgs = []
        for i, scene in enumerate(script.scenes, 1):
            log(f"drawing scene {i}/{len(script.scenes)}: {scene.label} ...")
            svgs.append(
                generate_scene_svg(client, scene.visual_description, scene.label, model)
            )

    tmp_created = workdir is None
    workdir = workdir or Path(tempfile.mkdtemp(prefix="speedraw_"))
    workdir.mkdir(parents=True, exist_ok=True)
    frames_dir = workdir / "frames"
    frames_dir.mkdir(exist_ok=True)

    try:
        animator = SceneAnimator(canvas, fps)
        audio_files = []
        frame_idx = 0

        if title_card:
            log("rendering title card ...")
            frame_idx = animator.render_title(
                script.title, TITLE_SECONDS, frames_dir, frame_idx
            )
            silence = workdir / "audio_title.wav"
            # audio must track frame count exactly to stay in sync
            _write_silence(silence, (frame_idx) / fps)
            audio_files.append(silence)

        for i, (scene, svg) in enumerate(zip(script.scenes, svgs), 1):
            wav = workdir / f"audio_{i:02d}.wav"
            duration = synthesize(
                scene.narration, wav, engine=tts_engine, voice=voice
            )
            if i == len(script.scenes):
                duration += END_HOLD_SECONDS
            log(f"animating scene {i}/{len(script.scenes)} "
                f"({duration:.1f}s): {scene.label}")
            start = frame_idx
            frame_idx = animator.render_scene(svg, duration, frames_dir, frame_idx)
            # pad/trim audio to the exact rendered frame span
            rendered = (frame_idx - start) / fps
            (workdir / f"svg_{i:02d}.svg").write_text(svg, encoding="utf-8")
            audio_files.append(wav)
            _pad_wav_to(wav, rendered)

        log(f"encoding video ({frame_idx} frames @ {fps}fps) ...")
        build_video(frames_dir, audio_files, output, fps, workdir)
        log(f"done: {output}")
        return output
    finally:
        if tmp_created and not keep_workdir:
            shutil.rmtree(workdir, ignore_errors=True)
        elif keep_workdir:
            log(f"working files kept in {workdir}")


def _pad_wav_to(path: Path, seconds: float) -> None:
    """Pad (or trim) a mono 16-bit WAV to exactly `seconds`."""
    import wave

    with wave.open(str(path), "rb") as w:
        params = w.getparams()
        frames = w.readframes(w.getnframes())
    target = int(seconds * params.framerate) * params.sampwidth * params.nchannels
    if len(frames) < target:
        frames = frames + b"\x00" * (target - len(frames))
    else:
        frames = frames[:target]
    with wave.open(str(path), "wb") as w:
        w.setparams(params)
        w.writeframes(frames)
