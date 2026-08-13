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

# ALIEN NARRATOR: a single expressive alien on a black stage performs a
# monologue straight to camera — acting, mimics, lip sync and camera moves
python -m speedraw --alien "How I accidentally discovered Earth"
python -m speedraw --alien --demo -o alien.mp4   # offline demo monologue
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
- **Characters are cartoon humans** with real anatomy: ~6-head-height
  proportions, arms that hang from actual shoulders, a neck, a collared
  and hemmed shirt, trouser legs with knees, shoes with a toe, mitten
  hands with thumbs, and an oval head with ears and a nose. Faces are
  drawn in neutral ink — white-sclera eyes with coloured irises,
  gaze-following pupils and a light catch, expressive brows, blush — and
  every character renders at 2x supersampling for smooth, antialiased
  linework. Four hair styles (spiky, curly, flat, bun) over a proper
  scalp, and a soft ground shadow that shrinks when they jump.
- **Classic animation principles** drive the movement. Jumps have
  anticipation (a crouch and arm wind-up), airborne stretch and a landing
  squash with bent knees — all **squash & stretch** is volume-preserving
  about the ground contact point, and walk/run strides squash subtly on
  each footfall. Walks **ease in and out** instead of starting at full
  speed, gestures snap into place with a damped overshoot, and when a
  character stops moving their body keeps going for a beat — a
  **follow-through** lean that settles like a spring. Hair drags behind
  motion (trailing spikes, swinging bun) and keeps swaying gently at rest.
- **Faces act too**: every emotion has matching **eyebrows** (high arcs of
  surprise, knitted anger, worried inner tilt), pupils **look at** the
  scene partner or where the character is walking, blinks are desynced per
  character, and while talking the mouth corners stay curled with the
  emotion — characters smile or droop *through* their dialogue.
- **Letter-level visemes**: on top of the loudness envelope, each word's
  letters shape the mouth — lips shut on m/b/p, nearly close on f/v,
  round on o/u/ö/ü, widen on e/i, and drop open on a.
- **Atmosphere**: every shot has a mood — `day`, `golden_hour`, `sunset`,
  `night`, `overcast` — painted as a watercolor sky wash on the paper, a
  per-frame color grade (warm gold, dusky blue, muted gray...), longer
  shadows in low sun, and glowing halos around streetlamps and campfires
  after dark. Claude matches the mood to the story's emotional arc.
- **The world moves too**: a rich prop library (layered trees, houses with
  smoking chimneys and four-pane windows, snow-capped mountains, cars with
  spinning wheels, balloons, kites, rain, pets...) with motions — a balloon
  can drift away mid-story, rain can fall, a ball can bounce. Every shot
  stands on a **rich ground band**: a scribble-filled rolling hill with
  grass tufts and pebbles instead of a bare line.
- **Depth and parallax**: scenery lives on two layers — sky, clouds and
  mountains sit on a far layer that follows the camera at ~45% speed, so
  pans and zooms have real depth.
- **Claude draws the scenery** (outside demo mode): each shot gets a
  bespoke pass of AI-drawn SVG set dressing — terrain, flora, weather,
  distant landscape matching the mood — layered around the procedural
  props, with far elements tagged for parallax. Disable with
  `--no-ai-scenery`.
- **Cinematography**: each shot gets a camera move — `focus_speaker`
  glides toward whoever is talking, `slow_zoom_in`/`out` build tension or
  reveal the scene, `pan_left`/`right` travel across the world. Shots are
  joined with a soft fade through the whiteboard.
- **Background music**: a procedurally synthesized underscore (triangle
  pads, plucked pentatonic arpeggio, sine bass over a I-V-vi-IV
  progression — no assets, no network) is mixed under the video and
  side-chain ducked beneath the dialogue. Works in explainer mode too;
  control with `--no-music` / `--music-volume`.

## Alien narrator mode

`--alien` puts one big-eyed alien in a spotlight on a black stage and lets
it perform a story straight to camera. Claude writes the monologue as
**beats** — each one a spoken line plus acting directions — and the
renderer plays the performance:

- **Acting**: 14 gestures (open arms, pointing, shrug, think, facepalm,
  jazz hands, clasped hands, crossed arms, a shocked recoil, a bow...)
  matched to the meaning of each line, with anticipation and settle.
- **Mimics**: huge glossy almond eyes with gaze, squints, eased blinks and
  twin highlights; brow ridges; antennae that perk up with excitement and
  droop with sadness; a breathing idle so the figure is never frozen.
- **Lip sync**: the same audio-envelope + letter-viseme system as story
  mode — lips shut on m/b/p, round on o/u, wide on e/i — with a tongue
  hint on wide-open vowels. The narration is pitch-shifted up for an
  alien timbre without changing its timing.
- **Camera**: each beat picks a framing — wide, medium, closeup, a slow
  `push_in` or a `pull_back` — and the virtual camera glides between them
  with a gentle handheld drift. The figure is **redrawn from vectors at
  the camera's exact zoom** every frame, so even extreme closeups stay
  perfectly sharp.
- **Stage**: black void with a twinkling parallax starfield, a soft
  spotlight pool and a floor glow.

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
| `--no-ai-scenery` | off | Story mode: skip the Claude-drawn scenery pass |
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
