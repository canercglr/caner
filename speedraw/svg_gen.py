"""Generate simple line-art SVG drawings for each scene with Claude."""

from __future__ import annotations

import re

SVG_SYSTEM_PROMPT = """\
You produce simple whiteboard-marker line drawings as SVG for speed-drawing
explainer videos. A drawing hand will trace your strokes on screen, so the SVG
must consist of plain stroked outlines only.

Hard requirements:
- Output ONLY an <svg> element, no markdown fences, no commentary.
- viewBox="0 0 1280 720".
- Use ONLY these elements: <path>, <line>, <circle>, <ellipse>, <rect>,
  <polyline>. No <text>, <g>, <defs>, gradients, images, or transforms.
- Every element: fill="none", stroke (default "#111"), stroke-width 4-8.
  You may use at most one accent color (e.g. "#c0392b" or "#1a6fb0") sparingly.
- Keep it SIMPLE: roughly 5-25 strokes total. Big, bold, cartoon-like shapes.
  Slightly imperfect, hand-drawn-looking curves are ideal.
- Order the elements in the order a person would naturally draw them
  (main subject first, then details, then arrows).
- Leave margins: keep the drawing inside x=[80,1200], y=[60,640].
"""


def generate_scene_svg(client, visual_description: str, label: str, model: str) -> str:
    """Ask Claude for a line-art SVG matching the scene's visual description."""
    with client.messages.stream(
        model=model,
        max_tokens=32000,
        system=SVG_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f'Draw the illustration for a scene labeled "{label}":\n\n'
                    f"{visual_description}"
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "refusal":
        raise RuntimeError("The model declined to draw this scene (stop_reason=refusal).")

    text = "".join(b.text for b in response.content if b.type == "text")
    return extract_svg(text)


def extract_svg(text: str) -> str:
    """Pull the <svg>...</svg> element out of a model response."""
    match = re.search(r"<svg\b.*?</svg>", text, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError("No <svg> element found in model output.")
    return match.group(0)
