"""Canned script + drawings for offline testing (no API key required)."""

from __future__ import annotations

from .script_gen import Scene, VideoScript

DEMO_SCRIPT = VideoScript(
    title="How Photosynthesis Works",
    scenes=[
        Scene(
            label="Powered by the Sun",
            narration=(
                "Every plant on Earth is powered by the same giant engine: the sun. "
                "Sunlight streams down carrying the energy that starts everything."
            ),
            visual_description=(
                "A big smiling sun with wavy rays over rolling hills, with a small "
                "sprout reaching up toward the light."
            ),
        ),
        Scene(
            label="Three Ingredients",
            narration=(
                "A leaf collects three simple ingredients. It soaks up sunlight from "
                "above, pulls in carbon dioxide from the air, and drinks water "
                "brought up from the roots."
            ),
            visual_description=(
                "A large detailed leaf with veins in the center; a small sun with an "
                "arrow, a puffy cloud with an arrow, and water droplets with an arrow "
                "all pointing into the leaf."
            ),
        ),
        Scene(
            label="Sugar and Oxygen",
            narration=(
                "Inside the leaf, those ingredients are transformed into sugar the "
                "plant uses as food, and oxygen is released into the air. That "
                "oxygen is what you are breathing right now."
            ),
            visual_description=(
                "A leaf with an arrow out to a sugar hexagon with a sparkle, oxygen "
                "bubbles rising, and a happy stick figure breathing them in."
            ),
        ),
    ],
)

# Hand-authored line-art SVGs, one per scene, in natural drawing order.
DEMO_SVGS = [
    # Scene 1 — smiling sun with wavy rays over hills, a sprout reaching up
    """<svg viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg">
  <path d="M 640,130 C 730,125 800,195 798,275 C 796,360 725,420 640,418
           C 552,416 485,355 486,272 C 487,193 552,134 640,130 Z"
        fill="none" stroke="#d37c1b" stroke-width="8"/>
  <path d="M 590,240 C 596,232 606,232 612,240" fill="none" stroke="#222" stroke-width="6"/>
  <path d="M 668,240 C 674,232 684,232 690,240" fill="none" stroke="#222" stroke-width="6"/>
  <path d="M 585,320 C 610,352 668,352 694,318" fill="none" stroke="#222" stroke-width="6"/>
  <path d="M 640,95 C 634,72 646,52 638,28"   fill="none" stroke="#d37c1b" stroke-width="6"/>
  <path d="M 748,152 C 764,134 768,116 786,100" fill="none" stroke="#d37c1b" stroke-width="6"/>
  <path d="M 822,270 C 846,266 862,274 888,268" fill="none" stroke="#d37c1b" stroke-width="6"/>
  <path d="M 752,392 C 770,408 776,426 794,440" fill="none" stroke="#d37c1b" stroke-width="6"/>
  <path d="M 530,394 C 512,410 506,428 488,442" fill="none" stroke="#d37c1b" stroke-width="6"/>
  <path d="M 458,272 C 434,268 418,276 392,270" fill="none" stroke="#d37c1b" stroke-width="6"/>
  <path d="M 534,150 C 518,132 514,114 496,98"  fill="none" stroke="#d37c1b" stroke-width="6"/>
  <path d="M 90,600 C 240,520 420,520 560,588 C 600,606 640,610 690,596
           C 830,528 1010,530 1180,606" fill="none" stroke="#222" stroke-width="7"/>
  <path d="M 300,592 L 302,512" fill="none" stroke="#278243" stroke-width="6"/>
  <path d="M 302,540 C 272,536 258,514 252,488 C 282,492 298,510 302,540 Z"
        fill="none" stroke="#278243" stroke-width="6"/>
  <path d="M 302,522 C 332,518 346,496 352,470 C 322,474 306,492 302,522 Z"
        fill="none" stroke="#278243" stroke-width="6"/>
</svg>""",
    # Scene 2 — detailed leaf, three labeled inputs with arrows
    """<svg viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg">
  <path d="M 640,160 C 840,196 912,372 806,486 C 752,542 692,566 640,572
           C 588,566 528,542 474,486 C 368,372 440,196 640,160 Z"
        fill="none" stroke="#278243" stroke-width="8"/>
  <path d="M 640,178 C 636,300 638,430 642,556" fill="none" stroke="#278243" stroke-width="6"/>
  <path d="M 640,262 C 688,282 724,314 748,352" fill="none" stroke="#278243" stroke-width="5"/>
  <path d="M 640,262 C 592,282 556,314 532,352" fill="none" stroke="#278243" stroke-width="5"/>
  <path d="M 641,360 C 686,378 716,406 736,440" fill="none" stroke="#278243" stroke-width="5"/>
  <path d="M 641,360 C 596,378 566,406 546,440" fill="none" stroke="#278243" stroke-width="5"/>
  <path d="M 642,452 C 676,466 698,486 712,508" fill="none" stroke="#278243" stroke-width="5"/>
  <path d="M 642,452 C 608,466 586,486 572,508" fill="none" stroke="#278243" stroke-width="5"/>
  <circle cx="200" cy="150" r="62" fill="none" stroke="#d37c1b" stroke-width="7"/>
  <path d="M 200,66 L 200,38 M 284,150 L 312,150 M 260,90 L 280,70 M 260,210 L 280,230 M 140,90 L 120,70"
        fill="none" stroke="#d37c1b" stroke-width="6"/>
  <path d="M 292,214 C 356,252 414,282 470,306" fill="none" stroke="#d37c1b" stroke-width="7"/>
  <path d="M 470,306 L 416,300 M 470,306 L 442,258" fill="none" stroke="#d37c1b" stroke-width="7"/>
  <path d="M 1005,120 C 1042,104 1088,112 1100,142 C 1132,138 1152,162 1142,186
           C 1156,208 1136,232 1104,230 C 1064,246 1010,238 996,212
           C 962,210 948,180 966,158 C 962,136 980,122 1005,120 Z"
        fill="none" stroke="#6e6e6e" stroke-width="6"/>
  <path d="M 986,262 C 924,300 866,330 810,354" fill="none" stroke="#6e6e6e" stroke-width="7"/>
  <path d="M 810,354 L 864,348 M 810,354 L 838,306" fill="none" stroke="#6e6e6e" stroke-width="7"/>
  <path d="M 208,536 C 188,568 188,594 208,610 C 228,594 228,568 208,536 Z"
        fill="none" stroke="#1a6fb0" stroke-width="6"/>
  <path d="M 282,570 C 266,596 266,616 282,630 C 298,616 298,596 282,570 Z"
        fill="none" stroke="#1a6fb0" stroke-width="6"/>
  <path d="M 330,540 C 396,528 462,516 520,502" fill="none" stroke="#1a6fb0" stroke-width="7"/>
  <path d="M 520,502 L 470,522 M 520,502 L 464,488" fill="none" stroke="#1a6fb0" stroke-width="7"/>
</svg>""",
    # Scene 3 — leaf producing sugar + oxygen, stick figure breathing
    """<svg viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg">
  <path d="M 340,220 C 480,246 532,372 456,456 C 416,498 372,516 336,520
           C 300,516 256,498 216,456 C 140,372 200,246 340,220 Z"
        fill="none" stroke="#278243" stroke-width="8"/>
  <path d="M 338,236 C 334,326 336,424 340,506" fill="none" stroke="#278243" stroke-width="5"/>
  <path d="M 338,310 C 372,326 396,350 412,378 M 338,310 C 304,326 280,350 264,378"
        fill="none" stroke="#278243" stroke-width="5"/>
  <path d="M 339,400 C 368,414 386,432 398,454 M 339,400 C 310,414 292,432 280,454"
        fill="none" stroke="#278243" stroke-width="5"/>
  <path d="M 480,368 C 540,366 600,364 656,362" fill="none" stroke="#222" stroke-width="7"/>
  <path d="M 656,362 L 606,340 M 656,362 L 608,388" fill="none" stroke="#222" stroke-width="7"/>
  <path d="M 700,330 L 760,296 L 822,330 L 822,398 L 760,432 L 700,398 Z"
        fill="none" stroke="#c0392b" stroke-width="7"/>
  <path d="M 760,296 L 760,432 M 700,330 L 822,398 M 822,330 L 700,398"
        fill="none" stroke="#c0392b" stroke-width="4"/>
  <path d="M 856,270 L 856,242 M 842,256 L 870,256" fill="none" stroke="#d37c1b" stroke-width="5"/>
  <circle cx="420" cy="252" r="20" fill="none" stroke="#1a6fb0" stroke-width="6"/>
  <circle cx="474" cy="192" r="15" fill="none" stroke="#1a6fb0" stroke-width="6"/>
  <circle cx="540" cy="140" r="11" fill="none" stroke="#1a6fb0" stroke-width="5"/>
  <circle cx="614" cy="104" r="8"  fill="none" stroke="#1a6fb0" stroke-width="5"/>
  <circle cx="1010" cy="180" r="46" fill="none" stroke="#222" stroke-width="7"/>
  <path d="M 994,172 L 998,176 M 1026,172 L 1030,176" fill="none" stroke="#222" stroke-width="5"/>
  <path d="M 992,200 C 1002,210 1020,210 1030,200" fill="none" stroke="#222" stroke-width="5"/>
  <path d="M 1010,226 L 1010,384" fill="none" stroke="#222" stroke-width="7"/>
  <path d="M 1010,270 C 976,290 950,310 934,332 M 1010,270 C 1044,290 1070,310 1086,332"
        fill="none" stroke="#222" stroke-width="7"/>
  <path d="M 1010,384 C 992,420 976,452 962,478 M 1010,384 C 1028,420 1044,452 1058,478"
        fill="none" stroke="#222" stroke-width="7"/>
  <path d="M 862,150 C 886,142 904,148 918,160 M 872,178 C 894,172 910,176 922,186"
        fill="none" stroke="#1a6fb0" stroke-width="5"/>
</svg>""",
]
