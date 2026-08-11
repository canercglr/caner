"""Story mode: Claude writes an animated stick-figure story as structured data."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Emotion = Literal["neutral", "happy", "sad", "angry", "surprised", "scared",
                  "excited", "love"]
Gesture = Literal["wave", "jump", "point_left", "point_right", "dance"]
PropKind = Literal["sun", "moon", "star", "cloud", "rain", "tree", "bush",
                   "mountain", "flower", "grass", "rock", "house", "bench",
                   "car", "ball", "balloon", "bird", "kite"]
Motion = Literal["none", "drift_left", "drift_right", "rise", "fall_loop",
                 "bounce", "spin", "sway", "float", "pulse"]


class StoryActor(BaseModel):
    id: str = Field(description="short lowercase id, e.g. 'pip'")
    name: str
    color: Literal["ink", "blue", "red", "green"] = "ink"
    voice: Literal["female", "male"] = "female"
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
    action: Literal["say", "walk", "emote", "gesture", "wait"]
    text: Optional[str] = Field(
        default=None,
        description="for say: one short spoken line, max ~70 characters",
    )
    emotion: Optional[Emotion] = Field(
        default=None, description="for emote (also allowed alongside say)"
    )
    to_x: Optional[float] = Field(
        default=None, description="for walk: destination x (may be off-screen)"
    )
    gesture: Optional[Gesture] = None
    seconds: Optional[float] = Field(default=None, description="for wait")


class StoryShot(BaseModel):
    props: List[StoryProp] = Field(description="scene dressing for this shot")
    events: List[StoryEvent] = Field(description="4-9 sequential events")


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
- Movement sells the story: walk actors between positions (x 120-1160,
  off-screen entries/exits via x < 0 or > 1280), and use gestures (wave,
  jump, point_left/right, dance) at emotional beats.
- Events run one at a time, in order. Keep 4-9 per shot.
- Dress each shot with 3-7 props, and give 1-3 of them motion so the world
  feels alive: clouds drift, a balloon rises, a ball bounces, rain falls,
  car wheels spin, flowers sway. Motion should serve the story (if the story
  is about a balloon flying away, the balloon gets motion "rise" in that
  shot).
- The ground line is at y=585. Actors are ~200px tall. Keep the sky area
  (y < 300) for sun/moon/clouds/stars and don't crowd the center where
  actors act.
- Shots reuse the same world: keep prop continuity where it makes sense,
  and remember actor positions carry over between shots.
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
            ],
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
            events=[
                StoryEvent(actor="pip", action="emote", emotion="surprised"),
                StoryEvent(actor="pip", action="say", text="Oh no! Come back!", emotion="surprised"),
                StoryEvent(actor="pip", action="gesture", gesture="point_right"),
                StoryEvent(actor="pip", action="emote", emotion="sad"),
                StoryEvent(actor="pip", action="say", text="My balloon is gone forever...",
                           emotion="sad"),
                StoryEvent(actor="momo", action="walk", to_x=820),
                StoryEvent(actor="momo", action="say", text="Hey Pip! Why the long face?"),
                StoryEvent(actor="pip", action="say", text="The wind took my balloon.", emotion="sad"),
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
            ],
            events=[
                StoryEvent(actor="momo", action="say", text="Cheer up! Look what I brought!",
                           emotion="happy"),
                StoryEvent(actor="momo", action="gesture", gesture="point_left"),
                StoryEvent(actor="pip", action="emote", emotion="surprised"),
                StoryEvent(actor="pip", action="say", text="A kite?! That's even better!",
                           emotion="excited"),
                StoryEvent(actor="pip", action="gesture", gesture="jump"),
                StoryEvent(actor="momo", action="gesture", gesture="dance"),
                StoryEvent(actor="pip", action="say", text="You're the best, Momo!", emotion="love"),
                StoryEvent(actor="momo", action="gesture", gesture="wave"),
            ],
        ),
    ],
)
