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
- Every element: fill="none", stroke, stroke-width 3-8 (thick 6-8 for main
  outlines, thin 3-4 for interior detail and shading). Palette: near-black
  "#222" for main outlines plus 2-4 supporting colors from
  {"#c0392b", "#1a6fb0", "#278243", "#d37c1b", "#6c3c9e", "#7a4a22", "#6e6e6e"}
  used meaningfully (sun = orange, water = blue, plant = green, wood = brown).
- Draw a RICH, ELEGANT illustration: aim for 60-130 strokes. Build it in
  layers like an illustrator would:
  1. One large, detailed main subject with interior detail (features, veins,
     panels, windows, spokes — whatever fits the subject).
  2. 3-6 supporting elements that set the scene (ground line, clouds, tools,
     small figures, secondary objects, foreground dressing like grass or
     small props that add depth).
  3. Shading: groups of 3-6 short parallel hatch lines (thin, width 3) on the
     shadow side of major shapes, plus a few short horizontal contact-shadow
     dashes under grounded objects — this makes drawings look finished.
  4. Arrows, motion lines, sparkles, or labels-as-icons last.
- Elegance comes from deliberate line-weight hierarchy and restraint:
  thick (7-8) confident outer contours, medium (5) secondary shapes, thin
  (3-4) interior detail and shading. Echo a large outline with a thin inner
  ring or double line where it adds sophistication. Give every grounded
  object a visual anchor (shadow, mound, or overlap with the ground line) so
  nothing floats. Prefer a few well-placed details over uniform clutter, and
  keep generous empty space around the composition's focal point.
- Pack several pen-lifts into one <path> using multiple "M" subpaths (great
  for hatching, rain, rays); the renderer lifts the pen between them.
- COLOUR THINGS IN: add data-fill="#hex" to closed shapes and the renderer
  fills them with a soft marker-scribble tint once the outline completes.
  Use it on the major shapes (sun disc, foliage, bodies, roofs, objects) —
  a mostly-coloured drawing looks dramatically more finished than pure line
  art. Pick the fill from the same palette as the stroke (the renderer
  lightens it automatically). Leave small details and hatching unfilled.
- Prefer organic, slightly wavy cubic curves ("C") over ruler-straight lines
  and perfect symmetry — it should feel drawn by a person, not a plotter.
  Faces, stick figures, and expressive cartoon detail read very well.
- Order the elements in the order a person would naturally draw them:
  main subject outline -> its interior detail -> supporting elements ->
  shading -> arrows last.
- Compose deliberately: main subject roughly centered or on one side with
  supporting elements balancing it. Keep everything inside x=[80,1200],
  y=[60,600] (the bottom strip is reserved for a caption).

Motion (optional but encouraged, 2-6 moving things): after the drawing is
complete, elements tagged with a data-anim attribute come alive:
  data-anim="float[:amp]"        gentle bobbing (bubbles, clouds, boats)
  data-anim="drift:dx,dy"        slow continuous glide in px/s (clouds, birds)
  data-anim="drift:dx,dy,wrap"   looping motion that resets after `wrap` px
                                 (falling rain, rising bubbles, smoke)
  data-anim="spin[:period_s]"    slow rotation about its center (sun rays,
                                 gears, wheels, orbiting moons)
  data-anim="sway[:deg]"         pendulum sway about its base (plants, trees,
                                 flames, antennas)
  data-anim="pulse[:amp]"        gentle scale beat (sun, hearts, sparkles,
                                 highlights)
Notes: spin/sway/pulse rotate or scale the WHOLE element about one pivot, so
put everything that should move together into ONE <path> using multiple "M"
subpaths. drift/float are pure translations, so separate elements with the
same parameters move in perfect sync. Animate meaningful things: rain falls,
smoke rises, wheels spin — don't animate ground lines or arrows.

You may also add a walking stick figure (drawn standing, then it walks):
  <walker x="200" y="560" to-x="900" scale="1" stroke="#222"/>
where x/to-x are the start/end positions and y is the ground level of its
feet. Use it when a person walking, arriving, or leaving fits the story.
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
