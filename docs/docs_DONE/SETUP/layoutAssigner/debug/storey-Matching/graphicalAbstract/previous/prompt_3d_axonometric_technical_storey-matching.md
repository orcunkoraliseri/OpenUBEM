# Image-generation prompt — `layout_assign` storey matching (Q3): hybrid annotated axonometric

**Source document:** `../PLAN_storey-matching_implementation.md`
**Style:** §2.3 of `docs/docs_EXPLANATION/OpenUBEM_graphic_summary_prompt_styles.md` — hybrid
annotated axonometric (realistic 3D render + full technical annotation layer).
**Tool:** Gemini web (or any comparable image model). Paste §"Prompt to paste" below **as-is**.
**Date:** 2026-07-26 · **Status of the work it depicts:** plan written, **not started**.

---

## What this image is for

Unlike the arc's general abstract (`../../../general-abstract/`), which explains *what
`layout_assign` does*, this graphic exists to make one **defect and its fix** legible at a glance —
because the defect is *geometric*, and a table of EUI numbers cannot show a 79 m² building rendered
as a 4-storey sliver.

It must carry the whole situation, honestly: the current behaviour, the one-line root cause, the
fix, **and** the three things that are still unknown or unpaid-for. A graphic that showed only the
fix would be a sales pitch, not a summary.

**Accent colour is deliberately different** from the arc's general abstract (which uses warm amber).
This one uses a single **cool teal** accent, so the two images are never confused: amber = "how the
mode works", teal = "what was wrong with it and what changes".

**Every quoted number below is traceable** to `PLAN_storey-matching_implementation.md` §4 (F-01 …
F-09). Do not substitute rounder or more impressive figures when regenerating.

---

## Prompt to paste

Create a single wide realistic 3D axonometric (isometric) architectural illustration in the style of an annotated engineering cutaway diagram — photorealistic materials, soft studio lighting, gentle contact shadows, neutral pale-gray background — overlaid with a full layer of thin precise leader-lines connecting elements to small rectangular technical annotation cards (white card, thin dark border, small clean monospace-style text, like index cards pinned into the scene). The illustration must work simultaneously as a realistic 3D rendering AND as a dense technical reference sheet. Do not simplify or shorten any quoted label.

Compose it as one continuous horizontal sequence of five connected vignettes, read left to right, each on its own small floating ground plane, linked by a thin cool-teal ribbon path. All five vignettes share the same camera angle, lighting, and material palette: soft neutral grays and warm concrete tones, with a single cool teal accent used consistently for every ribbon, leader-line, and card border — teal is never used decoratively.

**Vignette 1 — the real building (ground truth):** a small, low, wide two-storey residential building on a modest urban plot, modeled in warm realistic concrete and glass, correct and unremarkable in proportion. Neighbouring context buildings faded translucent gray. A leader-line points to a technical card reading exactly: "REAL BUILDING — footprint_area × num_floors = 79 m² total · 2 storeys · archetype = MidriseApartment".

**Vignette 2 — what the code does today (the defect):** the same building replaced by a tall, absurdly thin four-storey tower — a sliver — visibly wrong in proportion next to a faint dashed ghost outline of the correct low-wide building from Vignette 1 standing beside it for comparison. The sliver keeps full storey height but a tiny footprint. Render a translucent scaling grid squeezing it inward horizontally only, with horizontal corner arrows and a vertical dimension line marked with a small padlock icon. An engraved acrylic plaque beside it reads exactly: "S = real_area ÷ baseline_area · planar_k = √S applied to X,Y · Z LEFT UNCHANGED". A second white card, connected by a leader-line to the sliver's roof, reads exactly: "prototype keeps its OWN storey count — 4 storeys for a 2-storey building · plan area shrunk to 2.5%". A third card, pinned low near the ground plane, reads exactly: "MEASURED COST — nyc_suburban heating EUI 238.0 vs 118.1 kWh/m²/yr = 2.02× · stable at every size".

**Vignette 3 — the root cause, one line of code:** an abstract but physically-rendered mechanism sitting on the ground plane: two distinct solid metal tokens, one embossed "footprint_area" and one embossed "num_floors", both falling into a polished funnel that fuses them into a single plain metal ball embossed "real_area". Beside the funnel, the "num_floors" token is shown a second time, discarded on the ground, dulled and gray. A leader-line from the funnel to a card reading exactly: "builder.py:447 — real_area = footprint_area * num_floors". A second card below reads exactly: "num_floors is ALREADY at the call site and is thrown away · layout_assigner.py never references levels — the only mode blind to height".

**Vignette 4 — the fix: match storeys, scale the plate:** a clean DOE prototype rendered as an exploded stack of three distinct labeled floor bands separated vertically with visible gaps — bottom band "G", a repeated middle band "M" shown as two translucent identical slices, top band "T". A cool-teal arrow shows one middle "M" slice being lifted out and removed, leaving the stack at two storeys, matching Vignette 1's real building. A horizontal-only scaling grid applies to the floor plate; the vertical dimension line still carries its padlock icon. An engraved plaque reads exactly: "plate_target = real_area ÷ n_real · plate_proto = baseline_area ÷ n_proto · planar_k = √(plate_target ÷ plate_proto)". A card beside the lifted slice reads exactly: "storey HEIGHT stays the prototype's real height · only the storey COUNT and the plate follow the real building". A small realistic glass diamond-shaped plaque floats above, engraved "TALLER OR SHORTER?" with two thin teal paths leaving it: one solid, labeled by a card reading exactly "TALLER → Zone Multiplier on the middle band", one dashed, labeled by a card reading exactly "SHORTER → delete middle band · the COMMON case, median S = 0.054".

**Vignette 5 — verification:** three small identical neighbourhood blocks lined up side by side on one shared ground plane, each rendered as a miniature 3D city viewport with a thin teal frame: the first block low and correctly proportioned, the second block full of thin wrong slivers, the third block low and correct again. Small engraved nameplates under each read exactly, left to right: "REAL massing (auto)", "BEFORE — layout_assign today", "AFTER — storey matched". Above them, connected by a leader-line, a card reading exactly: "C02 — 12-cell / 8,160-building fleet re-run t20_* · sbatch array, ~15 h · target: heating ratio moves toward 1.0".

**Base plaque (bottom, spanning the full width, like a museum-exhibit caption rail):** a long thin horizontal plaque resting beneath all five ground planes, rendered in matte dark slate — a visually distinct material from every bright teal-accented card above, so it unmistakably reads as a footnote rather than a missed detail. Engrave it in small clean text, exactly: "STATUS — plan written, NOT started · no production code exists yet   ·   OPEN RISK 1: every layout_assign EUI number ever produced (T17/T18/T19) is void until the fleet is re-run   ·   OPEN RISK 2: num_floors is partly imputed — this fix converts imputation error into geometry error   ·   OPEN RISK 3: the storey-adjustment mechanism is NOT yet decided; it is measured at checkpoint CP-A, not assumed".

Keep every quoted technical string exactly as written above — do not paraphrase, shorten, reorder, or invent additional labels. Exclude all logos, watermarks, people, vehicles, sky, and background landscape. If the content does not fit the width, shrink card and text size rather than wrapping the vignettes onto a second row or dropping any card. The overall impression should be a realistic architectural illustration precise enough to use as a technical spec sheet — dense with correct text, elegant, not a flat diagram.

---

## Regeneration notes

- **Do not change the step content between iterations** (style-guide §4.4). Iterate only on layout
  and legibility — text size, card placement, ribbon routing.
- **The proportion contrast in Vignettes 1, 2 and 5 is the whole message.** If the model renders the
  "before" sliver as merely a normal narrow tower, the image has failed regardless of how good the
  text looks. Re-prompt with the sliver exaggerated rather than accepting it.
- **The base plaque is not optional.** Depicting the fix without the three open risks would present a
  plan as a result. If the model drops or shortens it, regenerate.
- **Vignette 5's "AFTER" block is a prediction, not a measurement** — it depicts C02's *target*. If
  this graphic is ever reused after C02 lands, the plaque's OPEN RISK 1 must be rewritten to the
  measured outcome, whatever that outcome turns out to be.

## Where the output goes

Save the generated image in this folder, alongside this prompt, named
`<model>_storey-matching_<YYYY-MM-DD>.png` (e.g. `GEMINI_storey-matching_2026-07-26.png`) — matching
the arc convention in `docs_DONE/GENERAL/graphicalAbstract/`. Per §2 and rule 1.11 of the plan,
every artifact of this arc stays under `debug/storey-Matching/`.
