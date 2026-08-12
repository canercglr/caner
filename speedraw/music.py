"""Procedural background music: a gentle, loopable underscore.

Synthesizes a soft I-V-vi-IV progression (triangle pads, plucked pentatonic
arpeggio, sine bass) with numpy — no assets, no network. The mix stage ducks
it under speech via ffmpeg's sidechain compressor.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100
BPM = 84
BEAT = 60.0 / BPM
BAR = 4 * BEAT
CHORD_LEN = 2 * BAR

C3 = 130.8128
# chords as semitone offsets from C3: C, G, Am, F
PROGRESSION = [(0, 4, 7), (-5, 2, 7), (-3, 4, 9), (-7, 0, 5)]
# C-major pentatonic offsets used by the arpeggio
ARP_PATTERNS = [
    (0, 7, 12, 16, 12, 7, 4, 7),
    (0, 4, 7, 12, 16, 12, 7, 4),
    (-3, 4, 9, 12, 9, 4, 0, 4),
    (-7, 0, 5, 9, 12, 9, 5, 0),
]


def _hz(semitones: float) -> float:
    return C3 * (2.0 ** (semitones / 12.0))


def _triangle(freq: float, n: int) -> np.ndarray:
    t = np.arange(n) / SR
    return 2.0 / np.pi * np.arcsin(np.sin(2 * np.pi * freq * t))


def _env(n: int, attack: float, release: float) -> np.ndarray:
    e = np.ones(n)
    na, nr = int(attack * SR), int(release * SR)
    if na > 0:
        e[:na] = np.linspace(0, 1, na)
    if nr > 0 and nr < n:
        e[-nr:] = np.linspace(1, 0, nr)
    return e


def _pluck(freq: float, n: int) -> np.ndarray:
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * freq * t) * np.exp(-t * 4.5)
            + 0.35 * np.sin(4 * np.pi * freq * t) * np.exp(-t * 6.5))


def compose_music(seconds: float, out_wav: Path) -> Path:
    n_total = int(seconds * SR) + SR
    buf = np.zeros(n_total, dtype=np.float64)

    t0 = 0.0
    ci = 0
    while t0 < seconds:
        chord = PROGRESSION[ci % len(PROGRESSION)]
        pattern = ARP_PATTERNS[ci % len(ARP_PATTERNS)]
        i0 = int(t0 * SR)
        nc = int(CHORD_LEN * SR)
        if i0 + nc > n_total:
            nc = n_total - i0
        if nc <= 0:
            break

        # pads: chord tones, two octaves
        for st in chord:
            for octave, amp in ((12, 0.030), (24, 0.016)):
                tone = _triangle(_hz(st + octave), nc) * _env(nc, 0.9, 0.9) * amp
                buf[i0:i0 + nc] += tone
        # bass: root, half notes
        half = int(2 * BEAT * SR)
        for k in range(0, nc, half):
            m = min(half, nc - k)
            tt = np.arange(m) / SR
            buf[i0 + k:i0 + k + m] += (0.05 * np.sin(2 * np.pi * _hz(chord[0] - 12) * tt)
                                       * _env(m, 0.02, 0.4))
        # arpeggio: eighth-note plucks, skipping some for air
        eighth = int(BEAT / 2 * SR)
        for k, st in enumerate(pattern * 2):
            if (ci + k) % 7 == 3:      # deterministic rests keep it human
                continue
            pos = i0 + k * eighth
            if pos >= i0 + nc or pos >= n_total:
                break
            m = min(int(0.9 * SR), n_total - pos)
            buf[pos:pos + m] += _pluck(_hz(st + 24), m) * 0.045

        t0 += CHORD_LEN
        ci += 1

    # gentle spectral lowpass (smooth rolloff above ~2.4 kHz) to soften the top
    spec = np.fft.rfft(buf)
    freqs = np.fft.rfftfreq(len(buf), 1 / SR)
    rolloff = 1.0 / (1.0 + (freqs / 2400.0) ** 2)
    out = np.fft.irfft(spec * rolloff, n=len(buf))

    # fade edges, normalize to a safe bed level
    out = out[: int(seconds * SR)]
    out *= _env(len(out), 1.2, 2.0)
    peak = np.max(np.abs(out)) or 1.0
    out = out / peak * 0.55

    data = (out * 32767).astype(np.int16).tobytes()
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)
    return out_wav
