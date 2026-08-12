"""Command-line interface for speedraw."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import DEFAULT_MODEL, run_pipeline


def parse_size(value: str):
    try:
        w, h = value.lower().split("x")
        w, h = int(w), int(h)
        if w < 320 or h < 240:
            raise ValueError
        # even dimensions required by yuv420p
        return (w - w % 2, h - h % 2)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid size {value!r}, expected e.g. 1280x720")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="speedraw",
        description=(
            "Generate a whiteboard speed-drawing explainer video from a single "
            "topic, using AI-generated scripts, visuals, and voiceovers."
        ),
    )
    parser.add_argument("topic", nargs="?", default=None,
                        help="the topic to explain, e.g. 'How does a bicycle stay upright?'")
    parser.add_argument("-o", "--output", type=Path, default=Path("explainer.mp4"),
                        help="output MP4 path (default: explainer.mp4)")
    parser.add_argument("--story", action="store_true",
                        help="story mode: an animated stick-figure story with "
                             "walking, emotions, gestures and spoken dialogue "
                             "instead of a speed-drawing explainer")
    parser.add_argument("--scenes", type=int, default=4,
                        help="number of scenes to generate (default: 4)")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Claude model id (default: {DEFAULT_MODEL})")
    parser.add_argument("--tts",
                        choices=["auto", "edge", "piper", "espeak", "none"],
                        default="auto",
                        help="voiceover engine: 'edge' = Microsoft neural voices "
                             "(needs network, emotion-aware), 'piper' = offline "
                             "neural (model auto-downloads once), 'espeak' = "
                             "offline basic, 'none' = silent, 'auto' = "
                             "edge->piper->espeak fallback chain (default)")
    parser.add_argument("--voice", default=None,
                        help="voice: a language code like 'en', 'tr', 'de' or a full "
                             "Edge voice name like 'en-US-AriaNeural' "
                             "(default: English)")
    parser.add_argument("--size", type=parse_size, default=(1280, 720),
                        help="video resolution WxH (default: 1280x720)")
    parser.add_argument("--fps", type=int, default=30, help="frames per second (default: 30)")
    parser.add_argument("--no-title", action="store_true",
                        help="skip the animated title card")
    parser.add_argument("--no-music", action="store_true",
                        help="disable the procedural background music bed")
    parser.add_argument("--no-ai-scenery", action="store_true",
                        help="story mode: skip the Claude-drawn per-shot "
                             "scenery pass and use only the procedural props")
    parser.add_argument("--music-volume", type=float, default=None,
                        help="music bed volume 0.0-1.0 (default: 0.3 story, "
                             "0.22 explainer)")
    parser.add_argument("--demo", action="store_true",
                        help="use bundled demo content instead of calling the API "
                             "(no ANTHROPIC_API_KEY needed)")
    parser.add_argument("--workdir", type=Path, default=None,
                        help="directory for intermediate frames/audio")
    parser.add_argument("--keep-workdir", action="store_true",
                        help="keep intermediate files for inspection")
    args = parser.parse_args(argv)

    if not args.demo and not args.topic:
        parser.error("a topic is required (or pass --demo)")
    if args.scenes < 1 or args.scenes > 12:
        parser.error("--scenes must be between 1 and 12")

    try:
        if args.story:
            from .story_pipeline import run_story_pipeline

            run_story_pipeline(
                args.topic or "demo",
                args.output,
                model=args.model,
                tts_engine=args.tts,
                voice=args.voice,
                canvas=args.size,
                fps=args.fps,
                demo=args.demo,
                title_card=not args.no_title,
                ai_scenery=not args.no_ai_scenery,
                music=not args.no_music,
                music_volume=args.music_volume if args.music_volume is not None else 0.3,
                workdir=args.workdir,
                keep_workdir=args.keep_workdir,
            )
        else:
            run_pipeline(
                args.topic or "demo",
                args.output,
                num_scenes=args.scenes,
                model=args.model,
                tts_engine=args.tts,
                voice=args.voice,
                canvas=args.size,
                fps=args.fps,
                demo=args.demo,
                title_card=not args.no_title,
                music=not args.no_music,
                music_volume=args.music_volume if args.music_volume is not None else 0.22,
                workdir=args.workdir,
                keep_workdir=args.keep_workdir,
            )
    except Exception as exc:  # surface a clean error instead of a traceback
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
