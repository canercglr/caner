# speedraw 🎬✍️

Generate **whiteboard speed-drawing explainer videos** from a single topic.
Give it a prompt like *"How does photosynthesis work?"* and it produces an MP4
where a hand draws simple marker line-art on a whiteboard, scene by scene, while
a narrator explains the topic — the classic "RSA Animate / VideoScribe" style,
fully automated:

1. **Script** — Claude writes a scene-by-scene script (narration + a visual spec
   per scene) using structured outputs.
2. **Visuals** — Claude generates rich line-art SVGs for each scene; the
   renderer traces every stroke progressively with a drawing hand overlay.
   Once a drawing is finished it comes alive: clouds drift, rain falls,
   sun rays spin, plants sway, and stick figures walk across the scene.
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

# STORY MODE: an animated stick-figure story instead of an explainer —
# characters walk, emote, gesture and speak with per-character voices
python -m speedraw --story "A stick figure who is afraid of heights climbs a mountain"
python -m speedraw --story --demo -o story.mp4   # offline demo story
```

## Story mode

`--story` switches from speed-drawing explainers to fully animated
stick-figure stories. Claude writes a screenplay as structured data — actors,
shots, scene props, and a sequential event timeline — and the renderer plays
it out:

- **Actors** walk between positions (with a proper walk cycle), enter and
  exit off-screen, and always subtly bob and blink.
- **Emotions** (happy, sad, angry, surprised, scared, excited, love) change
  the face, the posture *and* a floating badge above the head — a `!`, a
  heart, anger marks, a sweat drop, or sparkles.
- **Gestures** (16): wave, jump, cheer, dance, clap (with spark marks on
  contact), bow, nod, shake, shrug, point left/right, think (hand on chin +
  thought dots), facepalm, cry (tears + sobbing shoulders), laugh (leaning
  back, hand on belly, ha-ha marks), and sit (drops down to the ground).
  Actors can also **run** — a faster, leaning stride for urgency and chases.
- **Dialogue** is spoken with a distinct neural voice per character
  (male/female, language follows `--voice`) and a hand-drawn speech bubble
  that pops in above the speaker. Delivery is **emotion-aware**: sad lines
  play slower and lower, excited lines faster and higher. The mouth is
  **lip-synced to the actual audio**: a per-frame RMS envelope drives how
  far it opens, edge-tts word boundaries force the lips shut between words,
  and the zero-crossing rate picks the shape — round open vowels vs. wide
  flat consonants, with a dark mouth interior when wide open.
- **Characters are doodle people**, not bare stick figures: shirt-coloured
  torsos, four hair styles (spiky, curly, flat, bun), skin-tone hands,
  shoes, and a soft ground shadow that shrinks when they jump.
- **The world moves too**: the same prop library used by explainer mode
  (sun, clouds, trees, houses, cars with spinning wheels, balloons,
  kites, rain, birds...) with motions — a balloon can drift away mid-story,
  rain can fall, a ball can bounce.
- **Cinematography**: each shot gets a camera move — `focus_speaker`
  glides toward whoever is talking, `slow_zoom_in`/`out` build tension or
  reveal the scene, `pan_left`/`right` travel across the world. Shots are
  joined with a soft fade through the whiteboard.
- **Background music**: a procedurally synthesized underscore (triangle
  pads, plucked pentatonic arpeggio, sine bass over a I-V-vi-IV
  progression — no assets, no network) is mixed under the video and
  side-chain ducked beneath the dialogue. Works in explainer mode too;
  control with `--no-music` / `--music-volume`.

### Options

| Flag | Default | Description |
|---|---|---|
| `-o, --output` | `explainer.mp4` | Output MP4 path |
| `--scenes N` | `4` | Number of scenes (1–12) |
| `--model` | `claude-opus-5` | Claude model used for script + visuals |
| `--tts {auto,edge,piper,espeak,none}` | `auto` | Voiceover engine: `edge` = neural voices (emotion-aware), `piper` = offline neural (model auto-downloads once), `espeak` = offline basic, `none` = silent; `auto` = edge→piper→espeak chain |
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

- **Scribble-fill.** Closed shapes tagged `data-fill="#hex"` are coloured in
  with a marker-scribble tint (light base + wobbly diagonal strokes, soft
  bleed at the edges) the moment their outline completes — drawings look
  coloured-in, not just traced. Claude is prompted to fill major shapes.
- **Paper feel.** Every frame sits on a procedurally generated paper
  background (fiber grain + soft vignette), and strokes taper at both ends
  like a real marker nib.
- **Motion system.** Any SVG element can carry a `data-anim` attribute —
  `float`, `drift:dx,dy[,wrap]`, `spin[:period]`, `sway[:deg]`, `pulse[:amp]` —
  and starts moving the moment the scene's drawing completes. A custom
  `<walker x y to-x scale stroke/>` element adds a procedural stick figure
  that is drawn standing, then walks with swinging arms and bending knees.
  Claude is prompted to tag meaningful motion (rain falls, smoke rises,
  wheels spin) in the SVGs it generates.
- **Hand-drawn feel.** Every stroke gets subtle perpendicular wobble (two sine
  octaves, deterministic per stroke) and a slowly varying marker width, so even
  geometric SVG shapes look drawn by a person.
- **Scene captions.** After each drawing completes, the scene label is
  hand-written beneath it with the same wipe effect as the title card —
  serif italic with accent dashes, under a serif title card with a swash
  underline.
- **Snappy pacing.** Drawing fills only ~50-60% of each scene, at true
  speed-drawing tempo; the rest of the time belongs to motion and captions.
- **Drawing order matters.** The SVG prompt asks Claude to emit elements in the
  order a person would naturally draw them, so the reveal feels intentional.
- **Sync is frame-exact.** Each scene's audio is padded/trimmed to the exact
  number of rendered frames, so narration never drifts across scenes.
- **No binary assets.** The hand-with-marker overlay is drawn procedurally with
  Pillow (`speedraw/hand.py`).
- **Robust SVG handling.** `<path>`, `<line>`, `<circle>`, `<ellipse>`,
  `<rect>`, and `<polyline>` are all converted to sampled stroke polylines;
  disconnected subpaths lift the pen instead of drawing bridges.
