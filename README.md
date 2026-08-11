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
3. **Voiceover** — narration is synthesized with Microsoft Edge neural voices
   (edge-tts) by default, falling back to offline espeak-ng or a silent track.
4. **Assembly** — ffmpeg muxes the frames and audio into a single H.264 MP4,
   complete with an animated hand-written title card.

## Requirements

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) on your `PATH`
- [edge-tts](https://pypi.org/project/edge-tts/) for natural neural voiceovers
  (installed via requirements; needs network) and/or
  [espeak-ng](https://github.com/espeak-ng/espeak-ng) as the offline fallback
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

# More scenes, Turkish neural voice, 1080p
python -m speedraw "Bileşik faiz nedir?" --scenes 6 --voice tr --size 1920x1080

# Pick a specific Edge neural voice (see `edge-tts --list-voices`)
python -m speedraw "What is compound interest?" --voice en-GB-RyanNeural

# Try the pipeline offline with bundled demo content (no API key required)
python -m speedraw --demo -o demo.mp4
```

### Options

| Flag | Default | Description |
|---|---|---|
| `-o, --output` | `explainer.mp4` | Output MP4 path |
| `--scenes N` | `4` | Number of scenes (1–12) |
| `--model` | `claude-opus-5` | Claude model used for script + visuals |
| `--tts {auto,edge,espeak,none}` | `auto` | Voiceover engine: `edge` = neural voices, `espeak` = offline, `none` = silent; `auto` tries edge then falls back |
| `--voice` | English | Language code (`en`, `tr`, `de`, ...) or a full Edge voice name (`en-US-AriaNeural`) |
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
           voiceover.py ─► edge-tts / espeak-ng WAV per scene (frame-exact length)
                │
                ▼
          assembler.py ──► ffmpeg: PNG sequence + concatenated audio ─► final MP4
```

Design notes:

- **Hand-drawn feel.** Every stroke gets subtle perpendicular wobble (two sine
  octaves, deterministic per stroke) and a slowly varying marker width, so even
  geometric SVG shapes look drawn by a person.
- **Scene captions.** After each drawing completes, the scene label is
  hand-written beneath it with the same wipe effect as the title card.
- **Drawing order matters.** The SVG prompt asks Claude to emit elements in the
  order a person would naturally draw them, so the reveal feels intentional.
- **Sync is frame-exact.** Each scene's audio is padded/trimmed to the exact
  number of rendered frames, so narration never drifts across scenes.
- **No binary assets.** The hand-with-marker overlay is drawn procedurally with
  Pillow (`speedraw/hand.py`).
- **Robust SVG handling.** `<path>`, `<line>`, `<circle>`, `<ellipse>`,
  `<rect>`, and `<polyline>` are all converted to sampled stroke polylines;
  disconnected subpaths lift the pen instead of drawing bridges.
