# Graphical-Abstract Prompt — Phase C Geometry Fix-Batch

> Paste the prompt block below into a web-based image-generation LLM (e.g. GPT-image, Gemini, Midjourney-style).
> Companion to `PLAN_phaseC_geometry_fixbatch.md`. The concept: real-world building footprints have
> awkward shapes that break the "core + perimeter" zone-slicing step; our fix detects each failure and
> **gracefully falls back to a simple "one room per floor" model** so every building still simulates.

---

## PRIMARY PROMPT (full graphical abstract)

```
=== ABSOLUTE TEXT-RENDERING RULE (read first, applies to the whole image) ===
The ONLY words that may appear as visible text in the generated image are the strings I have wrapped
in "double quotes" below. Every other line in this prompt is a DRAWING INSTRUCTION describing what to
depict, NOT text to write on the figure. If a phrase is not inside double quotes, it is a direction,
not a caption — do not draw it.
- Two column-header words ARE wanted and should be drawn once, centered over the middle block:
  "BEFORE" (over the amber half) and "AFTER" (over the green half). These are the ONLY headers.
- Do NOT draw any of these meta words anywhere: "left", "right", "column", "panel", "row", "T02",
  "T03", "T04", "T05", "T07", "Style notes", or any parenthetical guidance.
- The closing style-notes paragraph is guidance for you only — it must NOT appear in the image.

A clean, modern scientific GRAPHICAL ABSTRACT, flat vector infographic style, white background,
soft drop shadows, isometric 3D building blocks, a restrained palette of slate-blue, teal,
warm amber for warnings, and green for success. Crisp thin labels in a sans-serif font.
Title at top center: "Robust Geometry Repair for Urban Building Energy Models".
Subtitle: "Weird footprints break core/perimeter zoning → fall back to one-room-per-floor → every building simulates".

LAYOUT: a single left-to-right pipeline with a vertical stack of 5 problem/solution rows in the middle.

[Far-left panel] The only heading text drawn here is "INPUT: real city footprints". Do NOT write the
words "left", "column", or "panel" anywhere in the image. Depict an isometric cluster of varied
building footprints pulled from a city map, a few of them highlighted in amber to mark them as
problematic shapes.

CENTER — 5 stacked rows, each row showing a small BEFORE (amber, cracked/red-X) and AFTER (green, check):

Row 1 (T02) — "Multi-part blob":
BEFORE: a building footprint split into two disconnected chunks (a MultiPolygon) with a red crack and a "crash" spark icon.
AFTER: only the LARGEST chunk kept, outlined green, a small flag/tag icon labeled "flagged", arrow to a clean single block.

Row 2 (T03) — "Library error before the safety net":
BEFORE: a gear/geometry-engine icon emitting an error bolt that bypasses a small shield labeled "existing guard".
AFTER: the error caught inside a try/except bracket box, arrow to a simple block sliced into flat horizontal floors ("one room per floor"), green check.

Row 3 (T04) — "Sliver slice":
BEFORE: a footprint cut into a CENTER zone (label the full word "center" clearly — never truncated to "cente") plus edge zones, where one edge zone is a razor-thin triangular SLIVER (0.06 m²) highlighted red, with a tiny "negative / inside-out" flip symbol.
AFTER: two new magnifying-glass detector icons labeled "area < 0.5 m²?" and "inside-out?", arrow to the building rebuilt as flat horizontal floors, green check.

Row 4 (T05) — "Mismatched surfaces":
BEFORE: depict two stacked flat surfaces that are meant to align but clearly do NOT — draw the top
surface with 12 corner-dots and the bottom surface with 11 corner-dots so the counts visibly differ.
Mark amber with a red X. The ONLY text drawn in this BEFORE cell is exactly the label "12 vs 11"
(do NOT write any other words here — no "should", "align", "different", "number of corners", or any
sentence; those are descriptions for you, not captions). Never label the counts as equal (no
"12 vs 12" / "11 vs 11").
AFTER: the building rerouted to clean flat horizontal floor slabs, green check. The ONLY text drawn
in this AFTER cell is exactly the caption "kept, not dropped" (no other words).

Row 5 (T07) — "Repair that only shaves":
BEFORE: a building with a tiny shaver/eraser icon nibbling one surface but the building still broken (red), red X.
AFTER: the same building rebuilt as clean flat horizontal floor slabs, green check. The caption under the AFTER building must read EXACTLY this grammatical sentence and nothing else: "now also falls back to flat floors" (do NOT write fragments like "upgrade horizontal floors").

[Far-right panel] The only heading text drawn here is "OUTPUT: 12-cell simulation, zero buildings
excluded". Do NOT write the words "right", "column", or "panel" anywhere in the image. Depict an
isometric city block fully rendered in green with a small energy/heat-map glow, a large green
checkmark badge labeled "100% simulated", and a tiny caption
"coarser model on a handful of odd buildings, negligible effect on city totals".

A unifying banner along the bottom reading:
"ONE PRINCIPLE: any degenerate shape → degrade gracefully to one-room-per-floor, never crash, never drop."

(Style notes — RENDERING GUIDANCE ONLY, do NOT draw any of these words in the image:
infographic / journal graphical-abstract aesthetic, no photorealism, no clutter,
generous whitespace, consistent icon weight, legible at thumbnail size, 16:9 landscape.)
```

---

## ALTERNATE PROMPT (simpler, single-building "before → after" hero image)

```
A minimalist scientific diagram, flat vector style, white background. One isometric 3D building.
LEFT ("BEFORE", amber/red): the building's floorplan sliced into a center zone plus thin perimeter
edge zones, with one edge zone rendered as a broken red razor-thin sliver and a "crash" spark —
labeled "core/perimeter zoning fails on awkward footprints".
A bold central arrow labeled "detect & fall back".
RIGHT ("AFTER", green): the same building rebuilt simply as clean flat horizontal floor slabs,
labeled "one room per floor — always valid". Green checkmark.
Caption underneath: "Graceful degradation: every building still simulates." Clean sans-serif, 16:9.
```

---

## Tips for the image LLM
- If the model crowds the 5 rows, generate the **ALTERNATE** hero image first, then ask for the 5-row version separately and stitch.
- Ask for "editable labels / leave space for text" if you want to relabel T02–T07 yourself afterward.
- Keep the amber = problem, green = fixed convention consistent — it carries the whole story.
- "one room per floor" is the load-bearing visual metaphor (flat horizontal slabs vs. center+edge slicing); make sure that contrast is unmistakable.
- **Verify these in every output (the model tends to slip on text):**
  1. T05 BEFORE reads **"12 vs 11"** — a true mismatch, NOT "12 vs 12"/"11 vs 11".
  2. T05 AFTER shows ONLY **"kept, not dropped"** — no leaked fragment like "SHOULD align but has a DIFFERENT".
  3. T04 spells **"center"** in full, not "cente".
  4. T07 AFTER reads the full sentence **"now also falls back to flat floors"**, not "upgrade horizontal floors".
  5. The words **"LEFT COLUMN" / "RIGHT COLUMN" / "Style notes"** do NOT appear anywhere — only "INPUT:…" and "OUTPUT:…" head those panels.
  6. Only **"BEFORE"** and **"AFTER"** appear as column headers (no "Row", no "T02".. labels).
  If any is wrong, re-prompt with just that element emphasized rather than regenerating the whole figure.
