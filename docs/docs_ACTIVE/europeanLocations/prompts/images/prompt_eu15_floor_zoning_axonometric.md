# Image prompt — `EU-15` how a storey is divided into dwelling zones + circulation

**Shows:** the ruled subdivision of one floor plate into residential zones and an unconditioned corridor / stair core.
**Style:** §2.3 hybrid annotated axonometric (`docs/docs_EXPLANATION/OpenUBEM_graphic_summary_prompt_styles.md`).
**Source of the rules:** `rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md` §2 (rules 1–6) and §3.1 ·
`rules/RULES_dwelling_layout_scheme_2026-08-28.html` · `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md` T02–T05.
**Attach alongside the prompt (strongly recommended):** `content/figure_4_2_dwelling_layout_schemes.svg` — the two
schemes in the image must match that figure exactly.

**Revision 2026-08-30** — rewritten after the first render: the two circulation schemes are now the centre of the image,
every label is short, and the duplication / invented-word failures of the first render are forbidden explicitly.

---

## Prompt to paste

Create one wide realistic 3D axonometric (isometric) architectural illustration in the style of an annotated engineering
cutaway — photorealistic materials, soft studio lighting, gentle shadows, neutral pale-gray background — with thin
precise leader-lines to small white rectangular technical cards (thin dark border, small clean uppercase sans-serif
text). It must read as a realistic render **and** as a technical plan reference at once.

**Colour rule, fixed for the whole image and never broken:** conditioned dwelling zones are **light blue** with a
**blue outline**; unconditioned circulation — corridor spine or stair core — is **warm amber** with an **orange
outline**; everything else is neutral concrete grey. A single **teal** accent is used only for connector ribbons and
leader-lines.

Compose it as one continuous horizontal sequence of five vignettes, read left to right, each on its own small floating
ground plane, linked by a thin teal ribbon, all sharing the same camera angle and lighting.

**Vignette 1 — the real plate.** An irregular real-world GIS building footprint slab with notched, noisy edges, and a
faint dashed ghost of a cleaned simplified outline snapped over it. One card: "REGULARISE — 0.15 m". One card: "REFUSE
IF AREA MOVES > 2 %".

**Vignette 2 — morphology.** A small engraved acrylic diamond plaque above the plate reading "MORPHOLOGY?", with four
thin teal ribbons fanning to four small physical model plates, each with one short engraved label beneath it: "POINT
BLOCK", "L-SHAPE", "I-SHAPE SLAB", "COURTYARD". Draw the courtyard plate with a real rectangular hole through it. No
other text in this vignette.

**Vignette 3 — circulation is placed first (the centre of the image, draw it largest).** Two floor plates side by side
on the same ground plane, both seen from directly above-oblique so the plan is fully readable:
- Left plate, labelled underneath "POINT BLOCK · 2 × 2": four equal light-blue dwelling rectangles numbered "1", "2",
  "3", "4", arranged two by two around one warm-amber rectangular block at the exact centre of the plate. One card:
  "2–4 PER STOREY → STAIR CORE". One card: "12–25 m² · 6–12 % OF PLATE".
- Right plate, labelled underneath "CORRIDOR SLAB · 3 × 2": one continuous warm-amber corridor band running the full
  length of the plate down its long axis, with three light-blue dwellings numbered "1", "2", "3" along one side of it
  and three numbered "4", "5", "6" along the other. One card: "5+ PER STOREY → CORRIDOR SPINE". One card with a thin
  dimension arrow across the amber band: "1.80 m DOUBLE-LOADED".

**Vignette 4 — how the cuts are found.** One concave L-shaped plate drawn twice, small: on the left a dimmed, greyed-out
version cut into equal-width strips of its bounding box, with one strip empty and a small red cross over it; on the
right the same plate cut into six light-blue cells of visibly equal area that follow the real outline, with a small teal
check mark. One card: "EQUAL AREA, NOT EQUAL WIDTH". One card: "DWELLINGS + CIRCULATION = PLATE · 0.00 %". A thin
dimension line on one outer dwelling edge tagged "FACADE ≥ 2.50 m".

**Vignette 5 — the stack and what is emitted.** Five translucent floor slabs stacked upward, each showing the light-blue
and warm-amber plan through it, with the amber core rendered as one solid vertical shaft piercing every slab from the
ground plane to the roof. One card: "CORE EXTRUDED z = 0 → ROOF". One card: "STRATIFY q / (q+1) PER STOREY". One card:
"NEVER REDUCE THE DWELLING COUNT". Beside it, one small dimmed grey building model with a dashed teal branch and a
single card: "REFUSED > 8 PER STOREY".

**Base plaque, bottom, full width, matte dark slate, visually different from the white cards.** Engraved in one line of
small clean text: "RULED GRIDS 1×1 · 2×1 · 2×2 · 3×2 · 4×2 — ceiling 8 dwellings per storey — bar ≥ 95 % of the fleet".

**Rendering hygiene, obey strictly.** Every card listed above appears exactly ONCE in the whole image; never repeat the
same label above and below a vignette. Do not add any card, title or word that is not written above. Spell every string
exactly as given — no invented words, no word repeated twice in a row, no truncation, no placeholder text. If a string
does not fit its card, reduce the font size; never abbreviate, wrap or garble it. Place all cards in a single upper
annotation band, one leader-line each, no crossing lines. No people, no logos, no watermarks, no sky, no landscape.
