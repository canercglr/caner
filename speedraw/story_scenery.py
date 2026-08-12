"""Claude-drawn scenery for story shots.

The procedural prop library stages the world; this module asks Claude to
dress it further with shot-specific SVG detail — flora, terrain, weather,
architecture — in the same hand-drawn marker style. Elements tagged
``data-depth="far"`` land on the far parallax layer (sky, horizon), the
rest on the near layer. Story characters are never drawn here.
"""

from __future__ import annotations

import re
from typing import List, Tuple

SCENERY_SYSTEM_PROMPT = """\
You dress animated story scenes with extra hand-drawn scenery, output as a
single SVG with viewBox="0 0 1280 720". A renderer traces your strokes with
a hand-drawn marker wobble, so keep shapes simple and confident.

Rules:
- Use ONLY stroked elements: <path>, <line>, <circle>, <ellipse>, <rect>,
  <polyline>. Every element needs stroke and stroke-width (3-6); no text,
  no <g>, no gradients, no transforms.
- Palette: ink #28303f, green #2f7d4f, dark green #256b41, blue #39729e,
  red #b8453c, warm #d9902b, gray #8b909a, brown #7b5233.
- Closed shapes that should be coloured in get data-fill="#hex" — the
  renderer scribble-fills them like a marker.
- The ground line is at y=585; things standing on the ground must touch it.
  The area below y=585 is grass; you may add small ground detail there
  (stones, tufts, fallen leaves) down to y=700.
- Sky and horizon elements (distant hills, far forests, flocks of birds,
  weather) get data-depth="far" — they move slower under the camera for
  parallax. Everything at ground level omits data-depth.
- IMPORTANT: the story's characters act in the center (roughly
  240 < x < 1040, 380 < y < 585). Keep that area clear — put scenery near
  the edges, in the sky, or as small ground detail.
- NEVER draw people, characters, animals with faces, or speech bubbles;
  the animation engine adds those.
- Optional gentle motion via data-anim: "float", "sway:6",
  "drift:12,0,wrap", "pulse:0.08" — use it on 2-4 elements at most.
- 25-60 elements. Respond with ONLY the SVG, no commentary.
"""

_ELEMENT_RE = re.compile(
    r"<(?:path|line|circle|ellipse|rect|polyline)\b[^>]*?/>", re.DOTALL)


def generate_shot_scenery(client, model: str, story_title: str, shot,
                          mood: str) -> Tuple[List[str], List[str]]:
    """Returns (far_elements, near_elements) as raw SVG element strings."""
    props = ", ".join(f"{p.kind}@x={p.x:.0f}" for p in shot.props) or "none"
    lines = [ev.text for ev in shot.events
             if getattr(ev, "text", None)][:3]
    user = (
        f'Story: "{story_title}"\n'
        f"Shot mood/lighting: {mood}\n"
        f"Props already staged by the engine (do not redraw them): {props}\n"
        f"What happens: {' / '.join(lines) if lines else 'wordless action'}\n\n"
        "Draw complementary scenery that makes this shot feel like a "
        "storybook place — terrain, flora, sky detail, distant landscape "
        "matching the mood. Remember: characters act in the center, keep "
        "it clear."
    )
    with client.messages.stream(
        model=model,
        max_tokens=6000,
        system=SCENERY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        text = "".join(stream.text_stream)

    m = re.search(r"<svg[^>]*>(.*)</svg>", text, re.DOTALL)
    if not m:
        raise ValueError("no <svg> found in scenery response")
    far: List[str] = []
    near: List[str] = []
    for el in _ELEMENT_RE.findall(m.group(1)):
        if 'data-depth="far"' in el or "data-depth='far'" in el:
            far.append(el)
        else:
            near.append(el)
    if not far and not near:
        raise ValueError("scenery SVG contained no usable elements")
    return far, near
