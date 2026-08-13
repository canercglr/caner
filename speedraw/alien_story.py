"""Alien narrator mode: Claude writes an acted monologue as structured data.

One alien on a dark stage tells a story straight to camera. Every beat
carries acting directions — emotion, gesture, camera framing — so the
performance follows the words.
"""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field

AlienEmotion = Literal["neutral", "happy", "sad", "angry", "surprised",
                       "scared", "excited", "love", "curious"]
AlienGestureName = Literal["none", "open_arms", "point_left", "point_right",
                           "point_up", "think", "shrug", "wave", "facepalm",
                           "jazz_hands", "clasp", "arms_cross", "recoil",
                           "bow", "count"]
Framing = Literal["wide", "medium", "closeup", "push_in", "pull_back"]


class Beat(BaseModel):
    text: str = Field(description="one spoken sentence or two short ones, "
                                  "max ~140 characters")
    emotion: AlienEmotion = "neutral"
    gesture: AlienGestureName = Field(
        default="none", description="acting gesture performed on this beat")
    camera: Framing = Field(
        default="medium", description="framing for this beat")


class AlienStory(BaseModel):
    title: str = Field(description="short title, max 6 words")
    beats: List[Beat] = Field(description="8-16 beats")


ALIEN_SYSTEM_PROMPT = """\
You write monologues performed by a single alien storyteller standing in a
spotlight on a black stage, speaking straight to camera. The alien has huge
glossy eyes, expressive antennae and long three-fingered hands; every beat
you write is acted out with a gesture, an emotion and a camera framing.

Craft rules:
- Tell one complete story with a clear arc: hook -> build -> twist or
  crisis -> resolution -> a warm or witty closing line to the audience.
- First person works beautifully ("I", "my ship", "my planet") — the alien
  is telling us something that happened to it. Keep each beat speakable:
  one sentence, max ~140 characters.
- ACT the words. Match the gesture to the line's content:
    open_arms    big reveals, welcomes ("the whole sky opened!")
    point_left / point_right / point_up   locating things in the world
    think        wondering, remembering (hand to chin)
    shrug        "who knows", helplessness
    wave         hello / goodbye to the audience
    facepalm     embarrassment at its own mistake
    jazz_hands   pure excitement, sparkle moments
    clasp        earnest, pleading, tender moments
    arms_cross   defiance, sulking
    recoil       shock, fright (leaning back, hands up)
    bow          thanks, endings
    count        listing things
    none         let a heavy line land without moving
- Emotions drive the face, antennae and posture — change them at the
  turning points, don't leave the whole story on one feeling. "curious"
  (head tilt, one raised brow ridge) is great for hooks and questions.
- The camera is your rhythm: "wide" shows the whole body (big physical
  beats), "medium" is the default storytelling frame, "closeup" fills the
  frame with the face (whispers, secrets, emotional peaks), "push_in"
  slowly creeps closer through the beat (rising tension), "pull_back"
  retreats (reveals, endings). Alternate framings; never use the same one
  three beats in a row, and save closeups for moments that earn them.
- 8-16 beats total. The last beat usually ends wide or pulling back, with
  a bow or wave.
"""


def generate_alien_story(client, topic: str, model: str) -> AlienStory:
    response = client.messages.parse(
        model=model,
        max_tokens=8000,
        system=ALIEN_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Write an acted alien monologue about:\n\n{topic}",
        }],
        output_format=AlienStory,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("The model declined this topic. Try rephrasing.")
    story = response.parsed_output
    if story is None:
        raise RuntimeError("Could not parse the generated monologue.")
    return story


DEMO_ALIEN_STORY = AlienStory(
    title="The Night I Found Earth",
    beats=[
        Beat(text="Oh! Hello. I didn't see you there.",
             emotion="surprised", gesture="wave", camera="medium"),
        Beat(text="Do you want to hear how I found this planet? By accident.",
             emotion="curious", gesture="think", camera="push_in"),
        Beat(text="I was piloting my ship with my eyes closed. Don't judge me.",
             emotion="happy", gesture="shrug", camera="medium"),
        Beat(text="Suddenly the whole sky opened up — and there it was. Blue. Round. Glowing.",
             emotion="excited", gesture="open_arms", camera="wide"),
        Beat(text="My navigation system said: 'that is a wet rock, ignore it.'",
             emotion="neutral", gesture="point_up", camera="medium"),
        Beat(text="But I got closer... and closer...",
             emotion="curious", gesture="none", camera="push_in"),
        Beat(text="And then your thunderstorm slapped my ship out of the sky.",
             emotion="scared", gesture="recoil", camera="closeup"),
        Beat(text="I crashed into something you call... a pumpkin field.",
             emotion="sad", gesture="facepalm", camera="medium"),
        Beat(text="For three days I hid. Cold. Alone. Covered in pumpkin.",
             emotion="sad", gesture="arms_cross", camera="closeup"),
        Beat(text="Then a small creature found me. Four legs. A tail. Extremely rude.",
             emotion="surprised", gesture="count", camera="medium"),
        Beat(text="It licked my antenna... and my whole heart lit up like a star.",
             emotion="love", gesture="clasp", camera="push_in"),
        Beat(text="I stayed a whole year because of that dog. Best crash of my life.",
             emotion="happy", gesture="jazz_hands", camera="medium"),
        Beat(text="So if your sky ever flashes green — that's just me, waving back.",
             emotion="love", gesture="wave", camera="pull_back"),
        Beat(text="Thank you for listening. Tell no one about the pumpkins.",
             emotion="happy", gesture="bow", camera="wide"),
    ],
)
