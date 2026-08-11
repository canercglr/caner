"""Voiceover generation. Default engine: espeak-ng (offline). 'none' = silence."""

from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path


class VoiceoverError(RuntimeError):
    pass


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def _write_silence(path: Path, seconds: float, rate: int = 22050) -> None:
    n = int(seconds * rate)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * n)


def estimate_speech_seconds(text: str) -> float:
    """Rough spoken duration used when no TTS engine renders audio."""
    words = max(1, len(text.split()))
    return max(3.0, words / 2.6)


def synthesize(
    text: str,
    out_wav: Path,
    engine: str = "espeak",
    voice: str = "en-US",
    speed_wpm: int = 160,
) -> float:
    """Create a WAV for `text`, returning its duration in seconds."""
    if engine == "none":
        dur = estimate_speech_seconds(text)
        _write_silence(out_wav, dur)
        return dur

    if engine == "espeak":
        exe = shutil.which("espeak-ng") or shutil.which("espeak")
        if not exe:
            raise VoiceoverError(
                "espeak-ng not found. Install it (e.g. `apt-get install espeak-ng`) "
                "or run with --tts none."
            )
        result = subprocess.run(
            [exe, "-v", voice, "-s", str(speed_wpm), "-p", "50",
             "-w", str(out_wav), text],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not out_wav.exists():
            raise VoiceoverError(f"espeak-ng failed: {result.stderr.strip()}")
        return wav_duration(out_wav)

    raise VoiceoverError(f"Unknown TTS engine: {engine!r} (use 'espeak' or 'none')")
