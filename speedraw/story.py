"""Story mode: Claude writes an animated stick-figure story as structured data."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Emotion = Literal["neutral", "happy", "sad", "angry", "surprised", "scared",
                  "excited", "love"]
Gesture = Literal["wave", "jump", "point_left", "point_right", "dance", "nod",
                  "shake", "clap", "bow", "shrug", "facepalm", "think", "cry",
                  "laugh", "cheer", "sit"]
PropKind = Literal["sun", "moon", "star", "cloud", "rain", "tree", "bush",
                   "mountain", "flower", "grass", "rock", "house", "bench",
                   "car", "ball", "balloon", "bird", "kite", "cat", "dog",
                   "butterfly", "bicycle", "campfire", "streetlamp", "fence",
                   "boat"]
Motion = Literal["none", "drift_left", "drift_right", "rise", "fall_loop",
                 "bounce", "spin", "sway", "float", "pulse"]
Camera = Literal["static", "slow_zoom_in", "slow_zoom_out", "pan_left",
                 "pan_right", "focus_speaker"]
Mood = Literal["day", "golden_hour", "sunset", "night", "overcast"]


class StoryActor(BaseModel):
    id: str = Field(description="short lowercase id, e.g. 'pip'")
    name: str
    color: Literal["ink", "blue", "red", "green"] = "ink"
    voice: Literal["female", "male"] = "female"
    hair: Optional[Literal["spiky", "curly", "flat", "bun"]] = Field(
        default=None, description="hairstyle; defaults by voice if omitted"
    )
    start_x: float = Field(
        description="initial x position (0-1280); use <0 or >1280 to start "
                    "off-screen and walk in later"
    )


class StoryProp(BaseModel):
    kind: PropKind
    x: float = Field(description="horizontal center, 0-1280")
    y: float = Field(
        description="sky objects (sun/moon/star/cloud/rain/bird/balloon-top/"
                    "kite-top): vertical center 60-300. Ground objects: their "
                    "base line, usually 585."
    )
    scale: float = 1.0
    motion: Motion = "none"


class StoryEvent(BaseModel):
    actor: str = Field(description="actor id this event belongs to")
    action: Literal["say", "walk", "run", "emote", "gesture", "wait"]
    text: Optional[str] = Field(
        default=None,
        description="for say: one short spoken line, max ~70 characters",
    )
    emotion: Optional[Emotion] = Field(
        default=None, description="for emote (also allowed alongside say)"
    )
    to_x: Optional[float] = Field(
        default=None, description="for walk/run: destination x (may be off-screen)"
    )
    gesture: Optional[Gesture] = None
    seconds: Optional[float] = Field(default=None, description="for wait")


class StoryShot(BaseModel):
    props: List[StoryProp] = Field(description="scene dressing for this shot")
    events: List[StoryEvent] = Field(description="4-9 sequential events")
    camera: Camera = Field(
        default="static",
        description="camera move for the whole shot",
    )
    mood: Mood = Field(
        default="day",
        description="lighting/color atmosphere of the shot",
    )


class Story(BaseModel):
    title: str = Field(description="short title, max 6 words")
    actors: List[StoryActor] = Field(description="1-2 actors")
    shots: List[StoryShot] = Field(description="2-4 shots")


STORY_SYSTEM_PROMPT = """\
You write short animated stick-figure stories rendered on a 1280x720 canvas
with a hand-drawn whiteboard look. Actors are expressive stick figures that
walk, gesture, emote (face + posture + a floating badge like ! ? or a heart)
and speak out loud with speech bubbles and real text-to-speech voices.

Craft rules:
- Tell a tiny complete story with an emotional arc: setup -> problem or
  surprise -> resolution. Make the FEELINGS change: use emote events
  (happy, sad, angry, surprised, scared, excited, love) at the turning points.
- Dialogue lines are short and speakable (max ~70 chars). Characters talk TO
  each other. Give each actor a distinct personality.
- Movement sells the story: walk or run actors between positions (x 120-1160,
  off-screen entries/exits via x < 0 or > 1280; run for urgency, excitement
  or chases), and use the gesture vocabulary at emotional beats:
    wave        greeting or goodbye
    jump        single joyful hop
    cheer       arms pumping overhead
    dance       celebration groove
    clap        applause (with spark marks on each clap)
    bow         thanks / apology / performance ending
    nod         agreeing        shake: refusing
    shrug       "I don't know", arms out palms up
    point_left / point_right    pointing at something
    think       hand on chin + thought dots
    facepalm    exasperation
    cry         hands to eyes, tears streaming (pair with emotion sad)
    laugh       leaning back, big open mouth, ha-ha marks
    sit         sits down on the ground (nice for calm or defeated beats)
  Pick the gesture that matches the line just spoken or the emotion just
  set — a story beat lands hardest as say -> emote -> gesture.
- Events run one at a time, in order. Keep 4-9 per shot.
- Dress each shot with 3-7 props, and give 1-3 of them motion so the world
  feels alive: clouds drift, a balloon rises, a ball bounces, rain falls,
  car and bicycle wheels spin, flowers sway, a butterfly floats, a campfire
  flickers, cat and dog tails wag on their own. Motion should serve the
  story (if the story is about a balloon flying away, the balloon gets
  motion "rise" in that shot). Pets (cat, dog), vehicles (car, bicycle,
  boat), places (house, fence, streetlamp, bench, campfire, mountain) let
  you stage richer worlds — use props that match the setting.
- The ground line is at y=585. Actors are ~185px tall cartoon people.
  Keep the sky area
  (y < 300) for sun/moon/clouds/stars and don't crowd the center where
  actors act.
- Shots reuse the same world: keep prop continuity where it makes sense,
  and remember actor positions carry over between shots.
- Give each shot a mood — the lighting and color atmosphere: "day" is
  neutral; "golden_hour" is warm late-afternoon light (great for happy
  endings); "sunset" is dramatic orange-pink; "night" is dark blue (put a
  moon and stars in the sky, and streetlamps or a campfire glow in the
  dark); "overcast" is gray and muted (perfect for sad or tense beats).
  Let the mood follow the emotional arc — e.g. overcast while things go
  wrong, golden_hour when they're resolved.
- Give each shot a camera move: "focus_speaker" is best for dialogue-heavy
  shots (the camera glides to whoever is talking); "slow_zoom_in" builds
  tension or intimacy; "slow_zoom_out" reveals the scene or ends the story
  wide; "pan_left"/"pan_right" travels across the scene (great when someone
  walks somewhere); "static" for calm beats. Vary the moves across shots.
"""


def generate_story(client, topic: str, model: str) -> Story:
    response = client.messages.parse(
        model=model,
        max_tokens=12000,
        system=STORY_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Write an animated stick-figure story about:\n\n{topic}",
            }
        ],
        output_format=Story,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(
            "The model declined to write a story for this topic. Try rephrasing."
        )
    story = response.parsed_output
    if story is None:
        raise RuntimeError("Could not parse the generated story.")
    return story


DEMO_STORY = Story(
    title="Pip and the Balloon",
    actors=[
        StoryActor(id="pip", name="Pip", color="ink", voice="male", start_x=-80),
        StoryActor(id="momo", name="Momo", color="blue", voice="female", start_x=1360),
    ],
    shots=[
        StoryShot(
            props=[
                StoryProp(kind="sun", x=190, y=150, scale=1.0, motion="none"),
                StoryProp(kind="cloud", x=760, y=120, scale=0.9, motion="drift_right"),
                StoryProp(kind="tree", x=1080, y=585, scale=1.0, motion="none"),
                StoryProp(kind="balloon", x=620, y=585, scale=1.0, motion="none"),
                StoryProp(kind="flower", x=350, y=585, scale=1.2, motion="sway"),
                StoryProp(kind="butterfly", x=900, y=360, scale=1.1, motion="float"),
            ],
            camera="slow_zoom_in",
            mood="day",
            events=[
                StoryEvent(actor="pip", action="walk", to_x=430),
                StoryEvent(actor="pip", action="say", text="What a perfect day for my balloon!",
                           emotion="happy"),
                StoryEvent(actor="pip", action="gesture", gesture="jump"),
                StoryEvent(actor="pip", action="say", text="Best. Balloon. Ever!", emotion="excited"),
            ],
        ),
        StoryShot(
            props=[
                StoryProp(kind="sun", x=190, y=150, scale=1.0, motion="none"),
                StoryProp(kind="cloud", x=920, y=110, scale=0.8, motion="drift_left"),
                StoryProp(kind="tree", x=1080, y=585, scale=1.0, motion="none"),
                StoryProp(kind="balloon", x=620, y=585, scale=1.0, motion="rise"),
                StoryProp(kind="bird", x=300, y=200, scale=1.0, motion="drift_right"),
            ],
            camera="focus_speaker",
            mood="overcast",
            events=[
                StoryEvent(actor="pip", action="emote", emotion="surprised"),
                StoryEvent(actor="pip", action="say", text="Oh no! Come back!", emotion="surprised"),
                StoryEvent(actor="pip", action="gesture", gesture="point_right"),
                StoryEvent(actor="pip", action="emote", emotion="sad"),
                StoryEvent(actor="pip", action="gesture", gesture="cry"),
                StoryEvent(actor="pip", action="gesture", gesture="sit"),
                StoryEvent(actor="momo", action="run", to_x=820),
                StoryEvent(actor="momo", action="say", text="Pip! I saw your balloon fly off!"),
                StoryEvent(actor="pip", action="say", text="It's gone forever...", emotion="sad"),
                StoryEvent(actor="momo", action="gesture", gesture="think"),
                StoryEvent(actor="momo", action="say", text="Hmm... wait right here!", emotion="excited"),
                StoryEvent(actor="momo", action="run", to_x=1360),
            ],
        ),
        StoryShot(
            props=[
                StoryProp(kind="sun", x=190, y=150, scale=1.0, motion="pulse"),
                StoryProp(kind="cloud", x=500, y=100, scale=0.7, motion="drift_right"),
                StoryProp(kind="tree", x=1080, y=585, scale=1.0, motion="none"),
                StoryProp(kind="kite", x=640, y=585, scale=1.1, motion="float"),
                StoryProp(kind="bird", x=1000, y=170, scale=0.8, motion="drift_left"),
                StoryProp(kind="flower", x=350, y=585, scale=1.2, motion="sway"),
                StoryProp(kind="dog", x=1180, y=585, scale=1.0),
            ],
            camera="slow_zoom_out",
            mood="golden_hour",
            events=[
                StoryEvent(actor="momo", action="run", to_x=820),
                StoryEvent(actor="momo", action="say", text="Ta-da! Look what I brought!",
                           emotion="happy"),
                StoryEvent(actor="momo", action="gesture", gesture="point_left"),
                StoryEvent(actor="pip", action="emote", emotion="surprised"),
                StoryEvent(actor="pip", action="say", text="A kite?! That's even better!",
                           emotion="excited"),
                StoryEvent(actor="pip", action="gesture", gesture="laugh"),
                StoryEvent(actor="momo", action="gesture", gesture="clap"),
                StoryEvent(actor="pip", action="gesture", gesture="cheer"),
                StoryEvent(actor="pip", action="say", text="You're the best, Momo!", emotion="love"),
                StoryEvent(actor="momo", action="gesture", gesture="bow"),
                StoryEvent(actor="momo", action="gesture", gesture="dance"),
                StoryEvent(actor="pip", action="gesture", gesture="dance"),
            ],
        ),
    ],
)
