"""Voiceover generation.

Engines:
- ``edge``   — Microsoft Edge neural voices via edge-tts (natural, needs network)
- ``espeak`` — espeak-ng (offline, robotic but dependable)
- ``none``   — silent track sized to an estimated speaking duration
- ``auto``   — try edge, fall back to espeak, then to silence
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import wave
from pathlib import Path


class VoiceoverError(RuntimeError):
    pass


def _log(msg: str) -> None:
    print(f"[speedraw] {msg}", file=sys.stderr, flush=True)


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


# Espeak-style language hints -> default Edge neural voices.
EDGE_DEFAULT_VOICES = {
    "en": "en-US-AriaNeural",
    "en-gb": "en-GB-SoniaNeural",
    "tr": "tr-TR-EmelNeural",
    "de": "de-DE-KatjaNeural",
    "fr": "fr-FR-DeniseNeural",
    "es": "es-ES-ElviraNeural",
    "it": "it-IT-ElsaNeural",
    "pt": "pt-BR-FranciscaNeural",
    "nl": "nl-NL-ColetteNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ar": "ar-SA-ZariyahNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "hi": "hi-IN-SwaraNeural",
}


def resolve_edge_voice(voice: str | None) -> str:
    if not voice:
        return EDGE_DEFAULT_VOICES["en"]
    if "Neural" in voice:  # already a full Edge voice name
        return voice
    key = voice.lower()
    if key in EDGE_DEFAULT_VOICES:
        return EDGE_DEFAULT_VOICES[key]
    lang = key.split("-")[0]
    return EDGE_DEFAULT_VOICES.get(lang, EDGE_DEFAULT_VOICES["en"])


def _synth_edge(text: str, out_wav: Path, voice: str | None) -> float:
    try:
        import edge_tts  # noqa: F401
    except ImportError as exc:
        raise VoiceoverError(
            "edge-tts is not installed (pip install edge-tts)."
        ) from exc
    import asyncio

    edge_voice = resolve_edge_voice(voice)
    mp3 = out_wav.with_suffix(".edge.mp3")

    async def go() -> None:
        communicate = edge_tts.Communicate(text, edge_voice)
        await communicate.save(str(mp3))

    try:
        asyncio.run(go())
    except Exception as exc:  # network / service errors
        raise VoiceoverError(f"edge-tts synthesis failed: {exc}") from exc
    if not mp3.exists() or mp3.stat().st_size == 0:
        raise VoiceoverError("edge-tts produced no audio.")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise VoiceoverError("ffmpeg is required to decode edge-tts output.")
    result = subprocess.run(
        [ffmpeg, "-y", "-i", str(mp3), "-ar", "44100", "-ac", "1",
         "-c:a", "pcm_s16le", str(out_wav)],
        capture_output=True, text=True,
    )
    mp3.unlink(missing_ok=True)
    if result.returncode != 0:
        raise VoiceoverError("failed to convert edge-tts audio to WAV.")
    return wav_duration(out_wav)


def _synth_espeak(text: str, out_wav: Path, voice: str | None, speed_wpm: int) -> float:
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        raise VoiceoverError(
            "espeak-ng not found. Install it (e.g. `apt-get install espeak-ng`) "
            "or run with --tts none."
        )
    # full Edge voice names don't apply here; keep just the language part
    v = voice or "en-US"
    if "Neural" in v:
        v = "-".join(v.split("-")[:2])
    result = subprocess.run(
        [exe, "-v", v, "-s", str(speed_wpm), "-p", "50", "-w", str(out_wav), text],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not out_wav.exists():
        raise VoiceoverError(f"espeak-ng failed: {result.stderr.strip()}")
    return wav_duration(out_wav)


def synthesize(
    text: str,
    out_wav: Path,
    engine: str = "auto",
    voice: str | None = None,
    speed_wpm: int = 160,
) -> float:
    """Create a WAV for `text`, returning its duration in seconds."""
    if engine == "none":
        dur = estimate_speech_seconds(text)
        _write_silence(out_wav, dur)
        return dur
    if engine == "edge":
        return _synth_edge(text, out_wav, voice)
    if engine == "espeak":
        return _synth_espeak(text, out_wav, voice, speed_wpm)
    if engine == "auto":
        try:
            return _synth_edge(text, out_wav, voice)
        except VoiceoverError as exc:
            _log(f"edge-tts unavailable ({exc}); falling back to espeak-ng")
        try:
            return _synth_espeak(text, out_wav, voice, speed_wpm)
        except VoiceoverError as exc:
            _log(f"espeak-ng unavailable ({exc}); using a silent track")
        dur = estimate_speech_seconds(text)
        _write_silence(out_wav, dur)
        return dur
    raise VoiceoverError(
        f"Unknown TTS engine: {engine!r} (use 'auto', 'edge', 'espeak' or 'none')"
    )
