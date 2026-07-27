# Image-generation prompt — `layout_assign` storey matching (Q3): **minimal-text** variant

**Source document:** `../PLAN_storey-matching_implementation.md`
**Style:** §2.3 of `docs/docs_EXPLANATION/OpenUBEM_graphic_summary_prompt_styles.md` — hybrid
annotated axonometric, **with a deliberate deviation:** the annotation layer is reduced to a handful
of very short, very large labels.
**Tool:** Gemini web (or any comparable image model). Paste §"Prompt to paste" below **as-is**.
**Date:** 2026-07-26 · **Status of the work it depicts:** plan written, **not started**.

---

## What this variant is for, and how it differs

This is the **companion** to `prompt_3d_axonometric_technical_storey-matching.md`, not a replacement.
Both describe the same five-step story; they differ only in how much text the image carries.

| | technical variant | **this minimal variant** |
|---|---|---|
| Labels per vignette | 1–3 dense cards, full formulas | **1 headline + 1 number, max** |
| Text size | small, spec-sheet dense | **large, readable at thumbnail size** |
| Formulas (`planar_k = √S …`) | shown verbatim | **removed — carried by the geometry instead** |
| Best for | reading closely, on screen, alone | slides, a printed page, a quick explanation to someone else |

**The reason a minimal version is worth having:** image models degrade badly as text volume rises —
long strings come back misspelled, truncated, or rendered as gibberish. Fewer words means the words
that survive are actually correct. The trade-off is real and one-directional: **this image cannot be
used as a technical reference.** It carries no formula and no call site. If someone needs to know
*how* the fix works, they need the technical variant or the plan itself.

**Same teal accent** as the technical variant, so the pair reads as one family (and stays distinct
from the arc's general abstract, which is amber).

**Honesty constraint, unchanged:** the base plaque still carries the status and the one risk that
would most mislead a reader. Compressing the graphic is allowed; compressing away the caveat is not.
That is why the plaque is the *only* place in this prompt where the text stays long-ish.

---

## Prompt to paste

Create a single wide realistic 3D axonometric (isometric) architectural illustration — photorealistic materials, soft studio lighting, gentle contact shadows, clean pale-gray background — with a very sparse annotation layer: only a few short labels, each rendered LARGE and clearly legible. This image must be readable at a glance from across a room. Prioritize legibility of the few words over density of information.

Compose it as one continuous horizontal sequence of five connected scenes, read left to right, each on its own small floating ground plane, linked by a thin cool-teal ribbon. All five share the same camera angle, lighting, and materials: soft neutral grays and warm concrete tones, with a single cool teal accent used for every ribbon, arrow, and label frame.

**Scene 1 — the real building:** a small, low, WIDE two-storey residential building in warm realistic concrete and glass, correct and unremarkable in proportion, on a modest plot with faded translucent gray neighbours. One large label below it reading exactly: "REAL — 79 m², 2 storeys".

**Scene 2 — what happens today:** the same building replaced by an absurdly THIN, TALL four-storey sliver tower — dramatically, obviously wrong in proportion — standing next to a faint dashed ghost outline of the correct low-wide building from Scene 1. Thin teal arrows squeeze the tower inward horizontally only; a vertical dimension line beside it carries a small padlock icon. One large label below reading exactly: "TODAY — 4 storeys, 2% of the floor plate". One separate large teal number floating beside the tower reading exactly: "2.0× heating".

**Scene 3 — the cause:** a simple physical mechanism on the ground plane — two solid metal tokens, one embossed "footprint_area", one embossed "num_floors", falling into a polished funnel that fuses them into a single plain metal ball. Beside the funnel, a second "num_floors" token lies discarded on the ground, dulled and gray, with a thin teal arrow pointing down at it. One large label below reading exactly: "CAUSE — storeys thrown away".

**Scene 4 — the fix:** a clean building rendered as an exploded stack of separated horizontal floor bands with visible gaps between them; a cool-teal arrow lifts one middle band out and away, leaving a two-storey stack that matches Scene 1. The remaining floor plate is shown widening horizontally, while the vertical dimension line still carries its padlock icon. One large label below reading exactly: "FIX — match storeys, widen the plate".

**Scene 5 — the check:** three small identical neighbourhood blocks side by side on one shared ground plane, each a miniature 3D city viewport in a thin teal frame — the first low and correctly proportioned, the second full of thin wrong slivers, the third low and correct again. Three short engraved nameplates beneath them reading exactly, left to right: "REAL", "BEFORE", "AFTER". One large label below the group reading exactly: "CHECK — 8,160 buildings re-run".

**Base plaque (bottom, spanning the full width):** one long thin horizontal plaque beneath all five ground planes, rendered in matte dark slate — visually distinct from the bright teal labels above so it reads clearly as a footnote. Engrave it in small clean text, exactly: "PLAN ONLY — NOT BUILT YET · every layout_assign energy result so far is void until the fleet is re-run".

Use only the labels quoted above — do not add any other text, callouts, captions, legends, axis labels, or numbers anywhere in the image. Keep each quoted string exactly as written, spelled correctly. Exclude all logos, watermarks, people, vehicles, sky, and background landscape. The overall impression should be a calm, elegant, realistic architectural illustration with very few words — every one of them large and perfectly legible.

---

## Regeneration notes

- **Legibility is the acceptance criterion.** If any label is misspelled, cut off, or too small to read
  in a thumbnail, regenerate. That is the entire point of this variant — a minimal image with broken
  text has no reason to exist, since the technical variant already covers the dense case.
- **Do not let the label set grow.** Each regeneration attempt tends to invite "just one more card".
  If a reader needs more, hand them the technical variant, not a busier version of this one.
- **The proportion contrast in Scenes 1, 2 and 5 carries the message here even more than in the
  technical variant** — there is no explanatory text to fall back on. If the "before" sliver reads as
  merely a narrow tower rather than an absurd one, the image has failed.
- **The base plaque stays.** It is the only thing preventing this graphic from presenting an unbuilt
  plan as a finished result.
- **Scene 5's "AFTER" block is a prediction, not a measurement.** It depicts C02's *target*. If this
  graphic is reused after C02 lands, the plaque must be rewritten to the measured outcome, whatever
  that outcome turns out to be.

## Where the output goes

Save the generated image in this folder, alongside this prompt, named
`<model>_storey-matching_minimal_<YYYY-MM-DD>.png` (e.g. `GEMINI_storey-matching_minimal_2026-07-26.png`)
— the `_minimal` suffix keeps it distinct from the technical variant's output. Per §2 and rule 1.11
of the plan, every artifact of this arc stays under `debug/storey-Matching/`.
