"""Voiceover generation.

Engines:
- ``edge``   — Microsoft Edge neural voices via edge-tts (natural, needs
               network). Supports emotion modulation (rate/pitch per emotion)
               and word-boundary timing for word-accurate lip sync.
- ``piper``  — Piper neural TTS (offline; voice models auto-download once to
               ~/.cache/speedraw/piper, ~60 MB per language)
- ``espeak`` — espeak-ng (offline, robotic but dependable)
- ``none``   — silent track sized to an estimated speaking duration
- ``auto``   — edge -> piper -> espeak -> silence
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from typing import Dict, List, Optional


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
    words = max(1, len(text.split()))
    return max(3.0, words / 2.6)


# ---------------------------------------------------------------------------
# Edge TTS
# ---------------------------------------------------------------------------

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

# how each emotion colours the delivery: (rate %, pitch Hz)
EDGE_EMOTION = {
    "happy": (8, 14),
    "excited": (16, 28),
    "sad": (-16, -22),
    "angry": (8, -12),
    "scared": (14, 22),
    "surprised": (6, 18),
    "love": (-6, 8),
    "neutral": (0, 0),
}


def resolve_edge_voice(voice: str | None) -> str:
    if not voice:
        return EDGE_DEFAULT_VOICES["en"]
    if "Neural" in voice:
        return voice
    key = voice.lower()
    if key in EDGE_DEFAULT_VOICES:
        return EDGE_DEFAULT_VOICES[key]
    lang = key.split("-")[0].split("_")[0]
    return EDGE_DEFAULT_VOICES.get(lang, EDGE_DEFAULT_VOICES["en"])


def _synth_edge(text: str, out_wav: Path, voice: str | None,
                emotion: Optional[str] = None,
                words_out: Optional[Path] = None) -> float:
    try:
        import edge_tts  # noqa: F401
    except ImportError as exc:
        raise VoiceoverError("edge-tts is not installed (pip install edge-tts).") from exc
    import asyncio

    edge_voice = resolve_edge_voice(voice)
    rate_pct, pitch_hz = EDGE_EMOTION.get(emotion or "neutral", (0, 0))
    mp3 = out_wav.with_suffix(".edge.mp3")
    words: List[dict] = []

    async def go() -> None:
        kwargs = {
            "rate": f"{'+' if rate_pct >= 0 else ''}{rate_pct}%",
            "pitch": f"{'+' if pitch_hz >= 0 else ''}{pitch_hz}Hz",
        }
        try:
            communicate = edge_tts.Communicate(text, edge_voice,
                                               boundary="WordBoundary", **kwargs)
        except TypeError:  # older edge-tts without the boundary parameter
            communicate = edge_tts.Communicate(text, edge_voice, **kwargs)
        with open(mp3, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    words.append({
                        "start": chunk["offset"] / 1e7,
                        "end": (chunk["offset"] + chunk["duration"]) / 1e7,
                        "text": chunk.get("text", ""),
                    })

    try:
        asyncio.run(go())
    except Exception as exc:
        mp3.unlink(missing_ok=True)
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
    if words_out is not None and words:
        words_out.write_text(json.dumps(words), encoding="utf-8")
    return wav_duration(out_wav)


# ---------------------------------------------------------------------------
# Piper TTS (offline neural)
# ---------------------------------------------------------------------------

PIPER_VOICES = {
    "en": ("en_US-lessac-medium", "en/en_US/lessac/medium"),
    "tr": ("tr_TR-fahrettin-medium", "tr/tr_TR/fahrettin/medium"),
    "de": ("de_DE-thorsten-medium", "de/de_DE/thorsten/medium"),
    "fr": ("fr_FR-siwis-medium", "fr/fr_FR/siwis/medium"),
    "es": ("es_ES-davefx-medium", "es/es_ES/davefx/medium"),
    "it": ("it_IT-riccardo-x_low", "it/it_IT/riccardo/x_low"),
    "ru": ("ru_RU-irina-medium", "ru/ru_RU/irina/medium"),
    "pt": ("pt_BR-faber-medium", "pt/pt_BR/faber/medium"),
    "nl": ("nl_NL-mls-medium", "nl/nl_NL/mls/medium"),
    "zh": ("zh_CN-huayan-medium", "zh/zh_CN/huayan/medium"),
}
PIPER_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
PIPER_CACHE = Path.home() / ".cache" / "speedraw" / "piper"

_piper_loaded: Dict[str, object] = {}


def _piper_model_path(voice: str | None) -> Path:
    """Resolve a language hint to a downloaded Piper model, fetching if needed."""
    if voice and voice.endswith(".onnx"):
        p = Path(voice)
        if p.exists():
            return p
        raise VoiceoverError(f"Piper model not found: {voice}")
    lang = (voice or "en").split("-")[0].split("_")[0].lower()
    name, subdir = PIPER_VOICES.get(lang, PIPER_VOICES["en"])
    model = PIPER_CACHE / f"{name}.onnx"
    if model.exists() and model.with_suffix(".onnx.json").exists():
        return model
    PIPER_CACHE.mkdir(parents=True, exist_ok=True)
    curl = shutil.which("curl")
    if not curl:
        raise VoiceoverError(
            f"Piper voice {name} is missing and curl is unavailable to fetch it. "
            f"Download {PIPER_BASE_URL}/{subdir}/{name}.onnx (+.json) into {PIPER_CACHE}."
        )
    _log(f"downloading Piper voice {name} (~60 MB, one time) ...")
    for suffix in (".onnx", ".onnx.json"):
        url = f"{PIPER_BASE_URL}/{subdir}/{name}{suffix}"
        dest = PIPER_CACHE / f"{name}{suffix}"
        result = subprocess.run([curl, "-sSL", "-o", str(dest), url],
                                capture_output=True, text=True)
        if result.returncode != 0 or not dest.exists() or dest.stat().st_size < 1000:
            dest.unlink(missing_ok=True)
            raise VoiceoverError(f"failed to download Piper voice from {url}")
    return model


def _synth_piper(text: str, out_wav: Path, voice: str | None,
                 emotion: Optional[str] = None) -> float:
    try:
        from piper import PiperVoice
    except ImportError as exc:
        raise VoiceoverError("piper-tts is not installed (pip install piper-tts).") from exc

    model = _piper_model_path(voice)
    key = str(model)
    if key not in _piper_loaded:
        _piper_loaded[key] = PiperVoice.load(key)
    pv = _piper_loaded[key]

    syn_config = None
    try:  # emotion -> gentle tempo change where supported
        from piper.config import SynthesisConfig

        scale = {"sad": 1.12, "love": 1.08, "excited": 0.9, "happy": 0.94,
                 "scared": 0.92}.get(emotion or "", 1.0)
        if scale != 1.0:
            syn_config = SynthesisConfig(length_scale=scale)
    except Exception:
        syn_config = None

    with wave.open(str(out_wav), "wb") as w:
        if syn_config is not None:
            pv.synthesize_wav(text, w, syn_config=syn_config)
        else:
            pv.synthesize_wav(text, w)
    return wav_duration(out_wav)


# ---------------------------------------------------------------------------
# espeak-ng
# ---------------------------------------------------------------------------


def _synth_espeak(text: str, out_wav: Path, voice: str | None, speed_wpm: int) -> float:
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        raise VoiceoverError(
            "espeak-ng not found. Install it (e.g. `apt-get install espeak-ng`) "
            "or run with --tts none."
        )
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


# ---------------------------------------------------------------------------
# Front door
# ---------------------------------------------------------------------------


def synthesize(
    text: str,
    out_wav: Path,
    engine: str = "auto",
    voice: str | None = None,
    speed_wpm: int = 160,
    emotion: Optional[str] = None,
    words_out: Optional[Path] = None,
) -> float:
    """Create a WAV for `text`, returning its duration in seconds.

    `emotion` colours the delivery on engines that support it. `words_out`,
    when given, receives word-boundary timings as JSON (edge engine only).
    """
    if engine == "none":
        dur = estimate_speech_seconds(text)
        _write_silence(out_wav, dur)
        return dur
    if engine == "edge":
        return _synth_edge(text, out_wav, voice, emotion, words_out)
    if engine == "piper":
        return _synth_piper(text, out_wav, voice, emotion)
    if engine == "espeak":
        return _synth_espeak(text, out_wav, voice, speed_wpm)
    if engine == "auto":
        try:
            return _synth_edge(text, out_wav, voice, emotion, words_out)
        except VoiceoverError as exc:
            _log(f"edge-tts unavailable ({exc}); trying Piper")
        try:
            return _synth_piper(text, out_wav, voice, emotion)
        except VoiceoverError as exc:
            _log(f"Piper unavailable ({exc}); falling back to espeak-ng")
        try:
            return _synth_espeak(text, out_wav, voice, speed_wpm)
        except VoiceoverError as exc:
            _log(f"espeak-ng unavailable ({exc}); using a silent track")
        dur = estimate_speech_seconds(text)
        _write_silence(out_wav, dur)
        return dur
    raise VoiceoverError(
        f"Unknown TTS engine: {engine!r} "
        "(use 'auto', 'edge', 'piper', 'espeak' or 'none')"
    )
