"""Assemble frames + audio into the final MP4 with ffmpeg."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple


class AssemblyError(RuntimeError):
    pass


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise AssemblyError("ffmpeg not found on PATH. Install ffmpeg to build videos.")
    return exe


def _run(cmd: List[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise AssemblyError(
            "ffmpeg failed:\n" + "\n".join(result.stderr.splitlines()[-15:])
        )


def build_video(
    frames_dir: Path,
    audio_files: List[Path],
    output: Path,
    fps: int,
    workdir: Path,
) -> None:
    """Mux the global frame sequence with the concatenated scene audio tracks."""
    ffmpeg = _ffmpeg()

    # Concatenate scene audio via the concat filter (tolerates mixed formats).
    audio_all = workdir / "audio_all.wav"
    cmd: List[str] = [ffmpeg, "-y"]
    for p in audio_files:
        cmd += ["-i", str(p)]
    chains = "".join(
        f"[{i}:a]aresample=44100,aformat=sample_fmts=s16:channel_layouts=mono[a{i}];"
        for i in range(len(audio_files))
    )
    joined = "".join(f"[a{i}]" for i in range(len(audio_files)))
    cmd += [
        "-filter_complex",
        f"{chains}{joined}concat=n={len(audio_files)}:v=0:a=1[out]",
        "-map", "[out]", str(audio_all),
    ]
    _run(cmd)

    _run([
        ffmpeg, "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "%06d.png"),
        "-i", str(audio_all),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        "-movflags", "+faststart",
        str(output),
    ])
