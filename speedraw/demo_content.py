"""Canned script + drawings for offline testing (no API key required)."""

from __future__ import annotations

from .script_gen import Scene, VideoScript

DEMO_SCRIPT = VideoScript(
    title="How Photosynthesis Works",
    scenes=[
        Scene(
            label="The Sun",
            narration=(
                "Every plant on Earth is powered by the same giant engine: the sun. "
                "Sunlight streams down carrying the energy that starts everything."
            ),
            visual_description="A big sun with rays shining down toward the ground.",
        ),
        Scene(
            label="The Ingredients",
            narration=(
                "A leaf collects three simple ingredients. It soaks up sunlight from "
                "above, pulls in carbon dioxide from the air, and drinks water "
                "brought up from the roots."
            ),
            visual_description=(
                "A large leaf in the center with three arrows pointing into it."
            ),
        ),
        Scene(
            label="The Payoff",
            narration=(
                "Inside the leaf, those ingredients are transformed into sugar the "
                "plant uses as food, and oxygen is released into the air. That "
                "oxygen is what you are breathing right now."
            ),
            visual_description=(
                "A leaf with an arrow out to a hexagon (sugar) and rising bubbles (oxygen)."
            ),
        ),
    ],
)

# Hand-authored line-art SVGs, one per scene, in drawing order.
DEMO_SVGS = [
    # Scene 1 — sun with rays over the ground
    """<svg viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg">
  <circle cx="640" cy="270" r="130" fill="none" stroke="#d37c1b" stroke-width="7"/>
  <line x1="640" y1="80"  x2="640" y2="30"  stroke="#d37c1b" stroke-width="6" fill="none"/>
  <line x1="640" y1="460" x2="640" y2="520" stroke="#d37c1b" stroke-width="6" fill="none"/>
  <line x1="450" y1="270" x2="390" y2="270" stroke="#d37c1b" stroke-width="6" fill="none"/>
  <line x1="830" y1="270" x2="890" y2="270" stroke="#d37c1b" stroke-width="6" fill="none"/>
  <line x1="505" y1="135" x2="465" y2="95"  stroke="#d37c1b" stroke-width="6" fill="none"/>
  <line x1="775" y1="135" x2="815" y2="95"  stroke="#d37c1b" stroke-width="6" fill="none"/>
  <line x1="505" y1="405" x2="465" y2="445" stroke="#d37c1b" stroke-width="6" fill="none"/>
  <line x1="775" y1="405" x2="815" y2="445" stroke="#d37c1b" stroke-width="6" fill="none"/>
  <path d="M 120,620 C 350,590 930,590 1160,620" fill="none" stroke="#111" stroke-width="6"/>
  <path d="M 560,560 C 580,500 700,500 720,560" fill="none" stroke="#278243" stroke-width="6"/>
</svg>""",
    # Scene 2 — leaf with three inputs
    """<svg viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg">
  <path d="M 640,180 C 860,220 900,460 640,560 C 380,460 420,220 640,180 Z"
        fill="none" stroke="#278243" stroke-width="7"/>
  <path d="M 640,200 L 640,540" fill="none" stroke="#278243" stroke-width="5"/>
  <path d="M 640,300 L 730,350 M 640,300 L 550,350 M 640,420 L 720,460 M 640,420 L 560,460"
        fill="none" stroke="#278243" stroke-width="4"/>
  <path d="M 250,140 L 430,240" fill="none" stroke="#d37c1b" stroke-width="7"/>
  <path d="M 430,240 L 380,225 M 430,240 L 420,190" fill="none" stroke="#d37c1b" stroke-width="7"/>
  <path d="M 1030,180 L 860,270" fill="none" stroke="#6e6e6e" stroke-width="7"/>
  <path d="M 860,270 L 915,265 M 860,270 L 895,225" fill="none" stroke="#6e6e6e" stroke-width="7"/>
  <path d="M 300,620 L 480,540" fill="none" stroke="#1a6fb0" stroke-width="7"/>
  <path d="M 480,540 L 425,545 M 480,540 L 450,585" fill="none" stroke="#1a6fb0" stroke-width="7"/>
  <circle cx="250" cy="640" r="26" fill="none" stroke="#1a6fb0" stroke-width="6"/>
</svg>""",
    # Scene 3 — leaf producing sugar (hexagon) and oxygen (bubbles)
    """<svg viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg">
  <path d="M 380,260 C 560,290 590,470 380,550 C 170,470 200,290 380,260 Z"
        fill="none" stroke="#278243" stroke-width="7"/>
  <path d="M 380,280 L 380,530" fill="none" stroke="#278243" stroke-width="5"/>
  <path d="M 560,400 L 760,400" fill="none" stroke="#111" stroke-width="7"/>
  <path d="M 760,400 L 715,375 M 760,400 L 715,425" fill="none" stroke="#111" stroke-width="7"/>
  <path d="M 900,330 L 970,290 L 1040,330 L 1040,410 L 970,450 L 900,410 Z"
        fill="none" stroke="#c0392b" stroke-width="7"/>
  <circle cx="500" cy="210" r="22" fill="none" stroke="#1a6fb0" stroke-width="6"/>
  <circle cx="570" cy="150" r="16" fill="none" stroke="#1a6fb0" stroke-width="6"/>
  <circle cx="640" cy="100" r="11" fill="none" stroke="#1a6fb0" stroke-width="5"/>
</svg>""",
]
