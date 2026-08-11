# speedraw 🎬✍️

Generate **whiteboard speed-drawing explainer videos** from a single topic.
Give it a prompt like *"How does photosynthesis work?"* and it produces an MP4
where a hand draws simple marker line-art on a whiteboard, scene by scene, while
a narrator explains the topic — the classic "RSA Animate / VideoScribe" style,
fully automated:

1. **Script** — Claude writes a scene-by-scene script (narration + a visual spec
   per scene) using structured outputs.
2. **Visuals** — Claude generates simple line-art SVGs for each scene; the
   renderer traces every stroke progressively with a drawing hand overlay.
3. **Voiceover** — narration is synthesized offline with espeak-ng (or a silent
   track with `--tts none`).
4. **Assembly** — ffmpeg muxes the frames and audio into a single H.264 MP4,
   complete with an animated hand-written title card.

## Requirements

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) on your `PATH`
- [espeak-ng](https://github.com/espeak-ng/espeak-ng) for voiceovers
  (optional — use `--tts none` without it)
- An Anthropic API key for AI generation (not needed for `--demo`)

```bash
sudo apt-get install ffmpeg espeak-ng     # Debian/Ubuntu
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

```bash
# Full AI pipeline: topic -> script -> drawings -> voiceover -> video
python -m speedraw "How does photosynthesis work?" -o photosynthesis.mp4

# More scenes, different voice, 1080p
python -m speedraw "What is compound interest?" --scenes 6 --voice en-GB --size 1920x1080

# Try the pipeline offline with bundled demo content (no API key required)
python -m speedraw --demo -o demo.mp4
```

### Options

| Flag | Default | Description |
|---|---|---|
| `-o, --output` | `explainer.mp4` | Output MP4 path |
| `--scenes N` | `4` | Number of scenes (1–12) |
| `--model` | `claude-opus-5` | Claude model used for script + visuals |
| `--tts {espeak,none}` | `espeak` | Voiceover engine (`none` = silent track) |
| `--voice` | `en-US` | espeak-ng voice |
| `--size WxH` | `1280x720` | Video resolution |
| `--fps` | `30` | Frame rate |
| `--no-title` | off | Skip the animated title card |
| `--demo` | off | Use bundled content, no API calls |
| `--workdir DIR` / `--keep-workdir` | temp | Inspect intermediate frames, SVGs, audio |

## How it works

```
topic ──► script_gen.py ──► VideoScript {title, scenes[{label, narration, visual_description}]}
                │
                ▼  per scene
            svg_gen.py ──► simple line-art SVG (stroked paths only)
                │
                ▼
           animator.py ──► samples every stroke into polylines, reveals them
                           frame-by-frame at a speed that fills the narration,
                           and overlays a procedurally drawn hand at the pen tip
                │
           voiceover.py ─► espeak-ng WAV per scene (padded to frame-exact length)
                │
                ▼
          assembler.py ──► ffmpeg: PNG sequence + concatenated audio ─► final MP4
```

Design notes:

- **Drawing order matters.** The SVG prompt asks Claude to emit elements in the
  order a person would naturally draw them, so the reveal feels intentional.
- **Sync is frame-exact.** Each scene's audio is padded/trimmed to the exact
  number of rendered frames, so narration never drifts across scenes.
- **No binary assets.** The hand-with-marker overlay is drawn procedurally with
  Pillow (`speedraw/hand.py`).
- **Robust SVG handling.** `<path>`, `<line>`, `<circle>`, `<ellipse>`,
  `<rect>`, and `<polyline>` are all converted to sampled stroke polylines;
  disconnected subpaths lift the pen instead of drawing bridges.
