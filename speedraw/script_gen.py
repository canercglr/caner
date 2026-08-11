"""Generate the explainer script (scene narrations + visual specs) with Claude."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Scene(BaseModel):
    label: str = Field(description="Short 2-4 word on-screen label for the scene")
    narration: str = Field(
        description="2-3 spoken sentences of narration for this scene, plain prose"
    )
    visual_description: str = Field(
        description=(
            "A concrete description of a SIMPLE line drawing that illustrates this "
            "scene: the few shapes to draw, their rough placement, and any arrows. "
            "Must be drawable as black-marker line art with no text."
        )
    )


class VideoScript(BaseModel):
    title: str = Field(description="Short video title, max 6 words")
    scenes: List[Scene]


SYSTEM_PROMPT = """\
You write scripts for whiteboard speed-drawing explainer videos: a hand draws
simple black-marker line art on a whiteboard while a narrator explains the topic.

Rules:
- Narration is conversational, clear, and beginner-friendly. Each scene's
  narration takes roughly 10-15 seconds to speak (2-3 sentences).
- Scenes build on each other and together fully answer/explain the topic.
- Visual descriptions must be genuinely simple: 2-5 basic shapes (circles,
  boxes, stick figures, arrows, simple icons) that a hand could draw in seconds.
  No text in the drawings, no shading, no fine detail.
"""


def generate_script(client, topic: str, num_scenes: int, model: str) -> VideoScript:
    """Ask Claude for a structured scene-by-scene script."""
    response = client.messages.parse(
        model=model,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Write a whiteboard explainer video script about:\n\n{topic}\n\n"
                    f"Use exactly {num_scenes} scenes."
                ),
            }
        ],
        output_format=VideoScript,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(
            "The model declined to write a script for this topic "
            f"(stop_reason=refusal). Try rephrasing the topic."
        )
    script = response.parsed_output
    if script is None:
        raise RuntimeError("Could not parse the generated script.")
    return script
